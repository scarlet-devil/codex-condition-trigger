# 爱丽丝小点成果增量审查 — 2026-10-10

## 结论先行

本轮新增材料值得保留，但**不能据此批准安装、采用或宣称真实效果**。它完成的是三项静态收口：

1. Trackio 旧待续静态审计从“缺结论/证据/收尾”推进到可审查；固定上游源码仍支持一个关键风险：本地发送线程会先清空内存队列，再调用捕获异常且只告警的写入函数，因此注入 SQLite 拒写时，确实可能出现“告警 + 0 行 + 队列已空”。这支持继续把 T07 设为预期失败的负例，但本轮没有真实复现。
2. AI 实验证据归档只证明了归档状态和缺口记录；两件 Library 原件共 45,506B 没有取得完整字节，所谓 25 项静态/夹具检查和 15 个场景均不能升级为爱丽丝独立验证或效果证据。
3. Claude Code / Rex 的官方材料能提供通信设计语义：显式失败关闭、状态与业务 ACK 分离。但它们不证明 Codex 或本项目已支持相同 Hook / OSC 7501 行为，也不构成运行验收。

因此该交付集合登记为 **partial**。最有价值的实际影响是：红魔可以把 Trackio 的下一次最小实验聚焦为 T07，而不是扩大到完整 T01–T08；通信系统可先吸收“状态不是 ACK、失败策略必须显式”的设计约束，无需安装或启动候选。

## 本轮直接检查

- Drive 关系：`40_REPORTS` 的父目录仍为 `new-skill-merge`；直接子项计数为 200。
- 新报告 [KELAN_INCREMENT_SURVEY_20261010_db099a48.md](https://drive.google.com/file/d/13QGcbcdqLifP-oIoqkXWw3AkQOs9Yppw/view)：16,894B，SHA-256 `e46cacbfcc7334959ca667b37da0ad7b74193a0adbb7893b3f6a5cff4cc6c8e3`。
- 新证据 [KELAN_INCREMENT_EVIDENCE_20261010_db099a48.json](https://drive.google.com/file/d/1hDkbdoMiJZgKRUweAq8BFQ0C_1n85F-W/view)：8,743B，SHA-256 `a7ec1c4309ad37fc645b0420fa2b0ca180ee8a69d3e9bdbad5e0ef69872612a5`。
- 关联旧冻结报告/证据重新读取后哈希仍分别为 `3966bf8a…`（17,287B）和 `b646da2e…`（17,292B），与既有账本一致。
- 新 JSON 内部计数自洽：14 个新版本合计 105,197B，2 个旧待续版本合计 8,773B，总计 16 个版本、113,970B；同一路径的 8,208B 与 8,739B work_log 是两个内容版本，没有误算成两个文件。
- 本轮只取得报告与汇总证据 JSON；JSON 所列 16 个底层 blob 没有作为本轮附件逐一取得，因此不能把柯蓝的 `stable=true` 或文件 SHA 冒充爱丽丝逐字节复核。
- 同目录新增的恢复监听修复报告/ZIP属于条件触发器工程交付，不并入小点成果账本。

## 分项判断

| 研究项 | 材料现在能证明 | 仍不能证明 | 决策含义 |
| --- | --- | --- | --- |
| Trackio R3 定点复核 | 汇总清单/计数自洽；冻结上游 [run.py](https://github.com/gradio-app/trackio/blob/605a645cf555da7945095ca50b0efb5de802df1b/trackio/run.py) 的本地路径在清队列后写入，写入异常只告警；T08 明确 BLOCKED | 没有 T01–T08 真跑、进程树资源保证、T05 拒绝边界、WITH-DML 负例或 T07 故障复现 | 不批准安装；若追加实验，只做独立沙盒 T07 |
| AI 证据归档 | 缺件、下载尝试和未完成状态被明确记录；没有把 403/完成状态杜撰出来 | 两原件原始字节、ZIP CRC/路径安全、25 检查的独立复核、模型效果和同任务对照 | 先补原件，当前不能纳入科研效果证据 |
| Claude Hook | 固定 changelog 确认 v2.1.295 增加 `onFailure: "block"`；v2.1.296修复 managed PreToolUse / prompt hook 拒绝时错误结束 turn 的行为；[官方 Hook 文档](https://code.claude.com/docs/en/hooks)说明失败默认继续，空成功只是“无决策”，退出码/事件的阻断能力不同 | Codex 具有相同字段/事件或本项目已配置 fail-closed | 只迁移语义，不迁移能力主张 |
| Rex / OSC 7501 | [协议 0.3](https://www.superlogical.com/rex/docs/build/program-status)定义 idle/working/done/blocked/error/clear；working/blocked 随进程退出或新 shell prompt 清理，done/error保留 | 终端显示即业务完成、Codex 当前支持协议、状态能替代精确回执 | 可用于 UI 状态层，不能替代 manifest/turn/业务 ACK |

### Trackio：为何 T07 是最优先负例

冻结源码的本地发送线程先复制并清空 `_queued_logs`，再调用 `_write_logs_to_sqlite`；后者捕获任何异常，只发一次非致命告警，不把批次放回队列。由此可静态推出：当 SQLite authorizer 拒绝写入时，“有告警、0 行、0 队列”是合理的失败观测。这个推断与柯蓝的新结论一致，但不是本轮真实运行。

这也限定了外推范围：

- 该结论直接针对本地 SQLite 路径；远端路径在发送异常后会尝试本地持久化，不能把两条路径混为一谈。
- T05 的控制阶段豁免、WITH 包裹 DML 和直接 PID/进程树预算依赖未取得的审计脚本/控制器原文，本轮只能记录为柯蓝转交主张。
- “3 metrics、step0 1 trace、2 spans、3 条 session JSONL”是夹具预期，不是观测结果。

### AI 归档：完成的是缺口登记，不是证据闭合

证据 JSON诚实地写明：两件 Library 原件只登记了 45,506B 元数据，本地验证字节为 false，CRC 未跑，完成状态 UNKNOWN。因而归档组的 38,823B 可读材料最多证明“归档如何记录缺件”，不能证明两原件内容、25 项检查或 15 个场景的实际结果。没有模型输出、同任务对照和归因指标，更不能判断业务收益。

### Claude / Rex：可迁移的是约束，不是实现

Claude Code 的官方文档说明：

- `onFailure` 默认为 `continue`；仅显式设置 `block` 才把启动失败、超时、非预期退出等变成阻断，且存在事件/后台 Hook 例外。
- 退出 0 且无有效决策只表示 Hook 成功并回到正常权限流程，不等于显式允许。
- 退出 2 是否能阻断取决于事件；例如 PreToolUse 可阻断，PermissionRequest 则要用决策对象。

Rex 的 OSC 7501 是状态报告协议，不是交付协议。它恰好支持本项目继续保持三层分离：运行状态、用户注意状态、可核验业务 ACK。对红魔的通信工作流，这比照搬某个终端图标更重要。

## 建议给红魔的最小下一步

1. **暂不批准 Trackio 安装或完整 R3。** 若决定追加一次实验，只授权离线临时目录中的 T07：注入 SQLite 拒写，断言 `SQLITE_AUTH`、告警、写前/写后行数和队列状态；保留当前预期 FAIL。运行前先补齐将被执行的固定脚本原字节/哈希。
2. **先补两件 AI 原件。** 取得完整字节后再做 SHA-256、ZIP CRC、路径安全和条目计数；这些通过后，才值得检查 25 项静态/夹具结果。模型效果另立同任务对照和归因指标，不与归档检查混记。
3. **通信系统先做规格映射，不做能力假设。** 把 `working/blocked/done/error` 用作展示层候选，把 manifest/turn/调用方核验继续作为业务 ACK；所有安全门须明确 fail-open/fail-closed 和事件例外。若以后要验证 Codex 支持，再单独授权无副作用探针。

## 可信范围

高可信：本轮直接读取的报告/JSON原始字节与哈希、JSON计数、固定 Trackio源码的队列/异常路径、Claude Code官方 changelog/Hook文档、Rex协议0.3。

中可信：柯蓝在报告中转交的 16 个底层版本哈希与静态复核结论；汇总内部一致，但底层 blob 未逐一交付给爱丽丝。

未验证：Trackio 候选执行、安装和真实收益；AI 原件与模型实验；Claude/Rex/Codex 本地运行兼容性；任何本机监听交付或业务 ACK。

本分析不改变本机试验、固定截止、定时器、窗口权限、模型配置或 PR Draft 状态。
