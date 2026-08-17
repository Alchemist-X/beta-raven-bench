# 术语表

## 评测对象

**Judgmental forecasting**  
对现实世界离散事件给出主观概率，例如“某国年底前是否降息”。它不同于预测一条温度或价格曲线的数值时间序列预测。

**Event / Question**  
Event 是被预测的现实事件；Question 是围绕该事件写出的可结算问题。多个 question 可能共享同一潜在 event，因此统计时需要分组。

**Anchor time `t`**  
模型被要求站在的历史或当前时点。它只能使用该时点之前可获得的信息。

**Information set `F_t`**  
截至 `t` 已公开的信息集合。Raven 的可信度取决于能否把模型限制在这个集合内。

## 两种时间模式

**Raven TimeLock**  
暂定名称。模型站在历史时点，使用冻结的历史信息预测之后发生的事件。也可称 pastcast、retrospective forecasting 或 hindcast，但需避免与 backcasting 混淆。

**Raven Live**  
模型预测仍未结算的事件。作答时答案尚不存在，因此天然避免结果已进入训练数据。

**Live Sentinel**  
持续运行的小规模 live 题流，用来检测 TimeLock 与真实前瞻表现是否系统性背离；不承担主榜样本量。

## 信息边界

**Parameter leakage**  
模型权重已经记住事件结果或事后材料。

**Retrieval leakage**  
搜索或检索返回锚点之后的信息，包括更新页面、错误时间戳和后续推荐模块。

**Shortcut leakage**  
题面、选题方式或提前结算在无意中暴露答案相关线索。

**Baseline leakage**  
把市场价、人群概率或其他事后共识交给模型，使其复制基线即可高分。

**Market-blind**  
模型运行时看不到市场价；市场价只在评分环境中作为同锚点基线使用。

**Effective cutoff**  
模型实际掌握的知识版本边界，可能与厂商自报 knowledge cutoff 不同。

## 评分

**Proper scoring rule**  
如实报告真实信念时，期望得分最优的概率评分规则。

**Brier score**  
二元题的平方误差 `(p-y)^2`，越低越好。

**Paired Brier difference / `ΔB`**  
同题基线 Brier 减模型 Brier。大于零表示模型优于基线，适合配对比较。

**Brier Skill Score / BSS**  
`1 - B_agent / B_baseline`。便于解释，但在某些容易题或切片上分母可能不稳定。

**Calibration**  
模型报 70% 的事件是否约有 70% 发生。

**Resolution**  
模型能否把更可能发生与更不可能发生的事件分开，而不是永远报 50%。

**Murphy decomposition**  
把 Brier 分解成校准、分辨率和不确定性等部分，用于诊断。

## 工程与治理

**Corpus manifest**  
记录语料对象、版本、时间、哈希和来源的不可变清单。

**Evidence receipt**  
一次 Search/Read 返回的文档 ID、抓取时间、内容哈希和索引版本，用于重放和审计。

**Verified result**  
由 Raven 官方或授权独立方在统一环境复跑或核验 trace 后签发的结果。

**Self-reported result**  
参评方自行运行并提交的结果，可以公开，但不能与 verified 成绩混为一谈。
