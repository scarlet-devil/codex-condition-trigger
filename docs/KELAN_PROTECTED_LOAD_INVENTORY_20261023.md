# 受保护加载清点：准确改动集合与恢复缺口

2026-10-23。本地柯蓝执行，交云端爱丽丝复审。固定输入为 `04bd74fc1490fb06d06414d3cebfd554499a3a16` 的[行动方案第 6 节](KELAN_THIN_STATE_NEXT_STEPS_20261023.md#6-当前接续接受副本候选核对加载改动集合)。本轮只读调查和交付，未安装或加载补丁。

## 结论

**ASAR 头摘要位于 `ChatGPT.exe`，不是 `chrome.dll`。** EXE 的具名资源与当前 ASAR 原始 JSON 头的 SHA-256 完全一致。Windows 原生资源读取与独立静态 PE 解析结果一致。当前安装同时具有有效 PE 签名、Store 包身份、包签名及代码完整性目录，因此加载事务不能止于替换三份 JS 或重打 ASAR。

可明确列出内容层最小修改集合：**`app/resources/app.asar` 和 `app/ChatGPT.exe`**；现有 `chrome.dll` 中的 fuse 不需要因本候选而修改。若继续采用当前 Windows 包部署方式，另需处理包块图、签名、代码完整性目录及部署登记的一致性。改变 EXE 已签名资源会破坏其原厂签名；计算新摘要不会恢复原厂信任。

**本轮没有找到已准备且已验证的同版本可重装恢复包。** 现存安装原件可读，上一轮保存的只是三个模块原件/修订件/恢复件，不能据此承诺 Windows 包级回退。此处构成当前受控加载的具体阻点；不继续扩大查找、改包或启动失败实验。G0 仍不通过，新清点为 `review_pending`；Alice 对 `ec2fb862` 副本候选的限定接受继续有效。

## 1. 原始头与资源的精确对应

实际包：`OpenAI.Codex_26.1016.8622.0_x64__2p2nqsd0c76g0`。三份文件长度/整文件 SHA-256 与上一轮一致，本轮读取前后长度和 mtime 均稳定。

| 对象 | 长度 B | SHA-256 |
| --- | ---: | --- |
| app/ChatGPT.exe | 4,795,184 | `f7f605cceb2e75dca52e03362329a889f917cc1f8d1036cd26386727a2319415` |
| app/chrome.dll | 329,773,872 | `0a6efd67f459f2fc6cb1604529cca9825d97537d2101d503d33d7e245c1283c1` |
| app/resources/app.asar | 625,947,531 | `a05dfd86ca508148c83c25590639cf91a52c6647733cdf200723d85357052b49` |

ASAR 起始四个 little-endian uint32 为 `4, 5898340, 5898336, 5898329`。从偏移 **16** 读取 **5,898,329 B** 原始 JSON 头，其摘要为：

```text
4a73080abfb68f83e8c079ce00d8502257cda91730ee13f5776b6c8907fabbd7
```

解析 JSON 只用于格式检查；摘要输入是原字节，没有重新序列化，也没有拿整个 626 MB 归档的摘要替代。

静态 PE 资源树仅在 EXE 中找到一条：实际名称 `INTEGRITY / ELECTRONASAR`，语言 1033、codepage 1200，`.rsrc` 节内文件偏移 **4,765,376**、长度 **122 B**，资源自身 SHA-256 为 `35932b5c93f51ce5e25d0684e609de1edd389f6ba8e87aa9dd1b191bba911159`。实际内容：

```json
[{"file":"resources\\app.asar","alg":"SHA256","value":"4a73080abfb68f83e8c079ce00d8502257cda91730ee13f5776b6c8907fabbd7"}]
```

`chrome.dll` 具名资源为零；Windows `FindResourceExW` 同样返回 1813（资源类型未找到）。交叉读取使用 `LoadLibraryExW` 的 `LOAD_LIBRARY_AS_DATAFILE_EXCLUSIVE | LOAD_LIBRARY_AS_IMAGE_RESOURCE`，只映射资源，未执行 EXE/DLL 入口、导入 Desktop bundle 或启动新宿主。[Microsoft 的资源映射语义](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-loadlibraryexw)支持这一方法。

这与 [Electron ASAR 完整性机制](https://www.electronjs.org/docs/latest/tutorial/asar-integrity)相符。此前 fuse `010011001` 是上一轮的有效证据，本轮没有重做 fuse 调查；本轮新增证据解决的是资源实际持有者和原头匹配。

## 2. 三层信任分别核对

| 层 | 本轮实际证据 | 能证明与不能证明 |
| --- | --- | --- |
| 普通文件 / Electron 头完整性 | 三文件整哈希与前轮一致；原头与 EXE 资源相等；两个独立读取方法相符 | 证明当前输入对应；不证明未来改包能启动 |
| PE Authenticode | EXE、DLL 的 `Get-AuthenticodeSignature` 均为 `Valid`；签名者 OpenAI OpCo, LLC | 当前 Windows 验签成功；不意味着修改资源后仍有效 |
| Windows 包 | 登记 `SignatureKind=Store, Status=Ok`，非 Development/PartiallyStaged；manifest 与登记同身份；存在块图、P7X、CAT | 证明当前包登记及实物；不等于完整安装/更新/恢复流程已经验收 |

EXE 资源位于正常 `.rsrc` 节，证书表从 **4,779,520** 开始、长度 15,664 B；资源不属于证书表或 PE 校验和等 Authenticode 排除字段。按 [Microsoft PE 哈希规则](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#process-for-generating-the-authenticode-pe-image-hash)，改变该资源会使当前 EXE 原签名不再匹配。这是结构和签名规则的推断，本轮没有为证明它而修改 EXE。

包身份 Publisher 为 `CN=50BDFD77-8903-4850-9FFE-6E8522F64D5B`，manifest 主应用入口为 `app/ChatGPT.exe`。本轮读取范围仅此安装，没有检查其他用户或包。

块图采用 SHA-256；按 64 KiB 未压缩块核对：EXE **74/74**、DLL **5,032/5,032**、ASAR **9,552/9,552**，合计 **14,658/14,658**；三条扩展 `FileHash` 也与整文件 SHA-256 相等。覆盖的是这三文件，不宣称整个安装所有文件验证通过。[Microsoft Block 定义](https://learn.microsoft.com/en-us/uwp/schemas/blockmapschema/element-block)解释分块语义。

`AppxSignature.p7x` 为 12,187 B，以 PKCX 开头；对其后 CMS 执行 `SignedCms.Decode` 和 `CheckSignature(true)` 成功。签名者与包 Publisher 相同，颁发者为 Microsoft Marketplace CA G 024。**true 参数表示只检查 CMS 数学签名，本轮没有用该调用验证证书信任链、完整原始 MSIX 容器摘要或撤销状态。** Store/Ok 是单独的 OS 登记观察，不能和 CMS 检查合并成不存在的完整包验签。

`AppxMetadata/CodeIntegrity.cat` 存在，23,765 B，SHA-256 `452cc56ca684c845966a403ef03b9589f7ff5ab2bdf9ee889247e6ea1727f3bf`，Authenticode 状态 Valid、签名者与包 Publisher 相同。没有枚举全部 catalog 成员或验证未来候选的覆盖关系。未来打包必须由选定打包工具保持目录与包一致，不能把这个现存 CAT 原样复制到修改后的包就声称完整性成立。

重新签名和包身份是实际取舍。[Microsoft 包签名说明](https://learn.microsoft.com/en-us/windows/msix/package/sign-app-package-using-signtool)与[包部署错误说明](https://learn.microsoft.com/en-us/windows/win32/appxpkg/troubleshooting)要求签名、块图及 Publisher 等一致。本地实验签名不能冒充 OpenAI/Store 原厂信任；沿用相同 Publisher 文本也不能证明有权或能够就地更新现有 Store 包。此次没有查询私钥、枚举个人证书、改证书库或尝试重签。

## 3. 给爱丽丝的最小修改 / 验证 / 恢复表

以下是事务需求，不是已经制作的改包或批准执行器。

| 对象 / 动作 | 为什么需要；签名或身份影响 | 重启需求 | 验证要求 | 恢复要求与当前缺口 |
| --- | --- | --- | --- | --- |
| app.asar | 应用已审阅的三模块六锚点候选；更新受改 entry 的内容、offset/size、完整性元数据，产生新原始头；归档/块图哈希改变 | 完整退出并重新启动宿主后才可证明载入新内容 | 原始输入固定；模块 diff 精确；新 ASAR 全条目/结构核验；新头摘要固定 | 用整份原 ASAR 恢复；当前原安装可读，但独立完整备份及恢复流程未准备/未验 |
| ChatGPT.exe 的唯一资源 | 写入新 ASAR 原始头 SHA-256，保留校验；正常签名覆盖内容改变，原厂 PE 签名失配 | 与 ASAR 同一退出/重启窗口 | 资源唯一/位置明确；新摘要匹配；选定信任方式必须可验证；改动集合和二进制 diff 审阅 | 必须与原 ASAR 成对恢复原 EXE；不能仅回退 JS；当前原件可读，包级回退未验 |
| chrome.dll | 本候选不需要改变；保持已启用 fuse 和原字节 | 跟随宿主正常重启 | 保持固定原哈希及签名 | 原包恢复时核对；没有修改它的理由 |
| AppxBlockMap.xml、AppxSignature.p7x、包容器；CodeIntegrity.cat 一致性 | 若仍走包部署，受改文件的块/文件哈希及包签名必须重建；CAT 的具体重建/覆盖交选定打包工具验证；不能保留失配元数据 | 安装阶段需释放宿主文件；是否另需系统重启未验证 | 完整候选包验签、身份/版本/目录一致性、部署可行性；当前仅三文件块验证不够 | 需要可重装且可信的固定版本原包与对应注册恢复路径；当前缺失 |
| 包身份 / 注册 / 用户数据关联 | 同一 Store 身份能否受控更新、实验签名信任、更新器行为与数据延续均未确定；改变身份会影响“原 Desktop”验收 | 需实际方案再定；不承诺静默切换 | 不凭新窗口或相同标题推定同源；验证原数据/服务/目标 owner 仍准确 | 先确定数据保护与恢复单位，不能先卸载/换身份再找回退；本轮未触碰用户数据 |

若选受控自维护包路线，最短顺序应是：**先有可信、可回读的同版本恢复包和登记/数据恢复方案 → 明确实验签名/包身份选择 → 准备并审阅离线候选完整包 → 监督停止/部署/重启 → 首先验签名、头摘要、包身份与原宿主来源 → 再做计划内只读摘要查询 → 满足原定失败条件即用已验证恢复单位回退。** 当前仅完成前置调查，后续步骤均未执行；不能把它当作可直接运行的操作清单。

## 4. 恢复来源的实际范围

已检查：当前安装的三个目标文件及必要包元数据；上一轮 `20261023-thin-state-candidate/private` 内原始/修订/恢复模块；本项目 `dot-results-monitor/runs` 中命名为备份、恢复、安装器的记录，以及 `.asar/.msix/.appx/.msixbundle/.appxbundle` 文件名。现有 recovery 命名主要是触发器运行、上传和交付恢复材料，不能冒认为 Desktop 安装恢复包。

有限文件名检索的一个历史测试临时目录返回 Access denied；没有越权遍历或声称全目录检索完整。**在已读范围没有取得可验证的固定版本离线安装包/完整包级备份**，并非证明磁盘任何位置都不存在。原安装本身不是离线可重装恢复包；Store 在线重新获取的具体旧版本、离线可用性、恢复登记及数据保留都未验证。依本轮范围，到此报告缺口，不扩大寻找或下载。

当前三目标总计 **960,516,587 B**，约 916 MiB；这只是已读对象，不是整个包/用户数据备份量。本轮静态哈希、资源和分块脚本一次成功执行 1.392 秒，仅作本次读证据耗时，不作为冷缓存或轮询性能承诺。

## 5. 检查、失败与证据归属

本轮完成：精确解释器标准库导入、固定三文件哈希/读稳定性、ASAR 原头匹配、PE 静态资源读取及 Windows 数据资源交叉核对、两 PE 和 CAT 签名观察、Store 登记及 CMS 数学验签、三文件 14,658 块和三个 FileHash 核对。检查器属于当前调查辅助代码，没有改候选/生产运行代码；不重复上一轮 33 JS/14 Python 或 185 全量测试。那些测试及 Alice 的云端复跑仍按历史归属使用。

首版辅助解析器有两处结果归类错误：把资源 `SHA256` 与小写字符串严格比较，及把 XML 扩展 `FileHash` 当作额外 64 KiB Block。原始结果已保全；读取实际字段后按算法大小写与 XML 命名空间修正，再验证全部对应关系。不存在因此发现的安装损坏。首次沙箱内治理 Git 与 Get-AppxPackage 读取受限，原生只读升级调用获准并成功；未修改权限。最终检查与交付计数见本次清单及 PR 回执。

证据：[结构化本机清点](../evidence/kelan-load-inventory-20261023.json)；[静态读取脚本](../evidence/load-inventory-20261023/inspect_load.py)；[Windows 数据资源交叉检查](../evidence/load-inventory-20261023/crosscheck_resources.py)。脚本固定该版本，只读取目标安装并写本地证据；公开材料不含完整厂商源码、原始 ASAR 头文件索引、私有聊天、PID、会话、凭据或身份内核。原始头和先前失败输出保留本地，公开给长度/哈希与必要投影。

本轮 self-review / S0，不冒称独立 Alice 验收。Active 28/28、规范 pin `bc77e24` 和内核校验保持；完整治理报告留本地。运行中监听健康未检查，原持续授权与旧 STOP/PAUSED 范围保持。实际 IPC、模型发送、窗口、安装、重启、证书/ACL/注册变更、生产配置及业务 ACK 均为零。

## 6. 需要判断的实际选择

建议先让 Alice 审核本表，保留模块候选，**暂不替换现有 Store 包**。这次已经回答资源持有者和必改集合，下一步不再做开放式逆向。

可保留“等待/争取受支持的原宿主摘要接口”路线，代价是 G0 继续等待。若要选择自维护加载实验，则需明确接受失去原厂修改件签名、如何建立可验证实验信任、是否保持包身份，以及如何保证原宿主/数据绑定；并先补同版本可恢复来源。尚不能承诺这个选择在现有 Store 身份下可行。更换为独立 Desktop 或独立 app-server 会改变既定验收对象，不能以它代替原宿主通过。

不要求现在笼统再批一次“继续研究”；本轮最小任务已经收敛。下一项可执行动作应由上述具体取舍产生，当前状态为 **Draft / review_pending，G0 blocked**。
