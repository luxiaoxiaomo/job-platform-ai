# R-P4-01 Match Quality P1 分层质量分析与调优建议 PRD

## AI 速读卡

- 产品目标：在 R-P3-10 质量看板基础上，回答“哪类岗位、城市、规则版本或实验桶质量变差，以及应该先调哪里”。
- 目标用户：平台管理员、规则运营；P0 仍沿用现有 `admin` 权限。
- P0 范围：质量分层、AB 基础显著性判断、低质量异常提示、规则调权建议草案、管理端质量洞察页。
- 主页面：复用并增强 `/admin-ra/match-quality`，新增 Segments、Experiment Confidence、Anomalies、Tuning Suggestions 四块。
- 关键数据：匹配审计、岗位城市、标准职位/职位类目、岗位标签、访问/收藏/投递行为、规则版本、实验桶。
- 关键接口：增强 `GET /api/v1/matches/quality/summary`，可选新增 `GET /api/v1/matches/quality/insights`。
- 主要风险：样本量不足导致误判、行为转化延迟、分层维度过细、把建议误解为自动调权。
- 验收摘要：后端测试覆盖分层/显著性/异常/建议；前端 build 通过；浏览器脚本完成筛选、洞察查看和截图。

## 第一章：背景与目标

### 1.1 当前背景

P3 已完成规则驱动的人岗匹配治理闭环。R-P3-10 已经提供基础匹配质量看板，管理员可以看到：

- 匹配量、平均分、高中低分布。
- 访问、收藏、投递数量和转化率。
- 按规则版本聚合。
- 按实验桶聚合。
- 按日期趋势聚合。

当前缺口不在于“有没有质量数据”，而在于“质量数据如何指导运营动作”。当某个规则发布后，管理员仍需要人工判断：

- 是哪个城市、职位类目或岗位标签拖低了整体质量。
- 实验 treatment 是否真的优于 control，还是只是样本太少。
- 哪些维度经常高分但低转化，可能是假阳性。
- 哪些维度经常低分但仍高转化，可能是假阴性。
- 下一步应该先调技能、城市、薪资、经验还是岗位意向权重。

### 1.2 产品目标

`硬约束` R-P4-01 的目标是在现有 R-P3-10 基础上扩展 Match Quality P1，不重做规则系统、不引入向量或 LLM 匹配：

1. 管理员可以按城市、标准职位类目、标准职位、岗位标签、规则版本、实验桶查看质量分层。
2. 系统可以对 AB 实验 control/treatment 做基础显著性判断，至少指出样本不足、差异方向和可用置信状态。
3. 系统可以识别低质量异常分层，例如投递率显著低于全局、低分占比过高、样本量突然下降。
4. 系统可以生成规则调优建议草案，但不自动修改规则。
5. 管理端页面能把“看数据”推进到“知道优先排查什么”。

### 1.3 设计原则

- `硬约束` 继续以 `match_rule_match_audits` 为质量分析事实源，不能绕过审计数据直接拼页面指标。
- `硬约束` 调权建议只能是建议草案，不得自动创建新规则版本，不得自动发布。
- `硬约束` 显著性判断必须暴露样本量和判断状态，不得只给“胜出/失败”的绝对结论。
- `推荐默认` P0 先做轻量统计和规则启发式建议，不引入独立 OLAP、离线特征平台或机器学习训练任务。
- `推荐默认` 页面复用 `/admin-ra/match-quality`，避免新增一个割裂的质量系统。
- `发挥空间` 前端可以在布局、排序、图表表达上优化，但不得隐藏样本不足和数据延迟提示。

## 第二章：用户角色与使用场景

### 2.1 用户角色

| 角色 | 当前系统角色 | P0 权限 | 说明 |
| --- | --- | --- | --- |
| 平台管理员 | `admin` | 查看质量洞察、筛选、查看建议、跳转规则/审计/实验页面 | P0 唯一可访问角色 |
| 规则运营 | 暂无独立角色 | 不单独实现 | P1/P4 可拆成 `rule_operator` |
| 规则审核 | 暂无独立角色 | 不单独实现 | P1/P4 可拆成 `rule_reviewer` |
| 招聘者 | `recruiter` | 无 | 不提供跨平台质量洞察 |
| 求职者 | `seeker` | 无 | 不展示后台质量指标 |

### 2.2 使用场景

#### 场景 A：规则发布后排查质量下降

- 入口：`/admin-ra/match-quality`
- 前置：某个 active 规则在最近 7 天有匹配审计和行为数据。
- 流程：管理员选择规则版本和时间范围，查看整体 KPI，再按城市、职位类目、岗位标签分层。
- 结果：页面指出低质量分层，例如“上海 / 技术类岗位投递率低于全局 8.5 个百分点，样本 120，建议检查 skill 与 salary 维度”。

#### 场景 B：判断 AB 实验 treatment 是否值得发布

- 入口：Rule AB Tests 或 Match Quality。
- 前置：实验存在 control/treatment 审计数据。
- 流程：管理员选择实验 ID，查看 control/treatment 的投递率、收藏率、平均分和显著性状态。
- 结果：页面给出“样本不足 / treatment 暂优但未达阈值 / treatment 明显优于 control / treatment 可能变差”等状态。

#### 场景 C：识别规则假阳性和假阴性

- 入口：Match Quality 的 Tuning Suggestions。
- 前置：存在维度快照和后续行为数据。
- 流程：系统聚合维度得分与行为结果，找出高分低转化、低分高转化的维度。
- 结果：页面给出建议草案，例如“skill 维度高分样本投递率低于总体，建议检查技能词命中是否过宽”。

#### 场景 D：数据不足时避免误判

- 入口：任何质量洞察区域。
- 前置：筛选条件过窄，样本量低于最小阈值。
- 流程：管理员查看结果。
- 结果：页面显示样本不足，不展示强结论，只显示原始指标和建议扩大时间范围。

## 第三章：范围与非范围

### 3.1 P0 范围

`硬约束` P0 必须包含：

1. 质量分层聚合：
   - `city`
   - `standard_position.category`
   - `standard_position.name`
   - `job.tags`
   - `rule_config_id`
   - `experiment_bucket`
2. 分层指标：
   - `match_count`
   - `avg_score`
   - `high_count / medium_count / low_count`
   - `visit_count / visit_rate`
   - `favorite_count / favorite_rate`
   - `application_count / application_rate`
   - `low_score_rate`
3. AB 基础判断：
   - control/treatment 样本数。
   - conversion delta。
   - avg score delta。
   - 样本量状态。
   - 简化置信状态。
4. 异常提示：
   - 低投递率。
   - 低收藏率。
   - 低分占比高。
   - 匹配量异常下降。
   - 高分低转化。
5. 调权建议草案：
   - 建议类型。
   - 关联维度。
   - 证据指标。
   - 影响分层。
   - 建议动作。
   - 置信等级。
6. 管理端增强：
   - Segments 表。
   - Experiment Confidence 区块。
   - Anomalies 列表。
   - Tuning Suggestions 列表。
7. 后端测试、前端 build、浏览器脚本验收。

### 3.2 P1/P4 延后范围

`推荐默认` 以下能力不进入本 P0：

- 招聘者反馈、面试、通过/拒绝等后链路指标。
- 定时任务生成日报/周报。
- 自动通知或飞书告警。
- 自动创建规则版本。
- 自动发布或自动回滚。
- 多角色审批流。
- 复杂统计显著性库、贝叶斯实验分析、MDE 样本量规划。
- 离线批量重算历史样本。

### 3.3 非范围

`硬约束` 本 PRD 不做：

- 向量召回、embedding、语义匹配。
- LLM 实时评分。
- LLM 自动生成规则。
- LLM 自动调权。
- 招聘者侧候选人排序。
- 新建独立 BI 系统。

P4 智能匹配可以单独立项，但不能混入 R-P4-01 的 P0 实现。

## 第四章：核心流程与状态机

### 4.1 质量洞察主流程

1. 管理员打开 `/admin-ra/match-quality`。
2. 页面默认加载最近 14 天全局质量数据。
3. 管理员选择规则版本、实验、城市、职位类目、岗位标签或日期范围。
4. 前端调用质量洞察接口。
5. 后端读取匹配审计，并关联岗位、标准职位、行为数据。
6. 后端返回 summary、segments、experiment_confidence、anomalies、tuning_suggestions。
7. 页面按风险优先级展示洞察。
8. 管理员可以跳转到规则详情、实验详情或匹配审计列表进一步排查。

### 4.2 样本量状态

`硬约束` 每个分层和实验判断必须返回 `sample_status`：

| 状态 | 条件 | 页面行为 |
| --- | --- | --- |
| `insufficient` | `match_count < 30` 或任一实验桶 `< 30` | 不给强结论，提示扩大时间范围 |
| `limited` | `30 <= match_count < 100` | 给趋势判断，但标注置信较弱 |
| `usable` | `match_count >= 100` | 可展示异常和建议 |

`推荐默认` 阈值 P0 固定为 30/100，后续可配置化。

### 4.3 实验置信状态

| 状态 | 含义 |
| --- | --- |
| `not_applicable` | 未选择实验或无 control/treatment 数据 |
| `insufficient_sample` | 样本不足 |
| `treatment_likely_better` | treatment 转化率高于 control，差值达到最小业务阈值 |
| `treatment_likely_worse` | treatment 转化率低于 control，差值达到最小业务阈值 |
| `no_clear_difference` | 样本可用但差异未达到阈值 |

`推荐默认` P0 使用业务阈值而不是复杂统计库：

- application_rate delta >= 3 个百分点，判定为明显业务差异。
- favorite_rate delta >= 5 个百分点，作为辅助证据。
- avg_score delta >= 5 分，作为解释性证据，不单独决定胜负。

### 4.4 异常状态

异常按 severity 返回：

| severity | 条件示例 | 处理建议 |
| --- | --- | --- |
| `high` | 可用样本下投递率低于全局 5 个百分点以上，或低分占比高于全局 15 个百分点以上 | 优先排查 |
| `medium` | 样本有限但趋势较差，或单项指标异常 | 观察并扩大样本 |
| `low` | 轻微波动或仅提示信息 | 可暂不处理 |

## 第五章：页面与交互设计

### 5.1 Match Quality 增强页

- 路由：`/admin-ra/match-quality`
- 菜单：沿用 `Match Quality`
- 页面目标：从基础看板升级为质量洞察页。

#### 筛选区

字段：

- Rule Config ID
- Experiment ID
- Scope
- Template
- City
- Position Category
- Standard Position
- Job Tag
- Created From
- Created To

动作：

- Apply
- Reset
- Open Audits
- Open Rule
- Open Experiment

失败路径：

- 接口 403：显示无权限，不展示数据表。
- 接口失败：保留筛选条件，显示重试按钮。
- 日期格式错误：前端阻止提交，提示使用 ISO 时间或日期。

#### KPI 区

沿用 R-P3-10 指标，并新增：

- Low Score Rate
- Sample Status
- Segment Count
- Anomaly Count
- Suggestion Count

#### Segments 表

用户目标：找出哪个分层表现好或差。

展示字段：

- Segment Type
- Segment Key
- Segment Label
- Match Count
- Avg Score
- Low Score Rate
- Visit Rate
- Favorite Rate
- Application Rate
- Delta vs Overall
- Sample Status
- Risk Level

动作：

- 按 Application Rate、Low Score Rate、Match Count 排序。
- 点击分层行，把该分层条件带入筛选。
- 跳转 Match Audits 查看该分层审计。

空状态：

- 无审计数据：显示 `No quality segment data.`
- 分层字段缺失：显示 `Unclassified`，不得丢弃样本。

#### Experiment Confidence 区

用户目标：判断实验是否值得继续、暂停或发布 treatment。

展示字段：

- Experiment ID
- Control Match Count
- Treatment Match Count
- Control Application Rate
- Treatment Application Rate
- Application Rate Delta
- Avg Score Delta
- Confidence Status
- Decision Hint

动作：

- Open Experiment
- Open Release Page
- Open Audits

失败路径：

- 未选择实验：显示“选择 Experiment ID 后展示实验判断”。
- 只有一个 bucket：显示 `not_applicable`，提示检查实验流量或样本。

#### Anomalies 列表

用户目标：快速知道需要排查的质量风险。

展示字段：

- Severity
- Type
- Segment
- Evidence
- Metric Delta
- Sample Status
- Suggested Next Action

动作：

- Filter by Segment
- Open Audits
- Open Rule Compare

#### Tuning Suggestions 列表

用户目标：拿到规则调优草案。

展示字段：

- Suggestion Type
- Dimension Key
- Priority
- Affected Segment
- Evidence
- Proposed Action
- Confidence
- Guardrail

建议类型：

- `lower_weight`
- `raise_weight`
- `narrow_logic`
- `broaden_logic`
- `review_dimension`
- `run_experiment`

`硬约束` 每条建议都必须显示 `Guardrail`：例如“仅生成草案，不自动修改规则；请通过规则编辑页创建新版本并走发布治理”。

## 第六章：数据模型与指标定义

### 6.1 数据来源

现有数据源：

- `match_rule_match_audits`
- `match_rule_configs`
- `match_rule_experiments`
- `jobs`
- `standard_positions`
- `job_visits`
- `job_favorites`
- `job_applications`

P0 不要求新增持久化表。后续如性能不足，可新增日级聚合表：

```text
match_quality_daily_segments
```

但该表不是 P0 硬要求。

### 6.2 响应模型建议

新增或扩展 schema：

```text
MatchQualitySegmentResponse
MatchQualityExperimentConfidenceResponse
MatchQualityAnomalyResponse
MatchQualityTuningSuggestionResponse
```

建议在 `MatchQualityDashboardResponse` 中新增字段：

```json
{
  "segments": [],
  "experiment_confidence": null,
  "anomalies": [],
  "tuning_suggestions": []
}
```

### 6.3 指标定义

`match_count`:

- business meaning: 当前筛选条件下产生的匹配审计数量。
- numerator: `count(match_rule_match_audits.id)`。
- denominator: 无。
- data source: `match_rule_match_audits`。
- refresh cadence: 请求时实时计算。
- caveats: 同一求职者重复打开同一岗位会产生多条审计时，P0 按审计条数计算。

`application_rate`:

- business meaning: 匹配样本中发生投递行为的比例。
- numerator: 审计样本中的 `(job_id, seeker_id)` 在 `job_applications` 存在记录的数量。
- denominator: `match_count`。
- data source: `match_rule_match_audits`, `job_applications`。
- refresh cadence: 请求时实时计算。
- caveats: 投递可能晚于匹配发生，短时间窗口会低估转化。

`favorite_rate`:

- business meaning: 匹配样本中发生收藏行为的比例。
- numerator: 审计样本中的 `(job_id, seeker_id)` 在 `job_favorites` 存在记录的数量。
- denominator: `match_count`。
- data source: `match_rule_match_audits`, `job_favorites`。
- refresh cadence: 请求时实时计算。
- caveats: 收藏不是强转化，只能作为辅助意向。

`visit_rate`:

- business meaning: 匹配样本中发生岗位访问行为的比例。
- numerator: 审计样本中的 `(job_id, seeker_id)` 在 `job_visits` 存在记录的数量。
- denominator: `match_count`。
- data source: `match_rule_match_audits`, `job_visits`。
- refresh cadence: 请求时实时计算。
- caveats: 匹配页本身是否计入访问取决于现有埋点，需在验收中确认。

`low_score_rate`:

- business meaning: 当前样本中低匹配等级占比。
- numerator: `level = low` 的审计数量。
- denominator: `match_count`。
- data source: `match_rule_match_audits`。
- refresh cadence: 请求时实时计算。
- caveats: 低分不一定代表质量差，也可能是规则正确过滤。

`application_rate_delta`:

- business meaning: 分层或 treatment 相对基线的投递率差值。
- numerator: `target.application_rate - baseline.application_rate`。
- denominator: 无。
- data source: 派生指标。
- refresh cadence: 请求时实时计算。
- caveats: P0 使用百分点差值，不做复杂归因。

### 6.4 分层定义

分层类型：

| segment_type | segment_key | segment_label | 来源 |
| --- | --- | --- | --- |
| `city` | 城市名 | 城市名 | `jobs.city` |
| `position_category` | category | category | `standard_positions.category` |
| `standard_position` | standard_position_id | name | `jobs.standard_position_id` + `standard_positions.name` |
| `job_tag` | tag name | tag name | `jobs.tags` |
| `rule_version` | rule_config_id | rule name + version | `match_rule_configs` |
| `experiment_bucket` | control/treatment | control/treatment | `match_rule_match_audits.experiment_bucket` |

缺失值统一归为：

```text
segment_key = "unclassified"
segment_label = "Unclassified"
```

## 第七章：接口与系统行为

### 7.1 推荐接口方案

P0 推荐增强现有接口：

```text
GET /api/v1/matches/quality/summary
```

新增 query：

```text
city?: string
position_category?: string
standard_position_id?: int
job_tag?: string
segment_type?: city|position_category|standard_position|job_tag|rule_version|experiment_bucket
include_insights?: bool = true
```

保留现有 query：

```text
rule_config_id?: int
experiment_id?: int
scope?: string
template_key?: string
created_from?: datetime
created_to?: datetime
```

如果实现上担心响应过大，可新增独立接口：

```text
GET /api/v1/matches/quality/insights
```

`推荐默认` 优先增强现有接口，减少前端状态和接口数量。

### 7.2 响应示例

```json
{
  "filters": {
    "experiment_id": 7,
    "created_from": "2026-06-01T00:00:00",
    "created_to": "2026-06-22T23:59:59",
    "city": "上海",
    "position_category": "技术"
  },
  "summary": {},
  "segments": [
    {
      "segment_type": "city",
      "segment_key": "上海",
      "segment_label": "上海",
      "match_count": 180,
      "avg_score": 82.5,
      "low_score_rate": 12.2,
      "application_rate": 8.3,
      "application_rate_delta": -5.4,
      "sample_status": "usable",
      "risk_level": "high"
    }
  ],
  "experiment_confidence": {
    "experiment_id": 7,
    "control_match_count": 120,
    "treatment_match_count": 128,
    "control_application_rate": 7.5,
    "treatment_application_rate": 11.2,
    "application_rate_delta": 3.7,
    "avg_score_delta": 4.2,
    "sample_status": "usable",
    "confidence_status": "treatment_likely_better",
    "decision_hint": "Treatment 投递率高于 control，建议继续观察或准备发布检查。"
  },
  "anomalies": [
    {
      "severity": "high",
      "type": "low_application_rate",
      "segment_type": "city",
      "segment_label": "上海",
      "evidence": "投递率比全局低 5.4 个百分点，样本 180。",
      "suggested_next_action": "查看该城市匹配审计，检查 skill 和 salary 维度。"
    }
  ],
  "tuning_suggestions": [
    {
      "suggestion_type": "review_dimension",
      "dimension_key": "skill",
      "priority": "high",
      "affected_segment": "上海 / 技术",
      "evidence": "skill 高分样本投递率低于总体。",
      "proposed_action": "检查技能关键词命中是否过宽，必要时收窄 logic 或降低权重 5%。",
      "confidence": "medium",
      "guardrail": "仅生成建议草案，不自动修改规则；请通过规则编辑页创建新版本并走发布治理。"
    }
  ]
}
```

### 7.3 系统行为

- 后端必须先按筛选条件取审计样本，再计算所有派生指标。
- 行为数据按 `(job_id, seeker_id)` 与审计样本匹配。
- 如果审计缺少 job 或 job 已删除，样本仍参与 summary，但分层归为 `unclassified`。
- job tags 是数组时，每个 tag 生成一个 segment；同一审计可以进入多个 tag segment。
- 实验判断只在存在 `experiment_id` 且有 control/treatment 数据时返回。
- 异常和建议必须基于同一次响应中的数据，不得使用未展示的隐式规则。

## 第八章：权限、风控与审计

### 8.1 权限

P0 权限：

| 操作 | seeker | recruiter | admin |
| --- | --- | --- | --- |
| 查看质量洞察 | 禁止 | 禁止 | 允许 |
| 查看异常提示 | 禁止 | 禁止 | 允许 |
| 查看调权建议 | 禁止 | 禁止 | 允许 |
| 跳转规则编辑 | 禁止 | 禁止 | 允许 |

`推荐默认` 后续可拆：

- `viewer`: 只读查看质量数据。
- `rule_operator`: 查看建议并创建 draft/testing 规则。
- `rule_reviewer`: 审核发布建议。

### 8.2 风控

`硬约束` 风控规则：

- 样本不足时不得输出强结论。
- 调权建议不得直接调用规则编辑、版本创建或发布接口。
- 页面必须显示样本量和样本状态。
- 页面必须显示行为数据延迟说明。
- 显著性状态不得命名为“统计显著”除非实现了对应统计检验。
- P0 的 `confidence_status` 是业务启发式判断，不是严格统计结论。

### 8.3 审计

P0 查看洞察不新增操作审计。

如果后续增加“采纳建议”“创建调权草稿”，必须写入操作审计：

- actor_id
- action
- source suggestion
- before/after rule draft
- reason
- created_at

## 第九章：异常、空状态与边界场景

### 9.1 空状态

- 无审计数据：展示空 KPI，segments/anomalies/suggestions 为空。
- 无行为数据：展示匹配质量指标，转化指标为 0，并提示“当前时间范围内暂无后续行为”。
- 无标准职位：职位分层归为 `Unclassified`。
- 无岗位标签：标签分层归为 `Unclassified`。
- 未选择实验：Experiment Confidence 显示选择提示。

### 9.2 异常状态

- created_from 晚于 created_to：接口返回 400，前端提示日期范围无效。
- segment_type 不合法：接口返回 422 或 400。
- experiment_id 不存在：接口返回空洞察或 404；推荐 P0 返回空洞察并保留筛选显示。
- 数据量过大：P0 可限制默认窗口为最近 14 天，最长 90 天。
- 行为表查询失败：接口整体失败，不返回半真半假的建议。

### 9.3 边界场景

- 一个审计有多个 job tags：该审计计入多个 tag segment；summary 不重复计数。
- 同一 `(job_id, seeker_id)` 多次匹配：P0 按审计条数计入 match_count，行为转化按每条审计映射同一行为。
- control 或 treatment 样本为 0：confidence_status = `insufficient_sample`。
- 投递率为 0 但样本很小：只提示样本不足，不报 high severity。
- 高分低转化可能来自岗位本身吸引力，不一定是规则错误；建议文案必须使用“建议检查”，不能写成“规则错误”。

## 第十章：开发优先级与验收标准

### 10.1 开发优先级

#### P0-1 后端 schema 与服务聚合

- 扩展 `MatchQualityDashboardResponse`。
- 新增 Segment、Confidence、Anomaly、Suggestion response schema。
- 扩展质量查询支持 city、position、tag 过滤。
- list_quality_audits 加载 job 和 standard_position。
- 计算分层指标和 sample_status。

#### P0-2 实验判断与异常建议

- 实现 experiment_confidence。
- 实现 anomalies 生成。
- 实现 tuning_suggestions 生成。
- 后端测试覆盖样本不足、treatment 更好、低质量分层、高分低转化。

#### P0-3 前端质量洞察页

- 增强 `/admin-ra/match-quality`。
- 增加筛选字段。
- 增加 Segments 表。
- 增加 Experiment Confidence 区块。
- 增加 Anomalies 和 Tuning Suggestions。
- 保留 R-P3-10 已有 KPI、Rule Versions、Experiment Buckets、Daily Trend。

#### P0-4 联调验收

- 增加浏览器验收脚本。
- 保存关键截图。
- 更新 `docs/HANDOFF.json` 和 P3/P4 计划文档。

### 10.2 后端验收标准

必须通过：

```powershell
.\.venv\Scripts\pytest.exe -q tests\test_api\test_matches.py
```

新增或更新测试至少覆盖：

- admin 可以带 city / position_category / job_tag 查询质量洞察。
- 非 admin 不能查询质量洞察。
- segments 返回 city、position_category、standard_position、job_tag 聚合。
- 样本不足时 sample_status = `insufficient`，不生成 high severity 强异常。
- 选择 experiment_id 时返回 experiment_confidence。
- treatment 投递率高于 control 达阈值时返回 `treatment_likely_better`。
- 低投递率分层返回 anomaly。
- 高分低转化维度返回 tuning suggestion。
- 无 job 或无 standard_position 时归为 `Unclassified`。

### 10.3 前端验收标准

必须通过：

```powershell
npm.cmd run build
```

前端行为：

- `/admin-ra/match-quality` 正常打开。
- 默认加载最近 14 天质量数据。
- city、position_category、standard_position_id、job_tag 筛选可输入并生效。
- Segments 表可展示分层指标、样本状态和风险等级。
- Experiment Confidence 在选择 experiment_id 后展示判断。
- Anomalies 按 severity 展示。
- Tuning Suggestions 展示建议、证据和 guardrail。
- 空状态、接口错误、样本不足状态都有明确展示。

### 10.4 浏览器手工验收脚本

建议新增：

```text
frontend/wechat-prototype/output/playwright/manual-rp401-match-quality-p1-flow.cjs
```

流程：

1. 启动后端和前端。
2. 生成或复用包含多个城市、职位类目、岗位标签的测试数据。
3. 触发多次匹配审计和访问/收藏/投递行为。
4. 打开 `/admin-ra/match-quality`。
5. 验证 KPI、Segments、Experiment Confidence、Anomalies、Tuning Suggestions 可见。
6. 使用 city / job_tag / experiment_id 筛选。
7. 截图保存。

截图建议：

```text
frontend/wechat-prototype/output/playwright/rp401-quality-segments.png
frontend/wechat-prototype/output/playwright/rp401-quality-experiment-confidence.png
frontend/wechat-prototype/output/playwright/rp401-quality-anomalies-suggestions.png
```

## 第十一章：开发者交接说明

你要实现的是 Match Quality P1，不是重做 P3 匹配，也不是启动 P4 智能匹配。

先从后端做起：

1. 阅读 `docs/HANDOFF.json`、`docs/p3-match/P3_人岗匹配与规则配置产品化收尾.md` 和本文。
2. 在 `backend/job-platform/app/modules/match/schemas.py` 扩展质量响应 schema。
3. 在 `backend/job-platform/app/modules/match/repository.py` 扩展 `list_quality_audits`，加载 job、standard_position、rule_config、experiment。
4. 在 `backend/job-platform/app/modules/match/service.py` 扩展 `get_match_quality_summary`。
5. 在 `backend/job-platform/app/api/v1/matches.py` 增加筛选参数。
6. 在 `backend/job-platform/tests/test_api/test_matches.py` 增加 P1 测试。

不要重新解释这些硬约束：

- P3 已完成，不要重做 R-P3-01 到 R-P3-10。
- P1 只生成调优建议草案，不自动改规则。
- P1 的显著性是基础业务判断，不是严格统计显著性。
- 样本不足必须显式展示。
- P4 向量/LLM 智能匹配不进入本实现。

前端优先改：

1. `frontend/wechat-prototype/src/admin-ra/app/dataProvider.js`
2. `frontend/wechat-prototype/src/admin-ra/resources/match-quality/dashboard.jsx`
3. `frontend/wechat-prototype/output/playwright/manual-rp401-match-quality-p1-flow.cjs`

验收时必须跑：

```powershell
.\.venv\Scripts\pytest.exe -q tests\test_api\test_matches.py
npm.cmd run build
node frontend/wechat-prototype/output/playwright/manual-rp401-match-quality-p1-flow.cjs
```

已知未知：

- 当前投递之后的面试、通过、拒绝等后链路指标不进入 P0。
- 行为数据是否存在延迟，需要在页面文案中提示。
- 如果本地种子数据不足，浏览器验收脚本需要主动构造多分层样本。
