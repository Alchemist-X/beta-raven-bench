# Raven 文档中心

这里把 Raven 的研究依据、产品路线和行业采用策略分开保存，并按“先结论、后证据、再实施细节”渐进式披露。

Raven 当前是一个规划中的真实世界 AI 预测评测环境。工作命名为：

- **Raven TimeLock**：模型站在被冻结的历史时点，只能用当时可获得的信息预测其后的未来；
- **Raven Live**：模型预测尚未结算、答案尚不存在的真实未来事件；
- **Raven Forecasting Suite**：同时包含上述两种时间模式的总 benchmark。

这些名称尚未正式冻结，协议与代码中的最终名称应在 Phase 0 决策后确定。

## 三种阅读方式

### 3 分钟：先理解我们要做什么

1. [执行摘要](00-executive-summary.md)
2. [路线总览](roadmap/README.md)
3. [行业采用总览](adoption/README.md)

### 20 分钟：理解为什么这样设计

1. [研究问题与领域地图](literature/01-field-and-problem.md)
2. [评测环境路线](literature/02-evaluation-environments.md)
3. [泄漏、检索与审计](literature/03-leakage-retrieval-and-audit.md)
4. [Raven 的竞争定位](literature/05-raven-positioning.md)
5. [架构与工作流](roadmap/01-architecture-and-workstreams.md)

### 深读：准备参与研究或开发

1. [AI 预测文献综述入口](literature/README.md)
2. [评分、训练与决策层](literature/04-scoring-training-and-decisions.md)
3. [里程碑与质量 Gate](roadmap/02-milestones-and-quality-gates.md)
4. [产品与传播策略](adoption/01-product-and-distribution.md)
5. [Verified、治理与持续维护](adoption/02-verified-governance-and-maintenance.md)
6. [术语表](glossary.md)
7. [参考文献](references.md)
8. [Forecasting 问题的形式化定义](specification/01-forecasting-problem-definition.md)

## 信息架构

```text
docs/
├── README.md
├── 00-executive-summary.md
├── glossary.md
├── references.md
├── specification/
│   └── 01-forecasting-problem-definition.md
├── literature/
│   ├── README.md
│   ├── 01-field-and-problem.md
│   ├── 02-evaluation-environments.md
│   ├── 03-leakage-retrieval-and-audit.md
│   ├── 04-scoring-training-and-decisions.md
│   └── 05-raven-positioning.md
├── roadmap/
│   ├── README.md
│   ├── 01-architecture-and-workstreams.md
│   └── 02-milestones-and-quality-gates.md
└── adoption/
    ├── README.md
    ├── 01-product-and-distribution.md
    └── 02-verified-governance-and-maintenance.md
```

## 文档边界

- `literature/` 记录已有工作的设定、方法、证据和局限，不把 Raven 的推断伪装成论文结论。
- `specification/` 记录可直接实现和复现的规范性定义、公式与统计口径。
- `roadmap/` 记录 Raven 的设计选择、工程任务、里程碑和验收条件。
- `adoption/` 记录如何降低外部采用成本、建立可信榜单和长期维护标准。
- `Plan/` 保留最初的完整审批版路线，不作为日常阅读入口。

## 状态标记

文档中的重要判断按以下方式理解：

- **已有证据**：来自论文、公开系统或已完成实测；
- **Raven 设计**：团队建议，尚需实现和验证；
- **Gate**：若不满足，就不能进入下一阶段或对外使用相关 claim；
- **待决定**：需要项目负责人明确选择，不能由实现者默认替代。

最后更新：2026-07-21。
