# 给爱丽丝：三项修复的 Windows 有界验收与剩余接入项

日期：2026-10-12。执行者：本地柯蓝。状态：**Windows 路径问题已修复并通过本轮检查；整体仍 review_pending，生产继续停止。外部同步尚未成功。**

本轮接手 [Draft PR #1](https://github.com/scarlet-devil/codex-condition-trigger/pull/1) 的固定版本 `03e66a37ceabcc66d5c3c5f36120fc6cdba364f5`，依据 [爱丽丝交接](https://github.com/scarlet-devil/codex-condition-trigger/blob/03e66a37ceabcc66d5c3c5f36120fc6cdba364f5/docs/ALICE_TRIGGER_FOLLOWUP_20261011.md)。红魔随后明确选择“稍后安排，先提交本轮结果”，因此真实注销/登录试验未启动。没有恢复原生产期限、监听、自启、原定时器或模型任务。

## 一、可接受与待验收范围

| 项目 | 本轮证据 | 结论 |
|---|---|---|
| Windows 回归 | 原版 170 项：164 通过、5 错误、1 跳过；修订版 172 项：171 通过、1 跳过、零错误/失败 | 路径修复 implementation_ready |
| 真实 Windows dry worker | 9 项检查通过；实际文件写入、扫描、子进程、重复启动、强制退出、30 秒失联提示、重新启动、STOP 退出 | 这一有界子进程链通过 |
| 登录恢复 | 独立 dry 验证脚本已准备、PowerShell 语法检查通过；15 分钟截止、单次 worker 最长 5 分钟、没有手工 Start-ScheduledTask；未注册任务 | 红魔选择稍后安排；不能以子进程重启替代登录实测 |
| 旧库迁移 | 只读备份至隔离副本；7 批旧字段/meta 不变，4 个 delivered ACK 不变，新结果列 unknown | 迁移检查通过，原库未写 |
| 原生结果 | 新只读查询返回准确回合 completed/error=null、线程 notLoaded；该回合不是任何原批次绑定 turn | 未套用到旧批次；独立 watcher 采集器尚未接入 |
| 上传续传 | 合成后端回归通过；真实 Drive 两次只读请求失败、上传调用 0；没有真实幂等创建证明 | 不宣布真实上传恢复通过 |

上述 172 项是实际收集总数，不写作“172 项全部通过”。Windows 跳过项是需要 symlink 权限的测试；云端此前跳过的 Windows overlapped-I/O 定点测试，本轮运行通过。两端 skip 不是同一项。

## 二、本轮发现并修复的 Windows 问题

`delivery_outbox.stage()` 将 64 位 job 哈希放入父目录，又在 blob 文件名中重复 64 位内容哈希。实际验收目录中，原子写临时路径达到 261 字符时，即便父目录真实存在，Windows 写入仍返回 FileNotFoundError；同父目录短文件名 196 字符写入成功。原版五个 OutboxTests 全部因此在冻结阶段出错。

先新增可跨平台复现 Windows 260 字符限制的回归，观察到原代码以 297 字符临时路径失败。随后将新 blob 文件名改为序号加 `.blob`。job 标识、描述、完整内容 SHA-256、长度、冻结字节核验及远端匹配要求保持原样。原任务保存的 blob 路径按原值读取，补充回归验证旧文件仍可续传。

实际测试代码提交：`7203734d347d37ca6615b55b91cd3903d9efb5f9`，父提交为上述 `03e66a3`。修改仅涉及 `delivery_outbox.py` 和两项新回归。本地分支 `codex/windows-three-fixes-acceptance-20261012`，没有修改旧运行 checkout 或安装候选。补丁和改动文件哈希随包提供。

这是去除已观察到的冗余路径增长，不声称任意深度 state_dir 都能兼容旧 Windows 路径限制；本轮没有改变操作系统长路径策略。

## 三、监听状态实测

隔离目录使用独立 input/state、全零合成 thread 标识和固定 150 秒截止，worker 强制 `--dry`。实际合成文件产生一个 ready 批次，submission/turn 均为空。重复 launcher 正常退出，但不能覆盖仍在运行实例的 latest-worker 回执。

强制终止本次创建的 launcher 后，真实工作进度停在原值；30.004 秒后报告 running/stale、attention_required=true、process_liveness=not_proven。重新启动同一隔离配置，新的 run_id 出现，旧 ready 批次保持不变。写入该隔离状态的 STOP 后，worker exit 0，progress 标明 stopped/STOP，latest-worker 保存终止快照。强制退出者没有伪造 exit 回执；重复实例与正常停止实例各自保留记录。

首次监督脚本误用 launcher PID 与 Python worker PID 相等作为重启条件，实际这两个 PID 不同，因此脚本等待失败；这不能归为候选源码故障。保留该轮证据，改为关联真实 run_id 后在全新隔离目录重跑通过。最终原生进程扫描为相关 worker 0，原生产和新测试任务对象均未登记；原 STOP/到期锁存在，原生周期任务仍 PAUSED。

## 四、原生失败与旧账本

历史保留的原生查询记录确实包含 `systemError` 和精确 `failed` 回合，该 turn 能唯一匹配原生产批次。这个批次后来经授权续接并已有业务交付 ACK，因此不能用先前失败证据回写成失败。隔离副本验证 `record-outcome` 拒绝改写已 delivered 行，4 个历史 ACK 保持完整。

本轮 `wait_threads(timeoutMs=0)` 只读返回最新回合 completed/error=null，但它是后续恢复回合，不是原账本中的任一准确 turn。我们没有把“最近完成”解释为任意待交付批次成功，也没有把线程 notLoaded 解释成需要开窗。

现有工具可以由当前 agent 取得结构化原生快照；仓库的 standalone worker 尚无调用这个工具的受支持命令接口。仓库 IPC `current_state()` 仍只投影 owner、revision、线程空闲状态，不返回已核对的逐 turn 原生结果。不能把本轮工具读取说成已实现自动采集器。后续接入必须保留 turn/batch/manifest 绑定，并验证过期、串批、失败与成功冲突；无法确认时保持 unknown。

## 五、真实上传后端仍缺的条件

核心 `delivery-stage/resume` 能冻结产物，并在恢复时先 lookup，再核远端 ID、parent、name 和完整字节。合成测试覆盖远端写成功但回复丢失、重启后查回、跳过已核验成员、冻结篡改、错误父级和错误字节。这些测试没有使用真实 Drive 后端。

当前可用 Drive 上传工具只提供 file_uri、文件名、MIME 和父目录参数，没有预留文件 ID、创建幂等键或查询同键在途操作的接口。因此不能把“文件名查不到”直接转换成 safe_to_create=true；也不从 Codex 私有凭据、缓存或会话提取认证材料补齐后端。

本轮 Drive 父目录读取与精确查重共两次均失败于 MCP transport send，尚未发起上传。GitHub head 刷新也发生相同连接器发送失败；备用 `git ls-remote` 在自动审批网络断流时明确未执行。这是传输/审批服务故障，非不安全判定、非缺少红魔上传批准。没有绕过检查或盲目重传，远端当前状态仍不能由旧快照证明。

建议爱丽丝分别裁定：接受本轮路径修复及有界 Windows 证据；登录试验按红魔选择延后；原生采集器先确定可维护的 standalone 入口；实际上传器必须由既有授权后端提供持久幂等/在途对账能力。若先沿用 agent 手工查重上传，应明确称为人工辅助交付，不能冒充 automatic delivery-resume 接入完成。

## 六、证据、交付与限制

附件包含：本报告、脱敏验证摘要、原版失败明细、修订版测试输出、先红后绿回归证据、路径探针及代码补丁。manifest 记录每件长度/SHA-256，ZIP 校验 CRC 和全部成员。完整原生回合材料、实际聊天/批次标识、Windows 用户路径、任务 XML 和治理登记留在本机；不上传会话正文、凭据、身份内核或不必要个人信息。

本地测试有三处夹具/环境修正：默认 sandbox TEMP 无访问权限，改用本验收目录；launcher PID 与 worker PID 不同，改用 run_id；旧库复制首次未走 load_config 规范化被绑定门拒绝，改用正常加载器后通过。原始失败未删除，未将它们列为源码产品缺陷。较长工具回显有截断；完整测试输出落盘，本报告使用已检查的完整结果。

预定交付仍为既有 new-skill-merge / 40_REPORTS 和同一 Draft PR。当前本地 prepared_pending_external_delivery；只有远端写入及内容回读核验后才能更新为 delivered。爱丽丝本轮 review_pending。无 merge、Ready、生产激活、旧批次 ACK 或监控续期。

## Governed Work Report

- Collaboration identity: Kelan；Acting role: 本地有界验收、修复与材料交接。
- Deployment environment: local Windows / 实际 CODEX_HOME 本地安装核验；不据此声称 developer 全文装配效力。
- Task assignment: 红魔转交三项修复并要求本机接续；随后明确“稍后安排，先提交本轮结果”。范围到本轮冻结交接；原两天期限不延长。
- Work surface: Codex Desktop + PowerShell + 隔离 Git checkout；Class C / enhanced（状态与恢复接口），既有指定 Drive/同 Draft 外部提交依已批准目的地执行 constitutional 边界。
- Registry: installed；规范 scarlet-devil/rule-of-rules，固定 387c98a45b8fcc4409647c5bdc3363d614542859。2026-10-12T00:46:55.536505Z 完整性 17/17 通过，必需 blob、干净工作树及来源/安装内核一致。
- Kernel SHA-256: e349ac44fda1c8011dd69e4a20295660cc645e3afbe492b06acd0f957d2dd414。没有上传身份/登记正文。
- Applicable project instructions: 已核对当前项目与隔离目录；无新增适用 AGENTS 冲突。原 Hook scope/约束/暂停边界保留，源变更需语义审读后显式核对。
- Capability gate: 本地读写、隔离测试可用；Drive/GitHub MCP 发送失败，备用只读 Git 受审批服务断流阻止。未访问凭据，外部动作未确认成功。
- Checks passed: 修订版 171 tests、9 Windows dry 检查、7 批复制迁移与历史 ACK 保护、合成续传回归、脚本语法。
- Checks failed/skipped: 原版 5 Windows 冻结错误；1 symlink 测试跳过；真实登录按 Human 决定延后，原生自动采集及真实幂等上传未验收。
- Review: 本轮方法为本地实测和 S0 自查；不宣称已得到 Alice 独立接受。Required Alice review: 本修复及剩余接口决策。Required Human decision: 日后安排登录窗口；当前无待批准生产启动。
