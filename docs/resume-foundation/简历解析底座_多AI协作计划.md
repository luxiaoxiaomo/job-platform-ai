# 简历解析底座多 AI 协作计划

本文用于协调 Codex 与 Claude 在同一个工作目录下开发简历解析底座。目标是避免重复改同一批文件、避免 Alembic 迁移冲突、避免前后端接口理解不一致。

## 总原则

- Codex 主负责后端底座、数据库迁移、API contract、后端测试。
- Claude 主负责前端体验、页面联调、字段映射评审、浏览器验证。
- 同一个阶段内，同一个文件只由一个 AI 修改。
- 后端迁移文件只由 Codex 创建，避免 Alembic revision 冲突。
- 前端页面文件默认由 Claude 修改，Codex 只提供接口约定和必要排障。
- 每个阶段先定 API contract，再并行开发。
- 阶段完成后统一跑后端测试、前端 build、手动上传简历验证。

## 当前基准文档

最终技术方案以这份为准：

- `docs/resume-foundation/简历解析底座技术设计.md`

任务协作和状态以这份为准：

- `docs/resume-foundation/简历解析底座_协作看板.md`

评审输入和参考资料：

- `docs/resume-foundation/简历解析底座_技术评审清单.md`
- `docs/architecture/设计遗漏检查清单.md`
- `docs/resume-foundation/STIC_表设计_核心表结构摘要.md`
- `STIC_AIGC_AI简历筛选功能说明书全新版本V1.3.docx`

如果参考文档与最终技术方案冲突，以 `docs/resume-foundation/简历解析底座技术设计.md` 为准。

## 阶段分工

### P0：当前可用性修复

目标：先修掉当前会影响测试体验的问题。

Codex 负责：

- 修复 `backend/job-platform/app/modules/resume/service.py` 的 `parsed_snapshot` 乱码。
- 明确上传返回的后端状态文案。
- 后端编译检查和相关测试。

Claude 负责：

- 简历画像页去掉误导性的 mock AI 文案。
- 上传页和个人中心展示真实简历状态。
- 前端构建验证。

P0 状态字段约定：

- P0 不新增复杂状态机字段，继续兼容当前 `GET /api/v1/resumes/me` 返回结构。
- P0 后端必须修复 `parsed_snapshot` 乱码，不临时关闭该字段。
- P0 前端可根据 `has_resume` 和 `resume.parsed_snapshot` 展示基础状态。
- P0 展示文案由前端负责映射，后端返回英文状态值时不返回中文状态。

P0 前端状态建议：

| 判断 | UI 状态 |
| --- | --- |
| `has_resume=false` | 未上传 |
| `has_resume=true` 且没有 P1 的 `latest_parse_run` | 已上传，等待解析能力接入 |
| 上传 API 报错 | 上传失败 |

文件边界：

- Codex 可改：
  - `backend/job-platform/app/modules/resume/service.py`
  - `backend/job-platform/app/modules/resume/schemas.py`
  - `backend/job-platform/tests/test_api/test_resumes.py`
- Claude 可改：
  - `frontend/wechat-prototype/src/seeker/SeekerPortrait.jsx`
  - `frontend/wechat-prototype/src/seeker/SeekerFlow.jsx`
  - `frontend/wechat-prototype/src/seeker/SeekerPages.jsx`
  - `frontend/wechat-prototype/src/services/resumes.js`

### P1：可追溯解析底座

目标：上传可追溯、解析有状态、原文可沉淀、chunk 可入库。

Codex 负责：

- 新增 Alembic 迁移：
  - `resume_uploads`
  - `resume_parse_runs`
  - `resume_extracted_texts`
  - `resume_chunks`
- 新增或扩展 SQLAlchemy models、schemas、repository、service。
- 上传接口返回 `{ resume, upload, parse_run }`。
- `.docx` 原文抽取。
- chunk 切分入库。
- 后端 API 测试。

Claude 负责：

- 根据新 API 改造前端上传体验。
- 展示上传历史、解析状态、原文预览。
- 浏览器联调并记录问题。

文件边界：

- Codex 可改：
  - `backend/job-platform/alembic/versions/*`
  - `backend/job-platform/alembic/env.py`
  - `backend/job-platform/app/modules/resume/*`
  - `backend/job-platform/app/api/v1/resumes.py`
  - `backend/job-platform/tests/test_api/test_resumes.py`
  - `backend/job-platform/tests/test_modules/*resume*`
- Claude 可改：
  - `frontend/wechat-prototype/src/services/resumes.js`
  - `frontend/wechat-prototype/src/seeker/*`

P1 API contract 由 Codex 先给出，Claude 按 contract 实现。

### P1 API Contract

P1 后端完成前，Claude 可以先按本节 mock 数据开发。

字段命名：

- 上传记录状态字段：`upload.status`
- 解析任务状态字段：`parse_run.status`
- `GET /api/v1/resumes/me` 的最新解析任务字段：`latest_parse_run`
- 不使用中文状态值，所有 API 状态值使用英文枚举。

`upload.status` 枚举：

| 值 | 含义 | 前端建议文案 |
| --- | --- | --- |
| `uploaded` | 文件已保存，未开始解析 | 已上传 |
| `processing` | 最新解析任务执行中 | 解析中 |
| `parsed` | 最新解析任务成功 | 已解析 |
| `failed` | 最新解析任务失败 | 解析失败 |

`parse_run.status` 枚举：

| 值 | 含义 | 前端建议文案 |
| --- | --- | --- |
| `pending` | 任务已创建，等待执行 | 等待解析 |
| `running` | 正在抽取原文或切 chunk | 解析中 |
| `succeeded` | 原文和 chunk 入库成功 | 解析完成 |
| `completed_with_errors` | 部分产物成功，部分失败 | 部分完成 |
| `failed` | 原文抽取或解析完全失败 | 解析失败 |

说明：

- 技术设计文档和 API contract 已统一使用 `completed_with_errors`。
- P1 阶段 `succeeded` 只代表上传历史、原文抽取、chunk 入库成功；不代表 AI 结构化解析已完成。
- P2 后才会出现结构化 JSON 和核心明细表的确认状态。

`GET /api/v1/resumes/me` 建议响应：

```json
{
  "has_resume": true,
  "resume": {
    "id": 12,
    "seeker_id": 1,
    "file_url": "/uploads/resumes/1_xxx.docx",
    "file_name": "王明雷简历.docx",
    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_size": 36212,
    "parsed_snapshot": "已上传简历文件，当前生成规则快照；后续可接入 AI 精细解析。",
    "created_at": "2026-06-15T10:00:00",
    "updated_at": "2026-06-15T10:00:00"
  },
  "latest_upload": {
    "id": 45,
    "status": "parsed",
    "original_file_name": "王明雷简历.docx",
    "file_ext": ".docx",
    "file_size": 36212,
    "created_at": "2026-06-15T10:00:00"
  },
  "latest_parse_run": {
    "id": 81,
    "status": "succeeded",
    "parser_version": "resume-parser-v1",
    "extractor": "docx",
    "error_message": null,
    "created_at": "2026-06-15T10:00:00",
    "finished_at": "2026-06-15T10:00:03"
  }
}
```

`POST /api/v1/resumes/me/upload` 建议响应：

说明：P1 当前采用同步本地解析，所以 `.docx` 上传成功后通常直接返回最终状态 `upload.status=parsed`、`parse_run.status=succeeded`。后续切换异步 worker 后，上传接口可能先返回 `processing/running`，前端需同时支持这两类状态。

```json
{
  "resume": {
    "id": 12,
    "seeker_id": 1,
    "file_url": "/uploads/resumes/1_xxx.docx",
    "file_name": "王明雷简历.docx",
    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "file_size": 36212,
    "parsed_snapshot": "已上传简历文件，当前生成规则快照；后续可接入 AI 精细解析。",
    "created_at": "2026-06-15T10:00:00",
    "updated_at": "2026-06-15T10:00:00"
  },
  "upload": {
    "id": 45,
    "status": "parsed",
    "original_file_name": "王明雷简历.docx",
    "file_ext": ".docx",
    "file_size": 36212,
    "created_at": "2026-06-15T10:00:00"
  },
  "parse_run": {
    "id": 81,
    "status": "succeeded",
    "parser_version": "resume-parser-v1",
    "extractor": "docx",
    "error_message": null,
    "created_at": "2026-06-15T10:00:00",
    "finished_at": "2026-06-15T10:00:03"
  }
}
```

`GET /api/v1/resumes/me/uploads?limit=20` 建议响应：

```json
[
  {
    "upload": {
      "id": 45,
      "status": "parsed",
      "original_file_name": "王明雷简历.docx",
      "file_ext": ".docx",
      "file_size": 36212,
      "created_at": "2026-06-15T10:00:00"
    },
    "latest_parse_run": {
      "id": 81,
      "status": "succeeded",
      "parser_version": "resume-parser-v1",
      "extractor": "docx",
      "error_message": null
    }
  }
]
```

`GET /api/v1/resumes/me/parse-runs/{parse_run_id}` 建议响应：

```json
{
  "upload": {
    "id": 45,
    "status": "parsed",
    "original_file_name": "王明雷简历.docx",
    "file_ext": ".docx"
  },
  "parse_run": {
    "id": 81,
    "status": "succeeded",
    "parser_version": "resume-parser-v1",
    "extractor": "docx"
  },
  "extracted_text": {
    "id": 12,
    "text_preview": "王明雷 PeopleSoft 技术顾问...",
    "quality_score": 0.6,
    "char_count": 4280
  },
  "chunks": [
    {
      "id": 101,
      "chunk_index": 0,
      "section": "raw",
      "content_preview": "王明雷 PeopleSoft 技术顾问...",
      "token_count": 260,
      "embedding_status": "pending"
    }
  ]
}
```

API 文档交付方式：

- Codex 会维护 Markdown contract，也会确保 FastAPI OpenAPI 可查看。
- 本协作文档中的 contract 是前端 mock 的依据。
- P1 后端完成后，以 `http://127.0.0.1:8003/docs` 和实际接口响应为准。

### P2：结构化 JSON 和核心明细表

目标：筛选功能可以后置，但筛选依赖的表底座提前建设。

Codex 负责：

- 新增：
  - `resume_structured_profiles`
  - `resume_basic_infos`
  - `resume_educations`
  - `resume_work_experiences`
  - `resume_projects`
  - `resume_skills`
  - `resume_certificates`
- 实现 JSON 到核心明细表的投影逻辑。
- 实现确认后回写 `seeker_profiles`。
- 新增 `resume_profile_change_logs`。
- 后端测试。

Claude 负责：

- 梳理 STIC 字段到我们字段的映射建议。
- 做解析结果确认页：左侧原文，右侧结构化字段。
- 标识字段置信度和待确认状态。
- 验证个人资料回写体验。

字段原则：

- JSON 是解析源结果。
- 明细表是业务查询投影。
- 每条明细记录必须包含 `seeker_id`、`upload_id`、`parse_run_id`。
- 低置信度字段先留在 JSON 或标记待确认，不强行进入明细表。

### P3：提示词、标签和关键词

目标：把 V1.3 的标签、关键词、匹配总结能力接入提示词管理。

Codex 负责：

- 扩展 `ai_prompt_configs` 的 `scenario_key` 类型。
- 后端接入场景：
  - `resume_structured_parse`
  - `resume_tag_extract`
  - `resume_keyword_extract`
  - `job_tag_extract`
  - `job_keyword_extract`
  - `match_summary`
- 新增：
  - `resume_tags`
  - `resume_keywords`
- 解析结果记录 prompt config/version。

Claude 负责：

- 管理端提示词配置页面补场景。
- 标签和关键词展示。
- 人工修正入口。
- 校验 JSON schema 是否易懂、可运营。

### P4：岗位解析、RAG 和人岗匹配

目标：从简历解析底座扩展到简历筛选和人岗匹配。

Codex 负责：

- `job_parsed_profiles`
- embedding 任务。
- pgvector 或 Qdrant 接入。
- `job_resume_match_records`
- `job_resume_match_details`
- 匹配分数、匹配理由、风险点后端逻辑。

Claude 负责：

- 招聘者端简历筛选页面。
- 匹配结果页。
- 筛选条件交互。
- 匹配解释展示。

## 协作流程

每个阶段按以下顺序执行：

1. Codex 更新 API contract 或数据库 contract。
2. Claude 基于 contract 做前端或字段映射。
3. Codex 跑后端测试。
4. Claude 跑前端 build 和浏览器验证。
5. 双方汇总问题，统一修复。
6. 通过后再进入下一阶段。

## 防冲突规则

- Alembic migration 只由 Codex 创建。
- `backend/job-platform/app/modules/resume/*` 默认 Codex 修改。
- `frontend/wechat-prototype/src/seeker/*` 默认 Claude 修改。
- `frontend/wechat-prototype/src/services/resumes.js` P1 由 Claude 修改，Codex 只提供返回结构。
- `docs/resume-foundation/简历解析底座技术设计.md` 由 Codex 维护，Claude 可以提出修改建议。
- 如果必须改对方负责文件，先在对话里说明具体文件和原因。

## 验证命令

后端：

```powershell
cd D:\AIposition\backend\job-platform
.\.venv\Scripts\python.exe -m py_compile app\modules\resume\service.py
.\.venv\Scripts\pytest.exe -q
```

前端：

```powershell
cd D:\AIposition\frontend\wechat-prototype
npm.cmd run build
```

联调：

```powershell
curl.exe -s http://127.0.0.1:8003/health
```

浏览器验证：

- 打开 `http://127.0.0.1:5175`
- 使用求职者账号登录。
- 上传 `.docx` 简历。
- 确认上传历史、解析状态、原文预览、画像页文案。

## 当前建议启动顺序

立即启动：

1. Codex 做 P0 后端和 P1 后端。
2. Claude 做 P0 前端和 P1 页面准备。

暂不启动：

- 岗位 JD 解析。
- embedding 和向量索引。
- 审计日志。
- 完整筛选页面。

这些放到 P3/P4，避免阻塞当前简历解析底座。
