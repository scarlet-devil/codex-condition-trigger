# 条件触发器重启恢复与待材料阻塞修复报告

接收者：爱丽丝。执行者：本地柯蓝。日期：2026-10-10。状态：修复已准备并用于原限时试验；独立云端复审 `review_pending`，PR 保持 Draft。

## 故障与原因

红魔报告小点投送新文件后未触发，随后明确要求修复重启失效、补齐日志和证据并恢复监听。原机于北京时间14:00:09重启；14:35定向查询未发现原监听进程，原部署只有临时进程，没有登录恢复入口。原 stdout 最后记录于10月8日23:52，stderr为空，也没有退出回执。因此只能确认当时监听缺失、重启后未恢复，不能确定原进程最初退出的时刻和原因。试验到10月10日21:11:50才到期，本次缺失不是到期停止。

另有独立的逻辑阻塞：两个早期批次已交付，第三批只有开工材料，模型回合已经完成但业务仍缺材料。旧调度要求前批交付才发送后批，导致补充文件也无法推进。诊断扫描发现14个未入运行账本的内容版本，共105197字节，覆盖后补审计、当日归档、备忘与索引。发现文件不等于其研究或业务交付完成。

## 本次修改

1. 新增 `trial_worker.py` 与当前用户登录任务安装脚本。使用隐藏的 pythonw、Interactive/Limited 权限、IgnoreNew和原SQLite锁；继续绑定原目录、原聊天和原截止时间。每次启动、退出、配置及六个运行源码哈希分别留据。固定截止不因重启或重试延长。
2. 记录到的 worker 异常最多重试三次，每次等待30秒；每次重试保持最初单调时钟预算，并检查STOP、到期锁和准确绑定。配置检查后直接传入本次已检查配置，避免检查与执行不一致。到期拒绝新工作；不取消已经发送的回合。
3. 新增显式 `defer-materials` 请求，要求准确批次、关联turn、实际manifest字节SHA及缺项理由，且 `delivery_verified=false`。只有真实完成、无程序持有或归属不明窗口时才进入 `waiting_materials`。原输入、回合和缺项继续保存；没有新字节不重发。
4. 后续新批次附上待续manifest引用，原任务按覆盖范围续接，只有实际Drive交付核验后才逐批ACK。旧ACK仍终态；过期轮询不能覆盖已交付或待材料状态。未显式申请待材料的completed、未知发送和未清理窗口继续阻塞。

以上只恢复原限时试验。原周期任务仍PAUSED；没有窗口backend、没有开关窗口、没有额外模型任务或人工dispatch来模拟自动触发。

## 验证及失败记录

最终回归154项：153通过、1项Windows符号链接权限跳过，失败和错误均为0。初始新增检查12项中11项失败，保留“未申请待材料仍阻塞”的通过项；新增有限重试检查先2项失败，再转绿。测试使用隔离合成目录，不执行小点投送代码。

本地受控S1/M1复核找到并关闭两项问题：manifest实际文件含末尾换行，回执必须按原字节哈希；重试若重新生成Store预算，会在UTC回拨时延长授权。同一时钟反例修前预算由110变211且超原期限仍未暂停；修后两个worker预算均110，mono111时暂停并生成到期锁。反例已纳入回归。此本地复核不等于Alice验收。

Windows原生测试得到两个不同结果，不能合并成笼统“自动重启通过”：

| 场景 | 实测结果 |
| --- | --- |
| Task Scheduler RestartOnFailure，强制终止测试子进程 | 未观察到自动重启；保留失败证据 |
| Task Scheduler RestartOnFailure，进程明确exit1后修正合成条件 | 超过两分钟仍未重启；不再依赖此设置 |
| 新有界入口，仅启动原生任务一次，前两次缺合成目录报错，随后提供同一路径 | 第三次自动恢复，未再次Start任务、未改配置、无IPC |
| 上一小试自然到期 | 07:01:55Z写STOP/到期回执，退出0，计划任务回到Ready；测试任务已移除 |

原生第三次试验验证的是最终预算继承修正之前的重试入口；最后的预算修正另由相同时钟反例及最终回归验证。真实恢复入口的六源码哈希另有启动回执，不把不同版本证据混称同版本全链验收。

Windows官方接口依据：[当前用户登录触发器](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasktrigger)、[计划任务设置](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset)、[运行主体](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtaskprincipal)。接口存在不代替本机实测。

## 真实恢复观察

北京时间15:06:37，唯一原试验监听通过已登记的原生任务恢复，继续使用同一账本。启动前只读IPC确认准确目标owner空闲；安装签名有效，Desktop版本26.1007.2314.0。六个加载源码哈希与本地文件逐项一致。旧两个已交付行全字段不变；旧缺材料批次进入waiting_materials，不是delivered。

07:08:52Z只读观察：14个新版本、105197字节已由监听自动形成一个新批次并获原聊天IPC接受，关联turn存在；07:09原生聊天状态为inProgress且已开始核对新批与旧待续材料。人工dispatch为0，窗口动作为0，修复方业务ACK为0。当前仍在处理，不能称报告已交付。详细阶段见配套 `evidence/recovery-repair-20261010.json` 的有时间戳观察；不同阶段分别记录。调用成功不能替代真实报告回读和业务ACK。

## 尚未验收的范围

- 已注册并回读登录触发器，本轮没有重启或注销用户电脑，真实冷启动到登录恢复链尚待观察。
- 登录前不会运行；本机会话、Desktop及准确owner仍须可用。owner缺失时等待，不能无监督开窗。
- 同次登录期间外部强杀整个入口进程，没有常驻守护自动拉起；记录到的worker异常有有限重试，下次登录有恢复入口。没有为此试验引入永久服务或延长授权。
- 原进程最初退出原因仍未知。原生RestartOnFailure未生效的底层原因未确定，本次不据此猜测Windows策略。
- 本次试验依旧在2026-10-10T13:11:50Z截止，未获永久启用、合并或无人值守窗口验收。

## Governed Work Report

- Collaboration identity / acting role：Kelan，本地工程实现和证据整理；Alice为独立复审接收者。
- Deployment / work surface：本地Windows Codex、解析后的本地CODEX_HOME；原生进程、计划任务和IPC回读取证。
- Task assignment / expiry：红魔当前明确修复、恢复及交接要求；原两天期限不顺延。既有Drive上传及同Draft公开同步批准继续适用；当前请求仅增加该试验的登录恢复。
- Class/profile：C状态接口修改；D限定本机激活与已批准公开提交，constitutional。无规范、身份、凭据或全局技能修改。
- Registry / integrity：installed schema1.1；固定规范387c98a45b8fcc4409647c5bdc3363d614542859，本机登记、规范仓库和内核检查保持一致；不以此声称developer装配验收。完整本机路径、内核哈希和17项核验只保存在私有证据。
- Project instructions / capability：未发现适用项目指令冲突。复用现有隔离checkout、原状态和私有配置；GitHub同Draft及Drive准确父目录在各次外部动作前核验。
- Repository / review：基于bb2abe0dfedeb0eb446a4c684ca96e1a9b170c20，保留Alice既有日志；本地受控复核S1/M1，最终云端审查review_pending。
- Evidence / privacy：公开包仅源码、合成测试、脱敏汇总和哈希；准确聊天ID、SID、会话、配置原文与私人材料路径不公开。部分早期工具聚合输出截断，相关最新条目已定向补读；测试首次Temp ACL与集合构造失败记录保留，不冒充产品失败。
- Human decision：本次恢复不需要重复批准；原到期后续期或永久运行须新决定。Alice需要复审状态释放与恢复边界，当前未声称她接受。

## 恢复后的独立平台阻塞（07:26Z核对）

原聊天真实turn已接受并读取材料，但07:20:09Z以failed结束：remote compact任务stream disconnected/network error/response body decoding失败。原生任务状态为systemError，运行约680.768秒。07:24:32Z监听进程仍在，新增三个ready批次（2/7/6版本）；原14版本批次未交付、未ACK。原生状态failed与历史task_complete导致的本地completed必须区别，本地completed只证明历史终止事件，不证明模型成功或交付。本次未以缺材料接口释放这个网络失败批次，也没有绕开失败回合重发。

Drive报告上传同样受服务故障阻断：首次自动审批超时；一次上传在OpenAI文件请求阶段网络失败；再次自动审批stream disconnected，工具明确本次动作未执行。中间一次精确查重为空；无Drive文件ID或成功上传回执，故Drive交付状态pending_upload。没有绕过审批，未将服务失败解释为内容违规或缺少Human批准。原始授权仍在，但网络/审批服务恢复前无法核验外部交付。

修复源码、报告、测试与脱敏证据已提交同一GitHub Draft；a631736远端头部确认，脱敏证据按Git LF规范及blob身份回读一致。直接比较checkout CRLF与Git LF首次不一致已单独查明，并保留原件与Git字节哈希两种口径，未把规范化比较冒称原始字节相等。补充日志提交包含上述新失败；供Alice判断已修复范围与尚未恢复的业务链。

当前可以确认“原监听已恢复并自动投递”，不能确认“全链业务已正常交付”。固定期限、已交付基线和失败/排队批次继续保留；不因网络失败无界重试、开启新窗口或续期。
