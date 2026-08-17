# Raven 开发路线

## 一页结论

Raven 应按以下依赖顺序建设：

```text
语料真实性与许可
→ 不可变 corpus manifest
→ Time-fenced Search/Read
→ 任务、锚点与结算管线
→ Context/Agent runner
→ 评分、统计与审计
→ 外部 closed beta
→ Raven Verified 与公开 v1
→ Live Sentinel 和持续更新
→ 独立 Raven-Train
```

不能调换的依赖是：没有可信语料，就没有 time-fenced retrieval；没有稳定 runner 和统计协议，就不应先发榜；没有轮换 verified set，就不应先开放训练环境。

## 六个阶段

| 阶段 | 时间目标 | 核心问题 | 退出结果 |
|---|---|---|---|
| Phase 0 | 2026-07-22—08-07 | 资产是否真的可用 | provenance、许可和成本 Gate |
| Phase 1 | 2026-08-08—09-18 | 能否可靠锁住信息边界 | Corpus Gateway Alpha |
| Phase 2 | 2026-09-19—10-30 | 能否端到端比较模型 | 200–300 事件 MVP |
| Phase 3 | 2026-10-31—12-15 | 科学 claim 是否站得住 | 1,000 事件、红队与审计 |
| Phase 4 | 2026-12-16—2027-01-31 | 外部团队是否真能使用 | 3–5 家 design partner beta |
| Phase 5 | 2027-02-01—03-31 | 能否公开成为标准 | v1、论文、Verified 榜单 |
| Phase 6 | 2027-04 起 | 能否持续维护和采用 | Live、季度更新、年度 major |

## 三条不能牺牲的主线

### 科学可信度

- 参数、检索、选题、market 和结算五类审计；
- 同题 paired comparison；
- 按 event 聚类统计；
- TimeLock 与 Live 交叉验证；
- 预注册指标和排除规则。

### 工程可复现性

- corpus、index、retriever、runner、model 都有精确版本；
- 每次检索有 evidence receipt；
- 完整 trace 可重放；
- 基础设施失败和模型失败分开；
- adapter 接口不绑定单一模型提供方。

### 行业可采用性

- 一天内完成 smoke test；
- 完整 run 的成本和时长可预估；
- verified/self-reported 分榜；
- 结果卡可直接进入 system card；
- 坏题、申诉、版本和退休流程公开。

## v1 范围

建议：

- 英语二元概率题；
- 至少 1,000 个相对独立事件；
- 每事件 2–4 个锚点；
- TimeLock–Context 与 TimeLock–Agent 两个正式主赛道；
- Live 先作为 Sentinel；
- 6 个现实领域，单一领域不超过 25%；
- 至少 5 个参考模型/agent；
- 至少一个同锚点 market 或 crowd baseline；
- verified、dev 和 audit/calibration 三类数据隔离。

## 详细文档

- [架构与工作流](01-architecture-and-workstreams.md)
- [里程碑与质量 Gate](02-milestones-and-quality-gates.md)
- [行业采用策略](../adoption/README.md)
- [完整原始审批计划](../../Plan/2026-07-21-raven-benchmark-industry-adoption-roadmap.md)
