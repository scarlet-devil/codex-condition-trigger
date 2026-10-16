# 条件触发器三项收尾修复与本机交接

状态：**代码候选已实现，云端回归通过；真实 Windows、原生结果采集及实际上传器验收待柯蓝完成。** 红魔在主讨论窗口授权解决三项建议，沿用 Draft PR #1。Alice 负责本次代码及 S0 自查，未声称独立复审或本机部署完成。

## 当前运行结论

收尾包证明历史上触发器确实自动向原聊天投递并完成过业务交付，也记录了监听中断、原生失败与上传阻塞。它不支持“已经长期稳定、全自动运行”的结论。两天试验已经结束：最后本机检查为监听器正常退出、登录恢复任务停用、相关进程为零，原周期任务 PAUSED。仍有六个版本未研究、两个 Library 原件缺失。这里不重写历史业务账本和 ACK，不恢复或顺延已到期试验。

输入代码基线 `5f782e22eccdc434b26f338725ae7382567bbc79`；发布前保留独立自动化窗口的 `eac0ab297b0002c0d4f05d7e3ce6b9725fa773b3` 接管记录。治理固定版本 `rule-of-rules@387c98a45b8fcc4409647c5bdc3363d614542859`，Class C / enhanced。报告和 ZIP 仍见 [收尾报告](https://drive.google.com/file/d/1P-6R7yu0gstc1XoiwY8b0S423pGVWQ5y/view)、[证据包](https://drive.google.com/file/d/1nhaXlQ__mtQvkUtPfMagUpYqZB52Id_9/view)、[交付回执](https://drive.google.com/file/d/1SVMOvMtS5d8Oh5Yxzh6S7g_E9LogJSuW/view)。

## 1. 监听状态可见

`status` 增加 watcher 进度、最后扫描/调度检查、停止或失败原因、未交付批次和输入版本数，以及上传任务列表。`watcher-progress.json` 由实际工作循环写入：等待时最多十秒更新一次，开始/完成扫描和调度检查时立即更新。三十秒以上未更新显示 stale；未来时间戳显示 clock_uncertain。二者均要求检查。长扫描或 IPC 阻塞会留下最后阶段，不由另一个心跳线程掩盖。

recent 只证明近期取得进展，**不证明此刻进程仍存活**；外部强杀可能留下 running/stale，停止原因此时未知。`latest-worker.json` 在正常/异常退出时更新，不再永久保留启动快照；更新发生在释放 worker 锁前，重复启动不能覆盖当前实例。Ctrl-C 记为 interrupted 且不自动重启。

```bash
python trigger.py --config local-production.json status
```

该命令不启动 watcher/模型。固定期限和 STOP 的既有约束继续适用。状态输出可能包含本地路径、聊天绑定及文件 ID，只在本机保留完整输出，公开证据需脱敏。

## 2. 结束、执行结果、业务交付分开

| 证据 | 生命周期/调度状态 | execution_outcome | 业务交付 |
| --- | --- | --- | --- |
| Desktop rollout 的 task_complete | ended | unknown | 未核验 |
| 关联回合的 task_failed / turn_aborted | failed | failed / interrupted | 未核验 |
| JSONL 关联回合明确 completed | completed | succeeded | 未核验 |
| 精确原生回合结果回执 | ended 或 failed | 明确结果 | 未核验 |
| 既有人工核验 ACK | delivered | 保留原结果 | caller_verified |

旧库增加可空语义为 unknown 的新结果列，保留原 state/detail/ACK。旧 Desktop completed 显示 lifecycle=ended、outcome=unknown；不追认历史成功。`ended` 和失败仍阻塞下一批，不能触发重发或自动交付。窗口清理仍需交付 ACK、关联结束事件及原有身份/监督检查；单独结束不能关闭窗口。

原生 `systemError` 的完整、稳定、按 turn 关联的数据接口尚未在本仓库确认，因此**没有新增猜测字段的自动采集器**。本版提供明确的结果登记入口，由调用者核验原生回合后提交：

```json
{
  "schema": 1,
  "batch_id": "EXACT_BATCH_ID",
  "turn_id": "EXACT_NATIVE_TURN_ID",
  "manifest_sha256": "SHA256_OF_ORIGINAL_MANIFEST_INCLUDING_FINAL_NEWLINE",
  "source": "caller_verified_native_turn",
  "native_turn_status": "failed",
  "native_runtime_status": "systemError"
}
```

```bash
python trigger.py --config local-production.json record-outcome BATCH_ID --evidence /absolute/path/native-outcome.json
```

支持 completed、failed、interrupted；线程级 systemError 不能单独绑定任意批次。回执登记保存证据路径/哈希和调用者声明，不冒充程序已独立验证原生平台。冲突回执拒绝覆盖；晚到的轮询不能覆写明确结果；已 delivered 的原记录不重写。此命令不补发模型任务、不 ACK。接入实际采集器前，unknown 必须保留并交本机核对。

## 3. 冻结成果的上传续传

产物生成后，先冻结本地文件；单文件上限 20 MiB、每任务最多 32 件。描述绑定原输入清单哈希、目标 parent ID、文件名、长度和 SHA-256，派生稳定 job/key，字节另存至 state 下。源报告后来改变不替换旧任务的冻结版本。

```bash
python trigger.py --config local-production.json delivery-stage BATCH_ID --parent-id EXACT_FOLDER_ID /absolute/path/report.md /absolute/path/evidence.zip
python trigger.py --config local-production.json delivery-resume JOB_ID
```

stage 只写本地状态。resume 是操作者明确发起的一次上传尝试，使用配置中的 `delivery_command` argv，默认无后端。**仓库没有真实 Hub/Drive 上传器，本轮没有实际上传。** 后端必须沿用本机已有授权、凭证及审批机制；此协议不绕开审批，也不能通过模型提示词重做研究。

resume 可在试验停止后完成冻结成果归档，因为它与 watcher/模型运行分离。它不清除 STOP、不改期限、不启动 watcher、不执行 dispatch。后台 watcher 不会自动调用它。本机需按现有上传授权调用；配置不存在时明确报错。

所有后端调用使用 JSON stdin/stdout、shell=false，默认单次 60 秒、允许范围 (0,120]。每次重试先 lookup；确认安全创建后，先持久写 upload_uncertain，再上传。超时、审批拒绝、未知响应均保留待核对状态。已核验成员可跳过，只处理剩余成员。即使全部 uploaded_verified，也不自动写业务 ACK。

| action | 请求字段（均含 schema=1） | 响应要求 |
| --- | --- | --- |
| lookup | key、batch_id、manifest_sha256、parent_id、name、sha256、size、冻结 path | 回显 key；唯一匹配 found + file_id，或 absent + safe_to_create=true；其余 unknown |
| upload | 同上，稳定 key 不变 | 回显 key，found + file_id；不完整回执留待 lookup |
| readback | 同上，另含准确 file_id | 回显 key、found、file_id、parent_id、name、完整 content_base64 |

**safe_to_create 的门槛：** 后端必须证明不会重复创建，例如使用远端保留的确定性 ID/幂等键，且排除仍在进行的同键请求。仅按文件名搜索为空、最终一致性列表暂时为空，不能返回 true；无法证明就返回 unknown 等人工核对。后端应保留原生文件 ID 和调用证据，并据真实远端读取返回字节，不能把本地源文件冒作回读。

核心解码远端字节，独立计算长度和 SHA-256，并检查准确文件 ID、父目录及文件名。目标不符、字节不符、冻结文件被改动均不得核验。并发续传由单独 delivery 锁串行，不占 watcher 锁。收到上传成功但回执丢失时，下次先查到旧对象再回读，不重新上传。

## 验证与柯蓝交接

云端 Linux / Python 3.12.14、watchdog 6.0.0：`python -m unittest discover -s tests -q`，170 项、169 通过、1 项 Windows overlapped-I/O 跳过，零失败。十六项新增回归含失联进度、退出快照、重复启动、Ctrl-C、结束误判、回执串批/并发覆盖、历史 ACK 保留、上传失回执后重启、冻结篡改、未知查重、错误父目录与字节、重复 stage。首次测试缺依赖及旧测试夹具重复收集的问题已记录并修正。详见 [验证记录](../evidence/alice-three-fixes-validation-20261011.json)。这只是 S0 自查和合成验证。

柯蓝在同一 Draft 接续以下验收并报告准确 commit 和证据；当前交接不等于已经收到或已执行：

1. 在隔离、固定期限的 dry 配置核对 Windows 进度、正常停止、强杀后 stale、重复启动及登录恢复；安排真实登录条件验证，不能用 Linux 重启子进程代替。保持旧试验任务停用，不把本次修复当成生产续期。
2. 从实际原生接口按准确 turn 采集成功/失败，使用已存失败材料复现 systemError 与 task_complete 同时存在的情况；无法确认字段时维持 unknown。验证新状态不被外围脚本误当业务成功，复制旧库测试迁移。
3. 为已有授权上传流程接入该窄协议，在合成文件上验证“远端创建成功、响应丢失、进程重启、精确查回、完整回读”；证明安全创建条件。未证明时停在 unknown，不能通过反复模型调用补救。

验收回执须分别说明三项通过/未通过、冻结与远端字节哈希、原账本/ACK 是否保持；任何真实上线、长期运行或更改窗口监督范围另有其授权边界。本次不合并、不 Ready，不扩大原最长 600 秒监督开关窗权限。
