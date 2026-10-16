# 原生结果采集修订复核

结论：限定本次原生采集增量，初审 P1/P2 已修正，新增 overlay 冲突策略通过独立反例。本次复核未发现剩余有效的阻断性代码问题。工程状态可记为 `implementation_ready`；这不表示 Alice 接受、真实原目标验收、合并、安装、无人值守上传或生产启用。

初审报告 `INITIAL_REVIEW.md`、原 `reproduction.json` 与脚本均保留。新证据是 `recheck_review.py`、`recheck-results.json`、`recheck-tests.txt`。

## 复核输入

亲读当前 `native_collector.py`、`owner_loading.py:257-277`、`tests/test_native_collector.py`，并核对差异。当前关键 SHA-256：

| 文件 | SHA-256 |
|---|---|
| native_collector.py | d5cba75c1b75fa3ce1aa90cf677687085569c5fb02c7a0a610a0c088984f955b |
| desktop_ipc.py | 6ea5657e827861ac2831825a6e65b93ca53ecff0e0a6b4c43fe6b1745051af9b |
| trigger.py | 624ffabd694c1b7ee04e537f21ad63d057f2e5fcd9188a90f69348e0bc6e050a |
| owner_loading.py | f1f3c21c393f0ba8acfde5abcf5854037fcc8cb4f490fed699b5584e0aa63c32 |
| tests/test_native_collector.py | 0aa1baa5eb5a0a504f01282d53b6ccfff39a063d3ef6346a102f84d88a88e386 |

## 独立反例重跑

使用原初审脚本中冻结的函数和夹具定义，在全新临时目录重跑；不执行原证据覆盖逻辑。复核脚本新增断言，运行 exit=0。

1. **P1 自动路径：通过。** 两轮真实 `cycle_tick` 都返回 failed，collector 共调用两次；第一轮写入 failed/failed，第二轮没有重复结果写入，之后手动 collector 返回空列表。合法 waiting_materials 不再绕过采集。采集入口位于 cycle_tick 的 paused/owner_verified 门之后、材料协调与窗口生命周期分支之前。
2. **P2 Windows cwd：通过。** 真实 IPCClient 合成 wire 接受大小写/斜杠变体，collector 也按相同规范化规则接受，记录 failed/failed。
3. **并发 ACK：通过。** 仍使用两个独立 SQLite 连接；读快照时另一连接执行 acknowledge，collector 返回 changed，最终 delivered/unknown，保留 caller_verified_delivery，execution_result 记录数为 0。
4. **Overlay 九例：通过。** 对 canonical completed/error=null，精确 turn 的 failed、inProgress、interrupted、completed+error、缺 error 或重复 overlay 均返回 unknown；一致的 completed overlay、无 overlay、仅其他 turn 的 failed overlay 均保留准确 completed。通过实际 IPCClient.current_state 的合成 wire 执行，不只是直接调用纯投影函数。

## 当前目标测试

亲自执行：

```text
python -B -X utf8 -m unittest test_native_collector test_native_state.SnapshotTests -v
Ran 14 tests in 0.473s
OK
exit_code=0
```

其中当前原生采集测试 10 项、既有快照绑定/过时 revision/错误 owner 等测试 4 项。完整 stdout/stderr 保存于 `recheck-tests.txt`。父任务的完整套件结果不计入本子任务亲跑证据。

## 范围结论与未裁决行为

- 已复核：自动采集入口、batch/turn/manifest 绑定保护、Windows cwd 等价性、冲突 overlay、unknown/业务交付分离、并发 ACK。
- Hub 上传接口设计与真实响应丢失恢复不属于此轮修订的原生代码复核；初审关于必须经 Hub 保留通道约束的建议仍有效。本轮未读取凭据/注册route、未调用 Hub/Drive。
- 真实目标 owner、客户端安装及真实原生历史读取仍以父任务各自证据为准；本轮只使用合成 wire，没有真实 IPC 调用。
- STOP 初始门由现测试验证；没有运行生产 watcher、登录、模型回合或旧数据库迁移。
- 不声称 S2、Alice 接受或真实无人值守端到端验收；不裁决合并、安装与生产批准。

## Governed Work Report

Collaboration identity: Kelan（本地 S1 审查子任务，非 Alice）
Acting role: 独立工程复核，`/root/review_condition_native`
Deployment environment and evidence: 当前 Windows/PowerShell 与受控本地工作区；治理环境证据由父任务提供，本子任务未独立重验。
Task-assignment source, scope and expiry: 父任务 followup，限定当前修订、原反例和 overlay 检查；本报告交付结束本轮复核。
Work surface: 本地工具，候选只读；新证据仅在 review-native。
Task class and triggers: C，自动状态采集与跨模块调用链。
Workflow state: implementation_ready，仅限已审原生增量；整体仍保留未完成验收边界。
Capability gate: 隔离 Python、合成 IPC、临时 SQLite 可用；没有外部或生产动作。
Kernel source and hash: 沿用初审限制，未独立重验。
Registry path and status: 父任务提供 Active 27/27；未冒充独立登记验证。
Canonical repository, remote, pinned commit and integrity: 父任务提供 387c98a；本轮未更改或重验。
Applicable project instructions and conflict status: 同初审及新 followup；无范围冲突。
Repository facts: 上述五个文件哈希界定本结论；未更改候选或 Git 状态。
Actions and material evidence: 新复核脚本、JSON、14项目标测试日志。
Checks passed: 原两反例、实际双连接 ACK、九项 overlay 检查、14项目标测试。
Checks failed or skipped: 本轮无失败；全套/真实原生/真实上传/登录未由子任务执行。
Truncation and redactions: 本轮所需源码和结果未截断；无凭据/消息正文。
Assumptions and deviations: 治理来源由父任务提供；复核脚本复用冻结夹具，但反例与断言独立于候选测试。
Known limitations: 独立任务受控输入 S1；方法为代码追踪与独立合成反例；运行后源文件改变则须重新界定适用哈希。
Required Alice review: 保留父任务既有 review_pending 边界。
Required Kelan review: 本次列举的原生修订复核已完成。
Required Human decision: 无新增批准请求；真实登录/安装/生产门未跨越。
