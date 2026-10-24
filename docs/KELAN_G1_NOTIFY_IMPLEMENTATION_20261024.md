# G1 规则与普通通知调度：实现与合成验证

执行：本地柯蓝；接收与下一轮审查：云端爱丽丝。输入为 PR #2 的 `db69330f9a893093a52d4dc2812626be52c649ea`，依据[行动方案第12节](KELAN_THIN_STATE_NEXT_STEPS_20261023.md#12-当前接续g0-限定接受与-g1-实现)。状态：**G1 implementation_ready / review_pending**。G0 沿用 Alice 已作出的限定接受；本轮没有重跑 G0。

## 结果和范围

G1 已接入现有 `Store → dispatch_one → DesktopAdapter → cycle_tick`。新增 Python 规则接口和独立通知状态；没有创建另一套投递器。**默认仍是 `verified_delivery`，只有显式 `dispatch_mode=notify` 才采用普通通知推进。**

合成演示使用真实 Store、SQLite 事务及 cycle_tick，传输为明确的 fake adapter：

| 情形 | A运行期间发送次数 | A准确终止并重新空闲后总发送 | B是否发送 | delivered / 业务ACK |
|---|---:|---:|---|---|
| notify | 1 | 2 | 一次 | 0 / false |
| verified_delivery | 1 | 1 | 仍等待 | 0 / false |

这是调度与恢复语义验证，不是新 Windows/Desktop 实机验收。本轮真实 IPC、模型任务、窗口操作、业务 ACK、安装、生产恢复均为 0。未检查现有生产监听健康，也未改变历史 STOP、到期、PAUSED 或连续授权。

## 已实现的契约

1. **初始内容与交付分开。** 首次启用默认把已有 SHA-256/长度写入 `baseline_versions`，不建立批次、不写 versions 的伪交付、不调用 seed。默认基线、目标占用和 enabled 在同一 SQLite 多数据库事务中提交；失败回滚。高级选项 `initial_files=process` 才处理已有材料。重启不会重建基线。
2. **规则预览与启用分开。** 预览只验证目录、catalog选择项及 rollout身份，读取材料并给出计数；不创建 state、数据库或基线，不调用原生连接。启用先做一次只读能力/空闲检查，再冻结初始基线。本轮该检查由 fake 执行。目录不可重叠或嵌套，READY 标志本身不作为成果内容。
3. **三个状态维度分开。** native acceptance、准确终止、通知释放分别保存；`delivered` 仍只表达业务交付。接收记录绑定批次、manifest hash、thread/cwd、request/client/turn、投递全文 hash 和意图前 rollout 基线；终止还要求基线之后对应 native turn 中恰好一条完整原文匹配及准确终止事件。
4. **后批推进有证据。** 释放前重新查询 idle，并保存对应 owner、thread/cwd、request ID、revision/requested_revision。只有布尔 `can_send=true` 不够；STOP、单调预算或绝对期限、暂停和容量检查仍生效。下一批实际发送还沿用原适配器的状态再核验。
5. **结果未知不等于终止未知。** 已确切终止的 `unknown`、`failed` 或 `interrupted` 可在 fresh idle 后允许下一批，但原结果保持原值；不宣称成功。缺 native receipt、缺终止、错误全文/回合/绑定或不确定写入均不释放。通知模式禁用旧全文回退来补造 native acceptance，严格模式保留原有回退和 ACK/material-wait 语义。
6. **持久证据与竞态。** acceptance/terminal 和批次状态原子提交。模拟接受回执落库前事务失败时，重启看到 uncertain，既不重发也不越过。已验证的首次业务 ACK 不能被后来的观察覆盖；迟到 running 或重复终止不能改写最终 outcome。
7. **同目标互斥。** 当前版本所有 worker 模式共享 per-user UUID 目标锁；已启用 notify 的持久占用也阻止别的 state 启动 strict worker，即使 notify worker 已退出。暂停释放占用，恢复重新竞争。不同 state 的锁竞争及真实子进程竞争已做合成验证。
8. **暂停不能被旧启用覆盖。** pause 递增持久 `pause_epoch`；enable 在能力检查前捕获，初始化事务提交前再次比较。能力查询或初始扫描期间发生的已确认暂停会取消该次启用并回滚基线。
9. **不可静默迁移。** 模式、schema、规则身份/revision、目录、目标、条件及 task_instruction 进入绑定。已有 strict 状态不能改配置变成 notify，反向同理。每批 manifest 记录规则 revision。用固定输入中的原始旧 `trigger.py` 实际打开新 notify 数据库：拒绝，数据库字节不变。回退须使用原配置及旧数据库副本；不能删新字段强行降级。
10. **容量与积压。** 默认 100 个未释放通知批次、1 GiB state。前者阻止冻结新批次而允许已有批次推进；后者阻止冻结和发送。积压按未释放通知统计，历史仍保留，不自动删除。测试使用很小的显式阈值验证，不是大规模压力测试。

## Python 接口与可复现演示

新入口 `rule_service.py` 提供 `preview / enable / pause / resume / status`；两种预设为 `new_content_stable` 和 `ready_content_stable`。三项业务输入是文件夹、预设和 catalog 已选择的条目，指令可选。ID、规则状态目录和初始 revision 由程序生成；完整配置保存在本机私有 state 的 `rule.json`，不应上传。

```python
from rule_service import preview, enable, pause, resume, status

# selected 是现有目录选择器返回的准确条目，包含 id/selection_key/cwd/rollout_path。
summary = preview(folder, "new_content_stable", selected, instruction="检查新增材料并返回摘要")
# enable 是显式动作，真实调用会只读核验 Desktop；本轮未作真实调用。
config = enable(summary["config"], adapter_factory=authorized_adapter_factory)
pause(config)
resume(config)
view = status(config)
```

本阶段未提供原规则就地编辑接口：revision 一旦进入状态绑定就不可改；改变条件或指令需要暂停旧规则并建立独立的新规则状态，旧待处理批次保留，不自动迁移。完整表单及编辑体验属于 G2，不能把当前接口称为成品 UI。

从仓库根运行只使用合成文件的双批演示：

```text
python -B experimental/notify_demo.py --temp-parent <writable-temporary-parent>
```

演示复用仓库测试夹具，输出 notify / strict 对照 JSON，不连接 Desktop，不需要真实 thread ID。首次演示尝试遇到沙箱默认 TEMP 的 PermissionError；新增显式临时目录参数后在可写隔离目录完成，失败保留在本地工具记录，未改系统权限。

## 实际验证与发现处理

本机固定既有 Python 3.12.14，无安装依赖。全套使用仓库冻结 Hub 集成测试子集，ZIP SHA-256 `21f736228e18f430e537e4845e69ae9a2f0727145587d5d3642746b3417de14d`，16 成员 CRC 和 15 项 manifest 长度/hash 全部核验。它不是生产 Hub 安装包。

- 最终项目全套：**230 方法，0 failure、0 error、1 skip**；即 229 通过。skip 是当前 Windows 不能创建符号链接；Windows overlapped-I/O 用例和 3 项冻结 Hub 集成用例均未跳过。
- 实验目录相关回归：**34 方法全通过**。
- 本轮新增 36 个方法，分别覆盖 12 个基础通知用例、15 个证据/恢复/互斥边界、9 个规则接口用例；它们已计入上述230，不能再相加。
- 本地独立子任务审查 S1/M0 找到两项：strict/notify 混合模式未共锁、初始化可能覆盖成功暂停。修复后独立复跑指定3项全部通过并关闭原两项。该3项与全套重叠，不冒充额外3项或 Alice 验收。
- 自查修复包括 native观察覆盖已登记 ACK、未保留新鲜 idle 证据、task_instruction 未纳入版本绑定。对应红测与修复记录保留；红测中夹具导致的清理错误、错误旧异常字符串/空历史夹具及错误期限字段名也明确区分，没有把全部红测都算成产品缺陷。
- Ruff 使用本地 TOOLS.md 的基础错误规则；默认配置扫描另与固定输入比较，既有诊断和新增风格诊断分别记录，不宣称默认 Ruff 全绿。无新增依赖；没有适用于该调度模型的已登记 Lean target，未另建形式证明。

验证摘要、源码及日志 hash、默认 lint 诊断计数和隐私扫描结果以[机器可读证据](../evidence/kelan-g1-notify-20261024.json)为准。原始失败和完整测试日志保存在本地隔离运行目录；公开材料只含必要脱敏结果和可复现代码。

## 保留限制与请求 Alice 判断

- 目标锁约束当前版本的本工具 worker，不能锁住用户手动发送、其他工具或未更新的历史二进制；idle 到 start 之间的原生竞态仍未消除。notify 配置拒绝自动开窗和 native_result_collection，避免把未验收路径默认带入。
- 持久目标占用故障采取保守停止；不自动删除别的规则、恢复备份或解除占用。当前规则不可就地编辑，未知投递保持待核对，不提供超时跳批或自动补发。
- 当前新鲜状态仍走既有完整历史接口；G0 小工作量结论没有证明长期轮询/历史增长成本。容量阈值和稳定文件测试不能代替长期生产压力试验。
- 本轮只交 G1 实现和合成证据。请 Alice 复审通知释放条件、事务/互斥与回退边界；接受后再明确 G2 表单及 G3 真实两批试验范围。PR 保持 Draft，未合并、部署或恢复生产。
