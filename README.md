# beta-raven-bench

`beta-raven-bench` 是一个面向 forecasting agent 的历史回放题集。它从
Polymarket 中选取在 **2026 年 3 月任意时刻可交易**、并且目前已经完成结算的
二元事件，让 agent 在冻结到历史时间点的信息库中重新预测。

> **状态：Beta / 尚未完成最终双人盲审。** 当前版本适合数据管线、检索隔离和
> agent 回放实验，不应直接作为不可变的正式排行榜版本。

## 发布内容

| 产物 | 说明 |
|---|---|
| [`agent_view/candidates_600/questions.json`](data/polymarket-march-2026/agent_view/candidates_600/questions.json) | 600 题候选池 |
| [`agent_view/selected_300/questions.json`](data/polymarket-march-2026/agent_view/selected_300/questions.json) | 最终精选 300 题 |
| [`manifest.json`](data/polymarket-march-2026/manifest.json) | 参数、筛选漏斗、统计、文件哈希和来源收据 |
| [`information_policy.json`](data/polymarket-march-2026/information_policy.json) | 冻结检索、路径隔离和预测市场域名屏蔽策略 |
| [`build_polymarket_past_pool.py`](scripts/build_polymarket_past_pool.py) | 数据采集、标准化、筛选、分层抽样和导出实现 |
| [`validate_polymarket_past_pool.py`](scripts/validate_polymarket_past_pool.py) | public/full 两种校验模式 |
| [`manual_exclusions.json`](config/polymarket_march_2026_manual_exclusions.json) | 多轮审计形成的显式排除清单 |

公开仓库**不包含** 261MB Gamma raw 数据、sealed labels、源市场映射、筛选拒绝明细
和 ID 派生密钥。它们属于本地 operator 数据，不应进入 agent 可访问的仓库。

## 时间定义

- 目标月份：2026 年 3 月。
- `available`：市场在 `2026-04-01T00:00:00Z` 前开始接受订单，并且没有在
  `2026-03-01T00:00:00Z` 前结算。
- 预测锚点：`max(2026-03-01T00:00:00Z, acceptingOrdersTimestamp)`。
- 5 月状态截面：`2026-06-01T00:00:00Z`，采用右开边界。
- 214/300 题在 3 月 1 日已经开放；86/300 题在 3 月内首次开放。
- 所有精选题现在均已结算；“5 月未结算”只描述历史截面状态。

## 数据采集方式

1. **分领域拉取。** 通过 Gamma `events/keyset`，对 politics、geopolitics、
   courts、AI、science、business、economy、disease、climate、energy 和
   pop culture 11 个非体育标签分别抓取 `closed=true/false`，再按 market 合并去重。
2. **以 market 为题目单元。** Event 只是容器；一个二元 market 才对应一个
   FutureX 题目。原始扫描得到 31,550 个 market。
3. **历史可用性。** 优先使用 `acceptingOrdersTimestamp` 判断首次可交易时间，
   不把 `createdAt` 或 event 创建时间当作 availability。
4. **结算与 5 月截面。** 使用 market 级 `closedTime` 判断是否在 5 月底前结算；
   最终 Yes/No 结果同时通过公开 CLOB winner 字段交叉验证。
5. **硬过滤。** 排除体育、资产价格/估值/赔率、非 Yes/No、无最终结果、锚点前
   已结算、匿名占位符、例行数据发布、市场依赖型结算以及明显不自洽的规则。
6. **时间标准化。** 从题名和 resolution criteria 解析截止日，处理 ET/PT/UTC/
   CET/JST/KST；Gamma 的午夜日期值按 date-level deadline 归一化。
7. **审计剔除。** 多轮规则、泄漏、重复和难度审计累计显式排除 149 个高风险 market。
8. **分层选择。** 从 5,643 个合格题生成 600 题候选池，再依据领域、5 月状态、
   时间跨度、事件族、题面模板和机制族精选 300 题。

官方接口说明：

- [Polymarket Gamma Events API](https://docs.polymarket.com/api-reference/events/list-events-keyset-pagination)
- [Polymarket public CLOB client](https://docs.polymarket.com/trading/clients/public)
- [FutureX public dataset](https://huggingface.co/datasets/futurex-ai/Futurex-Online)

## 最终结果

### 筛选漏斗

| 阶段 | 数量 |
|---|---:|
| Gamma raw markets | 31,550 |
| 过滤、标准化和去重后 | 5,643 |
| 候选池 | 600 |
| 精选集 | 300 |
| 独立 Polymarket event cluster | 300 |
| CLOB 最终结果验证通过 | 300 |

### 5 月历史状态

| 状态 | 候选 600 | 精选 300 |
|---|---:|---:|
| 2026 年 5 月底前已结算 | 300 | 150 |
| 5 月底未结算、之后完成结算 | 300 | 150 |

### 精选集领域分布

| 领域 | 数量 |
|---|---:|
| Politics and elections | 48 |
| Geopolitics and conflict | 72 |
| Law and regulation | 13 |
| AI and technology | 44 |
| Science and space | 11 |
| Business and organizations | 12 |
| Macroeconomics and public policy | 24 |
| Health and public safety | 2 |
| Climate and environment | 14 |
| Culture and media | 29 |
| Other | 31 |

最大单领域占比为 24%，未超过 25%。精选集中包含 GPT-6、AI 产品发布、
美伊冲突、俄乌停火、法院裁决、央行决策、公司行动、选举和科学事件等题型。

### 难度与时间跨度

- 启发式难度：196 hard、104 medium。
- 时间跨度：15 题 `<7d`、33 题 `7–30d`、54 题 `31–60d`、
  64 题 `61–120d`、134 题 `>120d`。
- FutureX `level` 全部为 1，因为这些题在提交格式上都是 binary single-choice；
  语义难度由扩展字段 `forecast_difficulty` 表示。

## FutureX 兼容格式

每题至少包含：

```json
{
  "id": "opaque-uuid",
  "prompt": "historically anchored question and resolution criteria",
  "end_time": "2026-06-30T23:59:59Z",
  "level": 1,
  "en_title": "Will ...?"
}
```

额外保留 `task_type`、`options`、`forecast_anchor`、`forecast_difficulty`、
`domain` 和 `temporal_archetype`，与 FutureX 的 passthrough 读取方式兼容。

## 泄漏边界

题名仍可能通过不受限制的互联网检索反查到预测市场结果。运行 benchmark 时必须：

- 只向 agent 挂载 `agent_view/`；
- 使用冻结 corpus，不开放实时互联网；
- 强制 `document.crawl_time <= forecast_anchor`；
- 屏蔽 Polymarket、Gamma、CLOB、Kalshi、Manifold 等预测市场来源；
- 不向 agent 暴露 labels、provenance、market IDs 或 post-anchor 文档。

完整约束见 [`information_policy.json`](data/polymarket-march-2026/information_policy.json)。

## 复现与校验

重新采集并生成完整本地 operator 数据：

```bash
python3 scripts/build_polymarket_past_pool.py --year 2026
python3 scripts/validate_polymarket_past_pool.py
```

仅校验公开仓库中的 agent view：

```bash
python3 scripts/validate_polymarket_past_pool.py --public-only
```

构建器只依赖 Python 标准库。完整采集会重新下载当前 Gamma 数据，因此结果可能受
上游后续修订影响；复现历史发布版本时应保存 raw 文件哈希或外部归档。

## 已知限制

- Gamma 是当前数据库视图，不是 2026 年 3 月的规则文本历史快照。
- 38/300 题的题面截止时间与 Gamma `endDate` 相差超过三天，需要最终人工裁定。
- `human_review_complete=false`；当前分数和难度是可复现启发式，不等同于双人盲审。
- 公开 manifest 会保留未发布 operator 文件的路径、大小和哈希收据，但不会公开内容。

