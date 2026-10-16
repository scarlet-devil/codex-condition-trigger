# Alice 复审：双批窗口循环与一个恢复缺口

日期：2026-10-08。输入：`2622fd65ae37c122cf4d563d5758757a560e569b`；父提交 `b8225af531d6da73f69dbd7dfc7d88a6b769f443`。同一 Draft PR #1。

**REQUEST CHANGES：一项 P2 恢复缺口须修复。** 限定接受报告中两批连续监督试验的实际路径；不把这个代码缺口改写为实机试验失败，也不据实机成功批准未覆盖的恢复路径。

## 任务、来源和审查范围

我是云端 Alice，本轮承担固定输入的独立源码/证据审查及云端隔离验证；本地实现者和接收修订者是 Kelan，红魔拥有目标与最终决定权。来源是红魔本轮转交的本地报告，以及前轮已授权的同一 Draft 实现/交接。任务为 Class C / enhanced（自动化工作流、跨模块生命周期与持久状态），本轮不含合并、安装、自启、原定时任务恢复或实际 Windows/模型动作。任务角色至本次结论交付结束；后续修订以本条交接范围为限。

当前工作面是 ChatGPT Work 云端，使用连接器读取固定 Git 提交，并在云端 Linux / Python 3.12.14 运行隔离检查；这不是用户本机。接手已读 CURRENT_STATE、WORK_LOG 增量、前轮有效目标、实施计划和材料。适用规范按个性化固定 `rule-of-rules@387c98a45b8fcc4409647c5bdc3363d614542859` 的导航读取完整 CONSTITUTION、GOVERNANCE、Alice 角色、交接协议及身份源；不以资料读取声称完成新的 developer 装配或本地治理安装。

核对 22 件取得文件的 Git blob 和 21 件清单 SHA-256；66 个清单路径完整覆盖 67 件 Git 文件（清单自身除外），不是全树正文重新哈希。最终五件运行源码的登记哈希分别可由准确 LF 或 CRLF 字节匹配。实机运行旧字节没有重新取得；最后 BeforeAction 期限检查及换行归一化的实机后增量按报告区分，未声称最终所有字节均参加过同一次实机。

上下文边界是红魔转交的本地 run（20261008-window-cycle）及固定提交，与此云端审查任务分离。对本地既有 Windows/42 项证据记录为 S2-M0；同方法复跑和补充隔离反例为 S2-M1，反例复用现有合成 fixture，不声称方法独立 M2。我的核对脚本、记录与审查方案为 S0。未使用子 agent。

## 已支持的结论

- 读取完整本地报告、脱敏 JSON、监督脚本和相关源码/测试，42 个唯一断言均登记通过，两个算术结果与发送/窗口计数一致。私人原生记录和 Drive 副本未在本轮复读；对真实工具输出、主窗口与 owner 观测的结论保持转交证据范围。
- 接受一次监督限定的脚本开窗、准确初始 route 绑定、IsIconic 最小化、第一批相关完成与调用者 ACK 后 WM_CLOSE，以及第二批自动复用存活 owner；2 次 start、0 次手动 dispatch，合成结果 459 / 461。
- 原 119 项中 118 通过、1 跳过是柯蓝本地结果。本轮云端只运行 `PYTHONPATH=.:tests python -m unittest test_owner_loading test_window_cycle -v`：**39/39 通过，0 失败/错误/跳过，0.155 秒**。没有重跑全套或启动实际 watcher。环境信息补查未找到 watchdog distribution 元数据；这两个定点模块不启动 watchdog，本轮未为此安装依赖。
- 代码中准确 expected_batch_id 约束阻止并发 ACK 导致下一批跳过清理；无 turn 关联的 cycle ACK 被拒；禁用 loading 不绕过活跃 cycle。相关既有反例复跑通过。接受这些修正的有限证据。
- 期限检查的最终源文件已静态检查；实机后该修订只有本地隔离验证，未重新演示 Windows。它加强动作前拒绝过期请求，不为此要求机械重复整轮实机。

## F1 — 未发送的 reused 周期在 owner 消失后不能转入加载

**位置：** [owner_loading.py 的 active 分支](https://github.com/scarlet-devil/codex-condition-trigger/blob/2622fd65ae37c122cf4d563d5758757a560e569b/owner_loading.py#L194-L205)、[reused 登记](https://github.com/scarlet-devil/codex-condition-trigger/blob/2622fd65ae37c122cf4d563d5758757a560e569b/owner_loading.py#L213-L219) 和 [claim_open 门](https://github.com/scarlet-devil/codex-condition-trigger/blob/2622fd65ae37c122cf4d563d5758757a560e569b/owner_loading.py#L103-L111)。

准备阶段查询 idle 后，程序先持久化 `phase=reused, lease=None`。若 owner 在发送前的再次查询时消失，dispatch 正确留下 ready 批次，且 dispatch_text / dispatch_meta 都仍为空。下一次 step 进入 active 分支，只返回 waiting_owner，永远不能走无 active 时的 claim_open；即使直接调用旧 claim_open，现有非 closed 记录与 INSERT OR IGNORE 也会阻止晋升。

在未修改的准确源码上，用真实 Store/调度函数及现有合成 IPC/window fixture 注入这一时间顺序，取得：

| 项目 | 实际输出 |
| --- | --- |
| 第一次 tick | waiting_owner |
| 批次与发送意图 | ready；dispatch_text、dispatch_meta 均为 null |
| 周期 | reused；lease 为 null |
| 重启后将模拟时钟推进至 next_try 后 60 秒，再作 3 次 tick | 均 waiting_owner；并非正常退避尚未到期 |
| 新增第二份文件后 | 仍 waiting_owner；2 个批次待处理 |
| 开窗 / 发送 | 0 / 0 |

补充验收脚本退出码为 **1**，因为“明确缺失且从未发送、没有开窗动作的周期应允许一次加载”未满足。没有重复发送或错误关闭；影响是原本可以恢复的未发送批次持续等待，并阻塞后续批次，需要人工重新加载。

可回跑的[探针](../evidence/alice-window-cycle-review-20261008/probe.py)、[实际观察与来源核对](../evidence/alice-window-cycle-review-20261008/observations.json)、[39 项复跑输出](../evidence/alice-window-cycle-review-20261008/focused-tests.txt)。在仓库根执行：

```bash
python evidence/alice-window-cycle-review-20261008/probe.py --repo .
```

该探针只使用临时文件、SQLite 和合成对象，不调用原生 IPC、UI 或模型。实际生产代码与原有测试本轮均未改。

## 给本地柯蓝的唯一必修项

沿用同一 Draft、适用本机规则及 CURRENT_STATE / WORK_LOG 入口，修复 F1：允许**同一批次、仍 ready、无持久发送意图、仅 reused 且无 lease/先前开窗动作**的周期，在 fresh 查询明确 owner 缺失时，原子取得该轮一次 opening claim，再执行原后端。具体实现由仓库事实决定，不强制新建状态框架。

保留既有边界：busy/unknown 不开；已有发送意图、opening/closing 不明结果、真实已消耗开窗额度和 legacy claim 不可被重置；同一批次仍至多发送一次。不要通过删除 cycle、清空状态库或放宽所有 active 周期来修复。

将这个反例纳入针对性回归：发送前 owner 消失可以一次加载并继续原批次，重启不会重复开窗；已有发送/开窗不明分支仍不重放。给出修复前失败、修复后通过与受影响两模块结果，更新共用日志后回到本 PR。只改 Python 状态逻辑时**不要求重演已通过的双批 Windows 试验**；只有改动实际涉及 Windows 后端或出现相关失败，才针对该差异补实机证据。本轮不增加模型调用或用户静默时段要求。

当前 REQUEST CHANGES 的必修范围仅 F1。修订以独立提交可回退；保留已取得的旧试验证据，勿覆盖原报告的执行归属。修复结果回传后，我再作定点复审。

## 尚未达到的产品目标

当前方案仍靠明确的不导航监督时段处理 initialRoute / 当前聊天识别不足，不能独立排除同名导航或 UIA 滞后。新窗口曾获得前台，8.552924 秒只是 invoke-to-minimize 采样间隔；冷恢复没有真实发生，合成 ACK 来自调用者核验。这些是已披露的接受范围，不新增为本次返工项目，也不能被“39 项通过”或 F1 修复消除。

用户希望减少人工介入的方向仍成立；本阶段已经证明两批监督路径，尚未完成无人值守正式业务。任意导航后的准确当前聊天识别是将来扩大采用范围时的实质缺口。PR 保持 Draft，原 timer PAUSED，历史及本轮 STOP 不解除；没有合并、部署或恢复运行。无额外 Human 决策请求。交接发布不证明柯蓝已读取或执行。
