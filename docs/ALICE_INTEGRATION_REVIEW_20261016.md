# Alice：原生采集、Hub 恢复与独立登录复核

日期：2026-10-16（Asia/Shanghai）。作者：云端 Alice，角色为接续审查及测试夹具小修。
原接续来源：红魔转交柯蓝的真实重启验收并要求“继续推进工作”。2026-10-16红魔确认交接误贴到另一项目窗口；本文保留实际技术核验，撤回由该窗口提出的后续执行计划。内容仅归属 `scarlet-devil/codex-condition-trigger`。
固定复核输入：`2711dbe4c68dd4cd3fe5cc99d28d943c79464760`；上次 Alice 记录为
`0d7f57616d0ca78e4b1d8ddf79deb238693328d9`，其后三个提交、23 个变更文件。
协作面仍为 `scarlet-devil/codex-condition-trigger` 的 Draft #1、`draft/initial-prototype`。

## 结论

**APPROVE，限于本轮新增实现及下表的有界验收。** 没有发现新增运行代码阻塞。
我修正了一处测试夹具的跨平台误报，未修改运行代码、正式安装或生产配置。
这取代上次复审中“standalone 原生采集和真实上传后端尚未接入”的当前状态；历史记录保留。
**原生产目标业务链路仍未验收，原 STOP／到期锁／PAUSED 不由本结论解除，PR 仍 Draft。**

| 内容 | 本轮结论与证据归属 |
|---|---|
| watcher 反馈与独立真实登录 | 接受柯蓝本机报告所限定的 dry 登录验收：新登录、一个合成文件形成 ready、正常 STOP、任务禁用。Alice 检查了脱敏摘要、测试脚本、源码绑定与时间顺序；没有亲自观察 Windows 登录或读取未外发的 SID/XML 原件。 |
| 原生结果自动采集 | 新代码已接入 live cycle，绑定准确 thread/cwd/turn/batch/manifest，终态与业务 ACK 分开；冲突、缺失及接口失败保留 unknown。原目标 owner 未加载的限制仍在，已加载的其他 chat 不能替代它。 |
| Hub 上传与失响应恢复 | 实现先持久绑定预生成 Drive ID，再按同 ID 查找、创建及全字节回读。接受真实 canary 的客户端失响应恢复报告；Alice 另外下载了那个既有远端文件并核验原字节。 |
| 整体业务运行 | 仍 pending。没有将 dry 登录、合成 provider 的进程死亡、真实 Drive 的客户端丢回执拼成一次未实际发生的完整生产试验。 |

默认关闭的 `native_result_collection` 不因代码接受而自动打开。Hub 本轮运行文件已由柯蓝安装，
条件触发器候选是否用于下一次运行仍需绑定准确配置。Hub 适配器上限为单文件 8 MiB，
通用 outbox 的 20 MiB 上限不变。Hub 没有新增自启动；本次重启后它由柯蓝恢复，
所以 dry 登录成功不证明完整上传链能在重启后自行恢复。

## 我实际核验了什么

- 23 个变更输入的原字节与 Git blob 一致；复用的既有源码也重新对照当前树，合计核对 55 个文件。
  这是本轮输入集，不是宣称读取了仓库全部历史文件。
- Hub ZIP：53,770 字节，SHA-256 `21f736228e18f430e537e4845e69ae9a2f0727145587d5d3642746b3417de14d`；
  16 成员 CRC、15 个清单载荷的长度和 SHA-256 均通过。
- 登录脚本 ZIP：3,237 字节，SHA-256 `6f6e2330d494341e013f3d94bdab3af49955a6bd8f4f60fc97be5130e13e29c5`；
  3 成员 CRC、2 个清单载荷均通过。登录回执的 11 项源码 pin 与取得的源码一致。
- Hub 安装回执列出的 3 个运行文件及摘要清单，与冻结包的安装后哈希一致。这证明交接内容一致，
  不冒称我直接读取了此刻 Windows 的安装目录或全部 73 个运行文件。
- 登录摘要有 26 项 true 检查，与声明计数一致。时间顺序为 boot 00:57:39.500 → task 00:57:58 →
  worker 00:58:08.570 → stop 01:00:06.846，均在调整后的 01:05 截止前，运行约 118 秒。
  原件哈希可追溯，但哈希本身不替代原件检查；新登录及任务触发的直接实测归属柯蓝。
- 通过 Drive 连接器独立读取既有 canary 的 metadata 和完整原件：
  `1v1auwzETb18D-MggC4KvTjo1Pg0TZCUm`，128 字节，
  SHA-256 `d8bf98ac97ee845e975071033b74e3943ef0eb417d867afcee3518f76bf3f372`，
  原报告父级一致、`shared=false`。没有上传新对象或重传旧成果。

真实 Drive 的故障注入点是 **Hub 已返回 found 后、测试客户端把回执交给 outbox 前 exit 23**。
它支持客户端失响应后的恢复，不宣称真实网络被切断或正式 Hub 被杀。
Windows 真管道／真子进程死亡使用的是合成磁盘 provider，继续作为另一项证据。
预生成 ID 重复创建不产生第二对象的接口依据是
[Google 官方文件创建说明](https://developers.google.com/workspace/drive/api/guides/create-file#generate-ids)；
文档契约与本轮真实原件回读分别记录，不互相冒充。

## 隔离回归与小修

云端 Linux / Python 3.12，复用固定 `watchdog==6.0.0`，加载冻结 Hub 包中的实际 LocalHub：

1. 固定输入全套条件触发器测试 **185 项：183 通过、1 失败、1 平台跳过**。
   失败是 `test_equivalent_windows_cwd_is_valid_after_native_verification`，将 Linux 路径转大写后仍期望相等。
   Linux 上这不是等价路径，运行代码拒绝它符合预期；不构成 Windows 正式功能失败。
2. 仅修正这个既有测试：Windows 保留原大小写／斜杠变体；其他平台使用同目录的 `/.` 变体，
   测试重命名为 `test_equivalent_cwd_is_valid_after_native_verification`。
   原失败项定点复跑 **1 项通过**。没有修改路径比较逻辑，也没有跳过此项测试。
   修正后没有重跑整个 185 项套件，不能把两个运行合写成一次全绿日志。
3. 冻结 Hub 的 `test_material_recovery.py` **7 项全部通过**，覆盖同 ID 恢复、错误绑定、旧操作互斥、
   远端不符、停用路由、跨 schema 占用与预留异常。条件套件另已包含 3 项 outbox→Hub 薄客户端检查。
4. 未重跑柯蓝的 324 项 Hub 目录套件、Windows 管道／登录、真实模型任务或 Drive 上传。
   冻结包没有包含 Google adapter 所需的完整既有依赖（例如 `ports.py`、`windows_credentials.py`），
   因此不声称复跑了其 6 项 Google wire 测试；已直接审查对应源码、补丁及柯蓝复核记录。

上述测试夹具小修属于 Alice 的 S0 自查；对柯蓝本轮增量的代码／证据审查与隔离复跑单独归属 Alice。
没有新增审查子代理，也不把之前 Alice 写过的基础代码重新算作独立实现。
验证计数、输入摘要与日志摘要见 [机器可读记录](../evidence/alice-integration-review-20261016.json)。

## 接续范围更正（2026-10-16）

此前列出的“一次模型回合、一次新合成回执上传、15分钟截止”方案已撤回，未实际派发，
不再作为当前待执行、待批准或必须验收的任务。原文只在[历史提交](https://github.com/scarlet-devil/codex-condition-trigger/blob/1278dc36088e4472e4c7921d4fb19068734f2fca/docs/ALICE_INTEGRATION_REVIEW_20261016.md)保留追溯。

本文的技术结果只属于条件触发器；后续由本项目工作面根据当前有效目标接续。
原目标业务链路未验收这一事实保持，具体如何继续不由误贴报告的窗口预先决定。
原STOP/到期/PAUSED与已取得结果保留；本次清理不启动模型、上传、登录、安装或生产恢复。

## 归属与限制

云端 Alice 直接执行 GitHub 读取、源码检查、包校验、Linux 隔离回归、测试夹具修正和 Drive 原件下载。
本机 Windows 登录、Hub 安装／重启、旧数据库和业务状态保全归属柯蓝的报告；本轮没有本机实时状态调用。
审查涉及跨模块接口及持久状态（Class C）；正式安装／启用边界沿既有具体批准与 STOP 处理。
共用日志和当前概览只追加本轮准确结果，保留旧正文和原 PR 正文；没有合并、Ready、部署或生产恢复。
初次批量工具输出发生显示截断，决定性报告／源码／规范随后分段读回；原始返回和失败日志保留。
交付完成后结束本轮，不声明后台等待或已通知正在执行的本机 agent。
