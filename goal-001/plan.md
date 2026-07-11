## Requirement Analysis

The full objective is a seven-part program for the current `D:\AIposition` empty-position publishing platform. Completion requires documented and verifiable deliverables for each part, not only a recommendation list.

### G1: P4 Intelligent Matching Planning And MVP Split

Required deliverables:

- P4 PRD for intelligent matching.
- API/interface contract.
- Data dependency map.
- Algorithm/rule boundary definition.
- Frontend/backend task split.
- Acceptance standards.

Planning constraints:

- Reuse P3 rule matching, audits, experiments, release governance, and Match Quality evidence as the foundation.
- Do not reclassify P3/R-P4-01 delivered features as pending.
- P4 MVP must explicitly decide what is in/out for vector recall, LLM explanation, hybrid scoring, offline evaluation, gray release, and recruiter-side candidate ranking.

### G2: Core Business Loop Acceptance

Required deliverables:

- Acceptance checklist for recruiter job publishing, seeker browse/search/application, recruiter candidate review, communication, and status flow.
- Defect list if any step fails.
- Automated/manual verification records.
- Repair task list for failures.

Planning constraints:

- Acceptance evidence must distinguish real API-backed flows from demo/mock pages.
- Existing business-loop docs, applications/messages/contact-exchange implementations, and local test accounts are starting points.

### G3: Match Quality Tuning Loop

Required deliverables:

- Operational process from quality issue discovery to rule adjustment to after/before verification.
- Definition of who can review/approve suggestions.
- Mapping from anomaly/tuning suggestion to rule edit, experiment, publish, and quality comparison.
- Acceptance evidence that the loop can be followed using current R-P4-01 outputs.

Planning constraints:

- Suggestions remain drafts; no automatic rule edits or releases without explicit governance.
- Sample status and confidence caveats must be preserved.

### G4: Pre-release Technical Audit

Required deliverables:

- Technical audit report covering migrations, permissions, data consistency, error handling, frontend build, API contract drift, logs, and sensitive information.
- Test/build evidence.
- Launch blockers and repair tasks.

Planning constraints:

- Audit must be evidence-based. Search results alone are not proof unless mapped to a requirement.
- Do not modify secrets or production configuration.

### G5: Base Data And Tag Governance Operationalization

Required deliverables:

- Operating workflow for standard position and tag add/edit/disable.
- Impact-check rules for jobs, seeker intent, structured resume profiles, search, and match quality segments.
- Admin acceptance checklist.

Planning constraints:

- Reuse existing `tag_ids` / `tag_refs` integration and base-data operation logs.
- Clarify what happens to existing business records when a tag or standard position is disabled.

### G6: Demo Environment And Sample Data

Required deliverables:

- Stable demo scenario definition.
- Sample data plan for company, jobs, seekers, resumes, match rules, applications, contact exchanges, and quality dashboard.
- Script/manual flow to prepare and verify demo data.

Planning constraints:

- Demo data may be artificial, but must be clearly separated from real acceptance evidence.
- Demo scripts should be repeatable and should not overwrite important local data without explicit approval.

### G7: Project Memory And Handoff Upgrade

Required deliverables:

- Workflow for updating `docs/HANDOFF.json`, PRDs, acceptance records, and collaboration docs.
- AhaDiff usage rule for generating project memory after major commits.
- Guidance for when Codex should use HANDOFF vs AhaDiff MCP vs narrative docs.

Planning constraints:

- AhaDiff is local memory, not a replacement for checked-in PRD or acceptance docs.
- HANDOFF remains the machine-readable current-state source.

## Execution Strategy

Execute the program in documentation and verification layers before implementation:

1. Product planning layer:
   - Create P4 intelligent matching PRD and interface/data/algorithm boundary documents.
   - This unlocks any future engineering implementation.

2. Acceptance layer:
   - Create and run core business loop acceptance.
   - Record defects as repair tasks instead of mixing fixes into acceptance.

3. Operational loop layer:
   - Convert Match Quality P1 into an operating procedure for tuning.
   - Link suggestions to rule edit, experiment, publish governance, and before/after quality comparison.

4. Engineering readiness layer:
   - Run pre-release technical audit.
   - Identify P0/P1 blockers before any release claim.

5. Operations and demo layer:
   - Formalize base data/tag governance.
   - Prepare stable demo data and scripts.

6. Memory and handoff layer:
   - Update HANDOFF/collaboration docs and AhaDiff workflow so future work can be resumed reliably.

## Success Criteria

[OK] P4 intelligent matching PRD exists and clearly states MVP in-scope and out-of-scope items.
[OK] P4 interface contract, data dependency map, and algorithm/rule boundary are documented.
[OK] P4 frontend/backend task package is independently executable and acceptance criteria are explicit.
[OK] Core business loop acceptance checklist exists and distinguishes real API-backed evidence from demo/mock evidence.
[OK] Core business loop verification evidence or defect/repair tasks are recorded.
[OK] Match Quality tuning loop is documented from issue discovery to rule adjustment to before/after validation.
[OK] Pre-release technical audit report exists with tests/build/inspection evidence and launch blockers.
[OK] Base data and tag governance workflow exists with impact checks and admin acceptance.
[OK] Demo data and demonstration workflow are documented with safe setup/rollback rules.
[OK] Project memory and handoff workflow documents when to update HANDOFF, when to run AhaDiff, and how to query project memory.
[OK] Final audit passes with no unresolved P0 or P1 risks.

## Validation Plan

Each task must provide at least one concrete evidence type:

- Document diff for PRD/contract/workflow deliverables.
- File inspection for source references and doc synchronization.
- Test command output for backend regression where behavior is verified.
- Build output for frontend readiness.
- Browser script output and screenshots for end-to-end acceptance.
- Manual verification record when automation is not yet available.

Minimum validation gates by area:

- G1: PRD/contract/data/boundary/task package reviewed against P3/R-P4-01 constraints.
- G2: E2E checklist mapped to available APIs/pages and either run or marked with defects.
- G3: Tuning loop can be simulated from existing Match Quality outputs without automatic rule changes.
- G4: backend targeted tests, frontend build, migration status, permission checks, and sensitive-log/config inspection.
- G5: base-data/tag governance workflow mapped to current APIs, UI pages, operation logs, and affected business records.
- G6: demo setup does not overwrite important data without explicit approval and can be verified by a script or checklist.
- G7: HANDOFF and AhaDiff workflow are documented and current MCP/config state is reflected accurately.

## Rollback Plan

- Documentation-only tasks: revert the specific document files changed by the task.
- Generated demo data/scripts: keep scripts idempotent where possible; include cleanup instructions before running destructive setup.
- Configuration changes: do not change secrets or production config in this goal without explicit approval.
- Code changes, if later tasks require them: keep changes scoped to the task, run targeted tests, and record rollback files in changelog.

## Risk Mitigation

- P1 scope creep in G1: require an explicit MVP/non-MVP table before any implementation task.
- P1 false acceptance in G2/G6: label evidence as real API-backed, seeded demo, or mock-only.
- P1 unsafe automatic tuning in G3: keep tuning suggestions as reviewable drafts and require rule version/release governance.
- P1 release-readiness gaps in G4: convert each blocker into a repair task before final completion.
- P2 repeatability issues in browser scripts: document ports, accounts, seed data, and screenshots.
- P2 stale handoff risk in G7: update HANDOFF only after a task has verified evidence, not based on intent.
