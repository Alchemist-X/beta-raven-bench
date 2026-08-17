# Forecasting 问题的形式化定义

状态：Draft 0.1  
用途：benchmark specification、论文方法章节和人类—Agent 对照实验的共同定义。

## 1. 一句话定义

**Forecasting 是一个受时间与信息边界约束的概率预测问题：在结果尚未知的锚点时刻，预测者依据当时允许获得的信息，对一个预先规定结算规则的未来事件给出发生概率；事件结算后，使用 proper scoring rule 评价所报告概率的质量。**

对于第 `i` 个二元预测问题，最小形式为：

$$
q_i=\left(x_i,t_{0,i},t_{1,i},\rho_i,\mathcal F_i(t_{0,i})\right).
$$

其中：

- $x_i$：问题文本及必要背景；
- $t_{0,i}$：forecast anchor，即信息截止与预测所代表的时点；
- $t_{1,i}$：outcome observation deadline，即判断事件是否发生的观察截止时点，且 $t_{0,i}<t_{1,i}$；
- $\rho_i$：在预测前固定的结算函数或结算规则；
- $\mathcal F_i(t_{0,i})$：截至 $t_{0,i}$，该实验协议允许预测者获得的信息集合。

这里的事件通常是“是否在 $t_{1,i}$ 之前或指定区间内发生”，不应笼统写成“是否恰好在 $t_{1,i}$ 时刻发生”。

## 2. 结果变量与可结算性

设 $\omega_{\le t_{1,i}}$ 表示现实世界截至 $t_{1,i}$ 的状态或事件轨迹。结算函数产生结果：

$$
Y_i=\rho_i\!\left(\omega_{\le t_{1,i}}\right)\in\{0,1,\bot\}.
$$

其中：

- $Y_i=1$：事件按预先规定的条件发生；
- $Y_i=0$：事件按预先规定的条件未发生；
- $Y_i=\bot$：问题无法有效结算，例如规则存在实质歧义、权威来源冲突或事件被正式作废。

一个合格的二元 forecasting question 必须满足：

1. **前瞻性**：在 $t_{0,i}$ 时，$Y_i$ 尚未知且没有被事实性确定；
2. **完备性**：Yes 与 No 互斥且穷尽所有有效结果；
3. **可判定性**：$\rho_i$ 能依据预先指定的证据判断 $Y_i$；
4. **规则冻结**：$x_i$、$t_{1,i}$ 和 $\rho_i$ 必须在预测提交前冻结；
5. **无后见修改**：不能在知道结果后，为使某个答案成立而改变问题含义；
6. **报告延迟不改变结果窗口**：实际裁决时刻 $t_{\mathrm{eval},i}$ 可以晚于 $t_{1,i}$，但裁决只能判断 $t_{1,i}$ 前定义的事实：

$$
t_{\mathrm{eval},i}\ge t_{1,i}.
$$

除非协议事先定义了 void penalty，否则 $Y_i=\bot$ 的问题不进入主评分，并必须单独报告作废率。

## 3. Agent、搜索与可审计轨迹

将一个预测 Agent 定义为：

$$
A=(M_\theta,S,D),
$$

其中：

- $M_\theta$：模型及固定参数、系统提示和版本；
- $S$：搜索与工具使用策略；
- $D$：把已获得信息综合成最终概率的决策规则。

Agent 在每一步 $k$ 根据当前历史选择动作 $a_{i,k}$，环境返回观察 $o_{i,k}$：

$$
a_{i,k}=S(H_{i,k-1}),
\qquad
o_{i,k}=E_i(a_{i,k}),
$$

$$
H_{i,k}=\left(H_{i,k-1},a_{i,k},o_{i,k}\right),
\qquad
H_{i,0}=q_i.
$$

完成搜索后，Agent 输出：

$$
\hat p_i=D(H_{i,K_i})=A(q_i,H_i)\in[0,1],
$$

其中 $\hat p_i$ 表示 Agent 对 $Y_i=1$ 的主观概率。

### 3.1 “允许任意搜索”的严格含义

“任意搜索”不能理解为不受约束地访问任何网页。正确表述是：

> Agent 可以在预注册的工具、时间和成本预算内，自主选择任意合法搜索动作；但所有返回给 Agent 的观察都必须满足该评测轨道的信息边界。

形式上，对所有搜索步骤要求：

$$
o_{i,k}\in\mathcal F_i(t_{0,i}),
\qquad
k\le K_{\max},
\qquad
C(H_i)\le B_i,
$$

其中 $K_{\max}$ 是最大工具步数，$C(H_i)$ 是本次运行的成本，$B_i$ 是预注册预算。

- **Live 模式**：只能使用提交截止前真实可得的信息；预测提交后获得的信息不得回填。
- **历史冻结模式**：搜索只能访问截至 $t_{0,i}$ 的冻结语料快照，网页当前版本和搜索引擎的日期过滤不能自动视为合格历史信息。

### 3.2 `H` 应记录什么

$H_i$ 应定义为**可观测、可重放的交互轨迹**，至少包括：

- 完整输入、系统提示及 question 版本；
- 每次工具调用、查询参数和时间戳；
- 每次返回的文档 ID、内容版本、抓取时间和哈希；
- 代码执行、结构化中间产物、错误和重试；
- 模型、工具、索引和运行环境版本；
- 最终概率、简明理由和提交时间。

规范不应声称记录了“所有内部思考过程”。模型未外显的内部 chain-of-thought 不可观测，也不应成为可复现性的必要条件。正式审计对象应是外部动作、获得的证据、可见中间产物和最终输出；自然语言 rationale 可以保存，但不能被当作内部推理的完整或忠实证明。

## 4. Forecasting 的统计目标

在给定信息边界下，理论上的目标概率是：

$$
p_i^\star
=
\Pr\!\left(Y_i=1\mid\mathcal F_i(t_{0,i})\right).
$$

Agent 的任务不是输出一个确定类别，而是使 $\hat p_i$ 尽可能接近 $p_i^\star$。

需要注意：对于一次性的现实事件，我们只观察到一个结算结果 $Y_i$，无法从单题直接观察其“真实概率”。因此，预测质量必须在一组预先定义、足够多且统计依赖得到处理的问题上评价。

## 5. Brier score

### 5.1 单题分数

对有效结算的二元问题，Agent 的 Brier loss 定义为：

$$
BS_i^{(A)}=(\hat p_i-Y_i)^2.
$$

其取值范围为：

$$
0\le BS_i^{(A)}\le1,
$$

且越低越好。

例如，Agent 报告 $\hat p_i=0.8$：

- 若事件发生，$BS_i=(0.8-1)^2=0.04$；
- 若事件未发生，$BS_i=(0.8-0)^2=0.64$。

### 5.2 为什么 Brier score 适合这个问题

令 $p_i^\star=\Pr(Y_i=1\mid\mathcal F_i(t_{0,i}))$。在信息集合 $\mathcal F_i(t_{0,i})$ 下，报告概率 $p$ 的条件期望损失为：

$$
\mathbb E\!\left[(p-Y_i)^2\mid\mathcal F_i(t_{0,i})\right]
=
(p-p_i^\star)^2+p_i^\star(1-p_i^\star).
$$

第二项与报告的 $p$ 无关，因此唯一最优报告是：

$$
p=p_i^\star.
$$

所以 Brier score 是严格 proper scoring rule：如果预测者希望最小化期望损失，最优策略是诚实报告其真实概率判断，而不是故意夸大或压低置信度。

### 5.3 数据集总分

对 $N$ 个有效问题，设预注册权重 $w_i\ge0$ 且 $\sum_iw_i=1$，Agent 总分为：

$$
BS_A
=
\sum_{i=1}^{N}w_i(\hat p_i-Y_i)^2.
$$

默认等权时：

$$
BS_A
=
\frac{1}{N}\sum_{i=1}^{N}(\hat p_i-Y_i)^2.
$$

权重必须在查看模型结果前确定。若一个现实事件下面展开了多个高度相关问题，应先在 event cluster 内聚合，再在独立事件之间平均，避免题目数量多的事件支配总分。

### 5.4 Brier score 能与不能回答什么

Brier score 同时受到 calibration 与 discrimination/resolution 的影响，适合用作概率预测质量的主指标，但单个均值不能说明模型为什么好或坏。正式报告还应给出：

- calibration curve 或预注册的 calibration error；
- 概率分布与 resolution/discrimination；
- 按领域、预测时距和题目来源划分的切片；
- event-clustered 置信区间；
- 作废率、缺失率和失败率。

本规范中的 `Brier score` 始终指 loss，越低越好。若产品界面展示 `1-BS` 或其他“越高越好”的变换，必须另行命名，避免方向混淆。

## 6. 多锚点评测

若同一事件 $i$ 在多个锚点 $t_{0,i,1},\ldots,t_{0,i,K_i}$ 上预测，记概率为 $\hat p_{i,k}$。这些预测共享同一个 $Y_i$，不是 $K_i$ 个独立事件。

可先计算事件内时间加权分数：

$$
BS_i^{(A)}
=
\sum_{k=1}^{K_i}v_{i,k}(\hat p_{i,k}-Y_i)^2,
\qquad
\sum_{k=1}^{K_i}v_{i,k}=1,
$$

再对事件聚合：

$$
BS_A=\sum_{i=1}^{N}w_iBS_i^{(A)}.
$$

$v_{i,k}$ 应等权或按预注册的时间权重计算。置信区间和显著性检验必须至少按 event cluster 重采样，不能把同一事件的多个锚点当作独立样本。

## 7. 人类与 Agent 的公平比较

设第 $h$ 位人类预测者对问题 $i$ 给出概率 $p_{i,h}^{(H)}$。在计算分数前，必须先声明“人类基线”指哪一个 estimand：

1. **Typical individual human**：随机选择一位符合纳入标准的人类，其单独预测的期望表现；
2. **Crowd forecast**：先聚合多位人类的概率，再对聚合概率评分；
3. **Expert/superforecaster baseline**：按预先规定的专家资格和聚合方法形成的基线。

三者不能混用。尤其是“人类预测的平均分”和“人类平均概率的分数”不是同一个量。

### 7.1 Typical individual human

若问题 $i$ 有 $m_i$ 位人类作答，先在问题内平均个人损失，再对问题等权或按预注册权重聚合：

$$
BS_{H,\mathrm{individual}}
=
\sum_{i=1}^{N}w_i
\left[
\frac{1}{m_i}
\sum_{h=1}^{m_i}
(p_{i,h}^{(H)}-Y_i)^2
\right].
$$

这个量回答的是：“在这些问题上，一位典型人类预测者的预测损失是多少？”若不同人回答不同题，还应报告参与者层面的分数分布，并使用能同时处理 participant 与 event 聚类的统计模型或重采样方法。

### 7.2 Crowd forecast

若比较对象是 crowd forecast，必须预先固定聚合函数 $G$：

$$
\hat p_i^{(H)}
=
G\!\left(p_{i,1}^{(H)},\ldots,p_{i,m_i}^{(H)}\right).
$$

最简单的预注册方案是算术平均：

$$
\hat p_i^{(H)}
=
\frac{1}{m_i}\sum_{h=1}^{m_i}p_{i,h}^{(H)}.
$$

人类基线的 Brier score 为：

$$
BS_H
=
\sum_{i=1}^{N}w_i(\hat p_i^{(H)}-Y_i)^2.
$$

这个量回答的是：“聚合后的人类群体概率表现如何？”由于先平均概率可以消除一部分个体噪声，crowd Brier 通常优于 typical individual human；因此论文必须明确写 `individual-human baseline` 或 `crowd baseline`，不能只写 `human performance`。

应使用同题配对差异比较 Agent 与人类：

$$
d_i
=
(\hat p_i^{(H)}-Y_i)^2
-(\hat p_i-Y_i)^2,
$$

$$
\Delta_{A,H}
=
BS_H-BS_A
=
\sum_{i=1}^{N}w_id_i.
$$

解释如下：

- $\Delta_{A,H}>0$：Agent 的平均 Brier loss 更低，优于人类基线；
- $\Delta_{A,H}=0$：没有观察到平均差异；
- $\Delta_{A,H}<0$：人类基线更好。

也可以报告相对技能分数：

$$
BSS_{A\mid H}=1-\frac{BS_A}{BS_H},
$$

但当 $BS_H$ 很小或切片样本很少时，BSS 会不稳定，因此主推断应使用 paired difference $\Delta_{A,H}$ 及其置信区间。

### 7.3 公平比较的必要条件

若要声称“Agent 的 forecasting 能力优于人类”，至少需要：

1. Agent 与人类回答相同的问题版本和相同锚点；
2. 使用相同的结算规则和最终标签；
3. 信息边界相同，或明确把实验分成不同工具轨道；
4. 时间、搜索、成本和外部协作预算可比；
5. 市场价格、人群概率等强基线对双方同样可见或同样隐藏；
6. 预先规定缺失回答、超时、拒答和无效概率的处理方式；
7. 在查看结果前固定人类聚合函数、题目权重、切片和排除规则；
8. 对同题差异做 paired inference，并按 event cluster 构造置信区间。

如果 Agent 可以无限搜索，而人类既不能搜索也没有相当时间，那么实验只能支持“该 Agent 系统在该资源配置下优于该人类条件”，不能直接支持“AI 本身比人类更会预测”。

## 8. 推荐的实验协议表述

下面这段可以直接用于论文或 benchmark 文档：

> 对每个二元事件 $q_i$，我们在预先指定的 forecast anchor $t_{0,i}$ 冻结问题文本、结算规则与可用信息边界。Agent 在统一的工具和资源预算下检索信息，并在结果未知时提交概率 $\hat p_i\in[0,1]$，表示其对事件在观察截止时点 $t_{1,i}$ 前满足结算条件的信念。我们记录所有可观测的模型输入、工具动作、检索证据、结构化中间产物和最终输出，但不把不可观测的内部 chain-of-thought 作为复现要求。观察窗口结束后，独立结算程序依据预先冻结的规则得到 $Y_i\in\{0,1\}$。主指标为 mean Brier loss，$BS=N^{-1}\sum_i(\hat p_i-Y_i)^2$，越低越好。Agent 与人类基线在同一组问题上通过 paired Brier difference，$\Delta_{A,H}=BS_H-BS_A$，进行比较，并使用按 event cluster 重采样的置信区间量化不确定性。

## 9. 最小协议与生产级协议

用户界面可以只展示两个时间：

```text
t0：信息截止并提交预测
t1：事件观察截止并进入结算
```

但生产级实现建议拆成三个时间字段：

$$
t_{\mathrm{anchor},i}
\le
t_{\mathrm{submit},i}
<
t_{\mathrm{resolve},i}.
$$

- $t_{\mathrm{anchor},i}$：允许信息的截止时间；
- $t_{\mathrm{submit},i}$：预测实际提交时间；
- $t_{\mathrm{resolve},i}$：事件观察截止时间，即上文的 $t_{1,i}$。

另记录 $t_{\mathrm{adjudicate},i}\ge t_{\mathrm{resolve},i}$，表示官方完成裁决的时间。这样可以区分“信息应截止到什么时候”“模型何时真正提交”和“事件按哪个时间窗口判断”。

## 10. Word 与 Markdown 可复制公式

### Markdown / LaTeX

```latex
q_i=\left(x_i,t_{0,i},t_{1,i},\rho_i,\mathcal F_i(t_{0,i})\right)
```

```latex
Y_i=\rho_i\!\left(\omega_{\le t_{1,i}}\right)\in\{0,1,\bot\}
```

```latex
\hat p_i=A(q_i,H_i)\in[0,1]
```

```latex
p_i^\star=\Pr\!\left(Y_i=1\mid\mathcal F_i(t_{0,i})\right)
```

```latex
BS_i^{(A)}=(\hat p_i-Y_i)^2
```

```latex
BS_A=\frac{1}{N}\sum_{i=1}^{N}(\hat p_i-Y_i)^2
```

```latex
\hat p_i^{(H)}=\frac{1}{m_i}\sum_{h=1}^{m_i}p_{i,h}^{(H)}
```

```latex
\Delta_{A,H}=BS_H-BS_A
```

```latex
BSS_{A\mid H}=1-\frac{BS_A}{BS_H}
```

### 粘贴到 Word

在 Word 中按 `Alt` + `=` 插入公式，将公式输入模式设为 LaTeX，再粘贴上面代码块内的单行内容。不要连同代码块的三个反引号一起复制。

## 11. 不应采用的含混表述

不建议写：

> 在时间点 t0 给 Agent 输入事件 qi，让它输出 t1 时刻 qi 会发生的概率，允许 Agent 做任意搜索并记录所有思考过程。t1 到来时计算 Brier score。

原因是：

- “t1 时刻发生”混淆了发生窗口、观察截止和裁决时间；
- “任意搜索”没有规定信息时间边界、工具和预算；
- “所有思考过程”包含不可观测的内部状态，无法验证；
- 没有定义问题的结算函数、void 状态和无效题处理；
- 没有定义多题聚合、相关事件、多锚点和人类对照的统计单位。

本文件第 8 节的协议表述可以作为其严格替代版本。
