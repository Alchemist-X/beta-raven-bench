# 评测环境路线

## 总览

评测环境工作可以分为 live、pastcast/TimeLock 和 simulation 三条支线。

| 路线 | 如何守住信息边界 | 主要优势 | 主要代价 |
|---|---|---|---|
| Live | 作答时答案尚不存在 | 最强的结果防泄漏 | 等结算、难复跑、样本慢 |
| TimeLock | 重建历史时点的冻结信息环境 | 可复跑、大样本、多锚点 | 参数与检索边界需额外证明 |
| Simulation | 在可推进的合成世界里预测 | 即时结算、完全可控 | 外部效度弱 |

## Live 路线

### ForecastBench

[ForecastBench](https://arxiv.org/abs/2409.19839) 建立了持续滚动的 live 预测 benchmark：从预测市场和真实数据源自动取得题目，定期让模型和人类预测，等结算后更新榜单。

关键贡献：

- 用尚未发生的事件避免静态 benchmark 污染；
- 建立公众和超级预测者人类基线；
- 把题目生产、结算和排行榜做成长期流水线；
- 研究联合事件概率，而不只测独立二元题。

主要局限：

- 每个模型必须等待新的事件结算；
- 不同批次题目难度不同，需要额外对齐；
- 市场题提供 crowd/freeze value 时，容易把复制市场误当成独立预测能力；
- 细小模型差距需要长期累积样本。

对 Raven 的启示：Live 应当持续运行，但不应独自承担快速复跑和高统计功效。

### FutureX

[FutureX](https://arxiv.org/abs/2508.11987) 把 live 出题推进到日常自动化，并重点评估能够自主搜索的 agent。其题目来自大量持续更新的网站，通过模板、变量随机化和自动结算扩展规模。

关键贡献：

- 证明多源、日更、自动结算的 live pipeline 可以规模化；
- 不局限于简单二元市场题；
- 把搜索工具和长程 agent 纳入评测。

局限：

- 自动出题和自动结算仍需要质量审计；
- 不同题型的分数聚合可能掩盖 construct 差异；
- live 的等待和批次可比性问题仍在。

对 Raven 的启示：Raven Live 可复用“少量人工维护题源、其余自动循环”的运营思想，但 v1 应先收窄到二元概率题。

### Prophet Arena

[Prophet Arena](https://arxiv.org/abs/2510.17638) 将市场事件、统一新闻上下文和市场价一起交给多个模型，分别观察 Brier、校准和交易回报。

关键贡献：

- 证明同一个“预测能力”需要从准确、校准和收益等不同角度看；
- 给所有模型相同上下文，分离检索与推理；
- 用市场价作为事件难度参照。

局限：市场价同时作为输入和基线，会让强结果很大程度上来自复制共识。它更适合研究“基于市场共识的修正能力”，不适合证明模型独立形成了预测。

对 Raven 的启示：保留统一上下文赛道，但主榜必须 market-blind。

### Foresight Arena

[Foresight Arena](https://arxiv.org/abs/2605.00420) 探索链上选题、市场快照、commit-reveal 和可验证评分，并强调小效应需要大样本。

关键贡献：

- 把提交不可篡改、市场基线和声誉记录纳入协议；
- 使用相对市场的 paired skill；
- 明确讨论方差和 power。

局限：早期版本主要依赖模拟，实际 live 数据和长期运营证据有限。

对 Raven 的启示：结果提交可以签名或 commit-reveal；统计功效必须成为发布 Gate，而不是附录说明。

## TimeLock / pastcast 路线

### Autocast

[Autocast](https://arxiv.org/abs/2206.15474) 是现代 LLM 事件预测的重要起点：从真实预测竞赛取得问题和人群预测序列，并按日期组织新闻语料。

关键贡献：

- 把“站在过去预测未来”做成明确研究设定；
- 同时提供问题、日期化语料和人类 crowd；
- 证明检索显著重要，并研究随时间更新预测。

局限：题目和语料对现代模型已较旧，参数污染风险上升；仅按发布日期组织内容并不自动证明页面是不可变快照。

对 Raven 的启示：继承时间化语料和逐日/多锚点思想，但用更强的 provenance、runtime time gate 和现代事件窗口。

### BTF-2

[BTF-2](https://arxiv.org/abs/2604.26106) 为每道历史预测题准备大规模冻结研究材料，让 agent 在封闭语料里搜索，并保存概率、理由和完整轨迹。

关键贡献：

- 用 hermetic/offline corpus 增强可复现性；
- 不只排名，还尝试分析推理为什么失败；
- 证明自主研究相对固定摘要有独立价值。

局限：语料通常按题准备、获取受限，难形成覆盖任意事件的通用历史信息世界。

对 Raven 的启示：BTF-2 是 Raven-Agent 最直接的对标；Raven 的潜在差异是“全量冻结语料 + 通用检索服务 + 多锚点”。

### OracleProto

[OracleProto](https://arxiv.org/abs/2605.03762) 把 pastcast 防线协议化：模型准入、工具层日期掩码和内容检测结合使用。

关键贡献：泄漏防线从单一日期过滤升级为多层协议，并实际报告残余泄漏。

局限：只靠软件识别和过滤仍可能留下约百分之一级别残余；它无法替代真实历史快照。

对 Raven 的启示：即使已有物理快照，仍应保留准入、内容 detector 和事后审计，形成 defense in depth。

### FutureSim

[FutureSim](https://arxiv.org/abs/2605.15188) 以真实历史事件逐日重放，让 agent 在信息陆续到达时持续更新预测。

关键贡献：

- 把预测从一次性答案变成长期 belief update；
- 直接比较 agentic 多轮搜索与单次检索；
- 提供多锚点和适应性评测的近期参照。

局限：题量、时间窗口和新闻覆盖有限，完整语料和索引的复现成本较高。

对 Raven 的启示：多锚点不应只是多算几次 Brier，而应定义方向、幅度和证据响应的更新指标。

## Simulation 路线

### ForecastBench-Sim

[ForecastBench-Sim](https://arxiv.org/abs/2606.18686) 在可继续推进的模拟世界中出题，因此能够即时获得未来结果。

优势：

- 没有等待结算；
- 环境完全可控；
- 可重复生成大量任务。

局限：文献报告模拟排名与真实预测排名的相关性有限，说明 simulation 不能替代真实世界 benchmark。

对 Raven 的启示：模拟环境可以做 CI、压力测试和训练，但不应承担 Raven 的主要外部效度 claim。

## Raven 应综合什么

```text
ForecastBench 的持续运营
+ BTF-2 的封闭可复现研究环境
+ FutureSim 的多锚点更新
+ OracleProto 的多层审计
+ Foresight Arena 的提交与统计纪律
= Raven TimeLock + Raven Live
```

这只是设计方向。只有第三方复现、泄漏审计和 live/pastcast 一致性实验完成后，才能声称 Raven 实际合并了这些优点。

下一步阅读：[泄漏、检索与审计](03-leakage-retrieval-and-audit.md)。
