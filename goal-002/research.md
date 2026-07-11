## User Goal

Form and execute the `goal-002` P2 gap repair goal for the empty-job posting platform. The concrete repair scope is:

- Execute or create evidence for a live 12-step browser E2E flow.
- Close the RP401 demo coverage boundary: RP401 is deterministic Match Quality demo data, not full company/resume/contact-exchange coverage.
- Verify contact exchange through structured APIs and browser-visible evidence.
- Govern demo credentials so fixed credentials remain local/demo-only and are not reused as production configuration.

## Known Constraints

- Goal Mode is in manual single-task mode; execute at most one task per turn unless the user explicitly asks for auto-continuation.
- Do not read, print, modify, or exfiltrate local `.env` secrets. Environment checks may verify only that the target is local/demo.
- Do not run cleanup, seed, migration, service restart, or database write operations without confirming they are scoped to local/demo data.
- Existing Playwright scripts assume local services are running. Common defaults found in docs/scripts are backend `http://127.0.0.1:8004`, frontend `http://127.0.0.1:5174`, and in `manual-rp310-flow.cjs` frontend `http://127.0.0.1:5175`.
- `docs/HANDOFF.json` is the current-state handoff source. It says no active handoff task is pending, but records P2 residual risks relevant to this goal.

## Existing Context

### Current P2/P3 gaps from authoritative files

- `docs/HANDOFF.json` records P2: live 12-step browser E2E has not been executed as a single script; T006 is only a dry-run acceptance record and T010 defines the demo plan.
- `docs/HANDOFF.json` records P2: RP401 seed covers deterministic Match Quality outputs but not full company/resume/contact-exchange flow.
- `docs/HANDOFF.json` records P2: demo credentials must remain local/demo-only and must not be reused for production.
- `goal-001/audit.md` final audit confirms no unresolved P0/P1, but keeps the same live E2E, RP401 seed boundary, demo credential, Vite chunk-size, and AhaDiff CLI residual risks as P2/P3.
- `docs/audit/上线前技术体检_空岗发布平台.md` records `T008-FU-01` to execute live browser 12-step E2E after demo seed plan is finalized, and `T008-FU-03` to keep demo seed credentials scoped to local/demo only.
- `docs/acceptance/核心业务闭环验收_空岗发布平台.md` maps the 12-step acceptance flow and states live API/browser evidence still needs to be collected.
- `docs/demo/演示环境与样例数据方案.md` defines demo environment, sample data, manifest, rollback/cleanup rules, and current gaps.

### Existing scripts and coverage boundary

- `frontend/wechat-prototype/output/playwright/manual-rp310-flow.cjs`
  - Covers admin login, recruiter registration, company certification creation/review, job creation/review, seeker registration, resume upload and structured confirmation, public job view, match, favorite, application, Match Quality API check, and Match Quality admin page screenshots.
  - Does not cover conversation opening, sending messages, contact exchange request/review, structured contact visibility, or a 12-step manifest that marks evidence source for every step.
  - Uses fixed local credentials for admin login and generated recruiter/seeker phones.

- `backend/job-platform/scripts/seed_rp401_demo.py`
  - Seeds deterministic Match Quality data with `source=rp401_demo`, fixed local admin/recruiter/seeker credentials, two RP401 jobs, 240 demo seekers, match audits, downstream behavior for the healthy segment, and an experiment.
  - Writes `frontend/wechat-prototype/output/playwright/rp401-demo-seed.json`.
  - Cleanup is scoped to `source=rp401_demo`, related jobs/applications/favorites/visits/seeker users, and the RP401 demo experiment. It reuses or updates admin/recruiter/standard-position records.
  - It does not create company certification, resume/profile, conversation, or contact exchange evidence.

- `frontend/wechat-prototype/output/playwright/manual-rp401-demo-acceptance.cjs`
  - Reads `rp401-demo-seed.json`, logs in as the seeded admin, verifies `GET /api/v1/matches/quality/summary` by experiment/category/city, checks risk/healthy city segments, anomalies, draft tuning suggestions, and experiment confidence.
  - Captures `rp401-demo-quality-insights.png` and `rp401-demo-risk-city-filter.png`.
  - It is a Match Quality acceptance script only.

- `frontend/wechat-prototype/output/playwright/manual-rp401-match-quality-p1-flow.cjs`
  - Verifies the Match Quality P1 admin page and captures `rp401-quality-segments.png` and `rp401-quality-anomalies-suggestions.png`.
  - It does not seed or prove full business-loop coverage.

- Existing backend tests provide API-level evidence for related capabilities:
  - `backend/job-platform/tests/test_api/test_business_loop.py` includes conversation/contact-exchange paths.
  - `backend/job-platform/tests/test_api/test_messages.py` covers `POST /api/v1/messages/conversations/open`, `POST /api/v1/messages/contact-exchanges`, review, and stats summary.
  - `backend/job-platform/tests/test_api/test_resumes.py`, `test_jobs.py`, `test_applications.py`, and `test_matches.py` cover resume upload, jobs, applications, and quality summary behavior.

## Best Practices

- Treat RP401 data as seeded demo evidence only. It can prove Match Quality UI/API behavior, but cannot prove full live business-loop acceptance.
- The live 12-step E2E should emit a run manifest with run id, environment, API base, app base, created IDs, source classification, API reread checks, and screenshots.
- Contact exchange acceptance must use structured APIs: open conversation, send message if needed, request exchange, peer reviews/accepts, reread exchange/conversation, confirm structured contacts are visible only after acceptance.
- Demo credentials should be documented as fixed local/demo credentials, blocked from production reuse by existing production config validation and by script-level environment checks before seed/demo execution.
- Cleanup must dry-run or be manifest-based; never delete objects outside explicit demo prefixes, `source=rp401_demo`, or recorded IDs.

## Risks

- P2: Running existing scripts against the wrong database could create or clean data outside demo scope if environment checks are weak.
- P2: A combined live 12-step E2E may fail if local backend/frontend services are not running or ports differ from defaults.
- P2: Existing front-end demo/mock/fallback areas can produce visually plausible but non-launch evidence unless scripts classify source and fail on mock-only steps.
- P2: Fixed demo credentials in scripts are acceptable only for local/demo; screenshots or manifests should avoid encouraging production reuse.
- P3: Frontend build has a known Vite chunk-size warning; it is unrelated to the P2 gap repair but should remain recorded as residual optimization.

## Assumptions

- The next executable work should first add or adapt acceptance scripts and manifests under existing local patterns rather than introducing a new framework.
- Local service startup may be handled by the user or a later task; T001 is file inspection and planning only.
- No production credentials or production database access are required for this goal.
- Because `apply_patch` failed due to the Windows sandbox helper, goal-file updates in this turn use narrow PowerShell `Set-Content` writes.
