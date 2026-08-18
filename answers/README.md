# answers/ — 加密答案（ground truth）

> **这个目录里是答案，不是题目。** 题目在 [`data/polymarket-march-2026/agent_view/`](../data/polymarket-march-2026/agent_view/)。
> 答案被刻意放在仓库最外层、`data/` 之外，就是为了让任何人一眼能区分，
> 并且不可能在挂载题目目录时被顺带挂进去。

## 先读这一条

**如果你要用 beta-raven-bench 测试 agent：不要下载这个目录，也不要解密。**

这是历史回放题集，题目本身没有秘密，泄漏点只有一个——最终 Yes/No 结果。
明文答案一旦进入你的工作目录、检索语料、prompt、日志或 CI 缓存，
这一轮评测结果就不再可信，而且很难事后判断污染程度。

只有在下面两种情况下才需要解密：

- 你已经跑完预测，要给结果打分；
- 你在做数据审计，需要核对结算结果。

打分和跑分请分成两步、两个进程、两个目录：跑分进程永远看不到 `answers/`。

## 只克隆题目，不落地答案

```bash
git clone --filter=blob:none --sparse git@github.com:Alchemist-X/beta-raven-bench.git
cd beta-raven-bench
git sparse-checkout set data docs scripts config
```

`--filter=blob:none` + `sparse-checkout` 会让密文文件根本不下载到本地。
如果你已经完整 clone 过，可以用同一条 `sparse-checkout` 命令把它从工作区移出。

单文件直取题目（完全不碰仓库其他部分）：

```bash
curl -fsSLO https://raw.githubusercontent.com/Alchemist-X/beta-raven-bench/main/data/polymarket-march-2026/agent_view/selected_300/questions.jsonl
```

## 内容

| 文件 | 说明 |
|---|---|
| `polymarket-march-2026-labels.tar.gz.enc` | AES-256-CBC 加密的答案包 |
| `SHA256SUMS` | 密文校验值 |

解密后得到：

```
polymarket-march-2026-labels/
├── NOTICE.txt                          字段说明
├── SHA256SUMS                          明文校验值
├── selected_300/labels_sealed.jsonl    300 行，对应精选集
└── candidates_600/labels_sealed.jsonl  600 行，对应候选池
```

按 `id` 与 `questions.jsonl` 关联。打分字段：

| 字段 | 含义 |
|---|---|
| `ground_truth` | `A` = Yes，`B` = No |
| `winning_outcome` | `Yes` / `No` |
| `final_resolution_state` | `resolved_yes` / `resolved_no` |
| `resolved_at` | UTC 结算时间 |
| `status_as_of_may_end` | 2026-06-01 截面所属分层，用于分层打分 |
| `clob_verification` | 公开 CLOB 交叉验证收据（含 condition id） |

哈希与 [`manifest.json`](../data/polymarket-march-2026/manifest.json) 中
`private/*/labels_sealed.jsonl` 的收据一致，可据此确认答案包未被改动。

## 加密与解密

密文由标准 OpenSSL 口令加密生成，参数如下：

| 项 | 值 |
|---|---|
| 算法 | AES-256-CBC |
| KDF | PBKDF2-HMAC-SHA256 |
| 迭代次数 | 600000 |
| salt | 随机，写在密文头部（`Salted__`） |

**口令不在本仓库任何位置**——不在 README、不在脚本、不在 commit message、
不在 issue、不在 release notes 里，只通过私下渠道口头传达。请你也照此处理：
不要写进公开的 issue、PR、博客、评测报告或聊天记录截图。

解密（脚本会提示输入口令，不会进入 shell history）：

```bash
./scripts/decrypt_answers.sh ~/raven-answers
```

或者直接用 openssl：

```bash
mkdir -p ~/raven-answers
openssl enc -d -aes-256-cbc -md sha256 -pbkdf2 -iter 600000 \
  -in answers/polymarket-march-2026-labels.tar.gz.enc | tar -xzf - -C ~/raven-answers
```

两条命令都请把输出目录指到**仓库之外**。

## 解密之后

- 明文只留在打分机器上，不要 commit、不要上传、不要放进共享盘；
- 不要放进任何 agent 可读路径、检索语料或 embedding 索引；
- 打分完成后删除明文；
- 不要以任何形式重新公开明文答案。

`.gitignore` 已经屏蔽 `answers/` 下的子目录、`*.jsonl`、`*.tar.gz`、`*.txt`
以及任何 `*labels_sealed*`，但这只是最后一道保险，不要依赖它。

## 为什么是加密发布而不是不发布

不发布答案，第三方就无法独立复现分数，benchmark 只能自证；
明文发布答案，题目和答案会一起被爬进训练语料，题集直接作废。
加密发布是折中：想打分的人拿得到，爬虫和顺手 `cat` 的人拿不到。

这不是强安全边界。口令是共享秘密，密文是公开文件，
拿到口令的人就拿到了全部答案。它防的是**意外污染**，不是**蓄意作弊**。
需要防作弊的正式排行榜，应当改为服务端打分、不下发答案。
