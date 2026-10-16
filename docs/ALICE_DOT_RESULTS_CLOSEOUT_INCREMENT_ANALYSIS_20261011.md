# 爱丽丝：2026-10-11 收尾包内小点材料增量审查

## 结论先行

本轮新增材料把“Library 两原件下载受阻”从概括性转述细化为三个失败阶段：模块导入、stdin JSON 解析、hosted-apps 工具发现/DNS。它的价值是建立了更清楚的失败分类和精确版本索引；**没有补齐两件 Library 原件，也没有证明下载程序、25 项历史检查、15 个案例或任何模型效果。**

因此本轮仍为 **partial**。不得据此批准安装、采用、恢复试验或继续下载；当前收尾报告明确任务已经结束，任何后续动作都需要新的明确任务与权限。

## 本轮直接检查

| 对象 | Alice 直接核验 | 结论 |
| --- | --- | --- |
| 收尾报告 | Drive `1P-6R7yu0gstc1XoiwY8b0S423pGVWQ5y`，17,709B，SHA-256 `2b2aedea46164b29b4908c09363cfea16ae2c95a187e7396d39a8aeaedfd4608` | 完整原字节已读 |
| 收尾 ZIP | Drive `1nhaXlQ__mtQvkUtPfMagUpYqZB52Id_9`，103,346B，SHA-256 `dcdd57e21b90cc17d1a31c2e0897ab2e0fe62884c06377c8030341e201c998ef` | 35 个成员；ZIP CRC 通过；34 个 manifest 条目长度/哈希全匹配；无绝对路径或 `..` 路径 |
| 交付回执 | Drive `1SVMOvMtS5d8Oh5Yxzh6S7g_E9LogJSuW`，2,886B，SHA-256 `e4e02b41d63a556729863ffdd3892cc767eab0f821c595678011a7fb06607143` | 记录准确父目录、未扩大 ACL、报告/ZIP 原字节相等 |
| 嵌入调查 | `KELAN_LIBRARY_FAILURE_SURVEY_20261010_df9a24ec.md`，10,977B，SHA-256 `4ae9691521415c2ca02145ed8b42364e8502d37d9118654ed2114f1e49d27c13` | 报告原字节已取得 |
| 嵌入证据索引 | `KELAN_LIBRARY_FAILURE_EVIDENCE_20261010_df9a24ec.json`，7,455B，SHA-256 `4f38d80b4e270ce71efa201cdd9b83868809af85d2ac9403656e8f6b8a4b75fe` | JSON 可解析；9 个路径版本、10,550B、8 个唯一 blob 的计数自洽 |

ZIP 的 35 个成员等于 34 个被 manifest 列出的文件加 manifest 自身。以上是 Alice 本轮对交付包的直接检查，不等于包内历史工程记录和本机状态的独立复跑。

## 真实问题与冻结验收

这项研究的真实问题不是“能否解释一个报错”，而是：能否取得两件 Library 原件，并在完整字节基础上复核归档、静态检查和模型实验。冻结验收至少需要：

1. 24,924B 中文说明原件的实际字节、身份和 SHA-256；
2. 20,582B 源包原件的实际字节、SHA-256、ZIP CRC、成员路径安全与展开对账；
3. 下载 helper 的准确源码/版本、原始 stdin、请求与原生执行回执；
4. 25 项检查和 15 个案例的逐项输入、输出、判定；模型收益另需同任务对照。

本轮只交付了失败调查报告和脱敏证据索引，不满足上述成果验收。报告本身也把两原件标为缺失，并将模型实验标为 not_run。

## 三类失败能证明什么

| 阶段 | 柯蓝转交主张 | 本轮可接受范围 | 仍不能推出 |
| --- | --- | --- | --- |
| 模块导入 | `ModuleNotFoundError: library_hosted_apps` | 可作为“组件未完成导入”的分类标签 | 不证明同名第三方包需要安装，也不定位是文件缺失、搜索路径还是部署上下文 |
| stdin 解析 | wrapper 表示 stdin 不是有效 JSON | 可作为“请求尚未可靠构造”的分类标签 | 未附原始 stdin、异常位置或 wrapper 源码，不能确认具体损坏原因 |
| 工具发现 | tools/list 阶段 DNS 失败 | 可作为“服务发现未完成”的分类标签 | 不证明 HTTP 403/404、权限结论、下载已开始或平台长期不可用 |

证据 JSON没有包含九个底层输入的实际字节，只列出路径、长度、哈希和提炼后的错误字段；收尾包也没有这些 stderr/exit/work-log blob。因此三类错误仍是**可追溯的柯蓝转交记录**，不是 Alice 对原始 traceback、stdin 或网络响应的逐字独立复核。

另有两个 15B exit JSON被记录为同字节。它们只能证明索引里存在两个路径版本，不能作为两次独立执行的证据。这一去重处理合理。

## 官方源码核对

固定 CPython 提交 `ebf955df7a89ed0c7968f79faec1de49f61ed7cb` 的导入代码在找不到 module spec 时抛出 `ModuleNotFoundError`；JSON 解码器会在无可解析值或尾随额外数据时抛出 `JSONDecodeError`。这支持将前两类错误归入“导入阶段”和“JSON 解析阶段”。

该源码只说明 CPython 通用机制，**不等于读取了私有 helper，也不证明投送环境使用相同 Python 版本或走了同一分支**：

- [CPython importlib 固定源码](https://github.com/python/cpython/blob/ebf955df7a89ed0c7968f79faec1de49f61ed7cb/Lib/importlib/_bootstrap.py#L1310)
- [CPython JSON decoder 固定源码](https://github.com/python/cpython/blob/ebf955df7a89ed0c7968f79faec1de49f61ed7cb/Lib/json/decoder.py#L330)

## 对红魔工作流的实际意义

可直接吸收的是证据规范，而不是候选能力：

- 下载链路应逐阶段记录“导入完成、输入解析完成、工具发现完成、原件读取完成、字节验收完成”，不能把退出码 1 或单个 DNS 字段合并成“下载失败”的唯一根因。
- 回执至少绑定原始输入哈希、helper 版本、阶段、退出码和原始 stderr；脱敏摘要适合公开交接，但不足以替代私有原件审计。
- “报告已归档”与“被研究的原件已归档”必须分开。本轮前者成立，后者仍不成立。

业务收益尚未测量。没有证据说明该 Library 材料能改善科研质量、技能发现或通信可靠性。

## 未闭合范围与最小下一步

当前不建议追加动作，因为本地任务已经收尾。若红魔以后另立任务，最小有效下一步应先交付两件 Library 原件和九个底层输入 blob，再做字节哈希、ZIP CRC、路径安全和逐项来源对账；模型效果另设同任务对照。不要以重试下载、安装模块或复跑 15 个案例替代原件补齐。

本次未安装、执行或启动候选；未接触本机；未改变生产账本、ACK、期限、定时器、窗口权限、PR Draft 状态或模型配置。实际模型与推理强度元数据未暴露，保持 unknown。
