# Raven 的竞争定位

## 1. 竞品不是一个榜单，而是几种不同能力

| 系统 | Live | 冻结检索 | 通用全量语料 | 多锚点 | Market-blind | 可训练环境 |
|---|---:|---:|---:|---:|---:|---:|
| ForecastBench | 是 | 不适用 | 否 | 弱 | 否/依设定 | 有限 |
| FutureX | 是 | 不适用 | 公网 | 否 | 依题源 | 否 |
| Prophet Arena | 是 | 不适用 | 统一新闻 | 多时点可分析 | 否 | 否 |
| Autocast | 否 | 日期化新闻 | 较大但旧 | 有时序 | 部分 | 是 |
| BTF-2 | 否 | 是 | 按题语料 | 主要单时点 | 可做到 | 有限 |
| OracleProto | 否 | 软件多层过滤 | 依外部检索 | 否 | 可做到 | 否 |
| FutureSim | 否 | 是 | 有限新闻源 | 是 | 依设定 | 是 |
| Raven 目标 | 两种模式 | 是 | 2.28 亿新闻目标 | 是 | 是 | 后置开放 |

表中 Raven 一列是目标，不是已验证现状。

## 2. Raven 的空白位置

现有工作尚未稳定合并：

1. 覆盖大量事件的通用历史信息环境；
2. 服务端强制的物理时间门；
3. 同一事件跨多个锚点的 belief update；
4. 完全 market-blind 的运行与相对市场评分；
5. pastcast 与 live 的一致性验证；
6. 对模型公司友好的统一 adapter 和 verified evaluation。

Raven 最有价值的主张不是“我们又收集了 1,000 道题”，而是：

> 我们提供一个可重放的过去信息世界，并能证明模型在其中如何研究、形成和更新概率。

## 3. 两个正式赛道的必要性

### Raven TimeLock–Context

所有模型读相同 evidence pack，适合比较：

- 证据综合；
- 基率与因果推理；
- 概率校准；
- 不同模型在相同信息下的判断差异。

### Raven TimeLock–Agent

模型自主使用受控 Search/Read，适合比较：

- 查询分解；
- 信息发现；
- 来源核验；
- 研究预算利用；
- 完整 agent 系统能力。

如果两者混榜，就无法分清模型权重、evidence pack 生成器和 agent scaffold 各自贡献。

Live 也可以采用相同的 Context/Agent 区分，但应在题量足够后再扩展，避免 v1 运营面过宽。

## 4. 论文应该集中讲什么

建议一篇主论文只围绕一个中心命题：

> 大规模、可审计的 time-fenced environment 能否让 retrospective forecasting 成为可信、可复跑并与 live 表现一致的模型评测？

围绕该命题组织四组贡献：

1. 历史语料 provenance 和强制 time gate；
2. TimeLock benchmark 与多锚点设计；
3. market-blind、参数、shortcut 和结算审计；
4. 与 Raven Live 的外部效度对照。

统一接口、云并行和 verified leaderboard 是形成行业采用的关键产品贡献，但不必全部伪装成新的学术方法。

## 5. 必须克制的 claim

在完成对应证据前，不应声称：

- “泄漏率为零”；
- “第一个预测 benchmark”；
- “模型真正超过了市场/人类”；
- “多锚点就是更多独立样本”；
- “全量新闻等于完整 `F_t`”；
- “TimeLock 排名能够直接代表 live 部署”；
- “一个总分完整衡量预测能力”。

更可信的论文会主动报告语料覆盖、许可、残余泄漏上界、任务排除、结算错误和 pastcast/live 差异。

## 6. 谁会成为 Raven 的用户

- 模型公司：需要在 system card 中报告现实世界预测能力；
- forecasting agent 团队：需要公平比较检索、推理和校准；
- 训练研究者：需要防泄漏的事件、历史证据和延迟结果；
- 独立评测机构：需要可复跑、可签名的标准；
- 风险与决策研究者：需要概率而不是只看 accuracy；
- 预测社区：需要 AI 与 crowd/market 的同题比较。

下一步阅读：[开发路线](../roadmap/README.md)和[行业采用策略](../adoption/README.md)。
