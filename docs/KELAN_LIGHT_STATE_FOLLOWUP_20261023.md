# G0 轻量状态路径：本机调查与有界读取

日期：2026-10-23。作者：本地 Kelan。接收者：云端 Alice。固定接手 `4dd30721de987aa779ea624ab83a94db8006e60e`，依据 Human 在原项目聊天转交的三项接续指示。

**结论：三项配置设计保留，G0 继续未通过。** 找到了无需订阅历史的部分设置读取，并实测小响应；它不能证明当前 idle/busy，也没有原生 cwd/revision，因此不能替代发送前的 current_state 门。本轮没有改运行代码、帧上限、配置、监听任务、业务 ACK，也没有模型发送或窗口动作。

## 1. 当前安装里的真实路径

安装仍是 `26.1016.8622.0`，签名 Valid；归档 SHA-256 `a05dfd86ca508148c83c25590639cf91a52c6647733cdf200723d85357052b49`。本轮先静态扫描 ASAR 的 `.vite/` 与 `webview/` 普通内嵌 JS，单文件 32 MiB 上限，无因该上限跳过的 JS。保存命中索引和本地代码定位，不向公开仓库复制整个安装源码。

主要来源 `.vite/build/src-CsH31EEu.js`：1,664,092 B，SHA-256 `6a266611954c6f0c72aca09bb13c0c793959a69e8d6330778a7cdef21835a1db`。以下偏移是此文件 UTF-8 解码后的零基字符位置，便于同版本复核，不是 Git 行号。

| 定位 | 源码事实 | 含义 |
| --- | --- | --- |
| `handleThreadStreamFollowingChanged`，355162；`sendConversationSnapshot`，356361 | 关注状态 true 会调用 snapshot；snapshot 传入 threadStore 的 conversation 对象 | **只删除 complete-history 调用仍会发送会话快照**；没有看到该请求的字段投影参数 |
| `thread-follower-load-complete-history`，530698 | 调用 getCompleteConversationTurns，再广播快照/返回 revision | 现有 small projection 不能限制接收历史成本 |
| `thread-follower-read-model-settings`，531636；方法表 8311；注册处 1594225 | v1；等待已有设置更新，断言当前仍为 owner，再从对应 conversation 返回七个设置字段 | 无 complete-history 或 follow 调用；返回 resumeState，但不返回 id/cwd/threadRuntimeStatus/revision |
| `assertThreadFollowerOwner`，1008800 | 当前 stream role 必须为 owner | 设置回复具备 owner 检查，但 owner/resumed 都不等于 idle |
| `readThread` 周边，475900 | 内部 `thread/read` 可传 includeTurns:false，走 app-server requestClient | 有更合适的内部 API 方向；尚未确认能从外部程序接入**原 Desktop 所属的那个 server** |
| IPC 转发注册 `T0`，1593719 附近 | 注册 owner discovery 和明确列举的 follower 方法 | 已检查路径中没有通用 `thread/read` 转发或完整的薄状态方法；不据此声称全产品永远不存在别的入口 |

当前 [官方 App Server 文档](https://learn.chatgpt.com/docs/app-server#read-a-thread) 说明 `thread/read` 默认不带 turns，返回 runtime status，且不会像 resume 一样加载聊天。这提供了候选方向；文档不证明本机 named-pipe 路由已经暴露它。启动另一个 app-server 后读到的 notLoaded，也不能充当原 Desktop 当前状态。本轮未启动独立 server、未连接未知端点、未注入 Desktop 或改安装包。

## 2. 有界实机探针

先核对准确 Python 解释器的标准库及现有适配器导入，再做七项合成边界检查和 Ruff 基础错误检查。只对两个此前确认的固定聊天各尝试一次。目标 ID/cwd/rollout 路径来自本地私有配置；SQLite 精确按 ID 的查询使用 mode=ro/query_only，并与最多 256 KiB 的 rollout 首行比较。公开结果仅保留别名、匹配布尔值与摘要。

**发送白名单只有 initialize、thread-owner-discovery、thread-follower-read-model-settings。** 不发送 follow、complete-history、start-turn，也不改变设置。探针独立进程临时登记已从安装代码确认的 v1 方法，不修改现有适配器文件或正在运行的进程。

固定预算：单帧 65,536 B；每目标累计接收 1,048,576 B（含帧头与无关广播）；每目标 initialize 起至最终回复共用 10 秒单调截止；重试 0。超限先拒正文，累计预算在读取前检查，错误 ID/广播不能刷新截止。连接关闭撤销本探针连接；没有订阅清理动作或窗口动作。

| 2026-10-23 UTC | 目标别名 | IPC 接收/发送，含帧头 | IPC 用时 | 含本地核验总用时 | 实际结果 |
| --- | --- | --- | --- | --- | --- |
| 08:52:23 | loaded_control | 2,059 / 804 B | 0.015 秒 | 0.890 秒 | owner 找到；379 B 设置回复，resumeState=resumed；runtime unknown，can_send=false |
| 08:52:24 | original_results | 1,245 / 476 B | 0.016 秒 | 0.860 秒 | owner_unavailable；未发送设置请求；runtime unknown，can_send=false |

接收包括初始化响应和其他客户端的跟随协调广播；探针自身未发送跟随消息。各帧类型、长度、请求匹配摘要见 [机器可读结果](../evidence/kelan-light-state-results-20261023.json)。没有保存会话正文或设置值（只保留 resumeState 和字段名）。

**测量边界：**上述字节是探针管道接收/发送，不是整台 Desktop 全局流量，也不代表服务端总内存/CPU。总用时另包含本地身份绑定、签名与归档哈希核验；归档 625,947,531 B，每目标核验会顺序哈希整个归档，并检查相关源码。这部分明显不是轻量高频 UI 操作，本轮未做缓存/增量优化。IPC 截止不含安装核验阶段；签名子进程超时 20 秒，归档读取未另设硬截止，实测耗时如表，不能宣称端到端严格 10 秒保证。

## 3. 新鲜度和不足

设置响应通过本次唯一 requestId、method 和精确 handledByClientId 匹配；源码要求该 owner 当时仍拥有目标。这足以说明这次请求关联的**部分设置**回复，不是从旧文件猜来的。但回复不回传目标 ID/cwd/revision，也不含 runtime status。目录/rollout 的历史身份核对不能补成原生 cwd 或新鲜 idle 证据；resumed 也可能正在执行。

因此本轮未得到正向 current_state 成功，不进行基于它的错误 cwd/错误 owner/旧 revision 真实对照；它们保持待验证，原有测试契约不能删去。没有为捕获 busy 主动启动模型。本轮七项合成检查只覆盖探针的帧预算、累计预算、截止不重置、异常对象、禁止 start-turn 和本地路径等价/不同目录；不能替代完整协议绑定测试。185 项历史生产套件没有重跑。

## 4. 交给 Alice 的取舍

| 路线 | 已知能做 | 当前不能证明/成本 | 建议 |
| --- | --- | --- | --- |
| 小型设置读取 | 很小响应、owner 查询和 resumed 字段 | 没有 busy/idle/cwd/revision | 可作为未来连接诊断，不能放行投递 |
| 现有 snapshot | 已有绑定/revision 判断代码 | 历史体量增长；32 MiB 实际失败 | 保留上限与 unknown，不靠加大限额过 G0 |
| 原 Desktop 的 `thread/read(false)` 桥接 | 官方接口与安装内部调用都存在 | 外部传输入口、原宿主绑定、新鲜度/不加载副作用尚无完整证据 | **下一项只研究这一接入缺口**，找到真实入口后再做同预算正反例 |
| 独立 app-server 或读静态目录 | 可读目录/自身 server 状态 | 不能代表原 Desktop 的在内存状态 | 不作为替代验收 |

暂时有界的可用替代只是“列目录 + 小型连接诊断 + 状态未知时等待”，成本有本轮测量，但不满足自动投递的 G0。若要新增 Desktop 桥接或采用另一集成路线，应先交回具体入口、字段与维护成本，不能把它混入已完成的证据补交。G1/G2 表单和调度仍不启动。

## 5. 归属、交付与复核边界

本轮 Human 指示覆盖两份历史材料的公开脱敏补交、实际安装静态研究和两目标有界只读验证。研究为 Class C/enhanced；同 Draft PR 的公开交付按具体授权的 Class D/constitutional 处理。本地完整性核验 Active 28/28，安装登记与内核来源一致；身份/登记原文不公开。执行与自审均为 Kelan，S0；Alice 新审查仍 `review_pending`。

产物包含原调查脱敏版、历史窄诊断派生件、本报告、实测摘要、实际探针源码及哈希清单。原始报告/失败和私有目标配置原地保留。安装代码全文、聊天 ID/标题、正文、凭据和无关个人资料不提交。工具中一次 GitHub 参数校验失败和沙箱直接网络 DNS 失败未产生外部写入，随后使用已有 GitHub 连接器；治理沙箱访问失败后宿主只读核验通过，未修订权限或治理。

本轮没有判断现有持续监听的实时健康，也没有把旧试验 STOP 或本地后来持续运行混写为新设计状态；两者均未改动。提交与完整远端回读结果以原 PR 的实际交付回执为准，保持 Draft，不合并，不声称 Alice 接受。
