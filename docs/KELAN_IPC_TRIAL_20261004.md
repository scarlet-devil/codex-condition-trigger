# 给爱丽丝：条件触发器 IPC 适配器与受控小试调查

作者：本地柯蓝。日期：2026-10-04。依据：`678f6366b5f56e25f98e78a699420d2a89419090` 的交接及红魔批准的验证范围。状态：实现候选 `implementation_ready`，整体 `review_pending`，PR 保持 Draft。

## 结论与需审查的问题

已完成文件触发核心与聊天适配器拆分，并建立实验性 Windows Desktop IPC 后端。当前机器上的管道连接、安装签名、协议初始化和指定聊天 owner 查询已真实通过；但**本轮没有发送 start-turn，没有唤醒原聊天，没有产生合成业务 ACK**。

发送前的受控审查发现：原聊天历史存在一次重叠开始事件，前一回合缺少明确的闭合记录。原解析器会被较晚的完成事件带回 `idle`，证据不足。修正后保守拒绝这种历史，因此单次合成试验停在投递前，固定批次保持 `ready` 和本地 STOP。最初只读探测中输出的 `can_send=true` 已撤回；管道、签名和 owner 查询的事实仍有效。

请爱丽丝优先审查：是否以一个严格绑定 owner、conversation、cwd 和当前 revision 的原生状态快照，解决历史观察无法证明当前空闲的问题。不能通过删除真实日志、忽略重叠、切换其他聊天或把新的完整回合当作自动豁免来推进。既有周期机制保持；本轮不提出生产替换结论。

## 实现变化

`trigger.py` 保留文件稳定判断、SHA-256 去重、不可变 blob、SQLite 批次、发送意图、退避、单 worker 与业务 ACK。`chat_adapters.py` 收纳既有 JSONL queue 后端及小型 inspect/observe/prepare/send/close 接口。`desktop_ipc.py` 实现 Windows 命名管道、可信安装检查、准确 owner 路由和指定 rollout 观察。

数据库增加可空 `dispatch_meta`，保存发送前历史基线、owner、request/client 标识与安装证据；旧库不补造缺失回执。数据库绑定后端，不能静默将 queue 待办改投 IPC。`delivered` 仍由同一条 SQLite 条件更新保护，旧观察不能覆盖交付证据。

IPC 的 `accepted` 与 queue 的 `queued` 分开：原生 start-turn 回复只记录 native turn ID，不产生虚构 submission ID。运行、完成、失败来自后续生命周期；完成不等于交付。已经接受或发送结果不明时不自动重发。忙碌、不明确或缺少 owner 时留在本地。

发送请求省略 model、cwd、审批、沙箱与权限覆盖，包括不传 `permissions: null`；明确使用 `inheritThreadSettings: true`。这条请求形状经过代码与夹具检查，当前安装内相关继承路径已只读核对；**真实发送后的有效设置仍未验证**。

新增可选 `task_instruction`，使明确配置的只读合成任务不混入默认业务交付/ACK 流程。输入文件内容仍作为数据。示例配置保留占位 thread 与路径，默认不授予真实投递资格。

## 来源及当前安装核对

交接基线完整克隆了 20 个已跟踪文件，并与该提交的 Git blob 核对。IPC 的公开协议参考固定为 [CodexAgentControl 7640887 的协议说明](https://github.com/Destiny-Rul/CodexAgentControl/blob/76408870888198f7ee3973b807d2302a86236143/skills/codex-desktop-control/references/protocol.md)，许可见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。这是第三方协议参考，不能称为 OpenAI 官方 IPC 契约。[官方 App Server 文档](https://learn.chatgpt.com/docs/app-server)也不能替代本次私有 Desktop 路径的现场证据。

既有私有实现提供了帧格式、owner 定位及回执关联的历史线索。只读核对后独立实现 Python 适配器，没有复制私有身份、绑定、会话内容或旧权限覆盖逻辑。历史上的接入成功不作本次成功证据。

| 当前实测项目 | 证据及边界 |
| --- | --- |
| Desktop 安装 | `26.930.3930.0`；实际 pipe server 为同一安装中的 ChatGPT.exe；Authenticode Valid，OpenAI 签名 |
| app.asar | 549,383,582 bytes；SHA-256 `af98213984ec4556778ef9276193d51460153fb9b30fded882d503637b84abba` |
| 协议表来源 | `.vite/build/src-ZHMZMKol.js`；SHA-256 `74a48cb34afbc59137618cf9e693859471956954a51331079bd19cd0bc8916bd` |
| owner/继承实现来源 | `.vite/build/bootstrap-CZlEGA2m.js`；SHA-256 `343072f02e604fe06f7864a72b1cbcc6004a8a318c66982995a188ee97430a3b` |
| 使用的请求 | initialize v1、thread-owner-discovery v1；二者真实完成。start-turn v2 仅静态/夹具验证，本轮未发送 |
| 版本判断 | 自动发现真实 pipe server 安装；方法版本核对与整包 hash 分开。没有将新 hash 自动判作不兼容，也未证明任意新版本兼容 |

普通命令沙箱打开 pipe 得到 Access Denied；在红魔批准的小试范围内，经过命令权限边界后才完成只读连接。程序本身没有提权或修改 ACL。首次签名子进程还遇到 PowerShell Security 模块加载失败，定位为子进程环境问题；改为显式加载该 PowerShell 自身模块并固定输出编码后通过，没有修改全局模块、信任或权限设置。

## 测试、审查与现场结果

| 证据层次 | 结果 | 不能推出的结论 |
| --- | --- | --- |
| 历史作者 Linux 结果 | 原修订版 44 项通过，沿用原证据 | 不是本轮 Linux 复跑 |
| 历史原版 Windows 结果 | 42 通过、1 SQLite 清理错误、1 跳过；原失败保留 | 不能回写成原 Head 全通过 |
| 本轮清理修正后的基线 | 44 项：43 通过、1 跳过 | 仅修正测试连接未关闭 |
| 最终 Windows 回归 | 69 项：68 通过、1 Windows symlink 条件跳过，6.812 秒 | 合成 IPC 夹具不是真实模型或工具运行 |
| 受控审查 | 本地隔离上下文技术审查，S1-M1；发现 3 项 Important，修正后 3/3 定向独立复核通过 | 不是云端爱丽丝/S2 验收 |
| 唯一合成文件 | 原生 Windows watcher 约 1.219 秒形成一个固定批次；补偿扫描间隔 60 秒；watcher 正常退出 | 尚未投递到聊天 |
| 原聊天端到端 | start-turn 0；结果核验 0；合成 ACK 0 | 工具、Hook、有效设置、模型结果和外部交付均未验收 |

完整最终回归见 [Windows 输出](../evidence/windows-ipc-tests-20261004.txt)，脱敏现场摘要见 [结构化证据](../evidence/windows-ipc-trial-20261004.json)。原始真实聊天标识、路径、源记录和诊断保存在受控本地运行目录，不进入公开仓库。

审查的三项问题均先构造反例再修复：

1. 重叠/重复 `task_started` 不能产生可信 `idle`。现在直接拒绝，需要补充原生状态证据；目标现场同样命中此限制。
2. 签名检查的 TimeoutExpired/CalledProcessError 现在进入受控投递退避。新增实际 watcher + 合成宿主失败实验，确认失败后仍保存后来到达的第二个本地批次。
3. overlapped I/O 等待中发生 KeyboardInterrupt 时，先取消并等候内核完成，再释放缓冲区、OVERLAPPED 与 event；合成内核反例已覆盖。依照 [ReadFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile)、[CancelIoEx](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex) 和 [GetOverlappedResult](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-getoverlappedresult) 的存储生命周期要求，取消后的回收等待不能冒充严格端到端墙钟截止。

只有第三项的控制流与 API 契约得到验证，没有制造真实内核异常或测量极端取消延迟。关于代码的独立复核与真实环境的父执行者证据分别标注，未合并为一次全面验收。

## 维护成本与接续边界

新增两份生产模块和两份测试模块，生产代码现在分布在三个文件；没有新增 Python 第三方依赖。维护面包括：3 个私有请求版本、帧结构、owner 路由、原生回复形状、设置继承字段，以及 session_meta/turn_context/生命周期/工具记录的私有 rollout 格式。

本轮实际适配成本已出现两类：Windows 子进程运行环境和历史生命周期歧义；它们不是协议版本升级故障。三项审查修正又补足了状态解析、故障隔离与 native I/O 回收。没有足够样本将这些成本换算成未来每次更新所需时间，或宣称后续维护很低。

当前还存在两个明确限制：检查到发送之间没有原生原子 idle compare-and-set，其他写入者可能抢先开始回合；每次观察最多读取指定 rollout 的 64 MiB，尚非可长期扩展的索引。不能以本次单版本连接成功证明长期无人值守可用。

本轮对已存在的 complete-history 请求做了有限源码核对：回复提供 revision，并广播快照，不能直接当作已验证的当前 idle API。接续应先明确快照字段、owner/目标/revision 关联与竞态策略，再决定是否值得实现；不在这次缺少该契约的条件下继续真实发送。

未改变原周期机制，未安装服务/自启，未修改 Desktop 设置、凭据或全局规则，未执行合并或正式采用。唯一真实目标的合成批次保留待续，默认暂停。下一位执行者应先读这份报告和当前状态，核对是否已有后续发送证据，避免重复试验。
