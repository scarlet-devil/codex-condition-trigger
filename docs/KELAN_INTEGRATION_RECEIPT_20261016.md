# 原生采集与 Hub 恢复候选回执

本地柯蓝，2026-10-15 开始、2026-10-16（Asia/Shanghai）收尾。
来源：Human“接下来按照这些继续做吧，推进到需要我真实登录告诉我”。
基线 `0d7f57616d0ca78e4b1d8ddf79deb238693328d9`，沿用 Draft #1。

**implementation_ready / review_pending；候选未正式安装，真实 Drive 与真实登录未验收。**

## 本轮实现和证据

1. `native_collector.py` 通过已验证 Desktop IPC 读取准确 turn 的终态。canonical history、
   当前 overlay、thread/cwd/revision 与 batch/turn/manifest 同时绑定；冲突或缺失保持 unknown。
   默认关闭的 `native_result_collection` 开关接入 `cycle_tick`；`collect-outcomes` 可单独执行。
   状态与脱敏证据同事务写入，保持并发 ACK、原有业务交付和 STOP 边界。
2. `hub_delivery_driver.py` 将冻结 outbox 的 lookup/upload/readback 接入原 Hub 边界。
   不读取凭据、不直接 HTTP、不另建 OAuth。每次只传一个文件；此 Hub 适配器上限 **8 MiB**，
   以容纳现有 16 MiB IPC base64 回读。通用 outbox 的 20 MiB 限制未改；8 MiB 以上本适配器拒绝。
3. 共用 Hub 隔离候选增加 versioned material recovery：原 project/identity/route/frame 校验后，
   先持久绑定预生成 Drive ID 再创建。重试只能使用相同 ID；旧歧义操作不迁移或重放。
   新旧 schema 在同一 SQLite 写事务下互斥占用 operation ID；media 下载在传输边界限长。

Google 关于预生成 ID 和重复创建 409 的接口依据：
[官方 create-file 文档](https://developers.google.com/workspace/drive/api/guides/create-file#generate-ids)。
官方契约与离线适配器测试不代替实际 Drive 验收。

| 验证 | 本轮直接结果 | 限制 |
|---|---|---|
| 条件触发器可用完整套件 | 185 项，184 通过、1 项 Windows symlink 权限跳过 | 隔离候选，非生产 |
| 本机可用 Hub 测试目录 | 324 通过，0 失败 | source-r2 是交付子集，不冒称上游全仓所有测试 |
| Hub 新增定点检查 | 13 通过；其中4项修前按预期失败 | 合成 HTTP/provider |
| 条件 outbox→薄客户端→真实 LocalHub | 3 通过，包含响应丢失及重新打开数据库 | 合成远端 |
| 原生独立工程复核 | 两项初审问题关闭；14项定点通过，另有9种 overlay 构造 | 本地 Kelan S1，不是 Alice |
| Hub 独立工程复核 | 两项 P2 关闭，19场景通过 | 独立 Hub/SQLite 连接线程；未冒称真实云端 |
| Windows 原生管道及进程死亡 | 服务写合成对象后 exit23；新服务/客户端恢复到 uploaded_verified，exit0 | 真管道/真子进程，provider 为本地合成磁盘 |

Windows 进程实测只预留1个 ID、创建1个对象，32字节原件 SHA-256
`e3885a0c569a1a80bfff230023c265f6b28f0b47c5a84b8d5401d6217c68f200`
回读一致；批次行、STOP 保持，模型派发0、业务ACK0、网络调用0。

已加载的本机当前 chat 经真实 IPC 取得 canonical 历史中一个准确已结束 turn 的
completed/error=null 投影；未恢复或派发回合。原生产目标 owner 只读探测返回
`owner_discovery:owner_unavailable`。因此只确认已加载 chat 的真实读取能力，
不将当前 chat 的结果归给原生产目标，也不据此续期旧试验。

## 发现、修正与失败材料

原生初审发现 waiting_materials 会绕过采集、等价 Windows cwd 被重复拒绝；已修正并独立复核。
另补 canonical/overlay 冲突回归。Hub 初审发现跨 schema 同号能重复上传、远端 media 限长太晚；
已先保留失败反例再修正。ID预留网络异常也固定为 `MATERIAL_RESERVATION_UNKNOWN`，避免退出整个服务。

一次条件套件误用了不含 watchdog 的通用 Python，185项中出现3失败/6错误/1跳过；原日志保留，
换回既有 watchdog6 环境后185项184通过/1跳过。未把依赖缺失误记产品失败，也未覆盖失败材料。
Hub第一次316项中 Windows junction 因沙箱 AccessDenied 失败，宿主单项通过；最终增加测试后的
324项在宿主隔离目录全部通过。两次沙箱管道测试看不到唯一测试管道；宿主同脚本通过。
所有进程结束/中断均只涉及本轮创建的测试子进程。

## 共用 Hub 的准确安装边界

当前原 Hub 普通上传接口没有预生成 ID 和恢复读取入口；直接复用凭据绕过它会丢失注册与路由门。
故需要安装已经准备好的 **3份运行文件 + 1份摘要清单**，不是仅切换触发器配置。
现有授权覆盖候选开发和验证；共用 Hub 的定点停启与正式覆盖尚待 Human 针对具体动作批准。
原因是本地 AGENTS §9 的 Class D 具体批准门，以及本项目原生产继续停止的有效边界；
没有自动审批拒绝，也不是要求重复批准已完成的开发。

[冻结 Hub 包](../evidence/hub-material-recovery-candidate-20261016.zip)：53770字节，
SHA-256 `21f736228e18f430e537e4845e69ae9a2f0727145587d5d3642746b3417de14d`；
16成员CRC及15负载manifest长度/哈希通过。包内 `HUB_INSTALL_MANIFEST.json` 固定前后精确字节，
[可读补丁](../evidence/hub-material-recovery-20261016.patch) 供审查。不含数据库、凭据或真实业务材料。

获准后的执行顺序：

1. 重新核验原3文件/摘要清单及实际 Hub 进程归属；核定无进行中的传输。
   如有活动上传则等待/停止本次安装，不强制中断上传。先保存原源码、清单、SQLite一致备份和进程证据。
2. 在短维护窗口仅定点停止确认的原 Hub 实例，应用列明文件和摘要登记，再沿原启动配置恢复。
   共用传输会在停启期间暂不可用；不更改登录、凭据、项目route、其他项目配置或旧歧义记录。
3. 源码回读符合新摘要、原项目登记与旧表内容保持后，绑定条件触发器的隔离 canary outbox。
   仅使用原项目标准路由内一个新的非敏感合成文件；先完整真实上传/回读，再在客户端回执交付前
   注入一次失响应，重启客户端按原ID找回并核验全字节。故障注入位置和实际创建次数分别取证。
4. 故障时冻结新 canary 任务、保留新表及故障证据，恢复准确原源码/清单和原启动方式；
   不回滚其他项目数据库、不删除云端材料、不用旧接口重放新任务。
5. 同步安装/实际上传结果并交 Alice 复核；保持旧生产STOP、到期锁、旧ACK及PAUSED。
   然后准备独立 dry 登录任务，告知 Human 保存工作并真实注销/登录。

当前没有注册或启动登录验收任务；登录将使用独立目录、固定15分钟有效窗口和5分钟运行上限，
无模型、无上传、无业务ACK。不得手动 Start-ScheduledTask 冒充登录；实际登录事件和任务触发来源需另证。

## Governed Work Report

Collaboration identity: Kelan。
Acting role: 本地实现、隔离验证和交接；root自查S0，两项独立子任务S1。
Deployment environment and evidence: 本地 Codex Desktop/Windows，解析 CODEX_HOME 已核验。
Task-assignment source, scope and expiry: 本轮Human指令；推进两项接入至真实登录前，原生产未续期。
Work surface: 当前可写 recovery 下独立 clone 与 Hub 副本；正式路径只读。
Task class and triggers: C / enhanced，跨模块接口及持久恢复；后续共用Hub正式变更按D/constitutional。
Workflow state: implementation_ready / review_pending；未安装、未合并、未Ready、未生产启用。
Capability gate: 本地测试/真实IPC/独立审查可用；真实Drive和正式切换尚未执行。
Kernel source and hash: 387c98a，SHA256 e349ac44fda1c8011dd69e4a20295660cc645e3afbe492b06acd0f957d2dd414。
Registry path and status: CODEX_HOME/KELAN_CONSTITUTION_INSTALL.json，installed；Active27/27。
Canonical repository, remote, pinned commit and integrity: 专用governance/rule-of-rules；
scarlet-devil/rule-of-rules；387c98a45b8fcc4409647c5bdc3363d614542859；2026-10-15T15:21:17Z验证通过。
Applicable project instructions and conflict status: 既有项目入口、用户本地内核；未发现适用冲突。
Repository facts: condition基线0d7f5761；原source-r2两个变更文件与原MATERIALS摘要一致。
Actions and material evidence: 候选源码、反例、测试、独立复核、原生只读投影、隔离管道进程恢复、冻结包。
Checks passed: 上表逐项；Checks failed or skipped: 上述依赖/沙箱失败保留，symlink1项跳过。
Truncation and redactions: 工具中部分长日志截断；本地完整日志保留，发布材料脱敏，不发布私有chat/turn/用户路径或凭据。
Assumptions and deviations: Hub运行上限8MiB；不把离线替身及当前chat读取推定为原生产/Drive验收。
Known limitations: 真实Drive、原目标owner、真实登录及整体验收仍未闭合。
Required Alice review: 本轮准确源码与Hub包、之后真实安装/传输证据。
Required Kelan review: 本轮独立工程审查完成；正式切换前复核精确当前基线。
Required Human decision: 共用Hub三文件及摘要登记的定点停启安装、一个新合成文件真实传输/恢复验收；稍后真实登录。
