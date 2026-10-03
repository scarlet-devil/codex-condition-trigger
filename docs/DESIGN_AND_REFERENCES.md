# 设计与参考来源

研究日期：2026-10-03。这里描述固定版本的观察，不承诺后续 Codex 版本保持相同协议或行为。

## 为什么把条件判断放到模型之外

“定时唤醒模型，然后由模型检查有没有新文件”仍然每次消耗一个模型回合。目标是让普通程序先完成事件观察、稳定判断和字节比较，有实际新工作时才向已有会话提交请求。

文件系统的一次保存可能产生多个事件，也可能先写临时文件再替换。因此事件只提示“重新检查”，不等于一个完整成果，更不应该与模型回合一一对应。

## 直接参考与调研比较的区别

| 来源 | 类型 | 采用或学到的思路 | 没有采用的部分 |
| --- | --- | --- | --- |
| OpenAI Codex | 官方协议和实现依据 | queue 请求结构、准确 thread ID、loaded 与 stored 的区别、回执语义 | 没有改写 Codex 源码，没有私有 UI 自动化 |
| Codex Triggers | 架构参考 | 检测、持久记录、投递解耦；任务状态独立于事件状态 | 未复用其源码；未采用其 macOS App 控制器、独立 app-server 或模型/权限覆盖 |
| watchdog 6.0.0 | 实际第三方依赖 | 使用操作系统事件观察，补偿扫描单独处理恢复 | 未复制库源码，未使用其 shell-command 模板 |
| chokidar-cdx | 比较对象 | 确认通用规则、过滤和去抖已有实现 | 未引入 YAML 执行器或文件名到 shell 的插值 |
| gnosis-container | 比较对象 | 确认容器内 Codex 的文件/Webhook 自动化已有实现 | 未引入 Docker 或替换既有 Desktop 运行面 |

SQLite 持久发件箱、内容哈希和状态分离是通用工程方法，本项目不将其描述为独创。这里的独立工作是把这些方法组合成适合“既有会话 + 文件内容条件”的小型原型，并显式保存投递证据的不确定性。

## 固定的官方源码依据

OpenAI 固定提交：`86a54b051c08f34f373c507ae16a91915ab08700`。

- [CLI 队列客户端](https://github.com/openai/codex/blob/86a54b051c08f34f373c507ae16a91915ab08700/codex-rs/tui/src/session_queue_commands.rs)：每次 CLI queue 调用生成新的 client message ID，然后发送 `thread/queue/add`。重新执行 CLI 不能被假定为幂等重试。
- [队列服务](https://github.com/openai/codex/blob/86a54b051c08f34f373c507ae16a91915ab08700/codex-rs/ext/queue/src/service.rs)：`enqueue` 保存输入后调用 `wake_if_loaded`；`dispatch_if_idle` 找不到已加载 thread 时直接返回。
- [请求处理器](https://github.com/openai/codex/blob/86a54b051c08f34f373c507ae16a91915ab08700/codex-rs/app-server/src/request_processors/thread_queue_processor.rs)：确认 queue 操作、归档限制和 start 需要已加载 thread。
- [协议类型](https://github.com/openai/codex/blob/86a54b051c08f34f373c507ae16a91915ab08700/codex-rs/app-server-protocol/src/protocol/v2/thread.rs)：确认 `threadId`、`clientUserMessageId`、分页队列和可选 resume 覆盖字段。
- [issue #44491](https://github.com/openai/codex/issues/44491)：提供未加载线程接受输入但不启动的观察与讨论。研究时状态是 `closed / not_planned`，本项目没有把它当作已修复证据。
- [官方 app-server 文档](https://learn.chatgpt.com/docs/app-server)：`fs/watch` 的作用是给客户端提供文件变化通知；它本身不是唤醒模型的事件任务。

这些源码检查不证明任意本机安装与该提交相同，也不证明 Desktop 原生工具必然能在独立 app-server 中使用。

## Codex Triggers 的参考与取舍

固定提交：`beac312b381cf2841ff46be8510f3a54ecd14ac4`。

[README](https://github.com/ank1015/codex-triggers/blob/beac312b381cf2841ff46be8510f3a54ecd14ac4/README.md) 和 [投递架构](https://github.com/ank1015/codex-triggers/blob/beac312b381cf2841ff46be8510f3a54ecd14ac4/DELIVERY_ARCHITECTURE.md) 将事件、通知和投递任务分开。这个边界很适合复用为设计思路：监听出错、目标繁忙和业务执行失败不能混为同一类状态。

实际检查还发现：

- [app-server 控制器](https://github.com/ank1015/codex-triggers/blob/beac312b381cf2841ff46be8510f3a54ecd14ac4/apps/trigger/src/delivery/services/codex-app-server/controller.ts) 自行启动 app-server 子进程，并在 resume/start 时传入模型和权限设置。
- [CLI 适配器](https://github.com/ank1015/codex-triggers/blob/beac312b381cf2841ff46be8510f3a54ecd14ac4/apps/trigger/src/delivery/services/codex-cli-service.ts) 通过 SDK 运行，并指定自身选定的模型和策略。
- [Desktop 控制器](https://github.com/ank1015/codex-triggers/blob/beac312b381cf2841ff46be8510f3a54ecd14ac4/apps/trigger/src/delivery/services/codex-app/controller.ts) 依赖 macOS 和私有 Electron/UI 细节。

这些方案各有用途，但本项目关注保留既有宿主及其设置，因此保留一个显式配置的原宿主代理边界，不把独立恢复出的同 ID 会话描述为原 Desktop 接入已通过。

## 本项目的关键选择

### 内容是去重依据，事件是检查信号

两次稳定快照、文件长度和 SHA-256 一起描述版本。相同字节的新路径不触发重复业务；同路径新字节产生新版本。删除文件不触发一个新调查任务。扫描失败不能覆盖既有处理基线。

### 先保存版本，再准备外部投递

固定 blob 和 manifest 保存后，SQLite 记录批次。源文件以后被替换也不会改写已经准备处理的版本。崩溃可能遗留未被批次引用的 blob；当前没有自动 GC，不把其清理加入首次部署要求。

### 入队、开始、完成和交付是不同事实

`queued` 仅表示队列接受。发送前，将完整投递文本与 sending 意图原子保存；只有已进入发送流程的批次，且历史中只有一条 userMessage 的单个文本项完整等于该原文时，才用对应回合更新运行/完成状态。普通批次编号引用、附加引用文字、多个相同匹配和缺少原文的旧批次不会被当成历史回执。文本匹配属于保守关联，不是宿主认证的消息来源证明；原文被改写会无法匹配，只有一条完全相同的人工复制也仍可能混淆。

`delivered` 需要调用者提供业务交付核验证据。状态更新在同一 SQL 操作中排除 delivered 行，所以旧轮询不能回退状态、改写证据或其他字段；并发 ACK 中先完成的记录保留。客户端 UUID 只用于关联，不假定服务器按该字段提供 exactly-once 语义。

RPC 响应等待在取消息前、取到消息后统一检查绝对截止时间。无关响应 ID、通知、服务端请求与正确响应都不能延长该响应等待窗口。这不是对所有文件、管道 I/O 或宿主取消耗时的保证。

### 不确定时保存证据缺口

在外部请求之前持久记录 sending；进程若在此后退出，下次启动将其记为 uncertain。恢复时先看已有 queue/history，找不到也不直接重发。代价是需要人工核对部分阻塞；这是当前原型的行为，不是对自动恢复完整性的承诺。

### 恢复与授权保持分离

默认不 resume 未加载 thread，也不强制启动暂停队列。显式允许 resume 时只发送 threadId；这不会证明原生工具继承正确。STOP 只控制本监听器后续动作，不能撤销目标宿主已经接受的工作。

## 证据边界

已实测：Linux 文件事件、双快照、批次持久化、固定版本、重启补偿和单 worker 行为。

替身验证：JSONL 初始化、准确 UUID/cwd 检查、队列接口、忙碌排队、回执丢失与历史关联。替身不会启动 Codex 或调用模型。

未实测：真实 Windows 监听、原 Desktop 宿主连接、原生工具/Hook 继承、真实模型执行与外部业务交付。

逐来源 URL 和 Git blob SHA 见 [SOURCES.json](../SOURCES.json)。
