# 评分、训练与决策层

## 1. 概率评分已经相对成熟

对二元事件，Raven 不需要发明新的 headline metric 才能产生学术贡献。

基础指标：

- Brier：`(p-y)^2`，越低越好；
- paired skill：同题基线 Brier 减模型 Brier；
- BSS：相对基线的标准化技能分；
- calibration：相同预测概率的事件是否按该频率发生；
- resolution：模型能否区分会发生和不会发生的事件；
- Murphy decomposition：把总分拆成可诊断部分。

Raven 的研究重点应放在可信的信息环境、事件级统计和多锚点更新，而不是为了“有新指标”过度设计复合分数。

## 2. 推荐的 Raven 评分结构

### 主比较

- Mean Brier；
- `ΔB = B_baseline - B_agent`；
- 按 `event_id` 聚类的 95% CI；
- BSS 作为对外易读展示。

### 诊断

- calibration/reliability curve；
- resolution；
- 领域、时距、证据密度、基率和预算切片；
- 多锚点的更新方向与幅度；
- token、工具调用、延迟和美元成本。

Context 与 Agent 不合并排名。预测准确度和交易收益也不合并。

## 3. 未结算题的临时评分

[Proxy Scoring](https://openreview.net/forum?id=8ZrpbYgFe6) 尝试只根据多个模型的预测矩阵构造代理结果，在没有真实结算时给模型临时排名。文献报告 proxy 与真实 Brier 排名存在较强相关，并可能比单批真实结果更稳定。

价值：

- live 题未结算时提供早期信号；
- 发现明显异常模型；
- 帮助运营监控。

限制：

- 独立于群体但正确的模型可能被惩罚；
- 一旦作为训练目标，模型会朝代理共识优化；
- 不能进入正式 verified 主榜。

因此 Raven 只把 proxy score 标为 `provisional`，事件结算后必须被真实 proper score 替换。

## 4. 过程和长文应该怎样评

概率本身能客观结算，但 rationale 的“质量”较难定义。可借用三类思想：

- 一致性检查：测试逻辑相关问题的概率是否自洽；
- 下游效用：把长文交给较弱预测模型，看其 Brier 是否改善；
- claim audit：把推理拆为原子事实，检查来源、时间和对预测的贡献。

Raven v1 应把 rationale 用于引用合规、泄漏审计和失败诊断，不应让 LLM judge 的主观推理分影响 headline leaderboard。

## 5. 从评测到训练

### Halawi：检索、推理和选择性微调

[Approaching Human-Level Forecasting](https://arxiv.org/abs/2402.18563) 结合限定日期检索、结构化推理、聚合和筛选出的微调数据，把系统推进到接近人群预测的水平。

启示：高质量检索和校准约束比单纯换大模型更重要；未来结果可以筛选有用轨迹。

### Curating the Future / OpenForecaster

[Curating the Future](https://arxiv.org/abs/2512.25070) 从冻结新闻自动生成预测题，并显示不做去泄漏和质量筛选时，更多训练数据反而可能让模型变差。

启示：Raven-Train 的价值不在“自动造很多题”，而在 outcome、时间和 shortcut 都经过策展。

### Mantic

[Mantic](https://openreview.net/forum?id=lbpDR9pj5F) 用 Brier 奖励强化学习预测模型，在固定研究资料条件下取得明显提升，并指出训练中实时检索仍是重要待办。

启示：Raven 的受控检索环境可能比单纯发布训练数据更稀缺；但训练服务应在 verified 评测轮换机制稳定后再开放。

### Future-as-Label

[Future-as-Label](https://arxiv.org/abs/2601.06336) 把真实事件后续结算作为可验证奖励，用于开放世界预测 RL。

启示：时间会持续产生监督信号。Raven 可以长期形成“出题—预测—结算—训练”的闭环，但评测题和训练题必须隔离。

### 语言化信念状态

[Bayesian-style forecasting agent](https://arxiv.org/abs/2604.18576) 使用显式 JSON 信念、支持/反对证据、待解决问题、多 trial 收缩和分来源校准。

启示：Raven-Agent 的 trace schema 可以记录结构化 belief state，帮助研究跨锚点更新，而不是只保存最终概率。

## 6. 概率准确不等于决策收益

### M6

[M6 forecasting competition](https://arxiv.org/abs/2310.13357) 发现预测准确度与投资绩效几乎不相关；更好的组合构建可以把相同预测转成更高收益。

### When Do Prophets Profit

[When Do Prophets Profit](https://arxiv.org/abs/2607.06166) 研究如何用与 proper scoring rule 对应的下注策略，把相对市场的预测优势转换为期望利润。

### Beyond Accuracy

[Beyond Accuracy](https://openreview.net/forum?id=TSA5kRUKZv) 显示准确率相近的系统可能有显著不同的 PnL，收益可能来自“犯错时买得更便宜”，而不是更常答对。

### WALLA

[WALLA](https://arxiv.org/abs/2607.04389) 用激励相容的下注机制学习多个预测者的聚合权重。

对 Raven 的范围结论：

- v1 只测概率预测质量；
- 市场价是 scoring baseline，不是 runtime input；
- 决策/交易层未来可以作为独立产品，不能用 PnL 替代预测主榜。

## 7. 训练与评测的隔离原则

```text
Raven Verified Set
  永不进入训练服务
  定期轮换并在退休后公开

Raven Dev Set
  公开，用于 adapter 和方法开发

Raven Train
  独立题源、独立 namespace、独立版本
```

如果训练和评测共享题目、结算或检索日志，Raven 很快会重演静态 benchmark 污染。

下一步阅读：[Raven 的竞争定位](05-raven-positioning.md)。
