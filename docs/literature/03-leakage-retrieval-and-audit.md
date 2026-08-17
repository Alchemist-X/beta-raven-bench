# 泄漏、检索与审计

## 1. 为什么检索是 Raven 的第一优先级

Forecasting agent 的能力高度依赖最新、相关、相互矛盾的外部证据。但 pastcast 一旦允许普通互联网检索，就可能直接找到事件结果。

[Temporal Leakage](https://arxiv.org/abs/2602.00758) 对搜索引擎日期过滤进行实测：Google `before:` 过滤后，71% 的问题仍至少返回一个包含重大后验信息的页面，41% 至少有一个页面直接暴露答案；使用泄漏文档时，模型 Brier 从约 0.242 虚降到 0.108。

常见机制包括：

- 页面发布后更新，但仍显示旧日期；
- 页面元数据或时间戳错误；
- related-content、推荐模块和侧栏含后续内容；
- 搜索排序系统本身使用了未来数据；
- URL 或“没有搜到什么”形成结果信号。

结论：搜索引擎日期过滤不是时间隔离。Raven 必须使用当时真实抓取且之后不可变的快照。

## 2. 检索质量本身又决定能力

[Autocast++](https://arxiv.org/abs/2310.01880) 表明，小模型配合更好的检索可以打败更大的模型，说明瓶颈常在证据发现而不只在参数规模。

[AIA Forecaster](https://arxiv.org/abs/2511.07678) 也显示搜索对预测分数有巨大影响，同时市场价能替代相当一部分“搜索增益”。这同时给出两个警告：

1. 不提供检索，会低估真实 agent 能力；
2. 提供市场价，会把复制共识误算成研究能力。

因此 Raven 需要分开两个赛道：

- Context：统一材料，测综合和概率；
- Agent：自主检索，测研究全流程。

## 3. 为什么模拟检索不能完全替代真实环境

[ZeroSearch](https://arxiv.org/abs/2505.04588) 证明在部分静态知识任务中，可以用模型模拟搜索结果训练检索推理，接近真实搜索效果。

但真实预测需要处理：

- 某天究竟有哪些报道可用；
- 多来源冲突与重复；
- 稀疏、噪声和来源信誉；
- 证据随时间到达；
- 当时没有被报道的信息。

模拟搜索适合作为训练或低成本开发工具，不适合作为 Raven 主榜的真实性依据。

## 4. 参数边界审计

厂商自报 knowledge cutoff 不能直接等同于模型实际知识边界。

[Dated Data](https://arxiv.org/abs/2403.12958) 使用按月版本化的 Wikipedia/新闻和 perplexity 曲线估计 effective cutoff，发现某些数据或模型实际对齐的版本可能比标称时间早数年，也可能被大量旧副本主导。

对 Raven 的使用方式：

- 要求精确模型 snapshot 和厂商 cutoff；
- 对能提供 token logprob 的模型运行月份化 probe；
- 为估计 cutoff 加缓冲期；
- 无法验证的模型进入 `unverified cutoff` 分榜；
- 用 Raven Live 检查 TimeLock 排名是否异常偏高。

effective-cutoff probe 是风险指标，不是“模型绝对没见过答案”的证明。

## 5. 题目与 shortcut 审计

[Pitfalls in Evaluating LM Forecasters](https://arxiv.org/abs/2506.00723) 系统总结了 forecasting benchmark 的泄漏和外推问题，并展示两个便宜但有效的诊断：

- 检查事件在锚点前是否已经事实上结算；
- 使用不可能知道未来的旧模型，在无检索条件下训练/测试；若仍远超随机，题面存在 shortcut 的可能性很高。

Raven 应建立 outcome-blind 流程：

```text
出题者只看锚点前材料
→ 写题面、锚点和结算规则
→ 独立 reviewer 检查歧义
→ 结算团队事后取得结果
→ earliest-known-date 审计
→ shortcut baseline
→ 才能进入 verified set
```

## 6. 按影响力审计泄漏

[Shapley-DCLR / TimeSPEC](https://arxiv.org/abs/2602.17234) 不只问“有没有一句泄漏”，而是：泄漏信息对最终预测贡献了多少。

方法大致为：

1. 把 rationale 拆成可核查的原子 claim；
2. 查每条 claim 最早公开日期；
3. 用近似 Shapley 值衡量该 claim 对预测的边际影响；
4. 计算由后验 claim 驱动的决策权重比例。

这比简单泄漏率更适合解释“少量但决定性的答案泄漏”。Raven v1 不必全量运行昂贵的 Shapley 审计，可以对 10% 高风险任务做深审计，并对全量运行轻量 detector。

## 7. Raven 的分层防线

| 层级 | 防线 | 主要防什么 |
|---|---|---|
| 数据 | 原始历史快照、真实 crawl time、内容哈希 | 后续页面更新 |
| 索引 | 固定 corpus/index version、服务端 `as_of` | 客户端越权和版本漂移 |
| 网络 | 禁止公网 egress | agent 绕过 Gateway |
| 内容 | 市场域名 blocklist、赔率/结果 detector | 基线与答案泄漏 |
| 模型 | cutoff 声明、effective-cutoff probe、缓冲期 | 参数记忆 |
| 任务 | outcome-blind authoring、earliest-known-date | 选题与提前结算 |
| 运行 | 完整 tool trace、evidence receipt | 无法复核的行为 |
| 事后 | 抽样人工审计、Shapley-DCLR 类深审计 | detector 漏报 |
| 外部效度 | Live Sentinel | pastcast 结构性未知风险 |

## 8. 如何报告“无泄漏”

不应写：

> Raven 的泄漏率结构性为 0。

更严谨的写法是：

> Raven 的检索只能返回在锚点前已经抓取并进入指定 immutable manifest 的对象。在分层抽样的 500 个返回文档中未观察到直接后验答案泄漏，对应二项分布下约 0.6% 的 95% 上界；参数污染仍由 cutoff probe 和 live sentinel 单独监测。

这种表述把机制保证、样本证据和仍未解决的风险分开，模型公司才敢引用。

下一步阅读：[评分、训练与决策层](04-scoring-training-and-decisions.md)。
