# dsh-token-saver

DeepSeek Harness 省钱插件：在你发出的自然语言指令进入模型之前做**无损瘦身**，并把省下的 token 与金额显示在**左侧栏**。

A DeepSeek Harness cost-saving plugin: it **losslessly slims your instruction before the model sees it**, then shows the saved tokens and money in the **left sidebar**.

---

## 中文

### 它做什么

1. **指令瘦身**（`agent/pre-step` 钩子）
   只做不改语义的删除：行尾空格、连续 3 个以上空格、连续 3 个以上空行、连续重复的非空行、重复段落（≥60 字符）、结尾寒暄（谢谢／麻烦了／thanks…）。
   **代码块（``` 围栏）内容一字不动**，运行时上下文消息一律跳过，单条消息瘦身收益不足 15 token 或不足 4% 时保留原文。
   改写只影响进入转写的新消息，历史消息不会被改写。

2. **真实用量记账**（`session/event` → `assistant/message`）
   每次模型调用记录输入未命中 token、输入命中缓存 token、输出 token。DeepSeek 的 `usage.inputTokens` 只含**未命中**部分，命中部分单独在 `cacheReadTokens`，两者相加才是本次输入总量——这个坑插件已经处理。

3. **左侧栏徽章**（`sidebar.footer.action`，id `token-saver`）
   宽栏显示 `本次 ¥0.02 · 累计 ¥13.11`，窄栏（56px 轨道）只显示本次。悬停八行明细：本次会话、累计省（缓存折扣 + 指令瘦身）、开启前/后对比、累计命中、调用次数、缓存前缀重建次数、瘦身条数。
   「本次」按最近一次有模型调用的会话统计，随 `~/.dsh/dsh-token-saver.json` 持久化，重启不清零，只保留最近 20 个会话。

4. **缓存健康度**
   记录 `request/header` 里 `startsSeries` 的次数。每重建一次请求序列，可复用的前缀就作废一次、下一次调用几乎全价，所以这个数字越小越好。

### 金额口径

价格写死在 `index.js` 的 `DEFAULTS`：`priceInputMiss: 2`、`priceInputHit: 0.2`、`priceOutput: 3`（元／百万 token，DeepSeek 官方档）。

- 累计花费 =（未命中 × 2 + 命中 × 0.2 + 输出 × 3）/ 1e6
- 缓存折扣已省 = 命中 token / 1e6 ×（2 − 0.2）
- 瘦身已省 = 省下的指令 token / 1e6 × 当前输入均价

指令瘦身省下的 token 会一直留在会话请求前缀里，后续每次调用都会再省一次，累计值按调用次数累加。

### 安装

- 在 dshfind 插件市场里搜 `dsh-token-saver`（包名 `@acmepoyen/dsh-token-saver`）一键安装；
- 或手工：把本包目录交给 `plugin_manager` 的 `install_bundle`（`target` 用绝对路径）；
- 或从 npm 装：`npm i @acmepoyen/dsh-token-saver` 后按上面的方式挂载。

安装后左侧栏底部会多出一个徽章，不需要重启 DSH 桌面端；改插件代码才需要。

### 文件

| 文件 | 作用 |
|---|---|
| `index.js` | 宿主半：瘦身 + 记账 + HTTP `/plugins/dsh-token-saver/stats` |
| `client.js` | 客户端半：侧边栏徽章，5 秒轮询 stats |
| `cordis.patch.yml` | 装载补丁，插入 `id: dsh-token-saver` |
| `locale/*.json`, `icon.svg` | 名称与图标 |

聚合数据落在 `~/.dsh/dsh-token-saver.json`。

### 已知边界

- 不改写模型回复，也不压缩上下文（那是 billion-context 的事），两者互补。
- 价格是硬编码常量，DeepSeek 调价后要改 `DEFAULTS` 并重启。
- 关掉瘦身：给装载行加 `config: { enabled: false }`，记账与侧栏照常工作。
- 单条用户消息短于 80 字符时不做瘦身，所以纯短指令省不下 token，这是刻意的保守取舍。
- 只统计 `assistant/message` 里带 usage 的调用；子代理调用同样计入累计。

### 开发

源码目录跑 `deploy.ps1` 可把宿主半写成薄壳（带 `?v=时间戳` 动态 import）指向工作区源码，再 `set_plugin false → true` 让装载器重启这一项。已安装位置是**拷贝**不是软链，改源码不改安装位置就永远不生效。

**禁止用 PowerShell 5.1 的 `Get-Content` / `Set-Content` 改这两个 .js 文件**：它按 ANSI 解码 UTF-8，中文会被写成乱码。改代码用编辑器或 node 脚本，编码一律 UTF-8 无 BOM。

---

## English

### What it does

1. **Instruction slimming** (`agent/pre-step`): removes trailing spaces, runs of 3+ spaces, runs of 3+ blank lines, consecutive duplicate lines, duplicated paragraphs (≥60 chars) and trailing pleasantries — never inside ``` fences, never on runtime-context messages, and only when the gain is ≥15 tokens *and* ≥4%.
2. **Real usage accounting** (`session/event` → `assistant/message`): records cache-miss input, cache-hit input and output per call. DeepSeek reports `usage.inputTokens` as the **miss-only** part with hits in `cacheReadTokens`; both are added for the true input total.
3. **Sidebar badge** (`sidebar.footer.action`, id `token-saver`): wide mode shows `本次 ¥0.02 · 累计 ¥13.11`; the 56px rail shows this session only. Hover reveals eight lines, including the pre/post-enable comparison, cache hit rate, call count and how many cache prefixes were rebuilt.
4. **Cache health**: counts `request/header.startsSeries` — every rebuilt request series drops the reusable prefix, so lower is better.

### Money

Prices are constants in `DEFAULTS` (`index.js`): input miss ¥2, input hit ¥0.2, output ¥3 per million tokens (DeepSeek list price).

- spend = (miss × 2 + hit × 0.2 + output × 3) / 1e6
- cache savings = hit / 1e6 × (2 − 0.2)
- slimming savings = removed prompt tokens / 1e6 × current blended input price

Slimmed tokens stay in the request prefix, so they are saved again on every later call; the all-time figure compounds per call.

### Install

Install `@acmepoyen/dsh-token-saver` from the dshfind marketplace, or hand the package directory to `plugin_manager`'s `install_bundle`, or `npm i @acmepoyen/dsh-token-saver` and mount it the same way.

### Boundaries

- It does not rewrite model replies and does not compress context (that is billion-context's job); the two are complementary.
- Prices are hard-coded; edit `DEFAULTS` when DeepSeek changes them.
- Messages shorter than 80 characters are never slimmed — a deliberate conservative choice.
- Aggregates persist to `~/.dsh/dsh-token-saver.json`.

## License

MIT
