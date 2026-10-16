# 给爱丽丝：准确聊天深链接、内部另开窗口与聚焦边界调查

作者：本地柯蓝；日期：2026-10-08。任务来源：红魔提供准确原聊天深链接，要求仔细研究内部另开窗口处理，并列出可解决、不可保证和待验证事项供爱丽丝判断。状态：研究材料已准备，review_pending；条件触发器保持实验 Draft。

## 1. 结论与前次表述的修正

**给定的 `codex://threads/<thread-id>` 可以精确表达要打开的既有聊天；它没有同时表达“必须另开一个指定窗口”。** 本轮核对了红魔给出的完整 ID：符合当前安装的 UUID 校验，内部路径保持同一 ID；原生只读聊天状态接口也能找到该 local 聊天，当时为 idle。这里没有用标题模糊匹配。完整私有 ID 保留在本地证据，不放进公开仓库。

前次“尚未确认准确聊天的新窗口入口”需要细分：准确聊天的深链接及内部路径已查明；准确聊天的新窗口处理在应用内部也确实存在；仍缺的是**从获支持的外部接口可靠调用这个新窗口动作、绑定新 HWND 并核验副作用**。这些不能合并成“深链接不准确”，也不能合并成“自动另开窗口已跑通”。

正常深链接会选最近活跃的主窗口（必要时选择其归属主窗口或创建主窗口），再在该窗口导航。现有窗口可能因此切换聊天。内部新窗口动作则使用另一条受信 renderer → Electron main 消息，并明确执行显示和聚焦。单纯追加猜测的 `newWindow=true`、`minimized=true` 或 `focus=false`，在已检查的既有聊天解析链中没有对应控制字段。

## 2. 本轮证据范围

- 实际安装：Windows `OpenAI.Codex_26.1002.7124.0`。app.asar SHA-256：`76fe7078248c00e4e03dd2177a4275ec9ce158a9dd43452a4f0427d39a4ed012`。以这份本机分发代码为当前实现证据，并非声称获得了 OpenAI 桌面应用的公开 GitHub 源码。
- 候选输入：`scarlet-devil/codex-condition-trigger` 的 `6f7f1c3cc131ec58bd235b7c9525b730fbfcddb3`。此次只补研究文档、证据、工作日志与当前入口；没有改触发器或聊天适配器代码。
- 六份相关安装文件的长度、SHA-256、16 个符号锚点及字符偏移见配套 JSON。偏移是 Unicode 字符偏移，不是字节偏移或行号；完整应用包及大段私有分发源码不上传。
- 九项隔离检查通过：标准 URL 分解、安装中 UUID 正则、精确内部路径函数、Windows/Apple 修饰键函数、host 选择函数。只执行单独提取的纯函数，catalog/navigator 是夹具；未执行完整 `Gt/q7` 解析器或 Electron 进程。这不是九项端到端验收。
- 一次原生只读聊天状态快照：准确目标存在、host=local、idle。该工具快照不替代 IPC owner-discovery，更不证明窗口已承载该 owner。
- 本轮实际打开深链接=0、UI 输入=0、新窗口=0、最小化=0、start-turn=0。未测焦点闪动时间，也未造出 notLoaded 状态。前次 UI 探测期间所选聊天发生变化的原因仍未确证，本轮不倒推归因。

官方也把此链接定义为按技术 ID 打开本地聊天，而设置文档确认支持聊天独立窗口；两者都不能单独证明存在外部“指定聊天并后台新建窗口”的参数。[OpenAI 命令与链接说明](https://learn.chatgpt.com/docs/reference/commands)，[OpenAI 设置说明](https://learn.chatgpt.com/docs/reference/settings)。

## 3. 两条调用链

### 3.1 普通深链接：指定聊天，复用导航窗口

1. MSIX manifest 为 `app/ChatGPT.exe` 声明 `codex` 协议。注册声明证明安装包提供此协议，不是本轮 OS 实际启动测试。
2. `bootstrap-Dz9A8y86.js:q7` 把既有 `threads` 链接转成 `localConversation`。它调用 `src-BPM2XJL0.js:Gt`：从路径取 conversationId，按 UUID 形状校验，保留准确 ID。
3. `bTe` 的深链接队列调用 `ensurePrimaryWindowVisible`；main 中该回调转到 `ensureWindow({forNavigation:true})`。
4. WindowManager 的 `getPrimaryWindow` 使用最近活跃的 primary window；`getOrCreateNavigationWindow` 再处理 page owner 与 main window 选择。**此处不是按目标 thread ID 查专用窗口。**
5. `rXe` 的 `localConversation` 分支把相同 ID 交给 `Wt` 生成 `/local/<id>`，发送 `navigate-to-route`；正常窗口路径会 restore/show/focus。

host 也是一个独立维度。`fXe` 会结合来源 host、catalog 记录、已连接 hosts 与匹配条目选 host，找不到时回落来源值或 `local`。红魔本次目标在只读接口中确认属于 local；以后多主机环境不能仅凭 ID 字符串推断最终执行位置，加载后仍要检查准确 thread、host/cwd 和 owner。

队列还有一个容易漏掉的限制：它取最后一个待处理链接，等待窗口期间会重新确认仍是同一条，随后清空队列。**多个同时到达的链接可能合并为最后一条。** 因而“协议被接受”不是“指定聊天已经完成加载”的回执，必须单次发起并核验结果。

`browserActive=false` 看起来像后台入口，实际是带严格 browserTabId、HTTPS backfill URL 等条件的专门浏览器分支。它不等于后台加载任意聊天，不能借此当通用静默开窗参数。

### 3.2 内部新窗口：明确 path，创建后聚焦

`local-conversation-page-4fbd5c19c96d.js` 的聊天页面 hook，从当前 conversationId 构造路径，派发 `open-in-new-window`；菜单也有相应动作。main 的受信 IPC 处理器校验 path，传入 `createFreshWindow` 和 opener，再执行 restore（如需要）、show、focus。

本机的 `createFreshWindow` 调用以 `show:true` 创建 primary window。另处出现的 `CODEX_ELECTRON_START_IN_BACKGROUND` 分支用于隐藏启动窗口的显示策略，不能据此声称这条新窗口路径会后台创建，也不能用启动脚本的 Hidden 选项抵消应用随后自己的 show/focus。

此消息是应用内受信 renderer 的消息，**不因名称相同就成为现有 codex-ipc pipe 的可调用方法**。当前暴露给本任务的原生导航工具只能定位聊天；`open_in_codex` 打开文件/Page/浏览器面板，也不是独立聊天顶层窗口入口。本轮没有找到受支持、可从外部直接调用并返回新窗口身份的等价方法；这是一项有范围的查找结果，不是证明所有版本永远不可能支持。

另一个线索在 `app-initial-25361a10f2bf.js:iBo`：侧栏行能从 `data-app-action-sidebar-thread-id` 取得准确聊天 ID，Windows Ctrl 分支可直接派发新窗口路径，并 preventDefault/stopPropagation。它依赖功能开关 `459748632`、本地聊天解析结果及事件落点。行内按钮、部分 anchor 被排除；落在 `data-interactive-row-link` 且带修饰键时也会提前返回。因此**不能泛化成“Ctrl 点击任何聊天标题都可以另开”**。这只是待实测的、可能无需先导航主窗口的 UI 路径。功能开关的当前账号启用状态、本机可见菜单和可靠事件落点尚未核验。

## 4. 聚焦问题能做到什么

Electron 区分 `show`、`focus` 与 `showInactive`；本机这条新窗口代码选用的是前两者。[Electron BrowserWindow 文档](https://www.electronjs.org/docs/latest/api/browser-window)。

Windows 对已识别的窗口提供 `SW_SHOWMINNOACTIVE=7`，可以请求显示为最小化而不激活该窗口。`ShowWindow` 返回值表达原先可见性，不能当成“最小化成功”；`ShowWindowAsync` 成功也只是发起操作，随后需要回读窗口状态。[ShowWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow)，[ShowWindowAsync](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindowasync)。

这使“允许短暂聚焦 → 识别刚创建的准确窗口 → 最小化 → 再查 owner”成为可验证方案；它不能撤销此前已经发生的焦点抢占，也无法事先承诺闪动少于多少毫秒。用户在这段时间的键盘输入可能受影响，故首次实验应在明确空闲的短窗口完成并记录实际焦点变化。

恢复旧前台窗口可以尝试，但 Windows 对 `SetForegroundWindow` 有限制；即使满足所列条件仍可能被拒绝。用户同时切换窗口时，盲目恢复旧 HWND 还可能打断用户的新选择。**不承诺总能恢复到原焦点**；需记录当前前台与用户操作变化，无法确认时停止后续自动恢复。[Microsoft SetForegroundWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow)。

不能仅按标题“ChatGPT”、进程名或“最新出现的一个窗口”选最小化对象。多窗口、同时开页及延迟显示都会造成歧义。至少需要受控操作前后窗口集合、相同应用进程归属、唯一新增窗口与准确聊天绑定的证据；若有多候选就不最小化任何一个。内部消息没有返回 HWND，这正是外部适配的主要缺口之一。

## 5. 给爱丽丝的判定清单

| 问题 | 当前判定 | 能解决的部分 / 剩余条件 |
|---|---|---|
| 准确选择原聊天 | 源码与隔离检查支持 | 给定完整 ID 进入同 ID 的本地聊天路由；实际聊天只读可定位。仍需加载后的目标检查。 |
| 深链接自动另开专用窗口 | 当前检查路径不支持 | 普通链接选导航主窗口，没有 newWindow 控制字段；不能作专用窗口后端。 |
| 主窗口保留原聊天 | 普通深链接不能保证 | 正常会在选中的主窗口导航；不能用“ID 精确”推导“主窗口不变”。 |
| 内部指定聊天另开 | 实现存在，外部调用待解 | 路径带明确 ID；菜单/页面依赖当前聊天，侧栏候选能直接用该行 ID。 |
| 避免先切换主窗口 | 有候选，未验 | 侧栏行 Ctrl 分支/对应上下文菜单值得优先试；需功能开关、准确目标和事件落点证据。 |
| 最小化准确新窗口 | Windows 接口可用，完整链待验 | 新 HWND 唯一且能绑定聊天后可做不激活最小化；不能拿主窗口或标题猜测。 |
| 全程零聚焦 | 当前新窗口链不能保证 | 源码明确 show/focus；未找到通用外部后台创建入口。 |
| 缩短聚焦时间 | 可测量、可尽力缩短 | 自动识别并尽快最小化；没有固定延迟上界或零输入干扰保证。 |
| 恢复原前台 | 尽力而为 | 受 Windows 前台规则及并发用户操作影响，不能作为必然成功条件。 |
| 最小化后 owner 仍可用 | 待实机核验 | 窗口状态不等于 owner 状态；需最小化后重新只读 discovery/snapshot。 |
| 从 notLoaded 自动恢复 | 本轮未验证 | 只读目标当时 idle，不能据此证明冷恢复；无需为研究强制关闭窗口制造条件。 |
| 长时保活、跨版本稳定、业务可用 | 未验收 | 安装内部符号、功能开关与窗口行为都可能变；本轮不改变既有验收边界。 |

## 6. 建议爱丽丝选择的下一步

**建议优先选择“已有 owner 复用；缺失时，在监督下验证准确聊天的原生 UI 另开窗口，再最小化”的有限方案。** 红魔已允许研究短暂聚焦，可把“零聚焦”保留为偏好，把本阶段验收聚焦到“目标准确、主窗口导航不变、只操作唯一新窗口、最小化后 owner 可用”。这是建议验收口径，待爱丽丝判断，尚未改变产品契约或开启自动化。

可选方案及代价：

1. **专用窗口 UI 路径**：侧栏/上下文菜单，必要时才走当前聊天菜单。优先核对可见入口与准确聊天身份。维护成本中等，依赖 UI 和功能开关；必须接受短暂聚焦可能性。入口不可靠时停止，不退到坐标猜测。
2. **普通深链接加载**：协议简单，聊天 ID 精确；代价是可能切换用户最近活跃主窗口中的聊天。只有红魔和爱丽丝明确接受该行为，才能作为回退；它不是先前“保留主窗口”的等价实现。
3. **受支持的后台新窗口接口**：继续追踪官方工具/产品入口；若能直接指定 ID 并回传窗口身份，维护成本更低。当前未找到，不值得为这一步补丁修改安装包、注入 renderer 或绕过受信 IPC 检查。

一个足够小的后续试验：无模型投递；确认目标及当前 owner；已有 owner 则结束加载；需要窗口时先确认准确 UI 入口，记录前台/主窗口/窗口集合；只执行一次另开；唯一绑定新 HWND 后最小化；复查准确 owner/thread/cwd/idle 和主窗口导航是否保持；报告焦点变化与耗时。任何身份或窗口歧义都不继续最小化或 dispatch。若基线自然 notLoaded，可以记录恢复证据；若本来就 loaded，只能验收开窗/最小化体验。

## 7. 历史与本轮结论不得混淆

此前单次 IPC 及已加载原聊天的监督自动监听已有 Alice 限定接受；前一版 owner 等待修复/默认关闭 loader 接口的 100 通过、1 环境跳过属于前轮代码测试，本轮没有重跑。本轮贡献是解释可调用路径、窗口选择与焦点边界，并提供 9 项隔离纯函数检查及一条只读聊天状态证据。没有安装新后端，没有将加载接口接入 watcher，没有证明无人值守业务可用。

原 timer PAUSED、两处 canary STOP 保持。报告提交与外部回读不是 Alice 接受；交付后继续 review_pending。精确安装来源哈希、研究证据及项目工作日志共同构成可追溯交接，独立爱丽丝复核待进行。
