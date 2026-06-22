# R-P3-10 匹配质量运营看板 PRD

## 目标

基于 R-P3-07/R-P3-08 已沉淀的匹配审计数据，叠加求职者后续行为数据，为管理员提供匹配质量运营看板，用于观察不同规则版本、实验桶和时间范围下的匹配质量与转化表现。

## P0 范围

1. 后端提供管理员质量汇总接口。
2. 指标来源包含匹配审计、职位访问、职位收藏、职位投递。
3. 支持按规则版本、实验桶、日期聚合。
4. 支持 `rule_config_id`、`experiment_id`、`scope`、`template_key`、`created_from`、`created_to` 筛选。
5. react-admin 新增 `Match Quality` 页面，展示 KPI、规则版本表、实验桶表、日期趋势表。
6. 通过后端测试、前端构建和浏览器手工流程截图验收。

## 接口契约

```text
GET /api/v1/matches/quality/summary
```

Auth:

- `admin`

Query:

- `rule_config_id?: int`
- `experiment_id?: int`
- `scope?: string`
- `template_key?: string`
- `created_from?: datetime`
- `created_to?: datetime`

Response:

```json
{
  "filters": {
    "rule_config_id": 24,
    "experiment_id": null,
    "scope": null,
    "template_key": null,
    "created_from": "2000-01-01T00:00:00",
    "created_to": "2999-01-01T00:00:00"
  },
  "summary": {
    "match_count": 1,
    "avg_score": 90,
    "high_count": 1,
    "medium_count": 0,
    "low_count": 0,
    "favorite_count": 1,
    "application_count": 1,
    "visit_count": 1,
    "favorite_rate": 100,
    "application_rate": 100,
    "visit_rate": 100
  },
  "rule_versions": [],
  "experiment_buckets": {
    "control": {},
    "treatment": {}
  },
  "time_buckets": []
}
```

## 指标定义

- `match_count`：符合筛选条件的 `match_rule_match_audits` 记录数。
- `avg_score`：匹配审计 `overall_score` 平均值。
- `high_count / medium_count / low_count`：按审计 `level` 统计。
- `visit_count`：匹配审计中的 `(job_id, seeker_id)` 在 `job_visits` 中存在访问记录的审计数。
- `favorite_count`：匹配审计中的 `(job_id, seeker_id)` 在 `job_favorites` 中存在收藏记录的审计数。
- `application_count`：匹配审计中的 `(job_id, seeker_id)` 在 `job_applications` 中存在投递记录的审计数。
- `*_rate`：对应行为计数 / `match_count` * 100。

## 前端

页面：

```text
/admin-ra/match-quality
```

菜单：

- `Match Quality`

页面结构：

- 顶部筛选条：规则 ID、实验 ID、scope、template、创建时间范围。
- KPI：匹配数、平均分、高中低分布、访问/收藏/投递数和转化率。
- `Rule Versions`：按规则版本聚合。
- `Experiment Buckets`：control/treatment 聚合。
- `Daily Trend`：按日期聚合。

## 验收记录

```text
.\.venv\Scripts\pytest.exe -q tests\test_api\test_matches.py => 25 passed
$env:TMP='D:\tmp'; $env:TEMP='D:\tmp'; .\.venv\Scripts\pytest.exe -q => 157 passed
npm.cmd run build => passed (Vite chunk size warning only)
node frontend/wechat-prototype/output/playwright/manual-rp310-flow.cjs => ok
browser screenshots => output/playwright/rp310-quality-dashboard.png, output/playwright/rp310-quality-filtered.png
```

## 完成状态

R-P3-10 P0 已完成。后续可在 P1 增加显著性检验、分岗位/城市/职位类型分层、离线重算、规则调权建议和自动预警。
