# Codex 条件触发器

**文件真的发生变化时，把新工作交给已有的 Codex 会话。**

[English](README.md) · [AI／开发接手入口](AGENTS.md) · [当前状态](CURRENT_STATE.md)

这是一个实验性的 Python 文件监听服务。普通程序负责检测变化、等待内容稳定、按字节去重、保存固定版本，再通过指定适配器把任务投递给原来的项目会话。

例如：研究 agent 写完一份报告，文件稳定后，原项目会话收到准确版本并开始审查。没有新内容、也没有待处理工作时，不会请求新的模型回合；本地补偿扫描仍会占用少量机器资源。

本项目由社区独立开发，与 OpenAI 无隶属关系。本地文件演示可以独立试用；真实 Desktop 接入需要核验安装版本和原聊天宿主，当前不能当作通用自动化平台或官方 Desktop API。

## 能做什么

- 用 `watchdog` 监听文件，并通过启动扫描、周期扫描补偿漏事件。
- 用稳定窗口和 SHA-256 排除未写完的文件与重复字节。
- 在 SQLite 中保存不可变输入版本、批次清单及投递状态。
- 提供独立的 JSONL 队列适配器和实验 Windows Desktop IPC 适配器。
- 分开报告监听健康、模型执行结果与业务交付，避免把“回合结束”当作“成果交付成功”。
- 冻结待上传成果，通过可选的既有 Drive Exchange Hub 按持久远端 ID 查回、续传和核验。

发送结果不明时保留待核对状态，不盲目重发；不承诺 exactly-once 执行。

## 先试文件演示，不调用模型

需要 Python 3.10+。安装依赖后，演示只会形成本地批次。

Windows PowerShell：

```powershell
git clone https://github.com/scarlet-devil/codex-condition-trigger.git
cd codex-condition-trigger
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$demo = Join-Path $env:TEMP "codex-trigger-demo"
$config = Get-Content .\example.windows.json -Raw | ConvertFrom-Json
$config.input_dir = Join-Path $demo "inbox"
$config.state_dir = Join-Path $demo "state"
$config.expected_cwd = Join-Path $demo "project"
$config.settle_seconds = 2
$config | ConvertTo-Json -Depth 8 | Set-Content .\local-test.json -Encoding UTF8
New-Item -ItemType Directory -Force $config.input_dir, $config.expected_cwd
"一份等待审查的报告。" | Set-Content (Join-Path $config.input_dir "report.txt") -Encoding UTF8
.\.venv\Scripts\python.exe .\trigger.py --config .\local-test.json scan
.\.venv\Scripts\python.exe .\trigger.py --config .\local-test.json status
```

首次应看到 `batch_ready`，状态为 `ready`；字节不变时再次执行 `scan` 不会生成第二批。演示全零 thread UUID 是占位符，不能拿来连接真实会话。Linux 的完整命令见[英文 README](README.md#linux)。

持续监听和停止：

```powershell
.\.venv\Scripts\python.exe .\trigger.py --config .\local-test.json run
# 在另一个终端执行：
.\.venv\Scripts\python.exe .\trigger.py --config .\local-test.json stop
.\.venv\Scripts\python.exe .\trigger.py --config .\local-test.json status
```

`run` 不加 `--live` 就是 dry 模式。STOP 持久保留；Ctrl+C 结束当前监听。演示需要重新运行时可先 `unpause`，但绑定的试验一旦到期不能靠此命令续期。已被宿主接受的模型工作，需要在宿主内处理。

配置路径必须为绝对路径，输入树与状态树不能相互嵌套。演示将稳定时间改为 2 秒，配置示例原值为 120 秒。请把演示状态与正式工作分开。

## 接入真实环境

| 部分 | 前提 |
| --- | --- |
| JSONL 队列 | 连接经过核验的原宿主；另开 app-server 并填写相同 UUID，不能证明是原运行环境。 |
| Windows Desktop IPC | 核对安装版本、准确 thread、cwd 和 rollout。宿主缺失或归属不明时等待处理。 |
| 原生结果采集 | 在已验证的 IPC 配置中明确设置 `native_result_collection: true`；默认关闭。 |
| 上传恢复 | 使用已安装并获授权、支持 material-recovery 的 Drive Exchange Hub，配置登记项目／路由及 `delivery_command`。本仓库不含独立可用的完整 Hub 服务。 |

入口：[集成说明](docs/INTEGRATION.md)、[IPC 说明](docs/IPC_ADAPTER.md)、[采集与上传设计](docs/NATIVE_DELIVERY_INTEGRATION_20261015.md)。带日期的报告保留当时状态，最新结论以 [CURRENT_STATE.md](CURRENT_STATE.md) 为准。

`run --live`／`dispatch` 可以发起真实工作；`delivery-resume` 可以继续上传冻结成果，但不会重跑模型或自动登记业务 ACK。Hub 适配器单文件上限 **8 MiB**，通用 outbox 上限 **20 MiB**。

## 已验证到哪里

| 能力 | 当前证据 |
| --- | --- |
| 自动触发 | 真实 Windows watcher 连续处理两个合成批次并投递原聊天，结果经调用者核验。 |
| 登录恢复 | 一次真实 Windows 登录启动独立 dry watcher，形成批次并在期限内停止。 |
| 原生结果 | 实现与审查完成，已加载聊天的真实 IPC 读取通过；原生产目标完整业务链路尚未验收。 |
| 上传恢复 | 一个真实 Drive 合成文件，在客户端丢弃回执后按原远端 ID 查回并核验字节。 |
| 最新回归 | 云端 Linux 共 **185 项：184 通过，1 项 Windows 专用测试跳过**，包含 3 项可选 Hub 集成测试。见[准确记录](evidence/alice-merge-validation-20261020.json)。 |

这些是分开的实验，不能拼成一次完整无人值守运行。Hub 重启后的自动恢复、原目标完整业务链路仍待后续验证。

当前窗口加载默认关闭；Windows UI 后端只支持最长 **600 秒**、不导航的明确人工监督区间。任意导航后的无人值守关窗尚未验收。聊天适配器不覆盖模型、审批或沙箱配置。代码合并本身不启用旧试验，也不清除 STOP／到期限制。

其他边界：只实现文件条件，没有通用规则语言、Webhook 服务或 GUI；按字节去重不等于语义去重；历史 blob 尚无自动清理策略。使用 READY 标记时，投送方必须先移除旧标记、写完内容后最后重建标记。

## 开发与反馈

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

请使用虚拟环境中的 Python。不同平台、可选 Hub 依赖是否可用会影响跳过数；报告实际结果及原因。上面的 184 项通过使用了冻结 Hub 包，不能等同于仅 clone 后的默认环境；复现方式与代码地图见 [AGENTS.md](AGENTS.md)。

欢迎通过 GitHub Issues 提交可复现的问题：附提交、系统／Python 版本、适配器、脱敏配置、步骤及预期／实际行为。公开内容请去掉凭据与私人会话材料。

参考来源见[设计说明](docs/DESIGN_AND_REFERENCES.md)、[固定版本索引](SOURCES.json)及[第三方说明](THIRD_PARTY_NOTICES.md)。当前仓库尚未选择项目许可证；第三方说明中的 MIT 文本仅归属于其引用项目。

