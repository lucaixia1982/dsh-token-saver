/**
 * Client half of dsh-token-saver: a compact badge beside the shipped sidebar footer
 * entries. It only reads `/plugins/dsh-token-saver/stats` from the same origin; the
 * host half owns every number.
 */
window.__ModuleLoader__.load({
  id: 'dsh-token-saver',
  factory(require) {
    const React = require('react');
    const h = React.createElement;

    // Sent with every poll so the host can tell which client build is live.
    const CLIENT_VERSION = '7';

    function shortTokens(value) {
      const n = Number(value) || 0;
      if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
      if (n >= 1e3) return (n / 1e3).toFixed(1) + 'k';
      return String(Math.round(n));
    }

    function money(value, currency) {
      const n = Number(value) || 0;
      if (n >= 1) return currency + n.toFixed(2);
      if (n >= 0.01) return currency + n.toFixed(3);
      if (n > 0) return currency + n.toFixed(4);
      return currency + '0';
    }

    function percent(value) {
      const n = Number(value) || 0;
      return (n * 100).toFixed(n > 0.995 ? 0 : 1) + '%';
    }

    function useStats() {
      const [stats, setStats] = React.useState(null);
      React.useEffect(() => {
        let alive = true;
        const load = () => {
          let signal;
          try {
            signal = AbortSignal.timeout(4000);
          } catch {
            signal = undefined;
          }
          fetch('/plugins/dsh-token-saver/stats', {
            credentials: 'same-origin',
            headers: { accept: 'application/json', 'x-token-saver-client': CLIENT_VERSION },
            signal,
          })
            .then((response) => (response.ok ? response.json() : null))
            .then((payload) => {
              if (alive && payload) setStats(payload);
            })
            .catch(() => {
              /* the host may not be ready yet; the next poll retries */
            });
        };
        load();
        const timer = setInterval(load, 5000);
        return () => {
          alive = false;
          clearInterval(timer);
        };
      }, []);
      return stats;
    }

    function normalize(stats) {
      const totals = stats.totals || {};
      const saved = stats.saved || {};
      const prices = stats.prices || {};
      const missPrice = Number(prices.inputMiss) || 0;
      const hitPrice = Number(prices.inputHit) || 0;
      const outputPrice = Number(prices.output) || 0;

      // `inputTokens` means "all input" once cache reads are folded in; older payloads
      // report the cache-miss part alone, which shows up as hit > input.
      const read = (block, savedTokens) => {
        const reportedInput = Number(block.inputTokens) || 0;
        const hit = Number(block.cacheReadTokens) || 0;
        const output = Number(block.outputTokens) || 0;
        const miss = hit <= reportedInput ? Math.max(0, reportedInput - hit) : reportedInput;
        const totalInput = miss + hit;
        const blended = totalInput > 0 ? (miss * missPrice + hit * hitPrice) / totalInput : missPrice;
        return {
          hit,
          output,
          totalInput,
          hitRate: totalInput > 0 ? hit / totalInput : 0,
          blended,
          spend: (miss * missPrice + hit * hitPrice + output * outputPrice) / 1e6,
          cacheBenefit: (hit / 1e6) * Math.max(0, missPrice - hitPrice),
          savedTokens: savedTokens,
          savedMoney: (savedTokens / 1e6) * blended,
        };
      };

      const all = read(totals, Number(saved.tokens) || 0);
      const mine = read(stats.session || {}, Number(stats.session?.savedTokens) || 0);

      return {
        currency: stats.currency || '¥',
        hitRate: all.hitRate,
        blended: all.blended,
        spend: all.spend,
        cacheBenefit: all.cacheBenefit,
        calls: Number(totals.calls) || 0,
        totalInput: all.totalInput,
        hit: all.hit,
        output: all.output,
        savedTokens: all.savedTokens,
        savedMoney: all.savedMoney,
        slimmed: Number(saved.slimmedTokens) || 0,
        rewrites: Number(saved.rewrittenMessages) || 0,
        seriesStarts: Number(totals.seriesStarts) || 0,
        enabled: stats.enabled !== false,
        session: {
          calls: Number(stats.session?.calls) || 0,
          hitRate: mine.hitRate,
          spend: mine.spend,
          cacheBenefit: mine.cacheBenefit,
          totalInput: mine.totalInput,
          savedTokens: mine.savedTokens,
          savedMoney: mine.savedMoney,
          totalSaved: mine.savedMoney + mine.cacheBenefit,
        },
      };
    }

    function TokenSaverBadge(props) {
      const stats = useStats();
      const wide = !!props.wide;
      if (!stats) {
        return h(
          'div',
          {
            title:
              'Token 节省 · 等待宿主统计\n/plugins/dsh-token-saver/stats 暂不可达。\n插件已装好时，重启一次 DSH 桌面端即可恢复。',
            style: {
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
              maxWidth: wide ? '100%' : '46px',
              padding: wide ? '2px 8px' : '2px 4px',
              borderRadius: '999px',
              border: '1px dashed var(--dsw-alias-border-l1, rgba(127,127,127,0.24))',
              background: 'transparent',
              color: 'var(--dsw-alias-label-secondary, inherit)',
              opacity: '0.7',
              fontSize: wide ? '11px' : '10px',
              lineHeight: '16px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              userSelect: 'none',
            },
          },
          wide ? 'Token 节省 等待统计…' : '…',
        );
      }

      const m = normalize(stats);
      const currency = m.currency;
      const totalSaved = m.savedMoney + m.cacheBenefit;
      const withoutPlugin = m.spend + totalSaved;
      const tip = [
        'Token 节省 · ' + (m.enabled ? '已开启' : '已关闭'),
        '本次会话 ≈ ' + money(m.session.totalSaved, currency) + '（' + m.session.calls + ' 次调用 · 命中 ' + percent(m.session.hitRate) + ' · 省 ' + shortTokens(m.session.savedTokens) + ' tok）',
        '累计省 ≈ ' + money(totalSaved, currency) + '（缓存折扣 ' + money(m.cacheBenefit, currency) + ' + 指令瘦身 ' + money(m.savedMoney, currency) + '）',
        '开启前约 ' + money(withoutPlugin, currency) + ' → 开启后约 ' + money(m.spend, currency) + '（按 ' + money(m.blended, currency) + '/M 输入混合价）',
        '累计命中 ' + shortTokens(m.hit) + ' / 输入 ' + shortTokens(m.totalInput) + ' tok（' + percent(m.hitRate) + '）',
        '模型调用 ' + m.calls + ' 次 · 输出 ' + shortTokens(m.output) + ' tok',
        '缓存前缀重建 ' + m.seriesStarts + ' 次（每重建一次就是一次全量未命中）',
        '指令瘦身 ' + m.rewrites + ' 条 · 省 ' + shortTokens(m.savedTokens) + ' tok',
      ].join('\n');

      const text = wide
        ? '本次 ' + money(m.session.totalSaved, currency) + ' · 累计 ' + money(totalSaved, currency)
        : money(m.session.totalSaved, currency);

      return h(
        'div',
        {
          title: tip,
          style: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
            maxWidth: wide ? '100%' : '46px',
            padding: wide ? '2px 8px' : '2px 4px',
            borderRadius: '999px',
            border: '1px solid var(--dsw-alias-border-l1, rgba(127,127,127,0.24))',
            background: 'var(--dsw-alias-bg-layer-2, rgba(127,127,127,0.08))',
            color: 'var(--dsw-alias-label-secondary, inherit)',
            fontSize: wide ? '11px' : '10px',
            lineHeight: '16px',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            userSelect: 'none',
          },
        },
        text,
      );
    }

    return {
      inject: ['slots'],
      apply(ctx) {
        ctx.slots.inject('sidebar.footer.action', () =>
          ctx.slots.register(
            {
              name: 'sidebar.footer.action',
              id: 'token-saver',
              order: 6,
              label: () => 'Token 节省',
            },
            TokenSaverBadge,
          ),
        );
      },
    };
  },
});
