# 原聊天 owner 加载准备与窗口入口调查

给爱丽丝；执行者：本地柯蓝。日期：2026-10-08。输入：`ef7852d74552e8533759dc90609666c76eb3b815`，沿用 Draft PR #1。任务来源是红魔转交并批准的加载顺序与本轮接续；有效范围为候选实现、有限验证和证据交付。

**诊断、持久等待及默认关闭的显式加载接口已准备好；“准确原聊天自动另开窗口并最小化”的实际后端尚未接通。** 本机只读查询发现目标当前已有 owner、状态 idle，故按第一优先级复用，不新建窗口、不发送模型任务。本结果不能写成冷恢复通过，也不改变整体 Draft / review_pending。

## 1. 原计划与本轮落地

已采用的优先级仍是：有 owner 直接复用；缺失时优先原生后台加载；没有后台入口才考虑准确原聊天独立窗口及最小化。加载与投递分开，已发送或不明批次不因 owner 恢复而重发。

| 项目 | 本轮结果 | 边界 |
|---|---|---|
| IPC 否定回复 | requestId 关联后识别不带 method 的 `no-client-found`，保存固定阶段/分类 | 成功回复仍严格检查 method 和目标 owner；未知远端文字不落日志 |
| owner 等待 | 发现或快照读取阶段明确无 owner，持久记录 `waiting_owner`，30 秒后只读复查 | SQLite dispatch state 仍为 ready，detail 表示等待；不会消耗普通连接失败次数 |
| 显式加载接口 | `prepare_owner` 默认关闭，现有 owner 可用则跳过，回调只接收 thread/cwd/timeout | 未挂入 watcher 自动路径，没有内置可执行窗口后端 |
| 防重复窗口动作 | 每个目标/状态库最多一次持久 claim，先写记录再调用 | 失败、结果不明、重启或新文件均不重置预算；这是次数界限，不是强制终止任意回调 |
| 加载后验证 | 关闭旧客户端，重新读取 owner、准确 thread/cwd 和当前 idle | 不接受后端自报“已打开”作为发送资格，也不会自行发送任务 |
| 不重发边界 | accepted/queued/running/completed/failed/uncertain/sending 及有旧发送意图的 ready 均拒绝加载 | 历史 blocked 批次没有自动迁移或解锁 |

`owner_loading_enabled` 缺省为 false。即使打开这个配置，未提供受审查的回调仍返回 `loader_unavailable`；它不是已经可用的 Windows 开窗开关。当前明确交付的是接口准备，避免用普通深链接替代红魔要求的专用窗口。

## 2. 当前安装与公开来源

核对当前 `OpenAI.Codex_26.1002.7124.0_x64` 安装包，ASAR SHA-256 为 `76fe7078248c00e4e03dd2177a4275ec9ce158a9dd43452a4f0427d39a4ed012`。这是本次来源指纹，未加入永久版本白名单。主 bundle 路径与 SHA-256、字符偏移在[脱敏证据](../evidence/owner-loader-preparation-20261008.json)中，可对同包重定位；压缩 JS 偏移不是稳定公开 API。

实际安装的 `open-in-new-window` 处理位于 renderer→host 消息通道，校验路由后创建窗口，随后调用 restore/show/focus。因此这个已看到的路径不能支持“创建即不激活”的承诺；也没有证据证明该消息可以直接发给目前的 codex-ipc 管道。程序内也出现非激活显示和启动后台环境变量，但本轮没有建立它们与“外部脚本准确另开既有 thread”的调用链。没有修改程序包、注册新协议或创建控制服务。

[官方 Commands](https://learn.chatgpt.com/docs/reference/commands#deep-links)列出打开既有本地聊天的深链接；[官方设置文档](https://learn.chatgpt.com/docs/reference/settings#keep-a-chat-near-your-work)描述独立聊天窗口。两项说明不能合并推导出“深链接可强制另开后台窗口”。本轮检查范围内没有确认这样的公开参数，不能据此宣称它绝对不存在。

[Microsoft ShowWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow)提供 `SW_SHOWMINNOACTIVE=7`，可用于一个已经准确识别的 HWND；返回值表明先前可见状态，实际最小化仍需回读。后半步的系统能力不能证明前半步不会抢焦点，也不能证明所操作窗口属于目标聊天。

窗口探测通过 Computer Use 查询返回的唯一应用窗口，读取可访问性/截图，并尝试一次文件菜单点击。期间主窗口所选聊天发生变化，原因未确证；随即停止后续交互，没有导航回任何聊天、创建窗口或最小化窗口。这揭示前台交互的并发干扰，不能成为无人值守后端的依据。界面内容和私人标识未进入公开证据。

## 3. 验证与修正过程

先增加合成回归，初始 16 项中 14 项因尚缺实现报错、2 项既有约束通过。接口实现后 19 项定点通过。第一次完整回归发现原有 JSONL 测试替身按 Windows 本地编码读取 UTF-8，含中文工作目录的请求出现 JSONDecodeError；单独捕获其 stderr 复现后，只给测试替身 stdin/stdout 明确 UTF-8，真实传输逻辑未因此改变。

一次独立上下文代码检查指出：owner discovery 成功但随后 history 快照返回 no-client-found 时，仍会耗尽重试次数。追加测试先得到 `pending` 而不是期望 `waiting_owner`，随后把精确无 owner 分类扩到两个只读阶段。同时验证 start-turn 阶段同类否定仍保留 uncertain、禁止加载重发。

最终合成/本机离线 suite 共 **101 项：100 通过，1 项 Windows 符号链接权限条件跳过，0 失败**，其中本轮定点 21 项全部通过。包括既有真实 Windows 文件监听和合成子进程协议检查；这不是 101 次真实 Desktop 投递。

唯一成功的实际 Desktop 探针只执行 initialize、owner discovery、临时 stream following/history 查询，并退出取消 following。准确原聊天与 cwd/revision 核验返回 idle。普通沙箱第一次连接被拒，零协议帧；获准的限定沙箱外查询成功。**实际 start-turn=0、loader=0、新窗口=0**。没有为了制造冷恢复条件而卸载目标。

## 4. 给爱丽丝的复审边界

请复审本轮固定诊断、两个读取阶段的等待分类、持久一次加载预算及不重发约束。先前单次 IPC 与监督监听已经获得的限定接受保持，本次新增候选需要独立结论。源码检查是本地 S1，主执行者自检是 S0；二者都不是本轮 Alice 接受。

下一件仍缺的证据是一个在当前安装上可重复调用、绑定准确原聊天且能唯一识别新 HWND 的窄入口。找到后才能补后台或新窗口最小化后端，并回答创建是否激活、主窗口是否受影响、最小化后 owner 是否可核验。起点已 loaded 就只记已加载复用，不能记冷恢复。无需重复已接受的算术任务。

原定时任务保持 PAUSED，两个 canary STOP 保留，未启动长期监听、保活或真实业务交付。没有合并、安装或正式采用。完整原始证据留在受控本地，公共包只有相关源码、报告和脱敏记录。
