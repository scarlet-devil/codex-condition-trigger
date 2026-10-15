# 原生结果采集候选初审

结论：`changes_requested`。发现 1 项 P1、1 项 P2；均已独立构造隔离反例。候选代码没有被本审查修改。此报告只评价初审输入哈希，修订后须重新读取受影响内容。

## 输入与方法

- 候选：`<isolated-work-root>\candidate`；父任务提供基线 `0d7f57616d0ca78e4b1d8ddf79deb238693328d9`，工作区有未提交 diff。
- 核心范围：`desktop_ipc.py`、`native_collector.py`、`trigger.py`、`tests/test_native_collector.py`、`docs/NATIVE_DELIVERY_INTEGRATION_20261015.md`。因自动调用链需要，另只读 `owner_loading.py`、`execution_result.py` 及测试夹具。
- `reproduce_review.py` 在 `review-native/tmp` 创建全新临时数据库，使用候选代码及合成 IPC wire。没有模型、生产调度、登录、Hub/Drive 服务调用；没有读取凭据或运行注册信息。
- 代码输入 SHA-256 保存在 `reproduction.json.source_hashes`；该 JSON 记录每个反例和 ACK 检查结果。
- 实际执行：隔离 Python `-B -X utf8`，`PYTHONPATH` 为候选及 tests，TEMP/TMP 为父任务 tmp。复现脚本 exit=0。
- 本审查另外亲自运行 `python -B -X utf8 -m unittest test_native_collector -v`：7 tests 全通过，exit=0。父任务报告的 179 项全套结果不是本审查亲自运行证据。

## 成立的保护

- 终态投影要求准确 `turnId`、唯一匹配和显式 `error`，未知结构不会直接成为成功。
- 原生证据保存最小字段，不包含消息或 error 正文。
- 本地结果与证据在同一 SQLite 事务写入，写入前重新核对 turn、manifest、现有结果及 delivered。
- 独立实际双 SQLite 连接检查：快照读取期间另一连接调用现有 `acknowledge`；采集返回 `changed`，业务 delivered 与原调用者证据保留，未写入 execution_result。
- 原生终态没有直接写业务 ACK。

## P1：窗口管理路径跳过 waiting_materials 的自动采集

定位：`trigger.py:485-487`，关联 `owner_loading.py:237-239,257-270`。

新增采集仅接在 `dispatch_one` 内，但实际 live watcher 调用 `cycle_tick`。启用 `owner_loading_enabled` 后，`cycle_tick` 先运行材料等待协调及窗口状态分支；waiting_materials 在没有活动窗口时直接 quiet，在 reused 周期时直接 cycle_deferred。两者都不到 dispatch_one。由 task_complete 产生 ended 后提交材料等待是合法路径，其原生结果仍可 unknown。

独立复现：创建 Desktop adapter 的全新 Store → 形成 ready 批次 → 绑定 exact turn 并置 ended → 经 `defer_materials` 接受合法等待凭证 → 保持 `native_result_collection=true`、`owner_loading_enabled=true`。合成原生快照报告相同 turn failed。连续两次 `cycle_tick` 返回 quiet，采集调用 0，批次仍 waiting_materials/unknown；随后手动调用同一 `collect_outcomes` 立即写 failed/failed。

影响：正常无人值守循环漏采这个合法批次；材料等待可能持续释放后续调度，而原生失败未入账。

最小修正：在 live cycle 统一入口经过 STOP/到期及 ownership 门后、材料协调与窗口分支前采集；避免 dispatch_one 重复采集。回归应调用 `cycle_tick`，不能仅 mock 直接调用 `dispatch_one`。

## P2：再次严格比较 cwd 拒绝 Windows 等价路径

定位：`native_collector.py:64-65`，关联 `desktop_ipc.py:400-403`。

IPCClient.current_state 已通过 normcase/normpath 验证 cwd；collector 随后用原始字符串 `snapshot['cwd'] != expected_cwd` 重新验证。Desktop 与配置使用不同大小写或斜杠时，同一个合法路径被拒绝。

独立复现：使用真实 IPCClient.current_state 的合成 wire，把临时目录 cwd 转为大小写和斜杠变体。原生函数接受绑定并返回 exact/failed；collect_outcomes 返回 unknown/ValueError，批次仍 ended/unknown。

最小修正：两层共用同一规范化规则，保留对真正不同目录的拒绝；增加 Windows 等价 cwd 回归。

## 上传接入边界

已只读亲查 Hub 源码：`D:\传输系统\source-r2\src\drive_exchange_local_hub\__init__.py:3490-3500` 验证 enabled、project_identity、注册 route、帧及 item 上限；3503-3529 建 operation/item；3585-3608 持久记录 DISPATCHING/次数后调用 adapter。`google_drive.py:371-398` 的 adapter 只检查传入 drive identity 并使用传入 parent，不承载前述 Hub 项目/路由/操作约束；upload 没有预生成对象 ID 参数，metadata 没 id。

因此 condition 候选直接导入 GoogleDriveAdapter 并读取既有凭据/route，不能称为复用等价 Hub 通道。建议在隔离 Hub 候选增加版本化接口：预留对象 ID → 同事务绑定 operation/item/source/route → 先持久化再创建 → 重启按原 ID 核对和完整字节读回。condition stdio driver 只作为该 Hub 接口客户端。保留原 project/route/drive 身份、单文件约束和旧 AMBIGUOUS 不自动重放的规则；不得靠新 operation ID、新文件 ID 或名称搜索绕过。此处只给接口位置和必要约束，未验证真实后端行为，也未修改 Hub。

## 本次未裁决的行为

- 真实原目标 owner 的可用性、当前 Desktop 原生 IPC 运行结果：父任务提供证据；本审查未另调用真实 IPC。
- Canonical 与 transient overlay 冲突的最终策略：父任务在初审过程中另发现并正在补充反例；本报告不宣称这部分已修复或独立验证。
- 真实 Drive 上传、响应丢失及重启恢复：尚未接入最终 Hub 接口，不可由当前测试推定。
- 旧生产 STOP/到期/PAUSED、旧业务库/ACK：本审查没有读取或改变旧运行状态，只遵守父任务提供的保留边界。
- 合并、安装、生产启用、真实登录与 Alice 接受：不在本审查授权内。

## Governed Work Report

Collaboration identity: Kelan（本地审查子任务，非 Alice）
Acting role: 独立工程审查；任务路径 `/root/review_condition_native`
Deployment environment and evidence: 当前工具环境 Windows/PowerShell，本地指定工作区；父任务提供本地部署/治理证据，本审查未独立重验。
Task-assignment source, scope and expiry: 父任务的受控审查包，来自本轮 requesting-code-review skill；限定本候选及上传方案源码评估，报告交付时本轮初审结束。
Work surface: 本地子代理工具；代码只读，证据仅写 review-native。
Task class and triggers: C，跨模块状态与上传接口评估。
Workflow state: changes_requested。
Capability gate: 本地源码读取、隔离 Python 与临时 SQLite 可用；没有外部动作或凭据访问。
Kernel source and hash: 未在子任务重验；不得以父任务声明代替子任务独立证据。
Registry path and status: 父任务报告 Active 27/27；子任务未亲验登记。
Canonical repository, remote, pinned commit and integrity: 父任务提供固定 387c98a，本审查未声称独立验证。
Applicable project instructions and conflict status: 用户粘贴内核及父任务边界；D:\Ai通信系统\AGENTS.md 不存在，候选下未检出 AGENTS.md；未发现需要修改性动作才能解决的冲突。
Repository facts: 本次亲读上述源文件；原始哈希见 reproduction.json。未改索引、HEAD、分支或候选工作树。
Actions and material evidence: 独立反例、双连接 ACK 验证、7 项原生采集测试；见本目录脚本和 JSON。
Checks passed: ACK 保留；7 项现有测试；复现脚本完整执行。
Checks failed or skipped: 两项行为反例成立；完整套件/真实 IPC/真实上传/登录未由本审查执行。
Truncation and redactions: 初次合并输出被工具截断，随后使用定位读取补齐有关代码；未复制凭据或私有消息正文。
Assumptions and deviations: 父任务治理与原生产边界作为输入，不冒充独立验证；无候选代码修改。
Known limitations: S1 控制输入子任务，方法为独立代码追踪与合成反例；无 S2 或 Alice 身份主张。
Required Alice review: 仍由父任务保留既有 review_pending 边界。
Required Kelan review: 修正后重新核对受影响内容及回归。
Required Human decision: 本只读初审无需新增批准；真实登录/安装/生产门仍未跨越。
