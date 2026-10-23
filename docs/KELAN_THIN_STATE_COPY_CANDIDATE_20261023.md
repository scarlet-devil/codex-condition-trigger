# 最小轻量状态补丁：副本候选与加载阻点

2026-10-23；执行者：本地柯蓝；接收/复审：云端爱丽丝。
输入为 PR #2 固定 `e3f479fbaf4e1e4135bec01f3c11339137bd677a` 的[行动方案](KELAN_THIN_STATE_NEXT_STEPS_20261023.md)。

## 当前结论

已形成独立、默认关闭的轻量状态候选；三份精确源码副本可应用并逐字节回退，合成逻辑及真实源码函数抽取检查通过。**模块级候选已可审阅，实际安装加载仍未通过，G0 不放行。**

新的实质阻点是当前安装启用了 ASAR 内嵌完整性校验及仅从 ASAR 加载。不能将“修改模块语法正确”或“重打包成功”当作原宿主可加载。此次未修改、重启、注入或启动任何 Desktop/app-server，也没有查询真实聊天、操作窗口或发送模型任务。已结束的现成端口调查没有重做。

## 实现范围与为什么需要三处源码

候选位于 [experimental/thin_state](../experimental/thin_state/README.md)，不改生产 `desktop_ipc.py`、调度器或配置。

| 文件/层次 | 最小改动 | 保留的行为 |
| --- | --- | --- |
| `.vite/build/src-CsH31EEu.js` | 新方法版本/注册；新增 follower case；对两个原生请求入口包一层仅识别私有摘要方法的包装 | 旧版本表值、旧方法注册及其他请求仍调用原处理器 |
| `webview/assets/app-initial-ad16eaadf81f.js` | 在复制的 renderer owner dispatcher 中增加同一 follower case | 原对话、完整历史和发送分支不改 |
| `.vite/build/application-network-startup-BG13czUt.js` | 只对新方法响应的完整编码 envelope 限制 64 KiB | 原快照等其他消息逐字节编码行为不改，包括其原大小边界 |

聊天 owner 在界面侧，而原连接对象及初始化代际在主进程。只在一个 dispatcher 返回少量字段不能证明连接属于原宿主，也不能防止查询途中换连接。候选因此使用一个固定名称的内部桥接 `kelan/thread/read-status`；它不接受任意方法或额外参数，不新增端口或服务。

调用顺序是：准确 owner → 原生桥接 → 当前已初始化且 connected 的 local stdio 连接 → 一次 `thread/read(includeTurns:false)` → 摘取 native `id/cwd/status` 及实际连接代际 → 再核验 owner。输入中的 thread ID 只用于定位和核对，输出的身份字段来自 native 响应。只读取被点名的字段，不复制、遍历或序列化 thread/turns/history。

原生侧在请求前后检查连接对象身份、`initializationGeneration`、认证/目录 lifetime、状态事件、disposed/stopping/quitting。Owner 侧检查原 requestClient、前后归属和期间任何归属变化；丢失后恢复同一 owner 也拒绝。没有 `ensureReady`、follow、resume、完整历史或模型发送。

## 调用端与新鲜度边界

`thin_client.query_status` 只接收已有传输对象，默认 `enabled=False`，没有真实管道工厂或 live CLI。未来必须先由独立入口核验原宿主、安装及补丁；传入 pipe 或打开实验开关不构成身份核验。

一次初始化加一次摘要 RPC；本地 v1 follower 请求省略 wire `hostId`，返回仍必须含 native `hostId=local`，并匹配指定 owner、thread 和规范化绝对 cwd。新接口没有捏造 revision；新鲜度依据是当次摘要请求以及该请求期间不变的原连接和 owner。旧快照的 revision 规则保持原样。没有宣称观察 idle 与随后发送之间具有原子性。

| native 状态 | 调用端观察 | 自动发送权限 |
| --- | --- | --- |
| idle | idle | 始终 false，本候选不执行发送 |
| active | busy | false |
| notLoaded | waiting_connection | false |
| systemError | unknown | false |
| 缺字段、错误目标、归属/连接冲突、未知方法 | 拒绝/unknown | false |

外部调用从 initialize 开始共享 monotonic 10 秒截止，帧体读取前限制 64 KiB，总接收不超过 1 MiB（含帧头及无关广播），重试为零，不回退到完整历史。服务端投影限制字段长度，传输编码器另检查新响应完整 envelope 的 64 KiB 上限。

Renderer 可能排队，单纯 Promise.race 超时不能取消队列项。因此内部请求携带同机 `issuedAtMs/expiresAtMs`；原生侧拒绝过期、未来或被延长的期限，并只使用剩余时间作为 monotonic 等待预算。**实机墙钟调整、休眠恢复及真实队列压力仍未验收**；外部调用自身的 monotonic 10 秒不因新请求 ID 或无关消息而重置。

## 副本及回退证据

输入归档为 Desktop `26.1016.8622.0`：625,947,531 字节，SHA-256 `a05dfd86ca508148c83c25590639cf91a52c6647733cdf200723d85357052b49`。本轮重新只读计算并按 ASAR 头提取三份模块；归档长度/mtime 在读取前后相同。

`patch_copy.py` 固定三个原始 SHA-256，逐项要求替换锚点唯一。它只有内存字节变换，不带安装路径写入功能。对三个模块分别执行 apply→revert，恢复内容与原始完整字节相同；六个错误原件和三个篡改候选反例均拒绝。最终模块长度、原始/修订/恢复哈希以及每项原始字节偏移见[结构化证据](../evidence/kelan-thin-state-candidate-20261023.json)。不发布完整厂商源码。

加载检查分为两层：六份旧/新模块经过完整 AST 语法解析；从实际源码抽取 dispatcher、注册器、协议版本、连接 API 和编码器，在隔离 VM 中执行合成输入。**没有 import 完整 Desktop bundle，没有重打包/启动完整 ASAR，也没有真实安装回退试验。** 当前回退证据证明模块副本原字节可恢复，不能代替将来安装事务的回退。

## 安装加载的明确阻点

当前 `ChatGPT.exe` 没有标准 fuse sentinel；进一步在同安装 `chrome.dll` 找到唯一 sentinel，wire v1、长度 9、ASCII `010011001`。按 Electron 官方 [config.ts](https://github.com/electron/fuses/blob/00f2479b958d917fe0f6e7711e85f62b74b3e7c2/src/config.ts) 和 [constants.ts](https://github.com/electron/fuses/blob/00f2479b958d917fe0f6e7711e85f62b74b3e7c2/src/constants.ts)，索引 4、5 都为 ENABLE，即 embedded ASAR integrity 与 ASAR-only loading。DLL 为 329,773,872 字节、SHA-256 `0a6efd67f459f2fc6cb1604529cca9825d97537d2101d503d33d7e245c1283c1`，本轮 Authenticode 状态 Valid，签署主体 OpenAI OpCo, LLC；三项 ASAR entry 均有 SHA256 integrity 元数据。

Electron [ASAR Integrity 文档](https://www.electronjs.org/docs/latest/tutorial/asar-integrity)说明：启用该机制时，运行时会核验归档头摘要；Windows 打包还需对应的 PE integrity 资源。这支持如下**源码/静态推断**：改模块后重算 ASAR entry 和归档头，并不足以让原受保护宿主接受新归档；还需要匹配的受信任内嵌基线。此次没有读取/修改 PE integrity 资源，也未通过实际失败启动来验证此推断。

候选没有关闭 fuse、删完整性元数据、改签名、放宽现有 verifier 或尝试加载任意归档。这里需要先选择受控加载与信任路线，不能直接进入真实聊天查询。

| 给爱丽丝的选择 | 当前能做的事 | 代价/限制 |
| --- | --- | --- |
| 由受支持的宿主构建提供窄摘要接口 | 现有候选可作为明确接口和回归材料 | 需要宿主提供方或受支持扩展入口，目前未取得 |
| 单独设计受控实验打包与信任基线 | 可继续只在副本上研究 PE/ASAR 配套及可逆安装事务 | 涉及原签名信任、Windows 包保护、更新与重启；是新的具体决定，不能沿用本轮副本测试作为批准 |
| 暂存候选，保留已知限制 | 现有生产实现和持续授权不变 | G0 及三项配置功能继续未验收 |

另开自管 app-server 或完整复制 Desktop 不能证明“原 Desktop 所属服务”；本轮没有采用该替代。每次约 626 MB 的安装哈希成本仍单独保留，没有通过缓存或降低校验解决。

## 检查结果与已修正缺口

本地柯蓝主执行，另按执行计划技能的要求进行一次受控子任务审查，任务 `/root/thin_state_candidate_review`，S1；这不是 Alice 审查，也不推定 S2。审查者只读候选与私有副本，独立复跑相同检查。

| 检查 | 最终结果 | 证明范围 |
| --- | --- | --- |
| JS bridge | 33/33 通过 | 摘要状态、失效、归属变化、过期与脱敏 |
| Python caller/patch guards | 14/14 通过 | 默认关闭、绑定、帧/总量/截止、拒绝未知源码 |
| 真实源码抽取 | 18 项通过，含 6 份语法解析 | API 形状/版本、真实插入点、旧路径及完整 envelope |
| 原有 IPC/native-state/chat-adapter | 36/36 通过 | 相关原行为回归；未运行整个 185 项套件 |
| 三模块 apply/revert | 3/3 精确字节相同 | 模块副本回退，不是安装回退 |
| Ruff / ESLint | 通过 | 新候选和本地提取脚本静态检查 |

S1 找到并关闭四项实质缺口：两个 P1（真实连接订阅方法名错误、显式 hostId 导致方法版本不匹配），两个 P2（排队迟到请求重新取得预算、host 错误路径可能反射原服务异常）。均为合成/静态反例，未在真实宿主执行或泄露信息。增加真实 AST API/版本检查后，候选不再只依赖人工模拟对象。

保留失败记录：最初 stub 阶段 JS 为 9 pass/21 fail，Python 为 3 failures/4 errors，按预期推动实现；随后 lint 首次报告 9 项 Python/1 项 JS 问题，已修正。相关旧测试首次模块路径错误，第二次沙箱临时目录权限失败；仅将合成临时目录固定到本 run 后 36 项通过。子任务一次错误 Acorn 路径导致测试未启动，使用已验证 Acorn 8.19.0 后通过。首次只检查 ChatGPT.exe 的 fuse 断言失败，后检查实际 chrome.dll 得到明确结果；一次官方 constants 获取发生 transport error，重取固定提交成功。公开基线首次通过长命令传递触发 Windows CreateProcessW 206，进程未创建；改用本地 JSON 文件保留精确字节。上述失败不描述为运行时缺陷修复或网络根因修复。

## 后续门与交付状态

本轮成果为候选源码、复现测试、精确变换、公开脱敏证据与本报告。PR 保持 Draft，Alice `review_pending`。公共日志原字节前缀保留；完整回读与 Git blob 哈希结果以本机交付回执为准。

下一步先由爱丽丝审查窄桥接及加载信任取舍。如果决定继续实验打包，先准备可审阅的加载/回退事务，获得该具体动作范围后再执行。只有原宿主新入口有界查询、准确身份及新鲜度证明、目录过滤/Tk 检查共同完成，才能补齐 G0；再进入专用对话的追问和忙闲试验。当前真实 IPC 查询、模型发送、窗口操作、安装替换、重启及业务 ACK 均为零。

治理归属：本地 Kelan，Class C/enhanced 候选；按已有明确同 Draft PR 发布授权执行 D/constitutional 脱敏交付。当前轮已通过 Active 28/28，规范固定版本与原内核未改。没有代 Alice 接受，也没有把其他 scope 的暂停或生产状态改写成本轮结论。
