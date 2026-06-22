# Claude P2 任务安排

这份清单给 Claude Code 使用。当前 P1 上传链路已经能测通，下一步进入 P2：结构化 JSON、核心明细表和确认页。Claude 只负责前端、字段映射和浏览器验证；后端表、迁移、投影 API 由 Codex 负责。

## 当前结论

P2 不做完整 AI 筛选，也不做向量匹配。P2 只解决一件事：把简历原文变成可确认、可追溯、可投影到明细表的结构化结果。

## Claude 任务

### R-P2-02：STIC 字段到核心明细表映射

Owner: Claude

目标：把 STIC/V1.3 里的字段压缩成我们 P2 真正要落库和展示的字段，不照搬大宽表。

交付物：

- 在 `docs/` 下输出字段映射文档。
- 明确每个字段属于哪个核心表：
  - `resume_basic_infos`
  - `resume_educations`
  - `resume_work_experiences`
  - `resume_projects`
  - `resume_skills`
  - `resume_certificates`
- 每个字段标注：
  - P2 必填 / P2 可选 / P3 后置
  - 是否需要用户确认
  - 是否适合后续筛选
  - 前端展示标签

不要做：

- 不要直接改后端 models 或 Alembic migration。
- 不要新增 STIC 大宽表。
- 不要把所有字段都列为 P2 必填。

验收：

- Codex 可以根据映射文档创建 P2 表字段和 schema。
- 字段数量控制在第一版可实现范围内。

### R-P2-04：解析结果确认页

Owner: Claude

目标：先做页面骨架和交互，等 Codex 给 API 后接真实数据。

页面建议：

- 左侧：原文预览。
- 右侧：结构化字段。
- 顶部：解析状态、解析时间、字段完整度。
- 字段级：置信度、待确认标记、编辑入口。
- 底部：确认回写、暂不确认、重新解析。

第一版字段：

- 基础信息：姓名、性别、手机号、邮箱、最高学历、工作年限、当前城市、目标岗位。
- 教育经历：学校、专业、学历、开始时间、结束时间。
- 工作经历：公司、职位、开始时间、结束时间、工作内容。
- 项目经历：项目名称、角色、时间、项目描述、职责。
- 技能：技能名称、等级、来源。
- 证书：证书名称、类型、获得时间。

不要做：

- 不要做真正 LLM 调用。
- 不要在前端硬编码“AI 已解析完成”。
- 不要直接覆盖 `seeker_profiles`。
- 不要修改后端投影逻辑。

验收：

- mock 数据下可以展示原文和结构化字段。
- 字段可以进入“待确认 / 已确认 / 低置信度”三种视觉状态。
- 用户能看懂哪些字段来自解析，哪些还未确认。

### R-P2-05：基础画像真实化前端

Owner: Claude，依赖 Codex 的 P2 后端 API。

目标：画像页只展示真实结构化数据，不再展示没有数据支撑的雷达图、AI 分数、薪酬建议。

第一版展示：

- 基础信息完整度。
- 教育/工作/项目/技能/证书摘要。
- 待确认字段数量。
- 简历原文和解析结果入口。
- 未接入能力说明：AI 匹配、薪酬建议、深度画像后置。

不要做：

- 不展示 mock 能力雷达图。
- 不展示 mock AI 匹配分。
- 不展示无来源的薪酬建议。

验收：

- 画像页的数据来源能追溯到 `resume_structured_profiles` 或核心明细表。
- 没有真实数据时显示空状态或待解析状态。

## 文件边界

Claude 可改：

- `frontend/wechat-prototype/src/seeker/*`
- `frontend/wechat-prototype/src/services/resumes.js`
- `frontend/wechat-prototype/src/services/*` 中和简历结构化相关的新 service
- `docs/*` 中字段映射文档

Claude 不改：

- `backend/job-platform/alembic/versions/*`
- `backend/job-platform/app/modules/resume/models.py`
- `backend/job-platform/app/modules/resume/service.py`
- `backend/job-platform/app/modules/resume/repository.py`
- `backend/job-platform/app/api/v1/resumes.py`

## 给 Claude 的当前开工顺序

1. 先做 `R-P2-02` 字段映射文档。
2. 同步给 Codex，等 Codex 定 P2 API contract。
3. 并行做 `R-P2-04` 确认页 mock UI。
4. API 出来后接真实数据。
5. 最后做 `R-P2-05` 基础画像真实化。

## 同步格式

Claude 每次同步只写：

```text
Owner: Claude
Doing:
Changed files:
Blocked by:
Next:
```

## Codex 已提供的 P2 API Contract

后端已经提供第一版 P2 接口，Claude 可以开始按真实 contract 做 mock/联调。

### 创建或更新结构化 JSON

```http
POST /api/v1/resumes/me/structured-profiles
```

请求：

```json
{
  "parse_run_id": 1,
  "schema_version": "resume-structured-v1",
  "source": "manual",
  "status": "needs_review",
  "confidence_score": 0.9,
  "structured_json": {
    "basic": {
      "name": "王明雷",
      "gender": "男",
      "highest_education": "硕士",
      "work_years": 12,
      "target_position": "PeopleSoft 技术顾问"
    },
    "education": [],
    "work_experiences": [],
    "projects": [],
    "skills": [],
    "certificates": []
  }
}
```

### 查询最新结构化结果

```http
GET /api/v1/resumes/me/structured-profiles/latest
```

返回包含：

- `profile`：结构化 JSON 和状态。
- `basic_info`：已投影的基础信息。
- `educations`
- `work_experiences`
- `projects`
- `skills`
- `certificates`

### 查询指定结构化结果

```http
GET /api/v1/resumes/me/structured-profiles/{profile_id}
```

### 投影到核心明细表

```http
POST /api/v1/resumes/me/structured-profiles/{profile_id}/project
```

请求：

```json
{
  "confirm": true,
  "min_confidence": 0.8
}
```

说明：

- `confirm=true` 时，结构化结果状态变为 `confirmed`。
- `min_confidence` 用于过滤低置信度数组项。
- 投影会清理该 `structured_profile_id` 下的旧明细，再写入新明细。

### 当前边界

- 后端只做 JSON 保存和规则投影。
- 不调用 LLM。
- 不直接覆盖 `seeker_profiles`。
- 字段映射仍需要 Claude 做 `R-P2-02` 评审，后端字段后续可按评审结果微调。
