# 原生结果与上传恢复接入计划

状态：implementation_ready / review_pending；真实Drive与登录未验收。基线：0d7f57616d0ca78e4b1d8ddf79deb238693328d9。
本机柯蓝；Class C / enhanced；来源：红魔“接下来按照这些继续做吧，推进到需要我真实登录告诉我”。
本记录同时承载设计、执行计划及验收边界，不重新批准既有目标。

## 已确定的实现边界

原生采集复用经过安装验证、owner 验证、完整历史 revision 核对的 Desktop IPC。
只投影准确 turnId 的终态，不记录消息正文。绑定 thread/cwd/batch/turn/manifest；
completed + error 或无法识别的结构保持 unknown；线程级 systemError 不推导任意回合失败。
结果以 evidence 摘要和原批次同事务登记；不得覆盖 delivered、冲突结果或并发改变的绑定。
`collect-outcomes` 为独立的一轮采集入口；正常 live 调度时自动调用同一采集函数。
STOP/到期时 watcher 不继续动作；明确执行采集入口只读取原生状态并保存结果，不恢复生产。

上传接入先核对现有 Hub 的权限、路由和恢复能力。核心继续使用已冻结的文件与
lookup/upload/readback 协议；真实后端必须在创建前持久绑定 Drive 预生成 ID，
恢复只核对该 ID；冲突/未知不换 ID，不上传第二份，不把名称搜索为空当创建许可。
只使用原有授权和目标；不得临时增加 OAuth 范围、修改凭据或另建目标。
Google 官方说明：预生成 ID 的重复创建返回 409，不生成重复文件：
https://developers.google.com/workspace/drive/api/guides/create-file#generate-ids
已安装 Hub 的普通 upload 目前不传预生成 ID，其歧义状态不能直接当安全重试；
先完成接口核定，不能将候选或合成替身描述为真实无人值守验收。

## 执行步骤

- [x] T1：原生状态投影及批次采集。先失败回归，再最小实现。覆盖失败与 task_complete
  共存、错 turn/manifest、未知结构、重复采集、并发 ACK 和原生接口失联。
- [x] T2（候选与离线/进程验证）：核定上传后端并接入持久对象身份。覆盖创建成功后响应丢失、进程重启、
  原 ID 查询与原字节读回、目标或源改变、并发重试、无凭据/审批拒绝。
- [x] T3（工程测试、复核及合成管道）：现有完整套件及独立 S1 工程复核；只读原生实测和独立小型合成上传验收，
  分别记录可证范围。旧业务文件、旧库、ACK、STOP、到期锁、PAUSED 不改。
- [ ] T4：更新同 Draft 的共用记录并全文回读。真实登录测试准备为独立 dry、固定截止、
  不启动模型的计划；到需要 Human 注销/登录时明确提示，届时再执行。

## 当前依赖与限制

条件触发器候选在独立 clone 中实施，旧候选只读；本记录仅承载本项目的实现与接续范围。
原实施工作目录来源保留于历史提交，不作为另一项目的任务入口或执行依据。
Python/watchdog 复用现有隔离环境。正式服务、生产调度、安装与合并不在本轮启动范围。
完整性 Active 27/27 于 2026-10-15T15:21:17Z 通过；固定治理 387c98a。

最新结果和未闭合动作见 [2026-10-16回执](KELAN_INTEGRATION_RECEIPT_20261016.md)。
