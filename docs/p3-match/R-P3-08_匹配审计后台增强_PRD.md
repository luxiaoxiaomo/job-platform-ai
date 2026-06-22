# R-P3-08 匹配审计后台增强 PRD

## 目标

把 R-P3-07 已经落库的匹配审计记录，从实验效果页里的附属列表，升级成可独立检索、可查看详情、可追溯规则计算过程的后台工具。

## P0 范围

1. 后端增强 `GET /api/v1/matches/audits`：
   - 支持 `job_id`
   - 支持 `seeker_id`
   - 支持 `rule_config_id`
   - 支持 `experiment_id`
   - 支持 `experiment_bucket=control|treatment`
   - 支持 `created_from` / `created_to`
2. 新增单条详情接口：
   - `GET /api/v1/matches/audits/{audit_id}`
3. 审计响应补充摘要：
   - 岗位摘要：`job.id/title/city`
   - 求职者摘要：`seeker.id/display_name`
   - 规则摘要：`rule_config.id/name/version/status`
   - 实验摘要：`experiment.id/name/status`
4. 维度快照增强：
   - `key`
   - `label`
   - `score`
   - `configured_weight`
   - `effective_weight`
   - `weighted_score`
   - `matched`
   - `missing`
   - `explanation`
5. react-admin 新增 `Match Audits` 页面：
   - 支持岗位、求职者、规则、实验、bucket、时间范围筛选
   - 支持列表查看
   - 支持打开单条详情
   - 展示维度快照表

## 非范围

- 不做审计导出。
- 不做批量重算。
- 不做投递/收藏/转化质量指标聚合，这部分进入 R-P3-10。
- 不新增复杂权限，仍然仅 `admin` 可访问。

## 验收

```text
.\.venv\Scripts\pytest.exe -q tests\test_api\test_matches.py => 23 passed
$env:TMP='D:\tmp'; $env:TEMP='D:\tmp'; .\.venv\Scripts\pytest.exe -q => 155 passed
npm.cmd run build => passed (Vite chunk size warning only)
browser flow => output/playwright/rp308-audit-list.png, output/playwright/rp308-audit-detail.png
```
