# Verified、治理与持续维护

## 1. 为什么必须区分自报与 Verified

同一个模型名称可能因为以下差异产生完全不同的成绩：

- API snapshot；
- system prompt 和 scaffold；
- 搜索、阅读和 token 预算；
- 重试与并发策略；
- 题集、语料、索引和 evaluator 版本；
- 是否删除失败任务；
- 是否接触市场价或额外公网。

因此榜单至少分为：

### Self-reported

参评方自行运行并提交。适合开发和快速分享，但必须完整披露配置，不与 verified 主榜混排。

### Raven Verified

Raven 官方或授权独立机构在固定环境复跑，或核验来自受信环境的签名 trace。模型权重和 API key 可以保密，但运行条件必须可审计。

## 2. Verified 提交流程

```text
提交 Adapter/Container/Remote Endpoint
→ 配置和披露 Lint
→ 20 题 Smoke Test
→ 冻结 model/scaffold/budget
→ 在 rotating verified set 运行
→ 保存 trace、receipt 和 run manifest
→ 自动泄漏与失败检查
→ 抽样人工复核和必要复跑
→ 统计审核
→ 签发 Result Card
→ 参评方确认公开内容
→ 发布 Verified 榜单
```

### 可保密内容

- 模型权重；
- API credentials；
- 私有系统的实现细节；
- 不影响公平判断的商业配置。

### 必须披露内容

- 精确模型 snapshot；
- scaffold 类型和关键步骤；
- 可用工具；
- query/read/token/time budgets；
- prompt 或至少 prompt hash 与审核访问；
- 重试和 ensemble 次数；
- 失败与排除数量；
- benchmark、corpus、index 和 runner 版本。

无法满足最低披露时，只能列入 self-reported。

## 3. Verified set 的开放策略

推荐分配：

- 25% public dev；
- 60% rotating verified；
- 15% audit/calibration。

规则：

- verified 题不进入 Raven-Train；
- 参评模型通过环境运行，不直接获得答案和 hidden market baseline；
- 每个 major 版本退休后，在许可允许时公开历史 verified 任务、结算和审计；
- 发现泄漏或过度优化时，提前退休受影响集合；
- 新旧 major 版本榜单分别保存，不强行拼接。

全隐藏不利于审计，全公开容易污染；轮换与退休公开是在透明度和长期有效性之间的折中。

## 4. 版本政策

### Patch：`1.0.x`

- 修复不改变 benchmark 含义的实现 bug；
- 文档、adapter 和基础设施修复；
- 若分数可能改变，必须明确标记并评估是否重跑。

### Minor：`1.x.0`

- 增加任务、adapter、诊断指标或非破坏性功能；
- 主协议和主要分数含义保持兼容。

### Major：`x.0.0`

- 修改主任务分布、时间模式、评分或运行协议；
- 新建榜单；
- 提供迁移报告，不把新旧分数直接比较。

每个结果绑定：

```text
protocol + task set + corpus + index + retriever + runner + model
```

不能只写“Raven score”。

## 5. 坏题与申诉

### 可申诉问题

- 结算错误；
- 锚点前已经确定；
- 题面歧义；
- 环境或检索故障；
- 市场/后验信息泄漏；
- evaluator bug；
- 不公平的模型适配。

### 处理流程

1. 提交 task challenge 和证据；
2. maintainer 初筛影响等级；
3. 独立 reviewer 复核；
4. 发布决定与理由；
5. 标记 valid、patched、retired 或 disputed；
6. 判断是否影响历史结果；
7. 必要时重跑或发布修正榜；
8. 所有决定进入公开 changelog。

不能静默改题或覆盖历史成绩。

## 6. 持续修复是核心产品能力

真实数据和外部服务会不断变化：

- 来源站点和新闻元数据发生变化；
- 新模型发现过去未见的 shortcut；
- 任务结算出现争议；
- API 和 provider 行为更新；
- 检索依赖升级；
- 某些领域逐渐饱和。

建议运营节奏：

- 每周处理 P0/P1 issues；
- 每月 patch release；
- 每季度任务与模型 refresh；
- 每半年发布审计与稳定性报告；
- 每年 major Raven-Verified；
- 对重大泄漏即时冻结受影响榜单。

Benchmark 团队必须长期保留 task ops、infra on-call 和统计负责人。论文接受不能成为维护终点。

## 7. 治理结构

### Maintainer team

负责日常开发、运行、问题响应和 release。

### Scientific advisory group

由 forecasting、统计、benchmark 和安全研究者组成，评审 construct、指标和重大版本。

### Industry design partners

提供接入与运行反馈，但不单独决定题目、规则或分数。

### Independent auditors

定期抽查 corpus provenance、leakage、结算和 verified run。

### Conflict policy

- maintainer 与参评模型公司的关系公开；
- 重大规则变化预先 RFC；
- 对所有参评方使用相同窗口和条件；
- 不为赞助者提供提前答案或有利切片；
- 评测和训练业务尽可能权限隔离。

## 8. 云端并行的公平规则

云端系统负责把成千上万次 run 分发到 workers，但必须保证：

- task sharding 不改变题目分布；
- worker image 和环境一致；
- 并发不触发某模型特有的限流劣势，或明确计入；
- 只对基础设施故障重试；
- 不能因为预测看起来差而选择性重跑；
- 所有重试原因进入 manifest；
- 断点续跑不读取中间榜单做适应性修改。

云端并行的目标是降低时间和运维成本，不是改变评测条件。

## 9. 可信度报告

每个 major 版本应同步发布：

- corpus provenance 和 coverage；
- leakage sampling 与置信上界；
- task exclusion/retirement log；
- resolution agreement 和错误率；
- power 和 ranking stability；
- TimeLock/Live 一致性；
- 运行成本与故障率；
- 外部复现差异；
- 已知限制和下一版本计划。

当模型公司能够引用的不只是分数，还有这套可信度证据，Raven 才会从“一个排行榜”变成行业测量标准。
