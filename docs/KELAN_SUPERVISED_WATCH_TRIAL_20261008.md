# 短时自动监听到原聊天投递试验报告（2026-10-08）

接收者：云端爱丽丝。执行者：本地柯蓝。红魔明确批准按照上一轮建议做一次监督试验，并提交结果。本轮结论是 **限定试验通过，implementation_ready；新增证据 review_pending**。前次单次手动恢复投递的接受范围保持，本轮不是爱丽丝已经接受的结论。

## 结果与实际使用判断

在原聊天已加载且可证明空闲的条件下，一个新合成文件经真实 Windows 文件事件、稳定判断、不可变批次保存、watcher 内部自动投递，进入准确原聊天；该聊天实际读取清单和 blob、核对哈希并返回 `173 + 284 = 457`。程序继续观察到同一回合完成，监督器随即停止 watcher；柯蓝独立核验后才登记合成 delivered 回执。**整个过程未手动调用 dispatch**。

这补上了此前“文件捕获与人工恢复投递分阶段”的空缺。当前可作为需操作者先打开目标聊天的短时监督试用候选，尚不足以接管小点正式投送或无人值守持续运行。试验结束后两个 canary 均保留 STOP，原定时任务保持 Human 设置的 PAUSED；未合并、安装自启、恢复原调度或部署。

## 固定输入、环境与授权边界

- 输入提交：`05864a467d12b1480bdb901d2f0ae1d27dc84e12`，实验前本地 clean、远端 PR Head 一致，44 项 SHA-256 清单全部匹配。候选生产代码和测试未修改。本轮提交仅追加文档和脱敏证据。
- 运行环境：Windows；复用原有隔离 Python 3.12.14 / watchdog 6.0.0。当前打包 Python 缺少 watchdog，改用已存在的项目隔离环境，没有安装新包。
- 实际管道服务：签名有效的 OpenAI Desktop 包 `26.1002.7124.0`；app.asar 为 561628354 字节，SHA-256 `76fe7078248c00e4e03dd2177a4275ec9ce158a9dd43452a4f0427d39a4ed012`。必需方法版本检查通过；这个检查本身不能代替实际链路验证。
- 试验限定：新建隔离 inbox/state，一个 91 字节 JSON、一个批次、最多一次 start 请求、最长 600 秒。正式投送目录没有读写或处理。沿用准确原目标，不更换聊天、不覆盖模型/权限/cwd、不 steering。
- 普通沙箱访问 Desktop 管道返回 WinError 5，依现有授权使用窄范围沙箱外执行；不修改 ACL、全局配置或权限策略。保护规范仓库读取也使用已批准只读路径，17 项当前完整性检查通过。

## 预检暴露的加载条件

重启后原生状态为 `notLoaded`。两次候选 owner 查询未取得 owner；带诊断的一次原始响应明确是 `resultType=error, error=no-client-found`。候选抛出的通用文字是 `IPC response method or owner mismatch`，因为该错误响应没有 method 字段；**这里不能把通用异常文字误判为实际协议版本失配**。

柯蓝通过原生界面打开准确原聊天，没有给它另发模型消息。随后相同候选取得 owner 与 `idle`，revision 6。真正投递阶段又两次核对 idle，revision 8 和 10，才写 start 请求。这证明本次“已加载原聊天”的路径可用；没有证明重启后能自行加载无人打开的聊天。错误提示可读性可作为后续局部改进项，本轮没有借试验修改候选逻辑。

## 方法与时间线

外层监督脚本调用未经修改的 `trigger.run(store, live=True, stop_event=...)`，并审计原生文件事件、候选事件、IPC 写请求与数据库状态。监督线程等 watcher 启动五秒后，独占写入唯一合成文件；此时初始空目录扫描和稳定扫描已结束。两秒稳定窗口，60 秒补偿扫描。真实 `WindowsApiObserver` 收到 created/modified 事件，约 2.172 秒后准备批次，时间早于下一次补偿扫描。

| 观察项 | 本轮记录 |
| --- | --- |
| watcher 启动 | 2026-10-08 02:58:20 UTC / 10:58:20 北京时间附近 |
| 文件写完至 batch_ready | 2.172 秒 |
| 文件写完至 IPC accepted | 8.172 秒 |
| 实际 start 请求 / 手动 dispatch | 1 / 0 |
| 原生模型回合耗时 | 81.611 秒 |
| watcher 总运行时间 | 101.188 秒 |
| 自然退出码 / 结束状态 | 0 / STOP，未强杀 |

这些是单次观察，不是延迟或性能基准。外层“一次发送/600 秒”限制是监督试验保护，并非新增产品能力。发送决策、稳定判断、批次生成、IPC 调用和后续回合观察均由原候选负责；没有替身代发或手动重试。

## 结果核验与回执

本地执行 27 项证据断言，27/27 通过。该数字表示这次验收脚本的断言数量，**不是新增单元测试数**；历史 Windows 80 项、Alice 14 项未在本轮重跑。

原生状态与精确基线之后的 rollout 对应同一 completed 回合；实际投递原文能逐字匹配。目标使用两次 functions.exec，产生四次成功 exec_command 输出，其中包括清单与 blob 的真实 Get-Content/Get-FileHash/Get-Item。marker、left、right、结果与输入一致，91 字节 blob 哈希 `e11f5493a4a50d47409149ec32f5bb3cc43e35e4f0c0bd34e4112d2e89852155`；476 字节清单哈希 `d933b43fabac3b2886af388b18795f37e62e77caf328ba87d93ebbc1dfc84691`，与发送前数据库备份保存的清单字节一致。不是仅依赖模型口头声称。

model、effort、approval_policy、sandbox_policy、cwd 与投递前目标设置逐项一致，请求未带这些覆盖字段。同回合 UserPromptSubmit 和连续性提示可见，目标只读核对，没有替其他 scope 写 source ACK；这只证明本次提示可达，不是整体 Hook 效果验收。

柯蓝核验上述证据后，才用本地合成结果回执登记 delivered。随后在 watcher 已停止时对相同现有字节做两次稳定扫描，仍是一批且 delivered 证据哈希未变，没有第二次 IPC。该项仅支持本次重复字节静态复扫；不等同并发 ACK 或长时运行的新增实机验收。这里的 delivered 是合成任务完成回执，不代表小点业务报告已交付。

## 维护成本与剩余边界

本次实际维护动作包括复用正确的隔离依赖、一次 no-client-found 的诊断、通过原生界面打开目标，以及受控执行管道访问。候选自身仍无法恢复未加载 owner，通用报错也不够精确。私有 IPC 方法版本、运行包及设置继承都须继续按实际环境取证；目前没有支持未来版本兼容、并发原子 idle-CAS、长时间常驻、重启补偿到实际聊天、多个业务批次或真实外部交付的实机证据。

建议爱丽丝按本轮边界审查“已加载且空闲的原聊天，单文件自动监听到原生投递”是否可接受；正式采用仍需另行限定业务范围和运行条件。保留 Draft，不把此一次成功升级成长期生产承诺。

## 证据位置与来源

公开附件：[脱敏试验证据](../evidence/supervised-watch-trial-20261008.json)。其中列出精确时序、27 项核验结果、包哈希、原始材料哈希与脱敏范围。原始管道/会话/数据库证据只保存在本地受控 run，不上传身份内核、凭据、私人路径或会话原文。

固定代码依据：[稳定扫描、投递与 watcher](https://github.com/scarlet-devil/codex-condition-trigger/blob/05864a467d12b1480bdb901d2f0ae1d27dc84e12/trigger.py#L300)、[IPC owner/当前状态](https://github.com/scarlet-devil/codex-condition-trigger/blob/05864a467d12b1480bdb901d2f0ae1d27dc84e12/desktop_ipc.py#L309)、[投递与限制](https://github.com/scarlet-devil/codex-condition-trigger/blob/05864a467d12b1480bdb901d2f0ae1d27dc84e12/docs/IPC_ADAPTER.md)。先前接受范围见 [Alice 2026-10-08 验收](https://github.com/scarlet-devil/codex-condition-trigger/blob/05864a467d12b1480bdb901d2f0ae1d27dc84e12/docs/ALICE_IPC_ACCEPTANCE_20261008.md)。本轮只对已固定候选做实机验证，没有引入新第三方实现。

[Governed Work Report]
Collaboration identity: Kelan。Acting role: 本地监督试验与证据交付。Deployment environment: local Windows Desktop，已验证 CODEX_HOME 登记。Task-assignment source: 红魔当前直接批准；Scope/expiry: 本次一个合成文件、一次发送、最长十分钟及结果交付，STOP 即停止新动作。Task class/profile: C / enhanced。Workflow state: implementation_ready、Alice review_pending、PR Draft。Capability gate: 本地、GitHub/Drive、准确 owner/idle 与管道来源已核验；不扩大权限。Kernel/registry: installed，规范固定 efd007a43d648f8460292db6308ba2538b3bcd36；完整内核和登记仅留本地。Repository facts: 输入 05864a467d12b1480bdb901d2f0ae1d27dc84e12，候选源码未改。Checks: 27/27 证据断言、一次实机回合、完整哈希与回执核验。Failed/skipped: 初始 no-client-found、普通管道权限拒绝；未复跑历史测试，未验证长期/业务/并发/跨版本。Truncation/redaction: 部分探索命令输出截断后按目标代码和证据定点读取，正式四件工具输出完整；公开附件脱敏。Assumptions/deviations: 需操作者打开原聊天，单次计时非基准。Required Alice review: 本轮限定实机结论。Required Kelan review: 交付与停止状态核对。Required Human decision: 本轮无待批动作，不自动进入下一阶段。
