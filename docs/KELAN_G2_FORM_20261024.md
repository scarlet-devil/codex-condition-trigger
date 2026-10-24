# G2 三项表单实现与 Windows 模拟验证

作者：本地柯蓝；接收与验收：云端爱丽丝。2026-10-24。状态：implementation_ready / review_pending。

候选已把“文件夹、触发条件、目标对话”接到实际文件监听器。真实 Tk 表单完成了目录选择、同名目标区分、预览、启用、两批模拟通知、暂停、恢复、最小化和关闭。传输始终使用显式 fake；没有真实 Desktop IPC、目标模型回合或生产启用。G0 limited_accepted、G1 accepted 继续有效；G2 尚待 Alice 验收，G3 未执行。

## 来源与改动

固定输入为 [d153f0b0](https://github.com/scarlet-devil/codex-condition-trigger/commit/d153f0b0ff950568d17ff04573819f77c29429b5)，执行其行动方案第 13 节。203 个输入 blob 已按 Git blob、长度和 SHA-256 核对。候选文件与最终检查的精确摘要见同批清单及 [证据](../evidence/kelan-g2-form-20261024.json)。

| 文件 | 实现与原因 |
| --- | --- |
| `simple_catalog.py` | 只读当前 Desktop SQLite 元数据；先检查 schema、500 条/1 MiB 边界，再提取必要字段。搜索使用参数；不读取聊天历史。保留 WAL 语义，查询有界。名称优先，重名显示项目、时间、短 ID；以稳定 ID 绑定，预览核对 rollout 首行。 |
| `simple_controller.py` | 预览代次、受管线程、每线程连接、保存规则校验、连续持有 worker/目标锁、暂停与关闭等待。只从本地状态刷新，不额外查询 Desktop。只有当前 worker/run_id 有实际扫描进度才显示监听。 |
| `simple_setup.py` | Tk 三项表单、两个条件预设、有限高级选项、精确摘要和独立状态。默认稳定 120 秒，默认忽略初始已有文件。最小化继续运行，关闭会等待退出。 |
| `experimental/simple_form_fake.py` | 可见、隔离的模拟入口；写入实际合成文件，通过原监听/调度链推进，不用夹具直接制造业务批次。 |
| `rule_service.py` / `notify_state.py` | 预览仅核对首行；启用支持取消和既有 Store 归属；记录真正提交的初始计数，避免把预览计数当基线。 |
| `trigger.py` / `worker_health.py` | 窄的 adapter/run_id 注入，默认调度参数保持；退出等待 observer，保留主错误。进度文件读写增加同进程锁和最多 250 ms 的 PermissionError 重试，仅用于健康回执，不重试发送。 |

保存规则只认本工具清单与一致绑定；文件缺失或冲突显示需核对，不自动建库或导入生产规则。重新加载不会自动恢复。改变输入需暂停后新建规则，旧积压保留。停止不清 STOP、不延长绝对期限、不取消已被宿主接收的回合。

真实来源的只读探测返回 7 个当前项目匹配候选；4 个 rollout 首行身份匹配，3 个文件已不可达，不能通过绑定核验。读取耗时约 0.031 秒；两个原始 cwd 表示不据此解释为两个不同项目。该探测早于最后的预算异常传播修正，源码摘要单独保留；它不是当前 owner 或可发送状态的证明，也不证明跨版本兼容。

## Windows 表单证据

第一轮保留为失败：目录和第二个同名目标选择正确，基线提交 1 个旧文件，扫描实际运行。A 只模拟发送一次，但 GUI fake 给出 `baseline.bytes=0`，被原有回执校验拒绝，保留 uncertain，未写 B 或重发 A。根因在新模拟器，不能由此前另一套 fake 的通过推定其正确。补齐合法合成基线后，增加使用同一 GUI fake 的完整双批回归。第一轮耗时 224.110 秒；基线/worker 在 156.672 秒提交，未达到两分钟配置目标。旧证据和暂停状态没有覆盖。

第二轮使用新合成目录和最终冻结代码：

- 默认 120 秒实际可见；本次通过表单改为 **1 秒**，只用于合成试验。仍默认忽略旧文件；预览和实际提交均为 1 个。
- 明确选择第二个同名目标，配置、两次 fake 发送目标和 rollout 身份一致。表单初始化后 71.640 秒基线提交并启动 worker；写入 A 的 86.687 秒之前，已观察到“监听中／扫描 ok”。这个有界自动操作配置过程在两分钟内；不代表真人学习成本。
- A 接收运行时 B 已稳定冻结但等待；A 准确终止、通知释放后，B 自动接收一次。A/B 各一次，共 2 次；终止后积压为 0，业务交付仍未核验，ACK=false，execution_outcome=unknown。
- 暂停落盘后 worker 退出；恢复同一规则产生新 run_id，不重建基线或重发已结束批次。最小化期间读取到 running 的新进度，恢复窗口仍显示监听。
- 关闭等待线程退出；进程退出码 0、窗口消失、两把锁可重新取得。只读重载保存规则通过且 enabled=false；输入及状态字节在收尾检查前后相等。独立重开 GUI 未另做，其恢复路径由控制器测试和只读重载覆盖。

完整第二轮操作 193.312 秒，比预估的约两分钟长；结束已通知红魔恢复键鼠。它是 Windows/Tk + 实际 watchdog 扫描 + fake 传输的证据，不能写成真实 Desktop 双批通过。`run` 日志的 `mode=live` 表示走调度分支；实际注入对象仍为 fake，未调用原生客户端。

## 检查、失败与修复

最终 Windows / Python 3.12.14 全套 **257 方法：256 通过、1 跳过、0 失败/错误，Python 原生退出码 0**。27 项新增来源/控制器方法计入其中。唯一跳过是 Windows 符号链接创建权限；Windows overlapped-I/O 和 3 项冻结 Hub 集成测试实际运行。Hub ZIP CRC、15 项载荷摘要已核验；未安装生产 Hub。没有重跑未改动的 G0 实机或 34 项实验回归。最终运行前后 10 份改动代码/测试摘要一致。

新增六文件默认 Ruff 及格式检查无诊断；十文件 E9/F63/F7/F82 检查无诊断。四个共用旧模块默认诊断从 30 到 32：新增 BLE001 为退出时保留主错误的边界捕获，SIM117 为进度锁与文件读取的嵌套 with；保留明示，不称整个项目默认 lint 全绿。16 份选定公开材料通过 Gitleaks 8.30.1 检查；私人聊天 ID、实际用户路径及凭据模式扫描无命中。未有适用 Lean target。

实质失败均保留：来源连接管理曾掩盖主异常；Windows 进度文件原子替换与读取曾冲突，移到原用户上下文仍可复现，不能归因为沙箱；尝试 FILE_SHARE_DELETE 未解决且已撤回；采用进程内锁与有界进度重试后通过。第二表单关闭曾暂停第一表单 worker，现以归属锁和原目标锁区分。独立审查复现了初始化扫描失败使保存清单失配，已修复为控制器统一持久化配对配置。另修复状态刷新无限保留已结束 Thread，以及元数据预算异常被误当作不支持 cwd 而静默过滤。每个行为修正有失败/通过证据。

本地受控子任务 `/root/g2_final_review` 为 S1/M1 技术审查，非 Alice、非 S2。独立核验冻结输入 209/209，执行冻结候选 24 项 G2 与 36 项 G1 检查；之后对初始化修复 1 项、线程引用修复 4 项、目录边界修复 2 项作窄复核，均通过。它们有重叠，不与主执行者全套相加。最终 GUI 与组合测试由主执行者负责；治理安装核验在子审查中明确引用主执行者证据。

初次 pythonw 后台启动没有出现可用窗口，退出原因未确证；后续使用受管前台命令启动自有 Tk 窗口。初次窗口输出在工具展示中截断，第一轮状态库和 UI 证据保留；第二轮 stdout/stderr 完整落盘。窗口自动化曾遇到模态索引缓存、Tk 文本输入方式问题；补测采用重新观察及普通键输入。收尾辅助脚本曾引用错误字段名，已改按实际 `business_delivery` 字段核对；没有因此重跑 GUI。最终全套另以 subprocess 捕获原生退出码和前后源码摘要，早先重复结果不累加。

## 复现、限制与下一步

模拟启动及操作见 [G2 使用说明](SIMPLE_SETUP_G2.md)。当前安装提供的 SQLite schema 属于版本相关内部来源；未知 schema 拒绝继续。保存规则列表目前以规则目录标识显示，交互仍是候选版。UI 刷新有短暂缓存延迟，但不会用旧 worker 的绿色状态假称仍在监听。

完整历史增长、原生 idle/start 之间的竞态、历史程序或人工发送不受当前锁约束等既有边界继续保留。本轮没有查生产监听健康，没有安装、合并、恢复生产、变更业务 ACK、旧 STOP、到期或 PAUSED。请 Alice 复核 G2 实现、失败修正及真实 Tk/fake 证据，决定是否接受。G3 的真实查询/发送数量和停止条件须另行限定，本轮不启动。

[Governed Work Report]

- Collaboration identity / Acting role：Kelan，本地实现、验证、证据交付；Alice 为接收与验收者。
- Deployment environment and evidence：本地 Windows Codex；解析后 CODEX_HOME installed 登记及当前轮 Active 28/28 通过，私有完整证明留本地。
- Task-assignment source, scope and expiry：红魔接续的 d153f0b0 第 13 节与两次明确窗口间隙；止于 G2 候选交回，非 G3/生产授权。
- Work surface / Task class：PowerShell、既有 Python/Tk/watchdog、Computer Use 与 GitHub 插件；实现为 C/enhanced，原 Draft 公开交付按具体授权的 D/constitutional 边界处理。
- Workflow state / Capability gate：implementation_ready、Alice review_pending；固定输入、最终源码和测试、隔离 GUI 均有证据。远端提交/回读状态另见交付回执，不以本报告创建代替交付。
- Kernel source and hash：bc77e24f12ff4899b572d6c704d59929b2e2369c 的 codex-home/AGENTS.md；SHA-256 e349ac44fda1c8011dd69e4a20295660cc645e3afbe492b06acd0f957d2dd414。
- Registry / Canonical repository and integrity：已安装登记指向专用治理仓库 scarlet-devil/rule-of-rules，同一 bc77e24 固定提交，树、必需 blob、根内核一致。私有绝对路径不外传。
- Applicable instructions / Repository facts：项目 AGENTS 与第 13 节已读，无实质冲突；203 输入 blob；保持原 PR #2 Draft/unmerged，不改历史接受结论。
- Actions / Checks passed / Failed or skipped：见上文及配套证据；不把自审或本地独立上下文审查当作 Alice 接受。
- Truncation and redactions：原始日志、数据库、截图与真实会话元数据留本地；公共材料只含源文件、合成证据、必要摘要及哈希；无凭据、身份正文或私人聊天 ID。
- Assumptions / Known limitations：内部 schema 与当前 Windows 安装绑定；上述 fake、计时、恢复及生产边界明确保留。
- Required Alice review：G2 阶段验收与后续 G3 简报。Required Kelan review：S0 与 S1/M1 已完成。Required Human decision：如平台阻止本批公开交付，仅就已准备的具体材料/目的地询问；不推定合并或生产批准。

