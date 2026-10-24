# 同一专用对话的代表性任务：Windows 有界联合验证

执行：本地柯蓝；接收与阶段审阅：云端爱丽丝。北京时间2026-10-24 01:10:11至01:14:07，约236.156秒。输入固定为 [`09e36beafeb293b3b6263b7b856cb841ff3cc605`](https://github.com/scarlet-devil/codex-condition-trigger/commit/09e36beafeb293b3b6263b7b856cb841ff3cc605)，执行[行动方案第11节](KELAN_THIN_STATE_NEXT_STEPS_20261023.md#11-当前接续代表性任务后的体量与回合关联)。

## 结论与待审范围

**本轮一次普通新回合已在原专用目标被接受并准确关联至结束；三个计量样本为 idle → busy → idle，任务前后绑定、新鲜度、最终 owner 和预算检查均通过。** 输出五项预期检查点一致，代表性任务后最大目标快照53,036 B，仍低于原32 MiB单帧预算。既有 Tk 烟测与 cwd 状态修复接受继续有效，不重做。

这组证据可交由爱丽丝判断是否关闭本版本、此目标与此工作量的有限 G0。当前标记 **evidence_ready / review_pending**，不自行宣称她已接受。G0只包含发现、绑定与有界状态可行性；G1规则/notify、G2完整表单、G3两批真实通知仍在后续范围，不再列为G0前置条件。

**保留一项执行偏差：目标任务的第三次工具调用尝试 WindowsApps 的 Python 应用别名，返回 ResourceUnavailable / exit 1，报告“系统无法访问此文件”，Python未启动；目标随后在同一回合改用 PowerShell 完成相同合成计算和输出回读，exit 0。** 控制器固定Python、IPC工具和发送路径未变，没有第二次start、第二模型回合或计量重试。第11节包含“更改执行工具先交回”的边界，因此不把这次目标内解释器切换抹去或自行解释为无条件合规：请爱丽丝判定它是否影响限定接收。没有重试该Python别名、修复系统、改目录或追加实验；真实结果与偏差一起冻结。

## 来源、筛选与材料

完整188文件候选按固定提交逐项核对Git blob、字节数和SHA-256，7个实际导入模块一致；试验结束后候选与6个冻结辅助器文件均未变化。运行源码与已接受d55c62d2相同，本轮不重跑既有34项实验及55项Windows相关测试。精确导入pin见[证据](../evidence/kelan-representative-task-20261024.json)。

沿用原创建回执、原始cwd/rollout与同一已创建的专用聊天；当前只读目录唯一候选及rollout首行ID/cwd核验一致。select_candidates保持500条/1 MiB限制；最终来源、归档/子任务过滤、name优先、同名稳定ID区分，引用上述34项中的12项目录测试，不重做历史目录大清点或完整列表UI。未新建、初始化、开关窗口或改绑业务聊天。

合成材料34,289 B，SHA-256 `5cc5433657424bea202100b3c5d096d1288d2e5765d67221e69eefc8cc70a4af`；122条、120个唯一record_id，预置完全重复R010、矛盾R033、amount缺项R070。输入、状态、输出分别为独立非嵌套目录；原业务数据、配置和数据库未读写。使用现有manifest/immutable blob与task_instruction，未临时改写dispatch_prompt。

## 本轮观测

| 指标 | 任务前 | 期间 | 任务后 |
| --- | ---: | ---: | ---: |
| native状态 | idle | busy | idle |
| revision / 请求下界 | 8 / 8 | 14 / 14 | 16 / 16 |
| 安装验证／最终owner一致 | true / true | true / true | true / true |
| 最大目标快照正文 B | 8,972 | 18,018 | 53,036 |
| 完成RX／预算扣除 B | 29,075 | 56,214 | 161,566 |
| TX B | 1,967 | 1,967 | 1,967 |
| 帧头／完整正文 | 11 / 11 | 11 / 11 | 12 / 12 |
| 目标快照正文帧 | 3 | 3 | 3 |
| 安装核验秒 | 0.921 | 1.078 | 1.016 |
| IPC秒 | 0.219 | 0.344 | 0.140 |
| 采样总秒 | 1.140 | 1.422 | 1.156 |

三个样本均snapshot_query_completed=true、无不完整I/O；计量器can_send=false、model_sends=0仅表示采样器只读，整个试验确实发送了1次模型任务。任务后较任务前最大快照增加44,064 B，单个采样完成RX增加132,491 B。每次查询里的3个目标快照广播不算3次独立采样。

预算继续为32 MiB单帧、128 MiB计量累计RX和安装核验后10秒IPC。总耗时单列安装哈希成本，仍使用完整历史路径；这次约53 KiB最大快照不能外推长期增长或低成本高频轮询。适配器不自动继承计量器累计RX契约。

## 全部请求与准确回合关联

总计 **1次start尝试且写入完成，3次计量，另有适配器2次完整历史状态检查**。所有已记录请求均完成写入，unknown写入集合为空。

| 请求类别 | 3个计量连接合计 | 发送连接 | 总计 |
| --- | ---: | ---: | ---: |
| initialize协议握手 | 3 | 1 | 4 |
| owner发现 | 6 | 2 | 8 |
| load-complete-history | 3 | 2 | 5 |
| start-turn | 0 | 1 | 1 |

initialize是协议握手，新增模型初始化回合为0。发送仍经dispatch_one/DesktopAdapter，先落盘意图，实际thread/client-message/request与意图一致；isSteering=false、inheritThreadSettings=true，原生回执含准确turn ID。随后用现有rollout读取器低频读文件24次，核对post-intent基线、完整投递原文、相同thread与同一receipt turn的task_complete；再做任务后查询。轮询文件不额外请求完整快照。

终止证据有58条记录，rollout观测长度466,164 B／SHA `1b5d5905d4dba01c6c56a878c51034f521e93e6af4eb1193babeecf995835056`；私有标识、完整正文和原始日志不公开。现有读取器仍给出 **state=ended、execution_outcome=unknown**：终止事件不能改写为成功。独立核验输出446 B／SHA `62a6baa4dc67e4837570dae39d025811a716a80bd460d31ae150390cc77f4491`，五项字段全部符合预期；这是“文件结果正确”的证据。**业务ACK为false**，没有实际业务交付试验。四次目标工具退出码0、0、1、0，最终聊天回复249字符；完整材料原文未在这四次工具记录中以完整字符串出现，此检查不等价于全面内容泄露证明。

## 辅助器检查、失败与范围

临时一次性辅助器不进入生产依赖。7项序列契约先红后绿；新增截止/STOP测试先3失败2通过，文本关联测试先2失败1通过，修正后最终15项全部通过、0失败/错误/跳过。仅E9/F63/F7/F82基础Ruff规则通过，不称完整lint全绿。

S1/M0独立本地子任务审查发现：只在样本入口检查外层期限，不足以阻止安装核验迟到后继续发请求。已在实测前补每次新请求及实际write前检查，并将I/O deadline收紧到外层期限；取消订阅只允许有界清理。文本关联遵循现有message/content字段，容忍非正文附加元数据；attempt/completed/unknown分列。复审接受冻结辅助器；审阅者只读源码与15项日志，没有重跑测试或真实IPC，也不是云端爱丽丝/S2。

安装哈希本身没有进程级硬中止；只能保证迟到返回后拒绝新IPC，不能声称整个进程必定在600秒硬退出。已经被宿主接受的模型回合也不会随本地STOP自动取消。本轮约236秒正常收尾，隔离STOP存在，一次性账本closed，未追加采样、重发、补ACK或恢复watcher。原生产安装/配置、连续授权、旧STOP/到期/PAUSED不改变，未检查当前生产监听健康。

## 给爱丽丝的判断项

1. 评估完整选择/绑定、前后有界状态、既有Tk证据是否足以限定关闭G0；本轮busy观测和普通新回合/准确turn关联已有实机证据。
2. 明确接收或保留目标内部Python启动失败后PowerShell计算的偏差。该问题未改变控制器传输链，但失败工具记录也影响本轮快照增长，当前数据不是“无错误的理想任务”基准。
3. 若限定接受，再确定G1最小通知调度范围。单次busy并未验证下一批延迟、连续两批推进或原子idle-and-start；G2/G3和长期历史增长继续独立验收。当前没有下一项自动执行安排。

## Governed Work Report

- Collaboration identity / acting role: Kelan；本地受限实验与证据作者。
- Deployment environment and evidence: local Windows；固定Python实际导入、原Desktop管道与当前完整性Active28/28。身份内核、登记及准确本地路径仅保存在本地治理报告。
- Task source/scope/expiry: Human转交09e36bea第11节；最多1start、3计量、600秒；本次窗口已闭合，旧额度未复用。
- Work surface/class: Windows Codex、PowerShell/Python；C/enhanced原生接口试验；公开新批次另按D/constitutional具体授权与审查处理。
- Workflow/capability: 本次证据implementation_ready，G0 review_pending；GitHub输入可回读，本文本身不预告交付已成功；PR Draft/unmerged。
- Kernel/registry/canonical/project: 同固定登记Active28/28、干净治理来源和根内核相符；适用项目AGENTS已读，无实质冲突；不公开身份文件。
- Repository/actions/evidence: 188文件候选无变化；模型任务1、计量3、总history5；[证据](../evidence/kelan-representative-task-20261024.json)和[清单](../evidence/kelan-representative-task-manifest-20261024.json)。
- Checks passed: 辅助器15项、选定基础Ruff、source/import/hash、绑定和输出五字段；旧34+55不重算本轮测试。
- Failed/skipped/deviations: 辅助器红测与修正保留；目标第三次工具启动失败及随后解释器切换单列；历史完整套件未重跑。
- Truncation/redactions: 部分广读工具展示截断后定向读取相关内容；完整本地原件保留。公开不含聊天ID、目录实值、会话、凭据、身份源或截图。
- Known limits/reviews: 全历史成本、非原子发送、终止不等于业务成功；S0自查和S1/M0辅助器审查，Alice新证据review_pending；阶段接受与公开传输批准分别处理。
