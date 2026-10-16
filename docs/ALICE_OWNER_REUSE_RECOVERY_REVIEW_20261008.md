# 爱丽丝定点复审：F1 已关闭

日期：2026-10-08（Asia/Shanghai）。执行者：云端爱丽丝；接收者：本地柯蓝；目标负责人：红魔。

**接受 `6c2589d7d100d135c1f5deb301268929d0b375c8` 的 F1 修复，本轮没有新增必修项。** 原先限定接受的两批监督实机路径继续有效。这里接受的是发送前 owner 消失后的首次开窗状态恢复，不是无人值守正式使用、真实冷恢复或合并部署验收。

## 输入与范围

- 同一仓库 `scarlet-devil/codex-condition-trigger`，Draft PR #1，分支 `draft/initial-prototype`；输入父提交 `93e3f969e12861193d6974d2acb104c4162b2dc1`。
- 沿用既有 GitHub 协作与日志授权，C / enhanced；规范固定版本 `rule-of-rules@387c98a45b8fcc4409647c5bdc3363d614542859`。本轮授权仅用于定点复审和记录，结论发布即结束，不延伸为运行授权。
- 输入只有一个新增提交、8 个变更文件；生产代码仅 `owner_loading.py`，测试仅 `tests/test_window_cycle.py`，其余为报告、状态、日志和清单。未修改 Windows 后端、IPC 发送实现或数据库模式。

## 源码结论

`step()` 只在活跃周期为 `reused` 且新的 owner 查询明确返回 `waiting_owner` 时进入恢复路径。`claim_open()` 要求唯一活跃周期绑定同一批次、没有 lease，且非空事件历史全部为 `fresh_idle_owner_reused`。已有开窗、动作不明或其他历史不能借此取得新额度。

晋升通过一条 SQLite UPDATE 同时比较旧周期完整值，并要求同一批次仍为 `ready`、`dispatch_text` 和 `dispatch_meta` 严格为 SQL NULL；空字符串也不能绕过条件。成功后保留旧事件并持久化 `opening`，再沿用既有开窗流程。过期快照不能覆盖新周期；STOP、禁用、legacy、busy/unknown、已发送和开关窗结果不明的保护保留。

## 爱丽丝直接验证

在云端 Linux / Python 3.12.14，使用准确 Git blob 物化的源码和现有合成 fixture；未安装依赖。

| 检查 | 实际结果 |
| --- | --- |
| 原 probe 正文保持不变，在旧实现上执行 | exit 1；重启、跨过退避期限和新文件后仍 0 开窗 / 0 发送 |
| 同一 probe 在修复后执行 | exit 0；恢复后为 accepted、running、running；新文件到达仍 running；总计 1 次合成开窗 / 1 次合成发送 |
| `PYTHONPATH=.:tests python -m unittest test_owner_loading test_window_cycle -v` | 46/46 通过，0 失败、错误或跳过，0.180 秒 |
| 内容完整性 | 25 个已读取 Git blob、24 项 SHA-256 一致；72 个清单路径覆盖 73 文件树中除清单自身的全部文件 |

新增 7 项测试覆盖首次恢复且不重复、busy/unknown、发送状态竞态（含空字符串）、lease/开窗历史、晋升后超时、旧周期快照、开窗额度已消耗后再次丢失 owner。原有测试继续覆盖未确认关闭、legacy、STOP、早期 ACK 等保护。本轮未额外扩大测试集合；生产代码和原测试未由爱丽丝修改。

旧实现复现使用上轮已校验的 `2622fd6` 源码副本；`93e3f96` 为后续文档/证据修订，未改变该运行实现。probe 来自本次固定输入，正文与上轮已发布版本相同。详细输出、实际运行字节哈希和范围见 [云端复审证据](../evidence/alice-owner-reuse-recovery-review-20261008.json)。清单路径覆盖不代表本轮重新读取了全仓库正文。

验证归属：爱丽丝复跑现有测试及上轮反例为 S2-M1（继续使用现有 fixture，并非 M2）；本轮自有记录与完整性检查为 S0。柯蓝的本地红绿过程保持原执行归属。没有子代理，也未重新读取 Drive 副本或私有 Windows 原始数据。

## 保留边界与交接

Windows 后端及原两批实机报告、证据、监督脚本、测试输出的 Git blob 保持不变。先前两批监督路径的限定接受继续有效；本轮真实 UI、原生 IPC、模型调用、watcher 启动均为 0，没有重跑 119 项全套或 Windows 两批试验。

准确当前聊天仍依赖限定“不导航”监督时段；前台聚焦、真实冷恢复、业务回执自动核验及最终期限门的实机验证范围沿用既有结论。这些是后续产品范围，不重新列为本次 F1 返工条件。柯蓝无需为这一 Python 修复补做另一轮完整实机试验。

F1 状态从 `review_pending` 更新为 `accepted`；本次复审结束，下一阶段范围待确定。PR 保持 Draft；原 timer PAUSED、全部既有 STOP 沿用，不合并、部署、自启或恢复正式运行。本轮没有访问或更改本机运行状态。记录可达不代表柯蓝已经读取。
