# 执行摘要

## 我们要建立什么

Raven 不是一套静态题库，而是一套让第三方模型公司能够接入、运行、复核和引用的真实世界预测基础设施：

```text
Raven Forecasting Suite
├── Raven TimeLock：冻结历史信息环境中的回溯预测
│   ├── Context：所有模型读取同一 evidence pack
│   └── Agent：模型在受控历史语料中自主检索
└── Raven Live：对尚未结算事件的前瞻预测
    ├── Context
    └── Agent
```

TimeLock 提供大样本、可复跑和多锚点诊断；Live 从构造上避免答案已进入训练数据，并用来检验 TimeLock 是否受参数污染或分布偏移影响。二者互补，不应合并为一个含义模糊的总分。

## 为什么现在已有 benchmark 仍不够

真实世界预测评测有一个决定性的约束：模型在锚点 `t` 作答时，只能使用 `t` 之前已经公开的信息 `F_t`。现有系统通常在四处失守：

1. 模型参数已经记住事件结果；
2. 检索返回了锚点之后更新或发布的内容；
3. 题面、选题过程或提前结算留下了答案捷径；
4. 模型直接看到了市场价或人群概率，再把复制共识包装成独立预测。

Raven 的核心资产不是新的 Brier 变体，而是把信息边界落实为可执行、可审计的环境。

## 差异化主张

Raven 计划把目前分散在不同工作里的四个能力合并：

- 大规模、按真实抓取时间冻结的全量新闻环境；
- market-blind 的相对市场评测；
- 同一事件多个历史锚点上的信念更新；
- TimeLock 与 Live 的交叉有效性验证。

在语料来源、许可、时间字段和第三方复现完成之前，这些只能称为设计目标，不能称为已经实现的贡献。

## v1 最重要的产品

1. `Raven Protocol`：任务、锚点、预测、结算、评分与披露标准；
2. `Corpus Gateway`：服务端强制 `crawl_time <= as_of` 的 Search/Read API；
3. `Task Registry`：事件族、相关性、锚点和结算证据；
4. `Harness`：模型 adapter、预算、公平重试和完整 trace；
5. `Evaluator`：Brier、paired skill、校准、分辨率、多锚点更新和置信区间；
6. `Raven Verified`：统一环境复跑、审计并签发可引用结果；
7. `Live Sentinel`：持续但规模较小的 live 有效性监测。

## 当前最优先的工作

第一优先级不是榜单、网站或训练，而是验证 2.28 亿新闻资产：

- `crawl_time` 是否真的是抓取时间；
- 是否保留不可变的当时正文、URL、响应信息和内容哈希；
- 更新页面是否覆盖旧内容；
- 新闻能否合法地用于内部运行、第三方评测和结果展示；
- 是否能从 manifest 重建固定版本的索引。

如果这些问题没有可靠答案，Raven 就不能声称“物理冻结信息边界”。

## 成功标准

科学成功：能够以足够样本量区分前沿模型，且通过检索、参数、shortcut、market 和结算审计。

工程成功：外部团队一天内接入 smoke test；完整 run 的版本、成本和失败原因可追踪；独立团队得到统计一致结果。

采用成功：Raven 结果进入主要模型的 system card 或 technical report，并由闭源、开源和独立评测机构共同使用。

## 推荐决策

- 总体采用“环境 + benchmark + verified service”，而不是只发布数据集；
- 使用 TimeLock 主榜 + Live Sentinel；
- v1 先做英语二元概率题；
- Context 与 Agent 分榜；
- 科学比较用 paired Brier difference 和 event-clustered CI，传播层同时展示 BSS；
- 公开 dev set，轮换 verified set，退休后公开历史集合；
- 先批准可行性 Phase 0，通过数据与许可 Gate 后再批准完整建设。

下一步阅读：[AI 预测文献综述](literature/README.md)或[开发路线](roadmap/README.md)。
