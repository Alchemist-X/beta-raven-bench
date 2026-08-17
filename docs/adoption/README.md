# 如何让 Raven 成为行业通用 Benchmark

## 核心判断

Benchmark 的流行不是靠一次 launch 制造的，而是来自一个持续循环：

```text
测量问题重要
→ 结果能揭示模型真实差距
→ 接入和运行足够便宜
→ 成绩可以被第三方验证
→ 厂商敢在正式报告引用
→ 社区发现问题并参与修复
→ 新版本更可信、更易用
→ 更多模型默认报告
```

OSWorld 的影响力并不只来自任务数据，而来自统一 agent interface、真实可执行环境、云端并行、public evaluation、Verified 更新和持续社区修复。Raven 应复制这种“测量标准 + 运行基础设施 + 认证与治理”的结构，而不是复制 GUI 任务本身。

## 模型公司采用一个 benchmark 的七个条件

1. **重要**：测的是用户和研究者真正关心的能力；
2. **有效**：分数确实来自能力，而不是泄漏、市场价或坏题；
3. **可比**：模型、scaffold、预算和题集差异被记录；
4. **低摩擦**：标准 adapter、smoke test、可预估成本；
5. **可诊断**：能说明输在检索、综合、更新还是校准；
6. **可辩护**：有 CI、审计、申诉、版本和 verified 结果；
7. **中立且持续**：规则不为某一家临时变化，项目不会论文后停摆。

## Raven 的采用产品栈

| 层 | 产品 | 解决的采用障碍 |
|---|---|---|
| 标准 | Protocol、schemas、adapter contract | 每家公司无需重写评测 |
| 开发 | 20 题 smoke set、local emulator | 不接触全量环境也能调通 |
| 运行 | 云端并行 Harness、预算与成本估算 | 完整评测不需要数周运维 |
| 证据 | trace、evidence receipt、result card | 结果可解释和复核 |
| 认证 | Raven Verified | 模型公司可在 system card 引用 |
| 传播 | leaderboard、trajectory explorer、发布报告 | 结果易理解、易讨论 |
| 治理 | 版本、申诉、退休、外部审计 | 厂商不用担心被坏题永久误伤 |

## 两类增长不能混淆

### 学术影响

- 论文引用；
- 数据或环境被后续研究复用；
- 新方法在 Raven 上做消融；
- benchmark 成为 forecasting 论文默认实验之一。

### 行业采用

- 新模型发布主动报告 Raven；
- 独立评测平台原生集成；
- 模型公司提供 adapter 或参与 verified run；
- system card 使用 Raven result card；
- benchmark 版本与模型版本形成长期时间序列。

两者都重要，但模型公司的正式采用比 GitHub star 或短期社交传播更接近最终目标。

## 渐进式采用路线

1. **Design partners**：发布前与少量模型公司和独立研究者共同试跑；
2. **Closed beta**：冻结协议，验证接入、成本、争议和复现；
3. **Verified launch**：首发即有多家模型和独立审计，而不是空榜；
4. **Integration phase**：进入模型评测框架、system-card pipeline 和第三方平台；
5. **Community flywheel**：公开问题修复、任务贡献、版本更新和年度 challenge；
6. **Standard phase**：建立外部治理席位和稳定年度 Raven-Verified。

## 详细文档

- [产品与传播策略](01-product-and-distribution.md)
- [Verified、治理与持续维护](02-verified-governance-and-maintenance.md)
- [开发里程碑](../roadmap/02-milestones-and-quality-gates.md)
