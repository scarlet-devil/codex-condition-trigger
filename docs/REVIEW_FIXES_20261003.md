# 静态复核后的三项修订

日期：2026-10-03（Asia/Shanghai）。执行：Alice，云端。状态：Draft / review_pending。

本轮输入是对固定提交 `9c658d6bffb16c53e8838f8432ac1e1319b6da6b` 的静态复核。开始前，当前 PR 仍指向该提交，15 个本地文件与其 Git blob 一致。静态报告没有执行候选；下述故障复现及修复测试由本轮实际运行，属于作者同一上下文自检 S0，不替代独立 Windows 验收。

## 复现、修复与回归

| 发现 | 旧版实测结果 | 修复 | 新回归 |
| --- | --- | --- | --- |
| P1：ACK 后旧轮询覆盖交付 | 确定性屏障放行后，delivered 分别回退为 completed、queued、uncertain | 同一 SQL UPDATE 原子排除 delivered 行，连同原证据及其他字段一起保护；dispatcher 返回实际终态 | 第二 SQLite 连接提交 ACK 后才放行旧 RPC；检查整行不变且 B 批次能继续投递 |
| P2：无关响应 ID 绕过截止时间 | 模拟时钟越过 deadline 后仍持续消费错误 ID；迟到的正确响应也被接受 | 取消息前和取消息后统一检查绝对 deadline | 连续错误 ID 有界退出；迟到正确响应拒绝；真实本地 watcher/代理替身进程收到 STOP 后退出 |
| P2：普通批次引用冒充回执 | ready 的首次投递被普通 user 引用拦成 completed；queued 引用也误关联 | sending 意图与完整投递文本一并持久化；仅对已发送流程中的批次做单个完整文本、唯一历史匹配 | 普通引用、带引用前缀/后缀的全文不关联；发送回执丢失后重启可匹配原文；多重全文匹配拒绝；旧库不补造原文 |

旧版定点运行 **7 个新增测试方法，全部失败**；含子例共 9 处断言失败。日志保存在 [review-20261003-before.txt](../evidence/review-20261003-before.txt)。旧版 deadline 复现采用有上限的消息替身，避免测试本身无限等待。

修订版完整运行 **44 项通过**：原有 33 个测试方法名称保留，新增 11 个。原测试 `test_running_and_completion_need_matching_user_message` 的正例改为使用真正投递的完整文本，符合修正后的关联契约。成功输出见 [test-results.txt](../evidence/test-results.txt)。新增测试位于 [test_review_regressions.py](../tests/test_review_regressions.py)。

## 可复跑方式

先按 README 安装依赖。旧版复现必须将 `trigger.py` 固定到上述旧提交，使用本修订的测试文件和合成配置；不要用含真实会话的状态目录。

```bash
PYTHONPATH=.:tests python -m unittest -v \
  test_review_regressions.AckRaceTests \
  test_review_regressions.RPCDeadlineTests \
  test_review_regressions.HistoryReceiptTests.test_unsent_user_reference_cannot_replace_first_dispatch \
  test_review_regressions.HistoryReceiptTests.test_queued_user_references_cannot_become_receipts
```

修订版完整回归：

```bash
python -m unittest discover -s tests -v
```

环境：Linux、Python 3.12.14、watchdog 6.0.0。失败日志只规范化了本轮工作目录前缀，保留断言、测试名与异常；成功日志直接保存本轮输出。所有 thread ID、文件和业务证据均为临时测试夹具。

## 仍然成立的限制

文本匹配是关联证据，不是宿主认证的投递来源证明。一次人工原样复制仍可能与实际原文混淆；宿主改写原文会漏匹配。使用稳定宿主消息关联字段仍待真实接口验证。旧库缺少 `dispatch_text` 的批次不会被回填猜测，参见 [兼容说明](INTEGRATION.md)。

统一 deadline 修复的是响应收件循环。它不为所有管道写入、文件 I/O 或宿主动作建立全局取消保证。STOP 也不取消已经接受的模型工作。

本轮实测的是 Linux 文件系统、SQLite 交错及 JSONL 协议替身。未执行真实 Codex 请求、模型回合、Windows/Desktop 原会话或原生工具继承测试。现有任务的切换不在此提交范围内。

## 初始 ZIP 的核验范围

作者侧重新核对了先前对话提供的 `codex-condition-trigger-public-20261003.zip`：29,661 字节，CRC 通过，15 个成员的 Git blob 与初始固定提交逐一相同。SHA-256 为 `10f684385fc68e763ce9d9a5e547b89265c648e1c4cebd5abc8bf33aa1596460`；机器可读结果见 [initial-archive-verification.json](../evidence/initial-archive-verification.json)。

这是对作者侧初始归档的补核，不是接收者对 ZIP 的独立回读，也不改变外部静态报告注明的可读性缺口。该旧 ZIP 不含本轮修复；本轮复核输入应固定到 PR 中记录的新提交。
