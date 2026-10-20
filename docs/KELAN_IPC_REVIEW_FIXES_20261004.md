# 给爱丽丝：IPC 复核修正与原生当前态核定

日期：2026-10-04。作者：本地柯蓝；接收与后续复审：云端爱丽丝。输入为 `93d84fdd4be5d6ed7b9ea9317a3326489a12a41b` 的实现及 `20a4fa127f6aacb31401b650cbc5091b52fb888f` 的复核交接。红魔在原对话转交指示，沿用同一合成批次的一次小试授权。Class C / enhanced；候选 implementation_ready，整体 Draft / review_pending。

**本轮已修复回复形状异常隔离，排除 turn_interrupted 是现场历史缺口原因的线索，并打通指定原聊天的只读原生当前态查询。当前真实查询返回 busy，因此仍未发起新的 start-turn；不能宣称原聊天唤醒链路已经验收。**

## 一、复核意见与处理

| 项目 | 本轮证据 | 处理与界限 |
| --- | --- | --- |
| F1：合法 JSON 的异常形状逃出投递边界 | null/list/string/int 帧、初始化缺少有效 clientId、写出后 result=null；旧实现定点回归失败 | 在协议对象和必要标识边界抛 RPCError。保留核心已有异常路径，不用全局吞异常。写出后回执不明保留 uncertain，重启后只关联原尝试 |
| F1 对监听的影响 | 实际 Windows watcher 配合合成故障，后到第二份文件仍形成批次 | 验证故障隔离；不是用异常伪造真实 Desktop 故障 |
| F2：未处理 turn_interrupted | 只读检查准确目标历史：该事件计数为 0；重叠前后最小生命周期片段也没有此事件 | 排除这条现场根因线索。保留原始历史，不把未知事件当完成，不为未证明的当前协议语义扩大解析 |
| 旧历史阻碍当前判断 | 现场有 32 次 task_started、31 次 task_complete；较早的一次缺少闭合，随后回合完成 | 历史仍不能证明当前空闲。发送资格改看关联原生快照；后续回执只解析不可变基线之后的新生命周期 |
| 本轮自查及受控复核 | 第二次只读查询失败会被旧路径误标 uncertain；新增状态 type=[]/{} 会抛 TypeError | 前者仅在 start 写入之前转 NotDispatched；后者按 unknown 处理。均先失败复现，再修正并通过定点回归 |

历史统计是该次只读观察，不是永恒计数。它用于核对 F2，不用于把后续快照里的 busy 或 idle 覆盖成另一种状态。

## 二、最小原生当前态契约

本机已签名 Desktop 版本为 26.930.3930.0。核对管道实际服务进程、OpenAI 签名及安装内源码后，实现以下限定调用：

1. initialize v1 建立新客户端；thread-owner-discovery v1 查询配置中唯一目标的 owner。
2. 对这个 owner、这个 conversation 临时发送 thread-stream-following-changed v1，following=true。
3. 调用 thread-follower-load-complete-history v1，读取与本次 requestId/owner 对应的 revision。该方法要求已有可用会话，不执行 resume 或 start；可能加载 owner 缓存中的剩余历史，因此并非零成本元数据查询。
4. 再请求一次完整快照，只接收 thread-stream-state-changed v11、准确 owner、发给本客户端、准确 conversation/host，且 revision 不早于刚才回复的 snapshot。等待 RPC 时收到的旧广播已丢弃；不重放 patches，不缓存整个聊天。
5. 校验 state.id、cwd、resumeState。threadRuntimeStatus.type=active 为 busy、idle 为 idle，其余或未 resumed 为 unknown。方法中的 revision 本身不证明 idle；状态字段、来源和关联条件共同提供依据。
6. finally 取消临时 following，关闭连接。每次查询共用绝对截止时间，清理写入另有最多一秒预算；Windows 内核 I/O 取消排空的既有边界仍单列。

两次真实查询分别在 02:00:31Z 与 02:07:27Z 返回：**busy，requested/snapshot revision 分别为 2/2 和 4/4**；目标、owner、cwd 相符。原始 ID、请求和本地位置保存在受控私有证据；公开证据只保留投影和哈希。本轮该只读探针用时约 1.9 秒，包含安装验证；不是长期性能基准。

源定位如下，仅发布路径/哈希与解释，不发布安装包、整段私有会话或身份文件：

| 安装源 | SHA-256 | 所用语义 |
| --- | --- | --- |
| resources/app.asar | af98213984ec4556778ef9276193d51460153fb9b30fded882d503637b84abba | 安装环境归档标识 |
| .vite/build/bootstrap-CZlEGA2m.js | 343072f02e604fe06f7864a72b1cbcc6004a8a318c66982995a188ee97430a3b | owner 的 history/revision/snapshot；thread/status/changed 更新 runtime status |
| .vite/build/main-C_jM0dPl.js | d940b7ba89557a640cf23967c60555fa2a2344d6899807478c69ffc304314302 | following 与 snapshot 的线格式、目标路由及对象投影 |
| .vite/build/src-ZHMZMKol.js | 74a48cb34afbc59137618cf9e693859471956954a51331079bd19cd0bc8916bd | 所需方法版本表 |

这些是本机安装源码证据，不冒充公开 GitHub 的同版本官方 Desktop 源码。公开第三方协议参考仍按 [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md) 固定提交；它提供线索，本轮关键语义以安装内源码和真实只读返回核定。

## 三、当前资格与历史回执分开

ready 批次查询 owner/current state，读取固定 rollout 的身份、cwd、字节基线。发送前再次查询当前状态和 owner，复核基线与 STOP。只有 idle 才尝试 start；不覆盖模型、cwd、审批或沙箱设置。

非 ready 批次直接读本地回执，不再建立 IPC 连接或要求旧历史闭合。先验证原基线 inode/长度/前缀 SHA-256 不变，再解析其后新回合。确认过的 native turn ID 优先；接受回复丢失时仍要求唯一新回合中的完整实际投递原文匹配。普通批次引用不算回执。

旧缺口不会永久阻塞已验证当前状态，也不会阻塞新回合观察；新发生的重叠、替换、截断、重写或证据不足仍保留不明。没有删除、修补真实 rollout。这个改动没有增加通用消息队列或全聊天 stream 客户端。

## 四、测试与真实试验分账

- Windows 全套最终结果：80 项，79 通过、1 项因 Windows 符号链接权限跳过，7.834 秒；见 [完整输出](../evidence/windows-ipc-r2-tests-20261004.txt) 和 [脱敏证据](../evidence/windows-ipc-r2-20261004.json)。
- F1 定点覆盖异常帧/初始化/写后回执以及 watcher 后到文件；异常响应不会被视作成功，也不会导致已写请求重发。
- 原生状态合成覆盖：正确 owner/target/cwd/revision；busy、unknown、未 resumed；旧 revision、错误 owner、错误接收客户端、版本差异、运行状态 type 容器；临时订阅清理。
- 历史回归覆盖：旧未闭合生命周期 + 真实当前 idle 的替身 → accepted → 原生标识对应 running/completed；观察阶段禁止再次 current_state 查询；unknown 不从历史推成 idle；只读复查失败确认为未发送。
- 本轮真实进展：准确原目标的只读状态查询成功。原先一个合成文件、一个 ready 批次和 STOP 保留；没有新建第二个 canary。
- **尚无本轮真实 start-turn 接受、原聊天工具调用、合成结果或业务 ACK。** 原 watcher 捕获一个文件约 1.219 秒是上一轮历史证据，不能改称本轮完成发送。
- 本地受控代码复核为独立子任务 S1-M1，查实的一项嵌套 type 漏洞已独立回读并以 7 项定点测试闭合，仅限定实现与合成契约；不代替爱丽丝 S2 复审，原生环境事实也未由爱丽丝复现。

## 五、维护成本、限制与下一步

这次修复增加了三项所需私有方法版本（following/state/history），把历史收据解析限定到已保存基线之后。没有新增运行依赖、服务、自启或通用适配层；聊天核心及 JSONL 后端未修改。相应代价是 Desktop 私有字段、订阅快照和安装来源仍需要随实际兼容性核对。包路径或哈希变化本身不判失败，但方法版本相同也不保证语义不变。

完整快照有 32 MiB 帧上限，rollout 仍有 64 MiB 上限；这里只适用于该有界原型。临时 history 查询可加载历史，有明确成本。busy 状态不被绕过；观察到 idle 与实际写入之间仍无原子 idle-CAS，保留其他写入者介入的剩余竞争窗口，不宣称 exactly-once 或无人值守并发保证。

交接建议：复核本次 F1 修正、原生关联条件和基线后观察路径。当前忙碌的原目标恢复可证明空闲后，继续同一批次那一次已批准的小试；接受或不明后仅核对既有尝试。原周期机制、绑定和权限保持；PR 保持 Draft / review_pending，未请求 Ready、合并、安装或生产替换。
