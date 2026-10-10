# 本机接入与交付回执

> 本文描述 `886755e` 的现有 JSONL/queue 实现。2026-10-03 已选择 [独立聊天适配器与 Desktop IPC 小试](IPC_ADAPTER_TRIAL_20261003.md) 作为下一步；新后端尚未实现/验收，不可把 IPC start-turn 直接当成本文的 queue/add。现有安全状态与业务 ACK 边界继续保留。

## 配置真实目标

从本机既有项目记录核对准确 thread UUID 和 cwd。示例配置全部使用虚构路径和全零 UUID，不含任何可用会话绑定。

`transport_command` 必须是连接已验证原宿主的 JSONL 代理 argv。按实际安装版本的帮助及支持接口确定命令；本项目没有验证过可普遍用于 Windows Desktop 的命令。不要把一个新启动的 app-server 填入此处当作原宿主。

只读探针：

```bash
python trigger.py --config local-production.json probe
```

它读取 thread、cwd 和队列，输出摘要。它不会提交消息，也不会证明 Desktop 工具已保留。

在真实投递前，用已授权的临时会话验证 idle、busy、notLoaded、应用重启、工具回调与设置继承；再对真实目标进行有界验证。确认后才登记 `owner_verified: true`。需要且已经验证恢复未加载 thread 时，才启用 `resume_unloaded`。

```bash
python trigger.py --config local-production.json run --live
```

本程序不会修改 model/cwd/approvalPolicy/sandbox 等会话设置，不会创建替代 thread，也不代替 Desktop 处理原生工具和权限回调。不能保持原宿主能力时应记录失败，保留原有机制。

## 迁移已交付基线

首次规划任何批次之前，将原流程已经核验交付的清单转换为：

```json
{
  "verified_delivered": true,
  "evidence": "Location of the verified delivery manifest",
  "files": [
    {"sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "size": 0}
  ]
}
```

这里的哈希只是空文件示例，不是实际处理基线。

```bash
python trigger.py --config local-production.json seed local-delivered.json
```

不要把当前目录快照全部标为已交付。已经创建批次的状态目录不能 seed。演示状态应与真实任务状态分开。

## 回执

业务工作流核验最终结果后：

```bash
python trigger.py --config local-production.json ack BATCH_ID --evidence /absolute/path/verified-receipt.json
```

Windows 使用对应的绝对证据路径。ack 可以与 watcher 并行，记录证据文件哈希和调用者的核验声明。程序不独立联系外部交付系统。模型回合 completed 不会自动成为 delivered。

delivered 是终态：SQL 更新原子排除该状态，旧轮询不能覆盖状态或原交付证据。重复 ACK 会报错并保留第一次证据，不表示发生新的交付。

| 状态 | 含义 | 后续行为 |
| --- | --- | --- |
| ready | 固定版本已准备，尚未发送 | 校验宿主后可发送 |
| sending | 外部请求前已写意图 | 重启后转 uncertain |
| queued | 队列已接受 | 查询已有队列/回合，不重复提交 |
| running | 本地有发送意图，历史中唯一的完整投递文本匹配，回合未结束 | 等待回合结果 |
| completed / failed | 对应回合已经结束 | 等待业务核验或处置 |
| uncertain | 发送结果或后续证据不明确 | 不自动重发 |
| blocked | 投递前连接失败达到上限 | 修复后显式 retry-connect |
| delivered | 调用者登记已核验交付 | 允许推进下一批次 |

连接修复后，仅对投递前 blocked 批次：

```bash
python trigger.py --config local-production.json retry-connect BATCH_ID
```

该命令不能重置已发送或 uncertain 批次。业务执行失败的续接不在本版自动重试范围内。

## 旧状态库与历史关联

首次打开旧状态库时，会增加可空的 `dispatch_text` 字段。新投递在发送之前将完整原文和 sending 状态一并保存。迁移不会为旧批次推测发送文本，也不会重写已有业务结论。

旧的 queued/uncertain 批次仍可按原 client ID 核对队列；离开队列后，缺少已保存原文就不能自动关联历史回合，将保留待核对状态。核实业务结果后仍可登记 ACK。若旧记录曾被普通引用误标为 completed/failed，需要人工核查，不能靠本次迁移认定实际业务已完成。

本版没有已验证的宿主消息 ID 到历史回合的映射。完整文本匹配不等于认证：宿主改写文本可能导致漏匹配，单次人工原样复制也仍可能混淆。多个完整匹配会拒绝自动认领。真实宿主试验必须验证这些字段和行为，不能以文本匹配证明 Desktop 原生能力。

## 完整性与停止

需要完整包条件时，配置 `ready_file`。投送者应先移除旧标记，完成写入后最后创建标记。稳定窗口、ZIP CRC、字节去重都不等同于语义上的完整或去重。

```bash
python trigger.py --config local-production.json stop
```

STOP 会阻止新的投递并结束 watcher；目标宿主已接受/开始的工作需要在该宿主内处理。不要把它作为跨宿主取消的保证。

## 何时切换已有机制

先验证真实链路：文件变化、稳定批次、准确 thread 实际开始、目标结果、业务核验、ack。再验证无变化不产生回合、重复字节不重复处理、busy 串行、重启补偿、STOP 边界。协议替身测试不能代替此步骤。

真实链路或工具继承失败时，保持已有机制。外部任务 ID、开机自启与部署方式由实际项目管理；本程序不自动安装、停用或替换这些任务。
