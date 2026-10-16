# 共用 Hub 上传恢复：具体接入范围

状态：proposed；本轮用户已授权实现条件触发器的两项接入，尚未把共用 Hub 正式切换登记为批准。
来源：Alice 0d7f5761 接续要求、当前 Human 继续实现指令，以及本机核对 R2 真实代码。

## 已观察的阻点

条件触发器已有冻结 job、稳定 key、先 lookup、上传前持久 upload_uncertain、完整字节回读。
现有 Hub 普通材料 upload 的 provider metadata 没有预生成 id；其既存 DISPATCHING/AMBIGUOUS
操作明确 retry_allowed=false/replay_allowed=false。仅从同名搜索为空不能安全再次创建。
Hub 自身还校验 project enabled/identity/route、单文件 frame、操作摘要，并持久记录副作用；
直接在触发器进程读 Hub 凭据调用 Drive 会跳过这些门，因此不是本方案。

## 最小修改

1. 在隔离 Hub 候选增加一个版本化的材料恢复接口；原 v1 exchange/receipt/旧歧义记录不迁移、不放宽。
2. 新操作仍绑定原 project/identity/standard route 与一件冻结材料，校验现有单文件及大小限制；
   key、parent、名称、长度、内容哈希、原 manifest 摘要共同形成不可变请求摘要。
3. 首次操作通过原授权门后预留一个 Drive file ID，先持久记录该 ID 与摘要，再允许 create。
   同一 key 换摘要拒绝。任意恢复使用原 ID；不换 ID，不改名重建，不根据列表为空再创建。
4. lookup 查询准确 ID；创建仍使用此 ID（Google 保证已创建 ID 再建返回409而不重复）。
   403/网络失败/未知响应维持 unknown。readback 校验身份、父级、名称、完整字节。
5. condition 仅增加 stdio→原 Hub 的薄客户端，不持有凭据，不另建 OAuth、不直连 Drive。
   不自动写业务 ACK，不恢复 watcher。可用一个新合成文件验证服务端创建后丢弃响应、
   客户端重启再查回，确认同 ID/同字节/一次实际对象创建。

## 必须先完成的审查和验证

隔离测试：原项目门、身份/route/单文件限制、同键异摘要、进程中止边界、409、错误字节、
并发续传、旧 v1/AMBIGUOUS 不变。独立工程审查后形成准确补丁/备份/回退清单。
正式 Hub 若需新接口，只有新的明确共用 Hub 切换批准覆盖时才部署；其他项目不停服或
影响窗口须先写明。先准备可审结果，不因本说明批准正式切换或凭据更改。

真实 Windows 登录验收与此共用 Hub 安装是两种动作。登录前继续保持原生产 STOP/到期锁，
计划使用独立 dry 配置和一次固定截止登录触发，无模型、无上传、无业务 ACK。
