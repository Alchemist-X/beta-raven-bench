# AI 预测文献综述

本综述关注的是“对未来离散事件报概率”的 AI forecasting，而不是一般数值时间序列预测。

## 先读什么

如果只想理解 Raven 为什么存在：

1. [研究问题与领域地图](01-field-and-problem.md)
2. [评测环境路线](02-evaluation-environments.md)
3. [泄漏、检索与审计](03-leakage-retrieval-and-audit.md)
4. [Raven 的竞争定位](05-raven-positioning.md)

如果准备做指标、训练或论文实验，再读：

5. [评分、训练与决策层](04-scoring-training-and-decisions.md)
6. [完整参考文献](../references.md)

## 文献地图

| 路线 | 核心问题 | 代表工作 | 对 Raven 的意义 |
|---|---|---|---|
| A. 评测环境 | 如何获得可信且可持续的题与信息环境 | Autocast、ForecastBench、BTF-2、FutureSim | 决定 benchmark 的基本形态 |
| B. 检索 | 如何取得有用资料而不越过时间边界 | Autocast++、AIA、Temporal Leakage | Raven 最大的工程与科学壁垒 |
| C. 评分 | 如何诚实评概率、诊断过程和连接决策 | Brier/Murphy、Proxy Scoring、M6 | 核心概率评分成熟，过程与决策仍开放 |
| D. 训练 | 如何把未来结算转成监督或 RL 信号 | Halawi、Mantic、Future-as-Label | Raven 环境可在后期成为训练基础设施 |
| E. 审计 | 如何证明 cutoff、检索和题目没有作弊 | Paleka、Dated Data、Shapley-DCLR | 决定 Raven 的 claim 能否被相信 |
| 邻域参照 | 其他 agent benchmark 如何处理真实环境与过程 | ToolGym、StockBench、TFRBench | 帮助设计 runner、过程审计和范围边界 |

## 贯穿全部工作的主线

领域真正未解决的并不是“有没有概率评分公式”，而是能否证明：

```text
模型预测 p = f(F_t)
```

其中 `F_t` 真的只包含锚点 `t` 之前可获得的信息。

Live 用“答案尚不存在”建立物理边界，但等待结算、难复跑且样本积累慢。Pastcast/TimeLock 用冻结历史环境换取可复跑与大样本，却必须处理参数、检索、选题和市场四条泄漏通道。

Raven 的研究路线不是在二者中只选一边，而是以 TimeLock 建立主评测，用 Live Sentinel 验证外部效度。

## 证据使用规则

- 表中数字是原论文或用户提供综述中的报告值，不自动等于我们已经复现。
- 未评审论文、匿名 OpenReview 稿和官网报告应明确标记成熟度。
- 论文声称“无泄漏”不等于已经证明无泄漏；优先看实际防线与审计方法。
- Raven 的设计推论集中在[竞争定位](05-raven-positioning.md)，不混入各论文摘要。

最后更新：2026-07-21。
