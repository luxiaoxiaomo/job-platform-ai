## Requirement Analysis

`goal-002` must turn the residual P2 findings from `goal-001` into verified acceptance evidence. The required final state is not only documentation: the repository needs executable or explicitly runnable evidence for the live 12-step business loop, RP401 demo boundary, contact exchange, and demo credential governance.

Concrete requirements:

- Live 12-step E2E evidence exists as a single runnable flow or an equivalent scripted acceptance flow with a manifest.
- RP401 demo evidence is kept scoped to Match Quality and cannot be mistaken for full company/resume/contact-exchange coverage.
- Contact exchange is verified through the structured conversation/contact-exchange APIs and, where practical, browser-visible evidence.
- Demo credentials remain local/demo-only, are documented, and are guarded before seed/demo scripts run.
- HANDOFF/goal docs are synchronized after implementation and validation.

## Execution Strategy

1. Extend or create a Playwright/manual acceptance script from `manual-rp310-flow.cjs` to cover the missing 12-step loop and contact exchange, preserving existing API helper patterns.
2. Add a run manifest format under `frontend/wechat-prototype/output/playwright/` that records created IDs, source classification, API reread checks, screenshots, and known gaps.
3. Add explicit environment/demo-scope guardrails to RP401/demo scripts or a shared preflight where it fits existing code style.
4. Run focused backend API tests for messages/business-loop and run the acceptance script against local services when services are available.
5. Update demo/acceptance/HANDOFF documentation only after validation evidence is collected.

## Success Criteria

[OK] P2 gaps from current HANDOFF/final audit are enumerated in `goal-002/research.md`.
[OK] Existing demo/browser/API scripts and their coverage boundaries are mapped in `goal-002/research.md`.
[OK] Required validation evidence is identified before implementation starts.
[OK] A live 12-step acceptance script or equivalent scripted flow verifies company, job, seeker, resume/profile, match, favorite/application, conversation, contact exchange, status/summary, and Match Quality evidence against local/demo services.
[OK] RP401 demo artifacts clearly identify seeded Match Quality evidence and do not claim full business-loop coverage.
[OK] Contact exchange evidence includes request, peer review accept, reread, and accepted structured contact visibility.
[OK] Demo credential governance prevents production reuse claims and documents local/demo-only scope.
[OK] Final validation records commands, outputs, screenshots/manifests, and any residual P2/P3 risks.

## Validation Plan

- File inspection: `docs/HANDOFF.json`, `goal-001/audit.md`, `docs/audit/上线前技术体检_空岗发布平台.md`, `docs/demo/演示环境与样例数据方案.md`, and relevant scripts.
- Backend focused tests: message/contact-exchange and business-loop API tests, at minimum `tests/test_api/test_messages.py` and `tests/test_api/test_business_loop.py` when implementation touches those surfaces.
- Browser/API acceptance: run the new or updated live 12-step script against local/demo backend and frontend.
- RP401 acceptance: run or inspect `seed_rp401_demo.py`, `manual-rp401-demo-acceptance.cjs`, and generated `rp401-demo-seed.json`/screenshots as needed.
- Documentation validation: parse `docs/HANDOFF.json`, scan new/updated docs for TODO/TBD placeholders, and record evidence in goal files.

## Rollback Plan

- Script changes: revert only the new/modified files under `frontend/wechat-prototype/output/playwright/` and `backend/job-platform/scripts/`.
- Documentation changes: revert affected files under `docs/` and `goal-002/`.
- Demo data: use only manifest-recorded IDs or existing `source=rp401_demo` cleanup boundaries; do not run cleanup outside local/demo scope.
- If local services are unavailable, keep implementation changes but mark runtime validation incomplete rather than claiming live acceptance.

## Risk Mitigation

- Add local/demo preflight checks before any seed or cleanup operation.
- Keep generated manifests free of production secrets; mask or avoid storing passwords unless the existing script explicitly outputs demo credentials and docs mark them local-only.
- Fail acceptance if a step relies on mock-only/fallback evidence.
- Prefer extending existing scripts over adding a new framework to reduce setup risk.
- Stop before destructive cleanup or service restarts unless the user explicitly approves them.
