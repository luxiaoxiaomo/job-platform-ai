## User Goal

The goal package contains seven workstreams for the current `D:\AIposition` empty-position publishing / recruitment platform:

- G1: turn P4 intelligent matching from a direction into an executable PRD and task package, including MVP scope, API contract, data dependencies, algorithm/rule boundaries, frontend/backend split, and acceptance standards.
- G2: run a full core business loop acceptance from recruiter job publishing through seeker browse/search/application, recruiter candidate review, communication, and status flow.
- G3: extend Match Quality from a dashboard into an operational tuning loop: discover quality issues, adjust rules, and verify before/after effect.
- G4: run a pre-release technical audit covering migrations, permissions, data consistency, error handling, frontend build, API contracts, logs, and sensitive information.
- G5: operationalize standard positions and tag governance, including add/disable rules, impact checks, and admin acceptance.
- G6: prepare stable demo data and scripts for end-to-end product demonstrations.
- G7: upgrade project memory and handoff by aligning AhaDiff, `docs/HANDOFF.json`, kanban, PRDs, and acceptance records.

## Known Constraints

- `docs/HANDOFF.json` is the current machine-readable truth source. It states that R-P3-01 through R-P3-10, P3 productization wrap-up, and R-P4-01 Match Quality P1 are done, with P4 intelligent matching deferred as a separate planning track.
- P3 boundaries are explicit in `docs/p3-match/P3_人岗匹配与规则配置产品化收尾.md`: P3 delivered rule-driven, configurable, auditable, publishable, observable matching governance. It explicitly did not include vector matching, embedding retrieval, LLM real-time scoring, LLM-generated explanations, automatic rule generation, automatic weight tuning, recruiter-side candidate ranking, complex RBAC, or approval workflows.
- R-P4-01 is already implemented and documented. Its hard constraints remain useful for G3: Match Quality P1 generates tuning suggestions only, does not automatically change rules, uses match audit data as the fact source, exposes sample status, and treats confidence as business heuristics rather than strict statistical significance.
- Existing browser acceptance scripts depend on local services, accounts, and seed data. P3 wrap-up notes that these should be organized into a more stable one-click acceptance baseline.
- Current worktree has `goal-001/` untracked. No application code changes were present before this goal task.

## Existing Context

### Authoritative Documents

- `docs/HANDOFF.json`
  - Current focus: R-P4-01 Match Quality P1 implementation is done; next step is product review or a new P4 intelligent matching planning track.
  - Verification evidence includes `tests/test_api/test_matches.py => 27 passed`, `npm.cmd run build => passed`, and `manual-rp401-match-quality-p1-flow.cjs => ok`.
  - No pending tasks are listed for Codex or Claude.

- `docs/p3-match/P3_人岗匹配与规则配置产品化收尾.md`
  - Confirms P3 completion and defines the P3/P4 boundary.
  - Lists key backend APIs such as `/api/v1/matches/jobs/{job_id}/me`, `/rule-configs`, `/rule-experiments`, `/audits`, `/rule-operation-audits`, and `/quality/summary`.
  - Lists admin routes such as `/admin-ra/match-rules`, `/admin-ra/rule-experiments`, `/admin-ra/match-audits`, `/admin-ra/rule-releases`, and `/admin-ra/match-quality`.
  - Identifies P4 candidates: Match Quality P1, release governance P1, permission governance P1, intelligent matching P4, and data operations P4.
  - Recommends P4 intelligent matching design as: vector recall, LLM explanation, hybrid scoring, offline evaluation set, and gray release plan, output as implementable PRD and interface contract.

- `docs/p3-match/R-P4-01_Match_Quality_P1_分层质量分析与调优建议_PRD.md`
  - Match Quality P1 has already been implemented, so G3 should not re-implement it. It should convert it into an operational loop.
  - Current P1 scope: segments, experiment confidence, anomalies, tuning suggestions, admin page, backend tests, build, and browser script.
  - Key data: match audits, job city, standard positions/categories, job tags, visits, favorites, applications, rule versions, and experiment buckets.
  - Key page: `/admin-ra/match-quality`.

- `docs/collaboration/AI协作机制_自动推进协议.md`
  - Defines `docs/HANDOFF.json` as the machine-readable handoff point.
  - Requires agents to read HANDOFF at startup, update status on completion, and use explicit `signals.pending_for_*`.
  - Relevant to G7.

- `docs/collaboration/标签库业务联动推进记录_2026-06-20.md`
  - Tags are integrated through `tag_ids` and `tag_refs` across jobs, seeker profiles, structured resume profiles, job search, and resume search.
  - Frontend uses `GET /api/v1/base-data/tags/public`.
  - Verification: 45 focused backend tests passed and frontend build passed.
  - Relevant to G5 and G6.

- `docs/collaboration/基础数据与通知后台测试文档_2026-06-20.md`
  - Defines admin test accounts and acceptance flows for standard positions, tags, operation logs, and push queue.
  - Notes real WeChat sending is not connected; current queue/provider readiness is preparatory.
  - Relevant to G5, G6, and G4.

- `docs/product/PRD评审报告_空岗信息发布对接平台v2.md`
  - The original PRD review identified the core business loop break: unclear final connection path and contact exchange.
  - Later notes say S3 was patched by defining first-phase successful connection as completed contact exchange, with `contact_exchange` event and acceptance AC-X-001/AC-X-002.
  - Relevant to G2.

- `docs/product/实施规划_真实业务闭环打通_空岗信息发布对接平台.md`
  - Defines the minimum real business loop and its acceptance steps.
  - Mentions real job, message, application, and recruiter processing paths.
  - Relevant to G2 and G6.

### Implementation Map

- Backend modules exist for the goal scope:
  - `backend/job-platform/app/modules/match`
  - `backend/job-platform/app/modules/application`
  - `backend/job-platform/app/modules/message`
  - `backend/job-platform/app/modules/base_data`
  - `backend/job-platform/app/modules/search`
  - `backend/job-platform/app/modules/notification`
  - `backend/job-platform/app/modules/resume`
  - `backend/job-platform/app/modules/seeker_profile`

- Match API implementation is in `backend/job-platform/app/api/v1/matches.py`.
  - `rg` confirmed routes for `/rule-configs`, `/rule-experiments`, `/rule-operation-audits`, `/quality/summary`, `/audits`, and `/matches/jobs/{job_id}/me`.
  - Match models include `match_rule_match_audits` and `match_rule_operation_audits`.
  - Match service includes quality audit filtering, behavior-pair aggregation, quality metrics, segments, experiment confidence, anomalies, and tuning suggestions.

- Frontend admin implementation exists under `frontend/wechat-prototype/src/admin-ra`.
  - `AdminRaApp.jsx` registers Match Audits and Match Quality.
  - `resources/match-quality/dashboard.jsx` contains Segments, Experiment Confidence, Anomalies, and Tuning Suggestions sections.

- Business loop implementation evidence:
  - Backend application models use `job_applications` with status and timeline support.
  - `frontend/wechat-prototype/src/services/applications.js` exposes seeker, recruiter, admin, stats, business-loop, deep-dive, and status APIs.
  - Recruiter talent pool pages distinguish real applications from demo talent pool cards.
  - Messaging services include conversations, messages, contact exchanges, and contact exchange review/stats.

- Demo/mock evidence:
  - Frontend still contains explicit demo/mock sections such as recruiter demo talent pool, original resume preview mock, demo insights, and mock service data.
  - This is relevant to G6: demo assets should be deliberate and separated from real acceptance data.

### Validation Evidence Identified

- Backend test files:
  - `test_matches.py` covers match/rule/audit/quality behavior and currently has the latest R-P4-01 evidence in HANDOFF: 27 passed.
  - `test_applications.py`, `test_business_loop.py`, `test_messages.py`, `test_notifications.py`, `test_base_data.py`, `test_jobs.py`, `test_resumes.py`, `test_search.py`, `test_seeker_profiles.py`, and related files cover adjacent goal areas.

- Browser/manual scripts and screenshots:
  - P3/R-P4 scripts: `manual-rp306-flow.cjs`, `manual-rp307-flow.cjs`, `manual-rp308-flow.cjs`, `manual-rp309-flow.cjs`, `manual-rp310-flow.cjs`, `manual-rp401-match-quality-p1-flow.cjs`, and `manual-rp401-demo-acceptance.cjs`.
  - R-P4 screenshots include `rp401-quality-segments.png`, `rp401-quality-anomalies-suggestions.png`, `rp401-demo-quality-insights.png`, and `rp401-demo-risk-city-filter.png`.
  - Base data/tag screenshots include `base-data-position-detail.png`, `base-data-tag-detail.png`, `base-data-tag-list.png`, and tag flow screenshots.

## Best Practices

- Treat `docs/HANDOFF.json` and current code/tests as authoritative over older planning notes.
- Preserve phase boundaries:
  - Do not relabel already completed P3/R-P4-01 implementation as pending work.
  - Do not mix P4 intelligent matching implementation into Match Quality P1.
  - Keep recommendations and automatic actions separate. Tuning suggestions may become rule drafts only after explicit product design and audit.
- For G1, define an MVP before implementation:
  - Data inputs: structured resume profile, seeker intent, job requirements/tags, standard positions, behavior data, existing rule audit data.
  - Algorithm boundary: baseline rule score remains explainable; vector/LLM components must be optional, auditable, and comparable.
  - Governance boundary: gray release and audit must reuse or extend P3 release/experiment infrastructure.
- For G2/G6, separate real acceptance data from demo/mock data. Demo flows can use seeded data, but acceptance claims must identify whether evidence is real API-backed or mock.
- For G4, use evidence-based audit: migrations, permissions, tests, build, API contracts, logs, sensitive config, and rollback plans.
- For G7, keep machine-readable state (`docs/HANDOFF.json`) separate from narrative docs, and record AhaDiff runs as local project memory rather than a replacement for PRD/acceptance docs.

## Risks

- P1: P4 intelligent matching can become too broad if vector recall, LLM explanation, hybrid scoring, offline evaluation, gray release, and recruiter-side ranking are planned as one undifferentiated build.
- P1: Existing Match Quality suggestions could be mistaken for automatic rule changes. Product copy and workflow must keep them as drafts until governance is designed.
- P1: Core business loop acceptance can give false confidence if demo/mock pages are mixed with real API-backed flows.
- P1: Data consistency and permission risks exist because the system spans jobs, applications, messages, contact exchanges, resumes, tags, match audits, notifications, and admin pages.
- P2: Existing browser scripts depend on local service ports, accounts, and seed data; repeatability is not yet a single command.
- P2: Tag governance has implementation evidence, but operational rules for adding/disabling tags and impact checks are not yet formalized.
- P2: AhaDiff MCP is registered, but project memory will be weak until meaningful AhaDiff runs are generated and referenced by the workflow.

## Assumptions

- The project root is `D:\AIposition`.
- The next executable goal task should be planning and task generation for the full G1-G7 package, not code implementation.
- Existing completed work should be reused and audited rather than rebuilt.
- If conflicts appear between older documents and `docs/HANDOFF.json`, prefer HANDOFF plus current code/tests, then record the inconsistency.
