# 里程碑与质量 Gate

## 团队假设

以下时间按 8–10 人核心团队估算：

- Benchmark/Research Lead ×1；
- Retrieval/Data Infra ×2；
- Eval/Harness Engineers ×2；
- Applied Scientists/Statistics ×1–2；
- Task/Resolution Ops ×2–3；
- DevRel/Program Manager ×1；
- 兼职或外部 Legal/Security。

若团队只有 3–4 人，应缩小事件数和赛道，不应删除 provenance、统计和审计 Gate。

## Phase 0：可行性与协议

时间：2026-07-22—2026-08-07。

交付：

- Protocol v0.1、threat model 和 schemas；
- 对 S3 语料做足够大的分层 inventory；
- timestamp/provenance/license 报告；
- 20–30 道 gold task，每题约 3 个锚点；
- 最小 Search/Read spike；
- 全量索引成本、吞吐和时间估算；
- primary score、赛道和公开策略决策。

Gate：

- 能证明历史正文未被后续内容覆盖；
- 时间字段含义满足 time-fence；
- 存在合法的第三方使用路径；
- 全量或足够覆盖的索引成本可持续。

任一失败：暂停“物理冻结”claim，优先解决数据资产。

## Phase 1：Time-fenced Retrieval Alpha

时间：2026-08-08—2026-09-18。

交付：

- 从 10M 渐进到全量索引；
- Corpus Gateway Alpha；
- BM25 reference retriever；
- manifest、receipt 和 local emulator；
- 越界与 market 负向测试集。

Gate：

- 合成越界测试 100% 拦截；
- 固定版本 top-k 可重放；
- 至少 500 个分层抽样结果中 0 个直接后验答案泄漏；
- 若为 0/500，只报告约 0.6% 的 95% 上界；
- p95 latency 和单位 run 成本达到 Phase 0 预算目标。

## Phase 2：端到端 MVP

时间：2026-09-19—2026-10-30。

交付：

- 200–300 个事件、600–900 个锚点；
- TimeLock–Context 与 TimeLock–Agent；
- 4–5 个 baselines；
- evaluator、cluster bootstrap 和 result card；
- market-blind enclave 和消融；
- container、CLI、quickstart、smoke set。

Gate：

- 两个内部团队独立运行同一模型；
- mean Brier 差异绝对值建议不超过 0.002；
- 每个结果都能追溯到 run manifest 和 evidence receipts；
- prompt/seed 的合理变化不颠覆主要结论。

## Phase 3：v1 数据与红队

时间：2026-10-31—2026-12-15。

交付：

- 至少 1,000 个事件；
- outcome-blind authoring 与 resolution；
- effective-cutoff probe；
- 检索、参数、shortcut、market、结算七组实验；
- 独立 leakage red team；
- Audit Report v0.9；
- staging leaderboard。

Gate：

- 高置信任务抽查结算错误率目标低于 1%；
- 低置信和争议任务不进入主榜；
- shortcut baseline 没有无法解释的强成绩；
- power analysis 支持目标效应量；
- 多锚点按 event 聚类，没有伪增样本量。

## Phase 4：Design Partner Closed Beta

时间：2026-12-16—2027-01-31。

参与目标：

- 3–5 家模型公司；
- 2 个 forecasting 研究团队；
- 1 个独立评测或统计团队；
- 闭源与开源均有代表。

交付：

- 外部 adapter 和 dry run；
- time-to-first-run、失败点和成本记录；
- 至少两次独立复现；
- RFC review 和 v0.9 release candidate；
- verified disclosure 模板。

Gate：

- 至少 3 个外部组织无需 maintainer 改核心代码完成 smoke test；
- 至少 2 个组织完成 full run；
- 外部统计 reviewer 接受主指标和 CI 方法；
- 无尚未处理的 P0 leakage/security 问题。

## Phase 5：Public v1

时间：2027-02-01—2027-03-31。

发布：

- Protocol、SDK、Harness、Evaluator；
- dev set、data card、audit report；
- Corpus Gateway 或受控复现环境；
- Raven Verified leaderboard；
- 主论文和 launch report；
- 已知限制、成本和负结果。

Gate：

- 外部 quickstart 到首个有效结果的中位时间少于 1 天；
- 至少 5 个 verified model/agent；
- 每个榜单结果有版本、预算、CI 和披露；
- 独立复现报告与发布同步可读。

## Phase 6：持续运营

从 2027-04 开始：

- 每月 patch；
- 每季度任务和模型 refresh；
- 每年 major verified 版本；
- 持续 Live Sentinel；
- 任务 challenge、申诉和退休；
- 外部复现 grant 和贡献奖励；
- verified 轮换稳定后再启动 Raven-Train。

## 跨阶段 Stop Conditions

| 发现 | 必须采取的动作 |
|---|---|
| 无法证明快照时间 | 停止 time-fenced claim，重做数据来源 |
| 许可阻止第三方评测 | 改为 bring-compute-to-data；仍不可行则换语料 |
| 样本不足 | 降低 claim 或扩大事件数，不能靠锚点虚增 n |
| shortcut baseline 强 | 删除或重写事件族 |
| TimeLock 与 Live 明显冲突 | 暂停统一排名解释，调查污染与分布偏移 |
| 外部复现不稳定 | 不发布 v1，先冻结版本与 retry policy |
| verified 运行过贵 | 研究分层抽样，并证明 ranking preservation |
| 参评方拒绝披露 scaffold/预算 | 只列 self-reported，不进入 verified |

## 发布后采用目标

12 个月：

- 10+ verified 模型/agent；
- 5+ 独立组织完成运行；
- 2+ 模型提供方在正式报告引用；
- 2+ 外部研究项目使用 Gateway 或 Harness；
- 至少一次独立方法与数据审计。

24 个月：

- 5+ 主要模型提供方采用；
- 25+ verified 系统；
- 3+ 第三方平台原生集成；
- 年度 Raven-Verified 和外部治理席位稳定运行。
