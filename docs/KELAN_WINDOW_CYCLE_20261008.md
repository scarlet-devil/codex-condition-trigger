# 给爱丽丝：逐批窗口循环实现与两批监督试验

日期：2026-10-08。作者：本地柯蓝；行动角色：工程实现、Windows 有限监督验证与证据交接。固定输入 `b8225af531d6da73f69dbd7dfc7d88a6b769f443`，沿用同一 [Draft PR #1](https://github.com/scarlet-devil/codex-condition-trigger/pull/1)。依据红魔转交的 [Alice 交接](ALICE_WINDOW_CYCLE_HANDOFF_20261008.md)，并获红魔本次最多 8 分钟不操作的明确确认。

**逐批状态逻辑和一个监督限定的 Windows 后端已实现；一次实机试验完成了开窗、最小化、第一批结果核验后关窗，以及第二批自动复用 owner。当前是 implementation_ready / review_pending，尚不是无人值守正式业务方案。**

## 1. 本轮实际结果

同一 WindowsApiObserver 从 10:04:37.803 UTC 运行到约 10:08:02.161 UTC，总时长 **204.359 秒**。两个不同字节的合成输入先后到达；第二份只在第一份已 delivered 且第一轮清理 closed 后投入。两个任务均由正常 watcher 循环发出，没有手动 dispatch。

| 项目 | 第一批 | 第二批 |
| --- | --- | --- |
| 实际计算 | 174 + 285 = **459** | 175 + 286 = **461** |
| 原生 start 请求 | 1 | 1 |
| 手动 dispatch | 0 | 0 |
| 实际工具调用 / 成功命令 | 2 / 4 | 2 / 2 |
| 不可变 blob | 93 bytes，SHA-256 已核对 | 93 bytes，不同 SHA-256，已核对 |
| Manifest | 456 bytes，SHA-256 已核对 | 456 bytes，SHA-256 已核对 |
| 文件写入至稳定批次 | 2.188 秒 | 2.093 秒 |
| 设置继承 | 对照真实 turn_context 与发送前 settings 一致 | 一致 |
| 回执 | 调用者核验后 synthetic-only ACK | 调用者核验后 synthetic-only ACK |
| 窗口路径 | 显式已加载目标后端探针开窗；最小化运行；交付后正常关闭 | 关闭后 owner 仍在，直接复用，无新开窗 |

本轮窗口动作总数：**新开 1、最小化 1、正常关闭 1**。两次模型发送均落到配置中的准确原聊天/cwd。主窗口在开窗和关闭的前后观测中保持发起聊天；主应用未退出。第一轮关窗后监听器继续运行并处理第二批，最终由试验监督器正常停止。

准确回合完成、最终 JSON、实际工具调用及成功返回、原输入文本、不可变材料哈希、设置继承和 ACK 文件哈希共核对 **42 项证据断言，全部通过**。它们是本地实机证据核对，不是 42 个独立重演的 Windows 场景。受控私有原始证据及交付回执保存在本项目 run；公开 JSON 只保留必要脱敏值和哈希。

## 2. 为什么第一轮另开窗口，第二轮没有再开

开始时 fresh 原生查询显示准确目标已经 loaded 且 idle。正式调度在这个状态应直接复用。为了实际检验新脚本，依照 Alice 允许的方式，在第一份稳定批次形成后，明确调用一次 `claim_open` 后端探针；记录真实 idle，没有伪造 owner 缺失。该调用只准备窗口，不发送模型任务。后续发送由 watcher 的正常 `cycle_tick → dispatch_one` 执行。

新窗口自身的 RootWebArea initialRoute 精确对应原聊天，标题相符；新增窗口集合唯一，且不同于主 HWND。后端设置专属窗口 token，记录进程启动时间、可执行文件路径和主窗口关联，随后调用 `ShowWindow(..., SW_SHOWMINNOACTIVE)`；Win32 `IsIconic` 返回 true。

第一批工具/哈希/计算核验后，调用者 ACK；worker 重新查相关 turn 完成、ACK 证据仍匹配、owner idle 和专窗关联，才发 `WM_CLOSE`。结果确认专窗已不存在、主窗口前后聊天一致。随后查询 owner 仍可用，第二批实际复用，没有增加窗口。

**本轮不证明冷恢复、最后一个窗口关闭后的 owner 生命周期或新 owner 创建。** 历史试验窗口未由本轮接管或关闭；此次观察到的 owner 存活不能推广为所有窗口组合。两次“owner 缺失后再开”的路径仅有隔离状态测试，没有将它写成实机通过。

## 3. 实现与回执的职责

- `owner_loading.py` 使用既有 SQLite meta 保存每批 window_cycle。opening 在外部动作前落盘，open 保存 lease；closing 在关闭前落盘，确认后 closed。复用已有 owner 记录 reused，不产生用户窗口关闭权。
- 原永久一次 `owner_load_attempt:<thread>` 不删除、不隐式解释为已完成；存在就报告 legacy_reconciliation_required，留给明确对账。开窗或关窗结果不明跨进程重启、新文件事件保留，不自动重复外部动作。
- 同一 Store worker 先处理上一轮清理，再投递下一批。调度传准确 expected_batch_id；独立 ACK 连接即使在准备/发送之间完成，也不能使发送函数重新挑选下一批。禁用 loading 也不能绕过未闭合 cycle。
- 接受回执丢失且 turn_id 尚未关联时，循环 ACK 会明确拒绝，等待 worker 用既有观察流程对账；不把文本 fallback 宣称为认证来源。确认交付之后，关闭失败只记录清理状态，既有 delivered 和证据不回退、不重发。
- `Store.acknowledge` 仍是调用者核验声明。本次独立监督脚本按合成任务契约检查结果后调用它，**没有新增通用业务核验器，也没有验证真实成果报告的 Drive 业务交付**。

`trigger.py` 的 live watcher 与显式 dispatch 均走这道循环；没有材料时不打开窗口或唤醒模型。默认 owner_loading_enabled=false；没有完成配置/授权就不会启动后端。正常 owner 检查仍区分 idle、busy、明确不存在和错误/未知。

## 4. 窗口归属有一个未解决的核心限制

当前 UIA 的 URL 是 **initialRoute**，不是可独立验证的当前聊天 ID。当前标题会随导航变化，但存在滞后，也不能排除切到同名聊天。进程、HWND、token、初始 route 与标题的组合不能消除这个反例。延长标题采样、可见标题唯一或只检查最小化状态，也不能据此宣称任意导航后的准确关闭。

因此当前 Windows 后端**明确限制为人工监督且期间不导航**：open 需要操作者登记不超过 600 秒的 supervised_no_navigation_until；lease 绑定同一期限；每个副作用前检查 STOP 和当前截止时间。试验使用红魔明确同意的 8 分钟时段，实际约 204 秒结束后已立即告知可以恢复操作。此参数只是有界监督条件，不检测或强制用户行为，不是新的自动身份认证。

任意导航后的无人值守精确关闭仍为 **unresolved / not accepted**。若要继续生产化，应先取得可回读的当前准确 thread/route 验证入口，或者由红魔/Alice 明确接受另一项有限操作契约。当前没有内部消息注入、renderer 补丁、应用重启、凭据访问或新增窗口控制框架。

## 5. 前台影响：有测量，但没有零聚焦结论

新窗口在最小化前的 `GetForegroundWindow` 采样为该新 HWND，证明它曾占据前台。从菜单 invoke 前记录到最小化后记录间隔 **8.552924 秒**，包含 UIA 核验、窗口初始化和本次脚本开销，不是连续焦点驻留测量或速度上界。

`IsIconic` 已确认最小化；紧接着的前台句柄采样仍指向该新窗口。因此这份报告不宣称焦点已立即交回主窗口，也不提供未测得的恢复延迟。主窗口聊天不变和前台焦点恢复是两项不同条件。真实体验是否足够好，留给红魔与 Alice 判断；完全后台创建尚未实现。

## 6. 测试、受控复核和实机后的最后修正

Windows / Python 3.12.14 / watchdog 6.0.0：**119 项测试，118 通过，1 项因 Windows 符号链接权限跳过**。保留原 owner/IPC 回归并新增 18 项窗口循环契约检查。受控本地复核为 S1-M1，不能代称云端 Alice；其定点两个模块 39/39 通过。

复核发现并关闭：ACK 让下一批跨过清理门、丢接受回执后过早 ACK 导致永远等待关联，以及关闭 loading 开关绕过未闭合 cycle。已保存修复前失败与修复后通过证据。

实机后还发现：只在 open 入口检查监督期限，后面的菜单/窗口等待可能跨过期限。已把期限检查加入每次副作用前的 BeforeAction。提取真实函数做隔离验证：旧函数放行已过期请求，修订函数拒绝，未过期请求放行；PowerShell 语法检查通过，实际 UI 调用为 0。**这项最后门控修正未再重跑真实模型/窗口试验**；证据 JSON 分别记录实机运行源码哈希和最终源码哈希，只有该 PS 文件有此增量，不把不同字节版本混为同一次实测。

起初沙箱默认临时目录不可写，改用本 run 的专用测试临时目录；已有项目隔离运行时被复用，没有安装依赖。最初后端子 PowerShell 被有效脚本策略阻止；有界宿主使用仅本进程 RemoteSigned 执行本地作者脚本，没有改变持久执行策略或组策略。普通沙箱看不到应用窗口，实机读取/动作使用具体授权的本机执行权限，没有修改 ACL。相关失败作为环境限制保留。

## 7. 给 Alice 的判断清单

| 已有证据支持 | 当前还不能接受或尚未验证 |
| --- | --- |
| 逐批持久预算、未知结果跨重启不重放、完成与 ACK 后清理、ACK 并发不越批 | 通用自动业务核验、无人值守真实成果交付 |
| 当前安装明确菜单脚本实际准确开窗、Win32 最小化、正常关闭 | 任意导航/同名聊天条件下的独立当前 thread 验证 |
| 两批正常 watcher 自动发送、第一轮关后第二轮继续且复用 | 两次真实冷恢复、owner 转移、最后专窗关闭的生命周期 |
| 本次主窗口聊天前后保持，主应用/监听器在关窗后继续 | 零聚焦创建、焦点自动恢复延迟或长期干扰水平 |
| 最终期限门的隔离验证、当前 app 版本正向实测证据 | 最后期限修正的额外实机重演、跨版本/语言/DPI覆盖 |

建议 Alice 限定复审为“监督窗口循环和双批自动投递证据”，并单独判断当前路由与焦点限制是否值得继续投入。维护点集中在中文菜单/UIA结构、真实主 HWND/进程绑定和内部 IPC 版本核验；没有维护这些条件的通用自动发现或跨版本承诺。

## 8. 接入契约与材料

`window_backend_command` 为参数数组，使用可用 PowerShell 的绝对路径和本脚本的绝对路径；不把文件名或任务材料插入命令字符串。后端 stdin 为 JSON：action(open/inspect/close)、thread_id、expected_cwd、stop_file、options，以及需要时的 lease。options 包含 main_hwnd、executable、main_title、target_title、open_menu_name 和有界监督截止时间。后端只输出结构化结果；超时作为未知，不自动再试。当前阶段不建议复制一个长期有效的配置当作常驻服务。

参考实现所用标准接口：[UI Automation Invoke](https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/invoke-a-control-using-ui-automation)、[ShowWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-showwindow)、[WM_CLOSE](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-close)。这些文档支持系统接口含义，不保证 Codex 的 owner 生命周期或内部窗口路由。

配套：[脱敏证据](../evidence/window-cycle-20261008.json)、[完整测试输出](../evidence/window-cycle-tests-20261008.txt)、[有限监督脚本](../evidence/window-cycle-supervisor-20261008.py)、[实施计划](WINDOW_CYCLE_PLAN_20261008.md)。私有配置、聊天/回合ID、HWND、原始会话、身份内核及个人路径不随公开材料上传。

原 timer 继续 PAUSED，原两处 canary STOP 和本轮 STOP 均保留；原业务状态、Hooks 配置和绑定字节未改。未合并、安装自启、恢复正式监听或改变现行治理。新实现和结果交 Alice review_pending，不声称她已接受。
