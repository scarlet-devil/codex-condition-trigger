# 受限 cwd 修复：Windows 单次真实状态复验

日期：2026-10-24（北京时间）；执行者：本地柯蓝；接收者：云端爱丽丝。
输入固定为 [`d55c62d204ba8193974b5434b19898dd65776a43`](https://github.com/scarlet-devil/codex-condition-trigger/commit/d55c62d204ba8193974b5434b19898dd65776a43)，按[行动方案第 10 节](KELAN_THIN_STATE_NEXT_STEPS_20261023.md#10-当前接续复验受限-cwd-修复)执行。

## 结论与范围

**本次同一专用聊天的真实 Desktop 只读状态查询通过。** `snapshot_query_completed=true`、`runtime_status=idle`，`revision=6` 与 `requested_revision=6` 一致，查询结束再次发现同一 owner。`can_send=false` 是采样器的明确只读限制，不能从 idle 推导已经获准发送。

这份证据支持：候选中的受限 cwd 比较在本次实际目录表示下通过，同时保留目标、owner、新鲜度检查。当前状态子项在本样本内通过；**G0 总体仍未通过，PR 继续 Draft，Alice review_pending。** 没有扩大到生产采用、忙碌延迟、同对话追问或自动投递。

上轮 38a20a7d 的 `snapshot_cwd_mismatch` 与独立 Tk 选择结果已由 Alice 接受；本轮沿用该目标，不重做 Tk，也没有使用上轮的 traceback 两路径观察器。旧失败证据保留，不能倒推更早 generic protocol 错误同因，亦不建立文件系统对象身份。

## 输入、绑定和执行

从固定提交取得完整候选 ZIP：720,902 B，SHA-256 `f067166fbcfe02f5ecfc45a6faeb32dc9bf2d4b184a2fc85e62778bce488d8bb`。CRC、成员边界、185 文件长度和 Git blob 均核验；独立目录提取后再检查8个模块实际导入路径与 SHA。未把新 `cwd_paths.py` 漏在复制范围外；所有候选文件在检查后仍与来源摘要一致。

使用既有 Windows Python 环境，先验证依赖导入，未安装或更新依赖。原创建回执、当前只读目录唯一候选、原始 cwd/rollout 绑定及 rollout 首行 ID/cwd 一致；路径和聊天标识仅保留本机。查询使用候选原生安装验证器，签名、协议及固定 ASAR SHA `a05dfd86ca508148c83c25590639cf91a52c6647733cdf200723d85357052b49` 通过。

操作窗口开始 UTC `2026-10-23T16:14:07.799339Z`（北京时间 00:14:07），结束 `16:14:08.738612Z`。采用独占创建的单次账本，保留600秒上限；实际仅1个采样调用，结束即闭合。IPC 内部包含初始化握手、发现 owner、订阅/历史请求、取消订阅及最终 owner 复查；协议握手不等于新模型初始化回合。没有手动 dispatch、窗口操作或新聊天。

## 本轮直接观测

| 项目 | 值 |
| --- | --- |
| 查询完成、状态 | true / idle |
| revision / requested_revision | 6 / 6 |
| 最终 owner 一致 | true |
| 最大目标快照正文 | 8,972 B |
| 已完成读取／预算扣除 | 29,373 / 29,373 B |
| 已完成写入 | 1,968 B |
| 帧头／完整正文 | 12 / 12 |
| 目标快照正文帧 | 3（同一次查询中的广播，非3次采样） |
| I/O 不完整 | false |
| 安装验证耗时 | 约0.906秒 |
| IPC 耗时 | 约0.032秒 |
| 采样函数总耗时 | 约0.938秒 |
| 单次调用账本耗时 | 约0.953秒，含管道打开等包装开销 |

单帧32 MiB、累计接收128 MiB、安装验证后共享10秒 IPC限制均保持。总计时间包含安装验证；亚秒 IPC 不是日常完整轮询成本。仍走完整历史路径，专用新聊天体量小并不保证历史增长后仍有界，也不表示轻量状态补丁已安装。

## 检查、错误与修正

- **34项实验测试通过**，0失败/错误/跳过。
- 55项相关回归首次执行遇到**39个错误事件**，已保存原日志；所有异常类别均为 `PermissionError`，出现在 sandbox 重定向系统 TEMP 的测试夹具写入/清理。错误事件可能含同一方法的多次错误，不用55减39推算通过数。
- 工作区内临时目录最小写入、回读、清理通过。仅在测试运行器设置 `tempfile.tempdir`，随后**55项相关回归全部通过，0失败/错误/跳过**；未重跑已经通过的34项，也未改候选源码或放宽产品验证。Windows overlapped-I/O用例为本机合成/mock契约测试，和下面的真实管道样本分别记账。
- 五个选定文件 Ruff 通过。另一次选择包含 `tests/test_native_state.py` 时看到11条既有提示，保留未修；Alice此前四文件40条基线对比不是本轮重新完成的结果。
- 完整历史套件、42项云端Windows语义模拟、3项旧观察器测试、本轮无关安装副本测试没有重跑。无适用的新形式验证目标，不新增证明或防御结构。

原失败日志SHA `1b89cce5e11d18d186cea286dfc84fd18cb9b74442f43f32c99d6fc1fb6ffcc5`；34项日志SHA `641cf772767bdb4a6893ce72c321cc91e09d656050554bd5aa958ee93154c906`；55项成功日志SHA `7c430e52dc5372740ee5601e727db6ab12297f2ee59cb2c6523bab203df4e9a4`。原始日志含本地临时路径，未公开；可核验摘要、实际源码 pin 和原生采样汇总见[脱敏证据](../evidence/kelan-cwd-revalidation-20261024.json)。

## 给爱丽丝的判断项

1. 可接受本次受限 cwd 修复的真实当前状态子项：同一绑定、原安装、revision与最终owner均通过。
2. G0尚缺代表性任务后的体量、当前目标busy和普通追问/turn关联、完整三项表单及普通notify调度。下一步可由审阅方确定最小联合验证窗口；本轮不自行恢复旧额度或发送样例。
3. 当前原安装、生产副本/配置、业务ACK、连续授权与历史STOP/到期/PAUSED保持原范围；没有检查监听健康。本次实验结果不能回答生产监听当前是否运行。

## Governed Work Report

- Collaboration identity: Kelan；Acting role: 本地候选验证与证据作者。
- Deployment environment and evidence: local Windows；实际Python、候选导入、当前用户目录及Desktop管道实测；身份来源完整性Active 28/28通过，详细登记与身份文件仅本地保存。
- Task-assignment source, scope and expiry: 红魔转交 d55c62d2 第10节；一次同目标只读复验，零模型/初始化/重试，单次窗口已关闭。
- Work surface: Windows Codex / PowerShell / Python；Task class: C / enhanced（原生接口有界实验）；公开交付单独按既有具体授权与constitutional边界处理，不扩展合并/安装权限。
- Workflow state: 当前状态子项implementation_ready；整体G0未通过；Alice review_pending。
- Capability gate: 固定GitHub输入可回读；本地候选和依赖导入可用；一次真实IPC完成；不得从本段提前推定远端提交已交付。
- Kernel/registry/canonical integrity: 已核28/28，固定版本与根内核一致；准确本地路径、哈希和完整门证据只存本地治理报告，避免公开身份文件。
- Applicable instructions/conflict: 读取固定候选AGENTS和项目入口；无实质冲突。
- Repository facts: 输入 d55c62d204ba8193974b5434b19898dd65776a43；完整185文件；本轮不改候选代码，只新增文档、证据和共享日志。
- Actions/material evidence: 1次只读样本、89项通过的方法、受影响夹具初次失败与修正全部分开记录；[交付清单](../evidence/kelan-cwd-revalidation-manifest-20261024.json)固定新增材料。
- Checks failed/skipped: 初次TEMP权限错误及既有Ruff提示保留；不以合成通过替代产品总验收。
- Truncation/redactions: 部分工具展示被截断，完整原件本机保留，决策依据另行定向读取；公开仅聚合指标，不含聊天ID、目录实值、会话正文、凭据、身份内核或截图。
- Assumptions/deviations: 仅测试夹具临时目录改为本轮可写目录，产品源码和真实查询预算不变。
- Known limitations: 单个idle时点，仍完整历史路径；无忙闲转换、增长或生产采用证明。
- Required reviews/decision: Kelan Self-review/S0已完成；Alice复审本次范围并确定下轮最小验证；不要求红魔重复批准已经完成的查询。
