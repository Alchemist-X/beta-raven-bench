# 产品与传播策略

## 1. 先把 benchmark 做成产品

模型公司不会因为论文中有一个新表格就长期采用。它们需要把 Raven 接入内部 release evaluation pipeline，因此产品接口必须稳定。

### 最小接入体验

```text
阅读 15 分钟 Quickstart
→ 实现/配置一个标准 Adapter
→ 运行 20 题 Smoke Test
→ 查看错误、成本和示例 Trace
→ 提交云端完整评测
→ 收到 Verified Result Card
```

目标：外部团队在没有 maintainer 修改核心代码的情况下，一天内得到第一个有效 smoke result。

### 必备材料

- Quickstart；
- 添加新 agent 的完整示例；
- OpenAI-compatible、Anthropic、Gemini、vLLM adapters；
- 20 题 smoke set 和预期输出；
- local corpus emulator；
- full-run 成本与时间计算器；
- error taxonomy 和 troubleshooting；
- result schema 与 system-card-ready 模板；
- benchmark FAQ；
- 公共 changelog 和 status page。

## 2. 统一接口为什么决定传播

Raven 的 adapter contract 应尽量小，让各种内部系统都能接入：

```python
agent.reset(task_config)
agent.predict(observation) -> action
```

环境而不是 adapter 负责限制工具、预算和时间。这样公司可以保留自己的模型 API、编排和私有实现，同时接受相同外部条件。

如果每家模型都需要 fork runner、改 evaluator 或手工准备 evidence，Raven 的实际比较会迅速分叉。

## 3. 结果必须方便被引用

模型发布团队需要的不只是 leaderboard URL，而是一组可以直接进入报告的稳定工件：

```text
Model: exact snapshot
Raven mode/track/version
Corpus and runner versions
Mean Brier and paired skill
95% event-clustered CI
Task coverage and failures
Search/token/time budget
Scaffold disclosure
Verification status and run date
```

同时提供：

- Markdown 表；
- CSV；
- 机器可读 JSON；
- 可嵌入图表；
- 结果签名；
- 一句话的 score interpretation。

## 4. 分数要能帮助模型团队改进

只有名次的 benchmark 容易被替换。能定位问题的 benchmark 更容易进入研发循环。

Raven 应提供：

- Context vs Agent 差距：研究能力还是推理能力；
- calibration vs resolution：概率表达还是区分能力；
- 多锚点更新：是否对新证据响应不足或过度；
- 领域和时距切片；
- query/read/token 的边际收益；
- 引用覆盖、冲突证据和失败轨迹；
- 环境错误、模型错误和预算耗尽的分离。

## 5. Design Partner 策略

Closed beta 不应只找关系最近的一家公司。建议组成：

- 2 家闭源前沿模型提供方；
- 1–2 家开源权重团队；
- 1 家 forecasting/deep-research agent 团队；
- 1 个独立评测机构；
- 1 个统计或预测学研究团队。

Design partner 不是购买背书，而是共同发现：

- 接口是否绑定某种 scaffold；
- 预算是否公平；
- 闭源 API 是否能精确固定 snapshot；
- 结果披露是否会暴露商业秘密；
- 哪些坏题会影响模型公司信任；
- 完整 run 的成本是否现实。

合作规则应公开：伙伴可以反馈协议，但不能获得有利题目、提前结果或特殊重试。

## 6. 首发策略

首发前必须具备：

- 至少 5 个 verified 模型/agent；
- 闭源与开源结果；
- 一个 market/crowd baseline；
- 一份独立复现；
- 一份 leakage/audit report；
- 公开 dev set、代码和 local emulator；
- 真实 full-run 成本；
- 已知限制和负结果。

首发叙事应围绕一个清楚问题：

> 当前 AI 能否在不偷看结果、不复制市场的情况下，利用当时信息形成并更新可靠概率？

不要用几十个指标和赛道稀释这个问题。

## 7. 传播内容层级

### 第一层：面向所有人

- 一句话定位；
- TimeLock 与 Live 的图示；
- 主要模型与 market/crowd 的结果；
- 三个代表性成功/失败案例。

### 第二层：面向模型团队

- track、预算、adapter；
- 版本和成本；
- result card；
- failure slices。

### 第三层：面向研究者

- Protocol；
- power analysis；
- leakage experiments；
- task construction；
- evaluator 和统计代码。

### 第四层：面向审计者

- corpus provenance；
- manifests/hashes；
- exclusion log；
- resolution disagreements；
- task challenges 和 rerun decisions。

这与本仓库文档的渐进式披露结构保持一致。

## 8. 社区增长机制

- `projects using Raven` 页面；
- provider integration guides；
- task source proposal 和 contribution bounty；
- 独立复现小额 grant；
- 年度 forecasting evaluation workshop/challenge；
- 每季度公开 failure report；
- 对有效 bug/leakage 报告公开致谢；
- retired verified set 在安全窗口后公开，支持研究。

## 9. 不应追逐的虚荣指标

- 首周 leaderboard 访问量；
- GitHub stars 本身；
- 单个模型厂商的转发；
- 用大量相近任务制造的虚高样本数；
- 没有版本和预算的“世界第一”；
- 通过频繁改榜制造新闻。

更重要的指标是独立复现数、正式模型报告引用数、外部 adapters、verified submissions 和问题修复周转时间。
