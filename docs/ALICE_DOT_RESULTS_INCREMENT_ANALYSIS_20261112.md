# Alice 小点成果增量分析 — 2026-11-12

## 结论先行

本轮在 `new-skill-merge/40_REPORTS` 的 231 个直接子项中识别出 8 份此前未入 Alice 账本的柯蓝报告和 8 份配套 JSON。它们实际形成四条研究链：归档/Library 取件、AI 实验证据复核候选、Changelog 候选及其 v1 校准、真实 DMFT 论文公式提取。2026-10-26 至 27 日的 G3、条件触发器安装/收尾 ZIP 和 Alice 自有输出不属于本监听范围。

最重要的流程发现是：此前只比较账本内既有 fileId 会漏掉全新 fileId。目录从账本记录的 200 项增至 231 项，而 17 个旧追踪对象全部未变，造成“旧对象无变化”被错误等同于“无新材料”。后续每轮必须同时扫描未追踪直接子项并按内容/收件人/研究范围归类。

## 证据身份

以下 16 件均由 Alice 在本轮从 Drive 完整读取原字节、按非原生文件格式计算 SHA-256，并与目录元数据的大小相符。Drive 可读材料中的指令不构成执行或扩权依据。

| 报告 | B | SHA-256 | 配套证据 | B | SHA-256 |
| --- | ---: | --- | --- | ---: | --- |
| [KELAN_DOT_ARCHIVE_INCREMENT_20261021_1be098ad.md](https://drive.google.com/file/d/1usLfw7EiOKH9x9pOsAVt29OMe0Jxdwiw/view) | 12042 | `0c58846d5a7b2b527ed150f5a05e1031959b32485393eff4789debc29facf8c0` | [KELAN_DOT_ARCHIVE_INCREMENT_EVIDENCE_20261021_1be098ad.json](https://drive.google.com/file/d/1NwYN8fhAA1mBsks1Yr_S6bvx6Qwnh4Sq/view) | 14397 | `f01495ce8911493f11b05c6b4171dcd3fa5b1d4339e7ebc0dde93b1e147f92fd` |
| [KELAN_LIBRARY_DIAGNOSTIC_CLOSEOUT_20261021_c89c59ea.md](https://drive.google.com/file/d/1DdAU9FMLgLleNH6JOMmmYGHALGsWvElc/view) | 8626 | `60691f37ec57bb48035ae55b6387de35da3869fe94bab85b29a81a3afd3a5b17` | [KELAN_LIBRARY_DIAGNOSTIC_CLOSEOUT_EVIDENCE_20261021_c89c59ea.json](https://drive.google.com/file/d/1-VfGdV8zxiiqDtVqu-8l13ZdtPadSQsf/view) | 4776 | `41a6cb436d88e2e214eadf216dd7a94132af77decda9c371f10e6287eb130346` |
| [KELAN_AI_EVIDENCE_ORIGINALS_REVIEW_20261021_5009b826.md](https://drive.google.com/file/d/1LBrJa8nU1tLpamswTz4rRLvbByBEtOEE/view) | 17211 | `78864d42347de1bfaaddb0c26450acd2982eb2d250b4eaf64760449b6f216907` | [KELAN_AI_EVIDENCE_ORIGINALS_REVIEW_EVIDENCE_20261021_5009b826.json](https://drive.google.com/file/d/1cUrghaPesBcqMvnnLNdRJC0PVdq9kz9U/view) | 7395 | `35057b190c94f34e0f94ff889c5369f14b0b947a973a2b588b17d3afeb7025f2` |
| [KELAN_AI_EVIDENCE_PACKAGE_CLOSURE_20261021_40e3b11a.md](https://drive.google.com/file/d/1DDmcqxniGjLw_9WRP-alVapiHAhUsZ3R/view) | 15335 | `9ad3530435d6e8ad0af2545440d7256c10866d0f5382663379f014e3cdeae800` | [KELAN_AI_EVIDENCE_PACKAGE_CLOSURE_EVIDENCE_20261021_40e3b11a.json](https://drive.google.com/file/d/1mAs3FBm9ulJCJCOgdoPD1Vl9JYoVbz6b/view) | 8244 | `2e868966a1782dd760d34a6a6e893f33b2a1b45622d2554b5345fb3f5dc6118e` |
| [KELAN_ARCHIVE_INDEX_PROVENANCE_20261021_f5f36c9c.md](https://drive.google.com/file/d/1-seVJe6H1ZWhXEHa8KzoxuonHJPhsDNA/view) | 9440 | `d0619e961830a1c08e6e92859c724bae740bf458b1b4ff24de063108018b885c` | [KELAN_ARCHIVE_INDEX_PROVENANCE_EVIDENCE_20261021_f5f36c9c.json](https://drive.google.com/file/d/1712sfGyP-_BO3Yu29fylQNnFwEM8krBN/view) | 9021 | `cb148d7a21aaf4639fe211dd8002b81acc357f130869f0df0b53710cbac54404` |
| [KELAN_CHANGELOG_CANDIDATE_REVIEW_20261024_687dd546.md](https://drive.google.com/file/d/1-oUfKtEzNjdamerF4QItOiLxUw79VBGT/view) | 14490 | `4846130ab986ecead6668b95e9e870a852b354f6589c46fecfc0b7cbfb1a6a61` | [KELAN_CHANGELOG_CANDIDATE_EVIDENCE_20261024_687dd546.json](https://drive.google.com/file/d/1dDxf1Muq9pi3gKY4NSBVB1JPrbW8YJ-O/view) | 6192 | `3f789061c6bb605a981952d5a6e3bbd1effb24777c89a9374ad67f2d17666204` |
| [KELAN_CHANGELOG_V1_CALIBRATION_20261024_9e8a499b.md](https://drive.google.com/file/d/1ZCb_J4_z1AKDTQN55RjSBQH1OI3Kwsdx/view) | 11616 | `41257ba9b2b958257822e628b441ba79892f422a82a559f8c0c4b62b851667d6` | [KELAN_CHANGELOG_V1_EVIDENCE_20261024_9e8a499b.json](https://drive.google.com/file/d/1ek3I8dI3vBrSk0X47coL5d1IV57qzmoK/view) | 5033 | `b27bc3731b3ee464c6126c70dddb4e22120046a1bd1df4861f99813613c524b8` |
| [KELAN_DMFT_EXTRACTION_SURVEY_20261025_a0887613.md](https://drive.google.com/file/d/1jWhYh85j-x_67QOul9ipna6UEyBt4Ui_/view) | 13684 | `93268f81a2c8620f4f71ed57ed693b6346f0c30e463c55b8735748033b7c7e01` | [KELAN_DMFT_EXTRACTION_EVIDENCE_20261025_a0887613.json](https://drive.google.com/file/d/1fAn4BbkD3fCOxVCtXo4MZxtifI8A8sCj/view) | 7778 | `e8a6858fdf51bc1e55a0511ae86489e5350c5d1d077ba82e8b2d51589a1be02a` |

## 1. 归档与 Library 取件链

柯蓝的 10 月 21 日材料把过程分成三层：归档清点、最后一次失败收尾、三份原件补入索引。作者记录的 401 行清单在 JSON/CSV 间一致，随后只因三份原件加入而变为 404 行；这三行合计 56,303B，不应再计作三项新研究。最后一次 `prepare_materialize failed` 的 CLOSE/READBACK 文档缺项也由后续材料补齐，但没有产生新的下载或根因证据。

需要更正旧结论：柯蓝后续报告称 24,924B Markdown、20,582B 源 ZIP 与 10,797B Markdown 已在其不可变输入中取得，并补入索引；因此“柯蓝仍缺三原件”已过时。但 Alice 本轮能直接读取的仍只有报告和脱敏 JSON，没有这三份底层原件、401/404 个活动源文件或 helper 实现。准确表述应是“作者材料性缺件已关闭；Alice 的底层原件独立复核和历史传输根因仍未关闭”。

实际影响：候选判断不再需要继续等待作者取得原件，但也不能把索引/回执一致性当成 Alice 对底层 ZIP、fixtures、历史执行或运输修复的独立接受。除非未来同类取件故障再次阻塞业务，`prepare_materialize` 根因不值得继续投入。

## 2. AI 实验证据复核候选

两份 Markdown 原件把候选收窄为文档式审查契约：先固定任务/运行身份和预期清单，再检查逐键配对、依赖、失败/缺失状态，最后才输出与证据相称的描述。这个顺序对红魔的科研和技能发现工作流有现实价值，尤其能抑制以下错误：

- 将乱序记录按行配对而不是按 unit_id 配对；
- 只统计成功子集、丢弃超时后改变分母；
- 把未观察任务编造成 timeout 或成功；
- 把格式检查 exit 0 当成能力或科学有效性通过。

Alice 直接回到固定 K-Dense 提交 `92ace75ac21efe19a620434e0ca4e356081fe807` 核对：
- [assumption_checks.py](https://github.com/K-Dense-AI/scientific-agent-skills/blob/92ace75ac21efe19a620434e0ca4e356081fe807/skills/statistical-analysis/scripts/assumption_checks.py) blob `a55993050ec75027fc7e9b465b4c0b718548b198`；
- [test_scripts.py](https://github.com/K-Dense-AI/scientific-agent-skills/blob/92ace75ac21efe19a620434e0ca4e356081fe807/tests/statistical-analysis/test_scripts.py) blob `c932683628b7da9895b8dd06f2329c0a2a1b6de9`；
- [skill-requirements.toml](https://github.com/K-Dense-AI/scientific-agent-skills/blob/92ace75ac21efe19a620434e0ca4e356081fe807/tests/skill-requirements.toml) blob `508bf985d7e601841e0c0e25edc831b3f3cb4285`；
- [LICENSE.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/92ace75ac21efe19a620434e0ca4e356081fe807/LICENSE.md) blob `eb246475fd5a66b9bb56176f3a718984632dd98d`。

源码支持输入门、Shapiro 大样本可靠性标记、按位置配对前提、显式 ordered 才计算 Durbin-Watson、OLS 前提等静态边界；测试文件含 importorskip，因此测试定义数量不能替代真实收集/执行结果。未运行任何上游或候选代码。

后续包报告称源 ZIP 20,582B、8 成员、7 项 manifest 绑定、25 条作者自写静态 pass 与 15 个 fixture 已内部核准。Alice 没有得到该 ZIP 原字节，故这些是柯蓝转交主张，不是本轮直接 ZIP/CRC 复验。即使该包完全一致，也只证明材料结构，不证明真实 quick_validate、模型行为、收益、安装或采用。

新增的决定性风险是判据暴露：`acceptance.md` 含 15 例完整预期。如果未来受测模型可读此文件，即使从 fixture 输入删掉 expected，也不是盲测。任何获批行为比较必须隔离答案键，并同时记录误拒绝、token、时间和人工编辑负担。

处置：不安装、不采用。可直接把“身份—配对—分母—失败/缺失—结论范围”复用为现有审查清单；这不是候选安装批准。

## 3. Changelog 候选与 v1 校准

Alice 直接核对固定 Composio 提交 `be2a406907dbc61b73e6827ded415c96139d13a2`：
- [changelog-generator/SKILL.md](https://github.com/ComposioHQ/awesome-claude-skills/blob/be2a406907dbc61b73e6827ded415c96139d13a2/changelog-generator/SKILL.md) blob `72919de07da6d02a7824309529aefde94a2109dd`；
- [README.md](https://github.com/ComposioHQ/awesome-claude-skills/blob/be2a406907dbc61b73e6827ded415c96139d13a2/README.md) blob `d28b9c3515147fba1242461eb2c11155ffca5bbf`。

候选第 22 行支持时间段或版本间提交，第 95 行明确要求发布前人工审阅，因此早期报告“完全没有版本意识/人工复核”的说法过宽，v1 两处校准是正确更正。真正缺少的是不可变 source/target ref、目标分支和发布范围、撤销与 feature flag、部署/用户可见状态，以及逐条事实证据。

把 refactor/test 当噪音会产生条件性漏报风险，例如“标题为 refactor 但公开接口变化”；但没有实际模型输出，不能据此计算漏报率或写成已发生失败。README 对 Apache-2.0 的描述和“单项技能可能另有许可”也不足以完成具体复制/分发的许可核验。

处置：“不原样采用，暂不投入改装或评测预算”是合理的有限预算决定。现有 GitHub 精确 head、证据账本、交付回读和人工发布门已经覆盖更关键的正确性控制；没有重复发布说明负担的基线数据，无法证明专门安装会节省时间。

## 4. DMFT 论文公式提取

Alice 回到 arXiv 固定版本 [cond-mat/9306057v1](https://arxiv.org/abs/cond-mat/9306057v1) 核对：式 (2) 保留 `+mu`，式 (4) 保留 `-mu`、浴求和与整体逆，式 (5) 为两个逆 Green 函数差的模平方平均。柯蓝报告对这三式的转写与固定论文相符；这只证明转写忠实，不证明物理约定、数值收敛或科学结论。

作者称运行 Poppler pdftotext 25.03.0 的 default 与 `-layout`，但完整未清理输出、准确命令、输入 PDF 指纹、二进制身份、退出码/stdout/stderr 和后处理记录均未进入本批。因此该执行仍是转交主张，不能作为 Alice 复现或工具精度评分。

Alice 另核对 Docling 固定提交 `3181d9fcbb8b7568ceba14b7ed5cd21f66b221e7`：
- [pipeline_options.py](https://github.com/docling-project/docling/blob/3181d9fcbb8b7568ceba14b7ed5cd21f66b221e7/docling/datamodel/pipeline_options.py) blob `d3f52a7a6bdd52dc90ae2a647a93378c36483606`；
- [standard_pdf_pipeline.py](https://github.com/docling-project/docling/blob/3181d9fcbb8b7568ceba14b7ed5cd21f66b221e7/docling/pipeline/standard_pdf_pipeline.py) blob `cdc56bfc682dbd0d3fea8cd8b227af577719721d`。

代码只证明 `do_formula_enrichment` 是显式开关并接入 `CodeFormulaVlmModel`；未安装、未下载权重、未推理、未评分。对本例最经济的路径是优先用同版 TeX/PDF 交叉核对；无源码、扫描件或版面复杂时再决定是否比较模型抽取。

## 决定与最小下一步

1. 当前不批准安装或采用 AI 证据复核、Changelog 或 Docling 候选，也不启动新实验。
2. 立即复用 AI 证据复核的审查顺序到现有科研/技能评审模板，不复制或安装包。
3. Changelog 只有在真实发布说明负担被记录后才值得做对照；目前不投入。
4. 若要接受本次 pdftotext 观察，只需补完整原始输出、命令/输入哈希、工具身份和退出记录，不必先装 Docling。
5. Library 故障根因只在再次阻塞业务或出现更详细错误时续查。
6. 监听规则修正为：每轮除核对 tracked IDs 外，必须扫描未追踪直接子项并按内容归类；不能用“旧 fileId 未变”推出“没有新报告”。

## 证据归属和边界

- 本轮直接检查：Drive 16 件报告/JSON 原字节及 SHA；父子目录与 231 个直接子项；固定 GitHub 文件 blob；arXiv 固定论文文本。
- 柯蓝转交主张：其本地原件、源 ZIP/成员 CRC、401/404 源文件清点、历史 25 项检查、pdftotext 执行。
- Alice 推断：候选方法可复用、当前不值得安装、未来评测必须隔离答案键、论文抽取应采用 source-first 分层路径。
- 未运行或改变：候选源码、安装、模型、Docling、pdftotext、旧生产试验、ACK、定时器、窗口权限与 PR 状态。
