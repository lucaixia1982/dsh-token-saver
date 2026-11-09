/**
 * Host half of dsh-token-saver.
 *
 * Two jobs:
 *  1. `agent/pre-step` — rewrite the user instructions that are about to enter the
 *     transcript so they carry fewer redundant tokens. Only lossless edits
 *     (whitespace, duplicated lines/paragraphs, trailing pleasantries); everything
 *     inside code fences and every runtime-context message is left untouched.
 *  2. Account every model call from `session/event` usage, turn that into prompt
 *     cache statistics plus saved tokens / money, and expose it over HTTP for the
 *     sidebar badge.
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { homedir } from 'node:os';

const NAME = 'dsh-token-saver';
const ROUTE = `/plugins/${NAME}/stats`;

const DEFAULTS = {
  enabled: true,
  minGainTokens: 15,
  minGainRatio: 0.04,
  priceCurrency: '¥',
  priceInputMiss: 2,
  priceInputHit: 0.2,
  priceOutput: 3,
  keepRecent: 12,
};

const STORE = join(homedir(), '.dsh', `${NAME}.json`);

/* -------------------------------------------------------------- text slimming */

const FILLERS = new Set([
  '谢谢', '谢谢！', '谢谢!', '谢谢啦', '谢了', '麻烦了', '麻烦你了', '辛苦啦', '辛苦了',
  'thanks', 'thank you', 'thx', 'ok', 'okay', '好的', '收到', '嗯', '嗯嗯',
]);

function isCjk(code) {
  return code > 0x2e80;
}

function estimateTokens(text) {
  if (!text) return 0;
  let cjk = 0;
  let other = 0;
  for (const ch of text) {
    if (isCjk(ch.codePointAt(0))) cjk += 1;
    else other += 1;
  }
  return Math.ceil(cjk + other / 3.5);
}

function slimSegment(segment) {
  let out = segment.replace(/[ \t]+$/gm, '');
  out = out.replace(/[ \t]{3,}/g, '  ');
  out = out.replace(/\n{3,}/g, '\n\n');
  const lines = out.split('\n');
  const kept = [];
  let lastNonEmpty = null;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed !== '' && trimmed === lastNonEmpty) continue;
    if (trimmed !== '') lastNonEmpty = trimmed;
    kept.push(line);
  }
  out = kept.join('\n');
  return out.replace(/\n{2,}$/, '\n');
}

function trimFillerTail(text) {
  const lines = text.split('\n');
  let changed = false;
  while (lines.length > 1) {
    const last = lines[lines.length - 1].trim();
    if (last === '') {
      lines.pop();
      changed = true;
      continue;
    }
    if (FILLERS.has(last.toLowerCase())) {
      lines.pop();
      changed = true;
      continue;
    }
    break;
  }
  const joined = changed ? lines.join('\n') : text;
  // a pleasantry glued to the last sentence ("…直接说结论。谢谢！")
  return joined.replace(
    /([。！？!?.~])\s*(谢谢|谢谢啦|谢了|麻烦了|麻烦你了|辛苦啦|辛苦了|thanks|thank\s*you|thx)[。！!.]*\s*$/i,
    '$1',
  );
}

function dedupeParagraphs(text) {
  const blocks = text.split(/\n{2,}/);
  if (blocks.length < 2) return text;
  const seen = new Set();
  const kept = [];
  let changed = false;
  for (const block of blocks) {
    const key = block.trim();
    if (key.length >= 60) {
      if (seen.has(key)) {
        changed = true;
        continue;
      }
      seen.add(key);
    }
    kept.push(block);
  }
  return changed ? kept.join('\n\n') : text;
}

function slimText(text) {
  if (typeof text !== 'string' || text.length < 80) return text;
  const parts = text.replace(/\r\n/g, '\n').split(/(```[\s\S]*?```)/);
  for (let i = 0; i < parts.length; i += 2) {
    parts[i] = dedupeParagraphs(slimSegment(parts[i]));
  }
  const last = parts.length - 1;
  if (last % 2 === 0) parts[last] = trimFillerTail(parts[last]);
  return parts.join('');
}

/** Rewrites the text blocks of one UserMessage. Returns null when nothing improves. */
function slimMessage(message) {
  if (!message || message.source?.kind === 'runtime-context') return null;
  if (!Array.isArray(message.content)) return null;
  let before = 0;
  let after = 0;
  let changed = false;
  const content = message.content.map((block) => {
    if (!block || block.type !== 'text' || typeof block.text !== 'string') return block;
    const next = slimText(block.text);
    if (next === block.text) return block;
    const from = estimateTokens(block.text);
    const to = estimateTokens(next);
    if (from - to < 1) return block;
    before += from;
    after += to;
    changed = true;
    return { ...block, text: next };
  });
  if (!changed) return null;
  return { message: { ...message, content }, before, gain: before - after };
}

/* ------------------------------------------------------------------- accounts */

function emptyTotals() {
  return { calls: 0, miss: 0, hit: 0, output: 0, savedTokens: 0, rewrites: 0, slimmed: 0, seriesStarts: 0 };
}

function sessionIdOf(payload) {
  const agent = payload?.agent;
  return agent?.session?.id ?? agent?.id ?? 'unknown';
}

export function apply(ctx, config) {
  const cfg = { ...DEFAULTS, ...(config && typeof config === 'object' ? config : {}) };
  const log = (msg, error) => {
    try {
      if (error) ctx.logger?.warn?.(`[${NAME}] ${msg}`, error);
      else ctx.logger?.debug?.(`[${NAME}] ${msg}`);
    } catch {
      /* logging must never break a turn */
    }
  };

  const totals = emptyTotals();
  const sessions = new Map();
  const open = new Map();
  const recent = [];
  const clients = new Map();
  let rewriteSeq = 0;
  let dirty = false;
  let lastSessionId = 'unknown';

  // restore aggregates so the sidebar does not restart from zero every launch
  try {
    const saved = JSON.parse(readFileSync(STORE, 'utf8'));
    if (saved && saved.version === 1) {
      const restored = saved.totals || {};
      // version 1 stored the miss count under `input`, before cache reads were split out
      if (restored.input !== undefined && restored.miss === undefined) restored.miss = restored.input;
      delete restored.input;
      Object.assign(totals, restored);
      if (Array.isArray(saved.recent)) recent.push(...saved.recent.slice(-cfg.keepRecent));
      rewriteSeq = Number(saved.rewriteSeq) || 0;
      if (saved.sessions && typeof saved.sessions === 'object') {
        for (const [id, block] of Object.entries(saved.sessions)) {
          if (!block || typeof block !== 'object') continue;
          const entry = emptyTotals();
          const copy = { ...block };
          if (copy.input !== undefined && copy.miss === undefined) copy.miss = copy.input;
          delete copy.input;
          Object.assign(entry, copy);
          sessions.set(id, entry);
        }
      }
      if (typeof saved.lastSessionId === 'string' && saved.lastSessionId) lastSessionId = saved.lastSessionId;
    }
  } catch {
    /* first run */
  }

  function flush() {
    if (!dirty) return;
    dirty = false;
    try {
      mkdirSync(dirname(STORE), { recursive: true });
      writeFileSync(
        STORE,
        JSON.stringify({
          version: 1,
          totals,
          recent,
          rewriteSeq,
          lastSessionId,
          sessions: Object.fromEntries([...sessions].slice(-20)),
        }),
        'utf8',
      );
    } catch (error) {
      log('cannot persist statistics', error);
    }
  }

  function sessionTotals(id) {
    let entry = sessions.get(id);
    if (!entry) {
      entry = emptyTotals();
      sessions.set(id, entry);
      if (sessions.size > 64) {
        const oldest = sessions.keys().next().value;
        if (oldest !== id) sessions.delete(oldest);
      }
    }
    return entry;
  }

  function recordRewrite(sessionId, before, gain) {
    rewriteSeq += 1;
    lastSessionId = sessionId;
    totals.rewrites += 1;
    totals.slimmed += gain;
    dirty = true;
    const id = `r${rewriteSeq}`;
    open.set(id, { sessionId, delta: gain });
    if (open.size > 400) {
      const oldest = open.keys().next().value;
      open.delete(oldest);
    }
  }

  function recordCall(sessionId, usage) {
    // usage.inputTokens is the cache-MISS portion only; cache reads are reported apart
    lastSessionId = sessionId;
    const miss = Number(usage.inputTokens) || 0;
    const hit = Number(usage.cacheReadTokens) || 0;
    const output = Number(usage.outputTokens) || 0;
    totals.calls += 1;
    totals.miss += miss;
    totals.hit += hit;
    totals.output += output;
    const own = sessionTotals(sessionId);
    own.calls += 1;
    own.miss += miss;
    own.hit += hit;
    own.output += output;
    // every slimmer message stays in the request prefix for the rest of the session,
    // so each following call re-saves its tokens.
    let saved = 0;
    for (const entry of open.values()) {
      // an unresolved owner counts for every session so the metric never silently reads 0
      if (entry.sessionId !== sessionId && entry.sessionId !== 'unknown') continue;
      saved += entry.delta;
    }
    if (saved > 0) {
      totals.savedTokens += saved;
      own.savedTokens += saved;
    }
    dirty = true;
  }

  function figures(t) {
    const missPrice = Number(cfg.priceInputMiss) || 0;
    const hitPrice = Number(cfg.priceInputHit) || 0;
    const outputPrice = Number(cfg.priceOutput) || 0;
    const totalInput = t.miss + t.hit;
    const hitRate = totalInput > 0 ? t.hit / totalInput : 0;
    const blendedInput = totalInput > 0 ? (t.miss * missPrice + t.hit * hitPrice) / totalInput : missPrice;
    const cacheBenefit = (t.hit / 1e6) * (missPrice - hitPrice);
    const spent = (t.miss * missPrice + t.hit * hitPrice + t.output * outputPrice) / 1e6;
    return {
      calls: t.calls,
      inputTokens: totalInput,
      cacheReadTokens: t.hit,
      outputTokens: t.output,
      cacheHitRate: hitRate,
      estimatedSpend: spent,
      estimatedCacheBenefit: cacheBenefit,
      seriesStarts: t.seriesStarts,
      savedTokens: t.savedTokens,
      savedMoney: (t.savedTokens / 1e6) * blendedInput,
      blendedInput,
    };
  }

  function snapshot() {
    const missPrice = Number(cfg.priceInputMiss) || 0;
    const hitPrice = Number(cfg.priceInputHit) || 0;
    const outputPrice = Number(cfg.priceOutput) || 0;
    const all = figures(totals);
    const own = figures(sessionTotals(lastSessionId));
    return {
      name: NAME,
      enabled: cfg.enabled,
      currency: cfg.priceCurrency,
      prices: { inputMiss: missPrice, inputHit: hitPrice, output: outputPrice },
      totals: {
        calls: all.calls,
        inputTokens: all.inputTokens,
        cacheReadTokens: all.cacheReadTokens,
        outputTokens: all.outputTokens,
        cacheHitRate: all.cacheHitRate,
        estimatedSpend: all.estimatedSpend,
        estimatedCacheBenefit: all.estimatedCacheBenefit,
        seriesStarts: all.seriesStarts,
      },
      saved: {
        tokens: totals.savedTokens,
        slimmedTokens: totals.slimmed,
        money: all.savedMoney,
        rewrittenMessages: totals.rewrites,
      },
      session: {
        id: lastSessionId,
        calls: own.calls,
        inputTokens: own.inputTokens,
        cacheReadTokens: own.cacheReadTokens,
        outputTokens: own.outputTokens,
        cacheHitRate: own.cacheHitRate,
        estimatedSpend: own.estimatedSpend,
        estimatedCacheBenefit: own.estimatedCacheBenefit,
        savedTokens: own.savedTokens,
        savedMoney: own.savedMoney,
      },
      recent: recent.slice(-cfg.keepRecent).reverse(),
      clients: Object.fromEntries(clients),
      generatedAt: new Date().toISOString(),
    };
  }

  /* ------------------------------------------------------------- pre-step hook */

  ctx.on('agent/pre-step', async (payload, next) => {
    const decision = await next();
    if (!cfg.enabled) return decision;
    if (!decision || decision.kind !== 'enter' || !Array.isArray(decision.messages)) return decision;
    let touched = false;
    const messages = decision.messages.map((message) => {
      let slim = null;
      try {
        slim = slimMessage(message);
      } catch (error) {
        log('slimming failed, keeping the original message', error);
        return message;
      }
      if (!slim) return message;
      if (slim.gain < cfg.minGainTokens) return message;
      if (slim.before > 0 && slim.gain / slim.before < cfg.minGainRatio) return message;
      touched = true;
      recordRewrite(sessionIdOf(payload), slim.before, slim.gain);
      if (recent.length >= cfg.keepRecent) recent.shift();
      recent.push({
        at: new Date().toISOString(),
        before: slim.before,
        after: slim.before - slim.gain,
        gain: slim.gain,
      });
      return slim.message;
    });
    if (!touched) return decision;
    // spread the decision so startsRequestSeries and anything else the loop attached survive
    return { ...decision, messages };
  });

  /* --------------------------------------------------------- usage accounting */

  ctx.on('session/event', (session, event) => {
    try {
      if (!event) return;
      if (event.type === 'request/header') {
        // a new request series drops the reusable prefix, so every one of them is a
        // cache miss waiting to happen; counting them keeps the ratio explainable
        if (event.data?.startsSeries) {
          totals.seriesStarts += 1;
          dirty = true;
        }
        return;
      }
      if (event.type !== 'assistant/message') return;
      const usage = event.data?.usage;
      if (!usage) return;
      recordCall(session?.id ?? 'unknown', usage);
    } catch (error) {
      log('usage accounting failed', error);
    }
  });

  /* --------------------------------------------------------------- web route */

  const webServer = ctx.get('webServer');
  if (!webServer || typeof webServer.register !== 'function') {
    log('webServer service is unavailable; sidebar statistics will stay empty');
  } else {
    ctx.effect(() => webServer.register({
      kind: 'exact',
      path: ROUTE,
      handler: (req, res) => {
        try {
          const clientVersion = req.headers['x-token-saver-client'];
          if (typeof clientVersion === 'string' && clientVersion) {
            clients.set(clientVersion, (clients.get(clientVersion) || 0) + 1);
          }
          const body = JSON.stringify(snapshot());
          res.statusCode = 200;
          res.setHeader('content-type', 'application/json; charset=utf-8');
          res.setHeader('cache-control', 'no-store');
          res.end(body);
        } catch (error) {
          res.statusCode = 500;
          res.end('{"error":"stats unavailable"}');
          log('stats route failed', error);
        }
      },
    }));
  }

  ctx.effect(() => {
    const timer = setInterval(flush, 5000);
    return () => {
      clearInterval(timer);
      flush();
    };
  });

  flush();
}

export { slimText, estimateTokens };
