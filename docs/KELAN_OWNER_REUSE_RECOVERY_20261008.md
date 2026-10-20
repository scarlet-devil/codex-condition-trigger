# 柯蓝修订报告：发送前 owner 消失的首次开窗恢复

日期：2026-10-08（Asia/Shanghai）。接收者：云端爱丽丝。执行者：本地柯蓝。
输入固定为 `93e3f969e12861193d6974d2acb104c4162b2dc1`，沿用 Draft PR #1。

**F1 已完成 Python 状态逻辑修复及定点回归，状态 implementation_ready / review_pending。** 爱丽丝已接受的两批监督试验继续有效；本次不扩大到无人值守正式验收。

## 问题与根因

按[爱丽丝交接](https://github.com/scarlet-devil/codex-condition-trigger/pull/1#issuecomment-6058420064)在准确旧源码执行原反例，退出码1。首次准备发现 idle owner，登记 `reused`；发送前独立查询发现 owner 缺失，批次仍 ready、没有 dispatch_text/meta，也没有 lease。Store 重启、模拟时间越过 next_try 60秒、三次轮询和新增文件后，仍 waiting_owner，开窗/发送均0。

根因是 active 分支只查询后返回等待，从不调用首次开窗；原 claim_open 又拒绝所有非 closed 周期。因此正常退避、重启或新材料无法恢复，后续批次被挡住。

## 最小修复

只修改生产文件 `owner_loading.py`，没有修改 Windows 后端、IPC发送实现、数据库模式或默认开关。active 周期 fresh 查询明确返回 waiting_owner 且 phase 为 reused 时，调用原开窗路径。

开窗前必须同时满足：唯一活跃周期绑定准确同一批次；仍为 reused；lease 为 null；历史事件非空且只有 fresh_idle_owner_reused，没有此前 opening/closing 或其他动作。SQLite 在一条 UPDATE 中比较旧周期完整值，并要求该批次仍 ready、两个发送意图字段严格为 SQL NULL。条件失效则不取得 claim，也不调用后端。已有事件保留，原记录不删除，取得 opening 后仍走原持久化与后端流程。

这保留了单 worker 约束和原有动作不明保护。开窗结果不明、已经开过但 owner 再次消失、已发送或已有发送意图、legacy claim、busy/unknown、STOP 和禁用条件都不能借恢复路径重放。调用者 ACK 和交付证据含义不变。

## 红绿证据

| 检查 | 修复前 | 修复后 |
|---|---|---|
| 爱丽丝原始 probe（正文未改） | exit1；0开窗/0发送 | exit0；1开窗/1发送 |
| 重启后3次tick | waiting_owner ×3 | accepted、running、running |
| 新文件到达后 | waiting_owner | running；没有额外开窗或发送 |
| 受影响两个模块 | 加首6项后45项中3失败 | 最终46项全部通过，0失败/错误/跳过 |

新增7项检查覆盖：发送前消失后恢复原批次且重启不重复；busy/unknown不晋升；fresh检查期间批次状态或发送意图改变时原子拒绝（包括空字符串意图）；存在lease或开窗历史时拒绝；晋升后的open超时持久化；开窗额度已消耗后不能再次开窗；旧周期快照不能覆盖已变化的周期。

先写6项测试并观察3项预期失败，再修代码；其余3项是保持原保护的检查。最后补充旧周期快照的CAS检查后46项通过，并未声称7项都曾失败。完整命令、退出码、红绿输出与源码SHA-256见[脱敏证据](../evidence/owner-reuse-recovery-20261008.json)。本轮自审为S0，不冒充爱丽丝独立验收。

## 保留的实机证据与限制

本轮真实原生IPC、UI动作、模型调用和正式watcher启动均为0。仅复用现有Python环境，在临时目录以真实Store/SQLite和合成边界对象验证逻辑；不安装依赖。按本次交接，不机械重跑全套或整轮Windows试验。

原 `windows_window_backend.ps1` 和 `evidence/window-cycle-20261008.json` 字节未改变。204.359秒双批、2次真实start、0手动dispatch、2份合成回执及42项实机断言保持原执行归属。本次1开窗/1发送是合成fixture计数，不能当成额外实机，也不证明自然缺失owner的冷恢复已验收。

准确当前聊天识别仍依赖“不导航”的监督时段；前台聚焦、焦点恢复延迟、跨版本兼容性、无人值守业务和最后期限门的实机验证范围均保留原结论。它们不被本次46项通过消除，也不新增为F1返工清单。

## 交接

建议爱丽丝针对原probe、原子晋升条件与7项新检查定点复审。无需红魔另给静默时段。修复及本报告更新到同一Draft，详细红绿证据一并提交；本机状态与共用日志同步。原timer保持PAUSED、所有既有STOP保持，不合并、不部署或自启。材料可达不等于爱丽丝已经读取或接受。
