# 真实重启登录验收回执 — 2026-10-16

本机柯蓝已核对 Human 真实重启后的独立 dry 登录链。Windows 启动时间为00:57:39.500，AtLogOn任务于00:57:58自动启动，worker于00:58:08.570进入监听。前后logon SID不同，源码pins与配置SHA完全一致；1个合成文件自动形成1个ready批次，没有模型派发、上传或业务ACK。01:00:06按既定收尾写独立STOP并禁用该任务，worker正常退出0，任务最终Disabled/LastTaskResult0，无残留worker。运行118.282秒，26项直接证据核对通过。全部时间为Asia/Shanghai，机器记录保留UTC/明确偏移。

Human曾错过00:49:42窗口，明确要求延至01:05；只改同一任务EndBoundary与内部期限，旧窗口未触发，原回执保留。这次触发发生在调整后的窗口内，没有手动Start-ScheduledTask或自动注销。

重启后原共用Hub未运行。已确认无标准serve进程、取得原first-instance管道，核对73项材料及4个安装目标摘要，再沿原Python/source-r2/state-local_system静默恢复单实例。原项目new-skill-merge/standard经真实命名管道只读返回TOPOLOGY_ACTIVE。没有重装文件、添加Hub自启动或重传已通过的Drive canary。

这关闭的是独立dry真实登录验收缺口。原生采集实现/工程回归、真实Drive单文件与失响应恢复证据沿用此前回执；原生产目标owner未加载的限制仍保留，原生产STOP/到期/PAUSED没有恢复。本轮不声明原目标业务执行、长期无人值守或永久启用通过。

证据：[脱敏检查及摘要](../evidence/kelan-real-logon-acceptance-20261016.json)。完整本地原件在`D:/Ai通信系统/.recovery/20261015/condition-integration/logon-dry/acceptance-20261016`及`logon-dry/state/worker-runs/20261015T165808Z-5f0419638f3f`。登录SID、用户路径、任务私有XML不上传。

TaskScheduler Operational日志原本关闭且未改；未声称事件119。初次沙箱Verify显示Not armed，宿主账户只读视图实际为Running，已保存后者及worker相符证据；该沙箱结果不解释为任务丢失。一次CIM对象JSON展开深度截断及过宽文件搜索截断已由选择具体字段/准确文件重新读取补齐；缺失的__main__.py/pyproject路径探查未执行任何Hub启动，实际使用已读取的cli入口。

[Governed Work Report]
Collaboration identity: Kelan
Acting role: Local engineering acceptance executor
Deployment environment and evidence: Local Windows Codex Desktop; native boot/task/process/worker evidence.
Task-assignment source, scope and expiry: Human批准最小Hub安装及真实验收；明确延至01:05，并确认重启完成。独立dry任务已关闭，原生产授权未续期。
Work surface: Existing local chat, PowerShell, Python, existing GitHub Draft #1.
Task class and triggers: Inherited Class D constitutional installation/host acceptance scope; all specific actions already authorized.
Workflow state: Bounded real-login acceptance passed; overall implementation_ready / Alice review_pending.
Capability gate: Host task/process visibility and original named pipe verified; existing approved same-Draft public summary destination.
Kernel source and hash: Prior verified codex-home/AGENTS.md at387c98a45b8fcc4409647c5bdc3363d614542859; SHA256 e349ac44fda1c8011dd69e4a20295660cc645e3afbe492b06acd0f957d2dd414. No governance change or repeated full check this increment.
Registry path and status: D:/codex/KELAN_CONSTITUTION_INSTALL.json; prior installed/Active27/27 at2026-10-15T15:21:17Z.
Canonical repository, remote, pinned commit and integrity: D:/codex/governance/rule-of-rules; scarlet-devil/rule-of-rules; same387c98a pin; prior verified status reused.
Applicable project instructions and conflict status: User local governance kernel and scoped production STOP; no new conflict identified.
Repository facts: Existing isolated candidate branch, Draft #1; no runtime-source edits in this increment, no merge/Ready.
Actions and material evidence: Real login readback, exact dry STOP/disable, original Hub restart/status, public report and shared-log increment.
Checks passed: 26 direct assertions, worker/task exit0, installed73 manifest hashes, original route TOPOLOGY_ACTIVE.
Checks failed or skipped: No SDK/model/upload regression repeated; native task eventlog unavailable; original production target acceptance not claimed.
Truncation and redactions: Discovery/CIM serialization truncations described above; all decisive records fully read. No credentials/private identity upload.
Assumptions and deviations: Human reboot plus changed logon SID and native boot/task times substantiate real new login; no simulated login substituted.
Known limitations: Independentdry scope; no production activation, same-session hard-kill relaunch or long-term reliability claim.
Required Alice review: Review this bounded acceptance and prior integration package; remains pending.
Required Kelan review: Direct evidence review complete; no new runtime implementation.
Required Human decision: None for completed scope; production enablement remains separate.
