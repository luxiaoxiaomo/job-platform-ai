# R-Stats/R-Notify/R-Search/R-AI-Cover/R-Admin 完成记录

日期：2026-06-19

## 完成范围

1. R-Stats-02 统计看板深化
   - 新增招聘者/管理员 deep-dive 统计接口。
   - 支持 7-30 天趋势、岗位排行、投递状态分布。
   - 招聘者统计页接入真实趋势和 Top 岗位数据。

2. R-Notify-04 推送 worker / 摘要生成
   - 新增到期推送任务 worker。
   - 支持 pending/deferred/digest_placeholder 处理。
   - 摘要占位任务会生成摘要 payload 并标记 sent。
   - 管理后台推送队列增加“运行 worker”按钮。

3. R-Search-01 AI/语义搜索 MVP
   - 新增 `/api/v1/search/jobs` 和 `/api/v1/search/resumes`。
   - 当前采用 `keyword_semantic_fallback`，基于岗位/简历结构化字段和 chunk 做规则相关度评分。
   - 求职者首页搜索接入后端搜索；无后端结果时保留本地筛选兜底。

4. R-AI-Cover-01 投递时 AI 求职信 MVP
   - 新增 `/api/v1/applications/cover-letter/suggest`。
   - 后端基于岗位、简历画像、技能生成可编辑求职信建议。
   - 投递确认页增加“AI 求职信”编辑区和生成按钮。
   - 投递时提交当前求职信内容到 `cover_message`。

5. R-Admin-Product-01 后台资源管理继续产品化
   - 新增 `/api/v1/users/admin` 管理员用户列表接口。
   - 支持角色筛选、分页、手机号解密展示。
   - 管理后台“用户管理”从 mock 列表改为真实 API 数据。

## 验证结果

后端组合回归：

```powershell
.venv\Scripts\pytest.exe tests\test_api\test_business_loop.py tests\test_api\test_notifications.py tests\test_api\test_search.py tests\test_api\test_applications.py tests\test_api\test_users.py -q
```

结果：33 passed。

前端构建：

```powershell
npm.cmd run build
```

结果：通过。Vite 仍提示部分 chunk 超过 500 kB，这是 react-admin 等历史依赖导致的体积 warning，不影响本次功能验证。

## 后续建议

- R-Search 后续可接 embedding/vector_ref，把当前 `keyword_semantic_fallback` 升级为真实向量检索。
- R-AI-Cover 后续可接 LLM 配置和 prompt 版本管理，目前是规则兜底生成。
- R-Notify 后续可接真实微信模板消息发送 provider，并补失败重试策略。
- R-Admin 后续可继续把岗位库、标签库、用户详情、权限动作产品化。
