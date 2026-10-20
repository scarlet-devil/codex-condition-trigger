# Hub 最小安装与真实上传恢复验收

**已安装并完成本次真实合成文件验收；真实 Windows 登录尚未执行，整体仍待 Alice 复核。**
Human 于本轮明确批准最小 Hub 安装和真实验收；安装前方案、文件、审查和回退范围见
[原候选回执](KELAN_INTEGRATION_RECEIPT_20261016.md)。本记录更新其中安装前的 pending 状态。

## 实际安装

- 安装前没有发现服务进程，随后成功取得原命名管道 first-instance 独占句柄，确认原入口未运行。
  因此没有终止任何旧进程；不能把本次记为“停止了正常运行的旧 Hub”。
- 原72项材料摘要全部通过。先保全原源码、摘要和 SQLite 一致备份，再覆盖已批准的3份运行文件
  与对应摘要清单；新73项文件摘要通过，原 OAuth/拓扑/来源配置哈希保持。
- 沿原 Python、状态目录和现有凭据静默启动。主启动器 PID50592、实际服务子进程PID49628
  的可执行路径、父子关系与 `drive_exchange_local_hub.cli serve` 命令已读回。
- 本次没有新增 Hub 自启动机制；当前会话的启动事实不等于注销后自动恢复。
  登录测试本身为独立 dry，不依赖 Hub；登录后另核对 Hub 实例状态。

## 真实端到端结果

只使用原 `new-skill-merge / standard` 路由中的一个新合成文件：
[CONDITION_HUB_CANARY_20261016.txt](https://drive.google.com/file/d/1v1auwzETb18D-MggC4KvTjo1Pg0TZCUm/view?usp=drivesdk)。

| 项目 | 实际证据 |
|---|---|
| 内容 | 128字节；只说明合成验收用途，不含业务或个人数据 |
| SHA-256 | `d8bf98ac97ee845e975071033b74e3943ef0eb417d867afcee3518f76bf3f372` |
| 首次上传 | standalone outbox客户端 → 正式 Hub → 真实 Drive |
| 失响应注入 | Hub已返回found后，测试客户端exit23，阻止该回执交给outbox |
| 保留状态 | outbox为upload_uncertain；Hub保留预生成ID及不可变请求摘要 |
| 恢复 | 新客户端先lookup同ID，再完整readback，结果uploaded_verified |
| 上传尝试 | Hub新表1条、upload_attempts=1、state=verified；未更换ID重建 |
| 目标/共享 | 独立Drive连接器metadata确认准确原父级、128字节、shared=false、仅owner权限 |
| 原状态保持 | 原11张数据库表的行数和完整逐行摘要不变；新表单独保存本次任务 |

这里证明真实上传以及客户端失响应后的恢复；没有故意中断真实网络或杀正式 Hub。
服务写对象后被终止的恢复另有真实 Windows 管道/子进程测试，其远端为隔离合成磁盘，
两类证据不混为同一次实测。旧成果上传0、模型派发0、业务ACK0、人工凭据配置/route变更0。
沿用原登录；没有审计或声称访问令牌未由现有机制自动刷新。

## 登录验收接续

准备独立 `Codex-ConditionTrigger-DryAcceptance-20261016` 登录任务，采用固定15分钟触发窗口、
最长5分钟运行、隐藏pythonw、独立输入与状态目录，只扫描一个合成文件。
没有模型、上传或业务ACK，也不恢复到期的原生产试验。原STOP/期限/PAUSED继续保留。

真实登录要由Human保存工作后注销Windows账户、再重新登录；锁屏、只关闭Codex或手动运行任务
都不等价。实际注册时间、截止时间和登录执行回执单独记录；本段不预称已经触发。
系统TaskScheduler Operational日志目前关闭，本轮不改变全局日志设置。
后续将结合Human实际动作确认、前后logon SID变化、唯一AtLogOn任务及worker源码/配置摘要核验；
不能宣称获得了没有记录的任务触发事件。若未在固定窗口内登录，不自动续期或改为生产启动。

原生采集增量已实现并通过本机工程测试和独立复核；真实已加载chat的准确历史turn投影已验证。
原生产目标owner当前未加载，仍保留这一限制，不把当前chat的原生结果冒充原目标结果。

## 归属、保全与治理

本地Kelan负责实际安装与测试；两项工程审查为本地独立子任务S1，不是Alice/S2验收。
仓库仍Draft/open/unmerged；原PR正文保持。共用WORK_LOG和CURRENT_STATE按增量续写。
[脱敏直接证据摘要](../evidence/kelan-hub-live-acceptance-20261016.json)包含准确前后文件摘要、
安装状态和本次远端回读结果。私有源码/数据库备份、完整进程/错误日志、故意丢弃的原回执均本地保留。
未删除合成云端对象，也未重传历史报告。

Governed Work Report增量：Collaboration identity Kelan；Acting role本地安装/真实接口验收；
Deployment environment本地Windows，沿前报告已验证CODEX_HOME/Active27；Task class D/constitutional，
具体授权为Human“批准最小Hub安装和真实验收”；Scope仅冻结三文件与摘要、原入口、一个新合成文件。
Capability gate为精确源哈希/全部原清单/独占原管道/备份、原注册与route门；
Workflow state为installed_live_canary_verified / review_pending；原11表与受保护配置一致；
无自动审批拒绝、无原始秘密外发。Required Alice review为整个接入及新增真实证据；
Required Human action为后续真实Windows登录；原生产启用仍未批准。


实际注册已完成，截止 2026-10-16 00:49:42 Asia/Shanghai；仍未执行真实登录。参见[注册回执](../evidence/kelan-logon-arm-20261016.json)。
