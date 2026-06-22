# 下一阶段多 AI 分工：投递管理闭环

日期：2026-06-12

## 当前基线

- 后端统一使用 `http://127.0.0.1:8003`。
- 前端统一使用 `http://127.0.0.1:5175`。
- 岗位发布主链路已具备：招聘者发布岗位 -> 管理端审核 -> 通过后 `active` -> 求职端公开岗位流读取 `listPublicJobs`。
- 管理端岗位审核已接真实待审岗位，并展示 AI 预审结果。
- 招聘者“我的岗位”失败时不再静默回退 mock。
- 未跟踪目录 `frontend/product-video/` 不属于当前任务，协作时不要误提交。

## 分工原则

- 每个 AI 只负责一个纵向闭环，避免多人同时改同一批文件。
- 后端先定义稳定 API 契约，前端按契约接入。
- Mock 只能用于未开工模块；已接真实接口的页面不允许静默回退 mock。
- 每个分支提交前至少跑对应测试或构建。

## Agent A：投递管理后端主链路

目标：完成求职者投递、招聘者查看投递、状态推进的后端闭环。

建议分支：`feature/applications-backend`

负责文件范围：

- `backend/job-platform/app/api/v1/applications.py`
- `backend/job-platform/app/modules/application/*`
- `backend/job-platform/app/main.py`
- `backend/job-platform/alembic/versions/*`
- `backend/job-platform/tests/test_api/test_applications.py`

API 契约建议：

- `POST /api/v1/applications`
  - 求职者对 `active` 岗位投递。
  - 禁止投递非 `active` 岗位。
  - 同一求职者对同一岗位不可重复投递。
- `GET /api/v1/applications/me`
  - 求职者查看自己的投递记录。
- `GET /api/v1/applications/recruiter`
  - 招聘者查看自己岗位收到的投递。
- `POST /api/v1/applications/{application_id}/status`
  - 招聘者推进状态：`viewed`、`interview_invited`、`rejected`、`hired`。
  - 只能操作自己岗位下的投递。
- `GET /api/v1/applications/admin`
  - 管理端后续审计用，可先做只读列表。

数据模型建议：

- `id`
- `job_id`
- `seeker_id`
- `recruiter_id`
- `status`
- `resume_snapshot`
- `cover_message`
- `reject_reason`
- `created_at`
- `updated_at`
- `viewed_at`
- `status_updated_at`

验收标准：

- 后端测试覆盖：投递成功、重复投递失败、非 active 岗位不可投、招聘者越权失败、状态推进成功。
- `pytest tests/test_api/test_applications.py -q` 通过。

## Agent B：投递管理前端接入

目标：把求职者投递和招聘者投递管理接到真实后端。

建议分支：`feature/applications-frontend`

依赖：Agent A 的 API 契约，后端可先 mock 但路径和字段必须固定。

负责文件范围：

- `frontend/wechat-prototype/src/services/applications.js`
- `frontend/wechat-prototype/src/services/index.js`
- `frontend/wechat-prototype/src/seeker/SeekerFlow.jsx`
- `frontend/wechat-prototype/src/seeker/SeekerExtra.jsx`
- `frontend/wechat-prototype/src/recruiter/RecruiterTalentPool.jsx`
- `frontend/wechat-prototype/src/recruiter/RecruiterPages.jsx`

页面改造：

- 求职者岗位详情页：
  - 只允许对真实 `active` 岗位投递。
  - 投递成功后显示已投递状态。
- 求职者“我的投递”：
  - 改为读取 `GET /api/v1/applications/me`。
- 招聘者候选人/投递列表：
  - 改为读取 `GET /api/v1/applications/recruiter`。
  - 支持推进状态。

验收标准：

- `npm run build` 通过。
- 后端断开时页面显示真实接口错误，不静默回退 mock。
- 一条 active 岗位可以完成：求职者投递 -> 招聘者看到 -> 招聘者推进状态。

## Agent C：岗位审核与提示词闭环

目标：把管理端岗位审核继续做完整，减少 mock 遗留。

建议分支：`feature/job-review-polish`

负责文件范围：

- `frontend/wechat-prototype/src/admin/AdminApp.jsx`
- `frontend/wechat-prototype/src/admin/AdminReview.jsx`
- `frontend/wechat-prototype/src/services/aiPrompts.js`
- `backend/job-platform/app/api/v1/ai_prompts.py`
- `backend/job-platform/app/modules/ai_prompt/*`

任务：

- `/admin/review/:id` 旧详情页仍是 mock，需要接真实岗位详情。
- 岗位驳回改为管理员填写原因，而不是固定文案。
- AI 预审提示词页面已有，下一步接真实模型调用。
- 模型调用失败时降级到当前规则引擎。

验收标准：

- 管理端岗位列表和详情页数据一致。
- 驳回原因能回写后端，招聘者端能看到。
- 提示词版本号能在审核结果里展示。

## Agent D：联调稳定性与去 mock 清单

目标：减少“看起来有数据但不是后端数据”的误判。

建议分支：`chore/integration-stability`

负责文件范围：

- `frontend/wechat-prototype/src/services/*`
- `frontend/wechat-prototype/src/seeker/*`
- `frontend/wechat-prototype/src/recruiter/*`
- `backend/job-platform/*.bat`
- `frontend/wechat-prototype/*.bat`
- `README.md`
- `docs/*`

任务：

- 给 API client 增加更清晰的网络错误提示。
- 文档统一端口：后端 `8003`，前端 `5175`。
- 标记仍然是 mock 的模块：
  - 批量导入岗位
  - 存草稿
  - 岗位暂停/恢复
  - 浏览量、留言数、UV
  - 聊天、通知、简历详情
- 每个 mock 模块写明“何时替换为真实接口”。

验收标准：

- 关键启动脚本和 README 不再出现旧端口 `8001/5174`。
- 已接真实接口的页面不会静默 fallback 到 mock。

## 推荐执行顺序

1. Agent D 先完成端口和联调文档清理。
2. Agent A 开投递后端。
3. Agent B 基于 Agent A 契约接前端。
4. Agent C 并行完善审核详情和提示词闭环。
5. 合并后做一次端到端验证：发布岗位 -> 审核通过 -> 求职者投递 -> 招聘者处理。

## 分支合并规则

- 不直接在 `main` 上多人同时开发。
- 每个 Agent 使用独立 feature 分支。
- PR 描述必须写：
  - 改动范围
  - 接口变化
  - 验证命令
  - 剩余 mock 点
- 合并前至少确认：
  - 后端相关改动跑 `pytest`
  - 前端相关改动跑 `npm run build`

