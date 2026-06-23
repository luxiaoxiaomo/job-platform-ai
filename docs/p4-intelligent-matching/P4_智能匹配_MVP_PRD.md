# P4 智能匹配 MVP PRD

## AI 速读卡

- 产品目标：在已完成的 P3 规则匹配治理闭环上，验证“规则基线 + 语义召回 + 混合评分”的智能匹配 MVP。
- 目标用户：平台管理员、规则运营、产品/算法评估人员；求职者侧只消费匹配结果，不进入复杂配置。
- P0 范围：离线评估集、向量召回候选、混合评分试算、灰度实验、可审计解释来源、管理端观察。
- 明确不做：LLM 实时评分、LLM 自动改规则、招聘者侧候选人排序正式上线、自动发布或自动回滚。
- 基线能力：复用 P3 的规则版本、实验、审计、发布治理和 R-P4-01 Match Quality 洞察。
- 关键数据：岗位、标准职位、标签、求职意向、结构化简历画像、应用/行为、匹配审计、规则配置。
- 主要风险：范围膨胀、解释不可审计、向量召回误伤、样本不足、线上灰度影响核心业务闭环。
- 验收摘要：PRD/MVP 边界明确，P0/P1/Deferred 可拆分，后续 T004/T005 可直接产出接口契约和任务包。

## 第一章：背景与目标

### 1.1 当前背景

`硬约束` P3 已完成的是规则驱动的人岗匹配治理闭环，不是智能匹配算法平台。现有可复用基线包括：

- 求职者侧真实匹配 API：`GET /api/v1/matches/jobs/{job_id}/me`。
- 规则配置、版本生成、版本比较、回滚生成新版本。
- 规则实验真实参与运行时匹配，支持稳定 AB bucket。
- 匹配审计落库，可追溯规则版本、实验、bucket 和维度快照。
- 规则发布治理、运行中实验阻断、操作审计。
- Match Quality 质量看板与 R-P4-01 分层质量分析、异常提示、调优建议草案。

这些能力已经解决“规则如何可配置、可审计、可发布、可观察”。P4 智能匹配要解决的是：在不破坏规则可解释基线的前提下，引入语义召回和混合评分，验证是否能提升匹配质量和投递转化。

### 1.2 产品目标

`硬约束` P4 MVP 的目标是验证智能匹配增量价值，而不是一次性重写匹配系统。

1. 在现有规则匹配结果之外，增加可选的语义召回候选来源。
2. 将规则分、语义相似度、结构化画像覆盖度和行为质量指标组合成可审计的混合评分。
3. 建立离线评估集，让每次算法/权重变更可以在上线前比较效果。
4. 通过现有实验和发布治理能力灰度验证，不直接替换全量线上匹配。
5. 在管理端明确展示智能匹配来源、命中原因、降级原因和质量表现。

### 1.3 P4 与已完成工作的边界

`硬约束` 不得把以下已完成能力重新列为 P4 待开发：

| 已完成能力 | 所属阶段 | P4 中的处理方式 |
| --- | --- | --- |
| 规则版人岗匹配真实计算 | P3 | 作为 baseline，不重做 |
| 规则配置落库、版本、比较、回滚 | P3 | 复用治理能力 |
| AB 实验运行时生效 | P3 | 复用为智能匹配灰度入口 |
| 匹配审计列表/详情 | P3 | 扩展审计字段，不另建黑盒日志 |
| 规则发布治理和操作审计 | P3 | 复用发布前检查和操作审计 |
| Match Quality 分层质量、异常、建议 | R-P4-01 | 作为质量判断和调优输入 |

`硬约束` P4 新增的是智能能力的“候选召回、混合评分、离线评估、灰度验证和可审计解释”，不自动修改规则，不绕过发布治理，不把建议直接变成生产配置。

## 第二章：用户角色与使用场景

### 2.1 用户角色

| 角色 | 当前系统角色 | P0 权限 | 说明 |
| --- | --- | --- | --- |
| 平台管理员 | `admin` | 查看、配置实验、查看评估和审计 | P0 唯一可操作角色 |
| 规则运营 | 暂无独立角色 | 不单独实现 | P1 可拆为 `rule_operator` |
| 算法/产品评估人员 | 暂无独立角色 | 不单独实现 | P0 由 admin 代替 |
| 求职者 | `seeker` | 查看匹配结果 | 不看到算法配置，仅看到可解释结果 |
| 招聘者 | `recruiter` | P0 不开放智能排序 | 候选人排序延后到 P1/P4 后续 |

### 2.2 使用场景

#### 场景 A：验证语义召回能否补充规则漏召

- 前置：已有岗位、标准职位、标签、求职意向和结构化简历画像。
- 流程：管理员开启智能匹配实验，系统对同一岗位生成规则候选和向量候选，比较召回交集、额外召回和质量表现。
- 结果：管理端能看到向量召回补充了哪些候选、这些候选的规则分、语义分和后续行为。

#### 场景 B：比较混合评分与规则基线

- 前置：存在离线评估集和历史审计/行为样本。
- 流程：管理员选择一组权重配置，系统离线计算规则 baseline 与 hybrid strategy 的排序/分层差异。
- 结果：页面展示覆盖率、低分率、投递/收藏倾向、人工样本通过率，以及是否达到进入灰度的门槛。

#### 场景 C：灰度智能匹配策略

- 前置：P3 规则实验与发布治理可用。
- 流程：管理员创建智能匹配实验，control 使用当前 active 规则，treatment 使用混合评分策略；实验期间所有结果写入审计。
- 结果：Match Quality 能按实验 bucket 对比质量表现，发布前仍需走治理检查。

#### 场景 D：智能能力不可用时降级

- 前置：向量索引缺失、画像缺失、召回服务异常或样本不足。
- 流程：系统自动回退到 P3 规则基线，并在审计中记录降级原因。
- 结果：求职者匹配页可用，管理员可在审计和质量看板看到降级分布。

## 第三章：范围与非范围

### 3.1 MVP 范围表

| 能力项 | MVP 决策 | P0 做法 | 非 P0 / 延后 |
| --- | --- | --- | --- |
| 向量召回 | In | 建立最小语义召回能力，召回岗位或候选简历的 Top N 候选，必须可开关、可审计、可降级 | 不做大规模实时特征平台，不承诺召回覆盖所有业务场景 |
| LLM 解释 | Out | P0 只展示结构化解释：规则命中、语义相似字段、分数贡献、降级原因 | LLM 自然语言解释延后；不得在 P0 生成不可追溯解释 |
| 混合评分 | In | 规则分为主，语义分和覆盖度为辅，生成 `hybrid_score` 和 `component_scores` | 不做端到端学习排序，不做自动权重学习 |
| 离线评估 | In | 构建小规模评估集，支持 baseline vs hybrid 对比，输出可复跑报告 | 不做完整 MLOps 训练流水线 |
| 灰度发布 | In | 复用现有 rule experiment/release governance，treatment 走智能策略 | 不做自动扩量、自动回滚、定时发布 |
| 招聘者侧候选人排序 | Out | P0 不改变招聘者候选列表排序，仅可输出研究/后续设计结论 | 后续单独 PRD，需处理公平性、解释、权限和业务闭环影响 |

### 3.2 P0 必须包含

`硬约束` P0 范围：

1. 智能匹配策略配置草案，至少包含 `baseline_rule`、`vector_recall`、`hybrid_score` 三类策略。
2. 向量召回候选生成，支持开关、Top N、最低相似度阈值和缺失降级。
3. 混合评分结果，返回总分、等级、规则分、语义分、覆盖度分和降级原因。
4. 离线评估集与评估报告，至少比较规则基线和混合策略。
5. 灰度实验设计，复用现有 AB bucket 和 match audit，不直接全量发布。
6. 管理端观察入口，能查看策略、评估结果、实验表现和审计详情。
7. 风控 guardrail：样本不足、画像缺失、索引过期、服务异常时回退到规则基线。

### 3.3 P1/P4 后续范围

`推荐默认` 后续能力：

- LLM 生成面向求职者或招聘者的自然语言解释。
- 招聘者侧候选人智能排序。
- 算法特征平台、批量重算任务、向量索引增量更新治理。
- 自动权重建议、自动创建规则草案。
- 复杂统计显著性、长期留存/面试/录用反馈纳入优化。
- 独立算法运营角色和审批流。

### 3.4 明确非范围

`硬约束` 本 PRD 不要求：

- 重做 P3 规则系统。
- 用 LLM 实时打分替代规则分。
- 用 LLM 自动修改规则或发布规则。
- 绕过 P3 审计、实验和发布治理。
- 在没有评估集和灰度证据前替换线上默认匹配。
- 将 demo/mock 数据当作真实验收证据。

## 第四章：核心流程与状态机

### 4.1 P4 MVP 主流程

1. 管理员准备或选择评估样本集。
2. 系统对样本运行当前 active 规则基线。
3. 系统调用语义召回，生成额外候选和相似度。
4. 系统计算 `hybrid_score`，并记录每个分数组件。
5. 管理员查看离线评估报告，判断是否进入灰度。
6. 管理员创建智能匹配灰度实验。
7. control 继续使用当前规则基线，treatment 使用 hybrid strategy。
8. 线上请求产生匹配审计，审计记录策略、分数组件、召回来源和降级原因。
9. Match Quality 按实验 bucket 观察质量表现。
10. 管理员根据灰度表现决定继续观察、暂停实验、调整策略或准备发布检查。

### 4.2 策略状态

| 状态 | 含义 | 允许动作 |
| --- | --- | --- |
| `draft` | 策略草案，未参与运行时匹配 | 编辑、离线评估、归档 |
| `evaluating` | 正在离线评估或已有评估报告 | 查看报告、调整参数、进入 testing |
| `testing` | 可被实验 treatment 引用 | 创建实验、暂停引用、归档 |
| `active` | 通过治理后成为默认智能策略 | 查看、复制新草案、归档 |
| `archived` | 历史只读 | 查看、复制新草案 |

`硬约束` P0 可以只实现到 `testing`，不要求智能策略成为默认 active。若实现 active，必须通过发布治理和回滚方案。

### 4.3 降级状态

| 状态 | 条件 | 系统行为 |
| --- | --- | --- |
| `normal` | 规则、画像、向量召回和评分均可用 | 返回 hybrid result |
| `partial_vector_missing` | 部分候选缺少向量 | 对缺失候选仅使用规则分，并记录原因 |
| `profile_incomplete` | 求职者画像关键字段不足 | 降低语义分权重或回退规则基线 |
| `vector_unavailable` | 向量服务、索引或召回失败 | 回退规则基线 |
| `sample_insufficient` | 评估或灰度样本不足 | 不允许给出强结论 |

## 第五章：页面与交互设计

### 5.1 智能匹配策略页

- 建议路由：`/admin-ra/intelligent-matching/strategies`。
- 用户目标：管理策略草案、查看状态、进入评估和实验。
- 字段：Strategy ID、Name、Status、Base Rule、Vector Recall Enabled、Hybrid Weights、Last Evaluation、Last Experiment、Created By、Updated At。
- 动作：Create Draft、Edit Draft、Run Offline Evaluation、Open Report、Create Experiment、Archive。
- 失败路径：无权限显示 403；无可用 active 规则时禁止创建灰度实验；向量索引不可用时允许保存草案但禁止进入 testing。
- 验收：管理员能看到策略列表和状态；draft 可编辑，testing/active 只能复制新草案；进入灰度的策略必须有关联评估报告。

### 5.2 离线评估报告页

- 建议路由：`/admin-ra/intelligent-matching/evaluations/:id`。
- 用户目标：判断 hybrid strategy 是否优于规则基线，是否值得灰度。
- 字段：Sample Set、Sample Count、Coverage、Recall Delta、Avg Score Delta、Low Score Rate、Application Proxy Rate、Manual Pass Rate、Risk Notes。
- 动作：Compare Baseline、Open Sample Detail、Export Evidence、Create Experiment。
- 失败路径：样本数不足时标记 `insufficient_sample`；样本包含 demo/mock 时标记 `demo_only`，不得作为上线证据。
- 验收：报告明确 baseline 与 hybrid 的差异；报告包含样本来源和可复跑参数；样本不足时不允许创建线上灰度实验。

### 5.3 智能匹配审计详情

- 入口：复用 `Match Audits`，扩展单条审计详情。
- 用户目标：解释某次智能匹配为什么产生该结果。
- 字段：`match_source`、`strategy_id`、`rule_score`、`vector_score`、`profile_coverage_score`、`hybrid_score`、`component_weights`、`recall_source`、`degrade_reason`。
- 动作：Open Strategy、Open Rule Version、Open Similar Samples、Open Quality Segment。
- 失败路径：老审计无智能字段时显示 `Rule baseline only`；智能字段缺失时显示 `Unknown` 并保留原始规则审计。
- 验收：每次 treatment 匹配都能追溯到策略、规则和分数组件；降级结果不伪装为正常 hybrid 结果。

### 5.4 Match Quality 观察扩展

- 入口：复用 `/admin-ra/match-quality`。
- 用户目标：对比智能策略 treatment 与规则基线 control 的质量。
- 字段：`strategy_id`、`match_source`、`experiment_bucket`、`hybrid_score_distribution`、`degrade_rate`、`vector_recall_coverage`。
- 动作：Filter by Strategy、Filter by Bucket、Open Experiment、Open Audits。
- 失败路径：灰度样本不足时显示样本不足；行为数据延迟时保留匹配质量指标，转化类指标标记延迟。
- 验收：能按实验 bucket 查看智能策略表现；能查看降级率和向量召回覆盖率。

## 第六章：数据模型与指标定义

### 6.1 数据依赖

P0 依赖现有数据：

- `jobs`
- `standard_positions`
- job tags / `tag_refs`
- seeker profile / 求职意向
- structured resume profile / 简历画像
- `job_visits`
- `job_favorites`
- `job_applications`
- `match_rule_configs`
- `match_rule_experiments`
- `match_rule_match_audits`
- `match_rule_operation_audits`

P0 可能新增的数据概念：

- intelligent matching strategy
- vector index metadata
- offline evaluation sample set
- offline evaluation run/report
- intelligent matching audit extension fields

`硬约束` T003 只定义产品范围；具体表结构、字段和接口契约由 T004 输出。

### 6.2 核心指标

`vector_recall_coverage`:

- business meaning: 当前样本中可被向量召回覆盖的比例。
- numerator: 有有效向量召回结果的样本数。
- denominator: 评估或灰度样本总数。
- data source: vector recall result + evaluation/audit sample。
- refresh cadence: 离线评估时批量计算，线上灰度按请求审计聚合。
- caveats: 覆盖率高不代表质量高，必须结合行为或人工评估。

`recall_delta`:

- business meaning: hybrid/vector 相对规则 baseline 新增候选的比例或数量。
- numerator: hybrid 候选中不在规则 Top N 的候选数。
- denominator: baseline Top N 候选数。
- data source: offline evaluation run。
- refresh cadence: 每次评估计算。
- caveats: 新增候选必须检查质量，不能只追求数量。

`hybrid_score`:

- business meaning: 规则分、语义分和画像覆盖度组合后的最终分数。
- numerator: weighted(rule_score, vector_score, profile_coverage_score, optional behavior_quality_score)。
- denominator: 无。
- data source: rule match result, vector similarity, structured profile coverage, quality metrics。
- refresh cadence: 请求时或离线评估时计算。
- caveats: P0 权重必须可解释，不允许黑盒模型覆盖规则分。

`degrade_rate`:

- business meaning: 智能策略回退到规则基线或部分降级的比例。
- numerator: `degrade_reason` 不为空的匹配次数。
- denominator: 智能策略 treatment 匹配次数。
- data source: match audit。
- refresh cadence: Match Quality 聚合时计算。
- caveats: 降级率高通常说明画像、索引或服务可用性不足。

`offline_win_rate`:

- business meaning: hybrid 在评估样本上优于 baseline 的样本占比。
- numerator: hybrid 排序/分层优于 baseline 的样本数。
- denominator: 有可判定标签的样本数。
- data source: offline evaluation sample labels。
- refresh cadence: 每次离线评估计算。
- caveats: 标签来源必须标记真实行为、人工评审或 demo 样本。

### 6.3 评估样本来源分级

| 来源 | 可用于上线决策 | 说明 |
| --- | --- | --- |
| `real_behavior` | 可以 | 来自真实访问、收藏、投递、联系交换等行为 |
| `manual_review` | 可以但需标记 | 由产品/运营人工判断样本质量 |
| `seeded_demo` | 不可以 | 只用于演示或联调 |
| `mock_only` | 不可以 | 只能验证页面和接口形态 |

`硬约束` 所有评估报告必须显示样本来源分布。

## 第七章：接口与系统行为

### 7.1 接口原则

`硬约束` P0 接口设计必须遵守：

- 保留现有匹配 API 的可用性；智能能力异常时不能让求职者匹配页不可用。
- 所有智能结果必须写入或关联匹配审计。
- P0 可以新增接口，也可以扩展现有 `/matches` 和 `/quality` 接口；最终契约由 T004 定义。
- 向量召回、混合评分和离线评估必须可开关，不能默认全量启用。

### 7.2 建议接口族

T004 需要展开以下接口族：

```text
GET  /api/v1/matches/intelligent/strategies
POST /api/v1/matches/intelligent/strategies
GET  /api/v1/matches/intelligent/strategies/{strategy_id}
POST /api/v1/matches/intelligent/strategies/{strategy_id}/evaluations
GET  /api/v1/matches/intelligent/evaluations/{evaluation_id}
POST /api/v1/matches/rule-experiments
GET  /api/v1/matches/audits/{audit_id}
GET  /api/v1/matches/quality/summary
```

### 7.3 运行时行为

- 默认线上匹配仍使用现有规则 baseline。
- 只有命中智能策略实验 treatment 的请求才执行 vector/hybrid 分支。
- vector/hybrid 分支失败时回退规则 baseline，并记录 `degrade_reason`。
- 智能策略不得直接发布为 active，除非通过发布检查和回滚方案。
- 智能字段不得覆盖原有规则审计字段，只能扩展。

## 第八章：权限、风控与审计

### 8.1 权限

P0 沿用现有 `admin`：

| 操作 | seeker | recruiter | admin |
| --- | --- | --- | --- |
| 查看智能策略 | 禁止 | 禁止 | 允许 |
| 编辑策略草案 | 禁止 | 禁止 | 允许 |
| 运行离线评估 | 禁止 | 禁止 | 允许 |
| 创建灰度实验 | 禁止 | 禁止 | 允许 |
| 查看智能审计字段 | 禁止 | 禁止 | 允许 |
| 查看求职者匹配结果 | 允许本人 | 禁止 | 允许 |

P1 可拆分 `viewer`、`rule_operator`、`rule_reviewer`、`algorithm_operator`。

### 8.2 风控规则

`硬约束` P0 风控：

- 样本不足不得输出强结论。
- seeded_demo/mock_only 不得作为上线证据。
- LLM 不得参与 P0 实时评分或自动解释。
- 智能策略不得自动修改规则、自动发布或自动回滚。
- 任一智能组件异常必须降级到规则 baseline。
- 线上 treatment 必须写入审计，且可按 experiment_bucket 聚合质量。
- 发布前必须能比较 baseline 与 treatment 的质量证据。

### 8.3 审计要求

智能审计最小字段：

- `strategy_id`
- `strategy_status`
- `match_source`: `rule_baseline | vector_recall | hybrid`
- `rule_config_id`
- `experiment_id`
- `experiment_bucket`
- `rule_score`
- `vector_score`
- `profile_coverage_score`
- `hybrid_score`
- `component_weights`
- `recall_source`
- `degrade_reason`
- `created_at`

## 第九章：异常、空状态与边界场景

### 9.1 空状态

- 无策略：显示空策略页，引导创建 draft。
- 无评估样本：禁止运行评估，提示先准备 sample set。
- 无向量索引：策略可保存为 draft，但不能进入 testing。
- 无审计数据：Match Quality 显示空洞察，不生成建议。
- 无行为数据：仅展示匹配分布，不展示转化结论。

### 9.2 异常状态

- 向量服务超时：回退规则 baseline，记录 `vector_unavailable`。
- 简历画像缺失：回退或降低语义权重，记录 `profile_incomplete`。
- 岗位标签缺失：继续规则匹配，语义召回使用岗位标题/描述，记录覆盖度不足。
- 实验配置无效：阻止实验运行，不进入线上 treatment。
- 权重配置非法：接口返回 400，前端保留草案内容。

### 9.3 边界场景

- 同一候选同时来自规则和向量召回：合并候选，保留两个来源和分数组件。
- 向量召回新增候选规则分很低：不得直接高排，必须受规则分和风控阈值约束。
- 规则高分但语义低分：仍保留规则结果，标记语义不一致供审计。
- demo 数据进入评估：报告可生成，但必须标记 `demo_only`，不得创建上线灰度。
- 招聘者候选列表排序：P0 不改变现有排序，避免影响业务闭环验收。

## 第十章：开发优先级与验收标准

### 10.1 开发优先级

#### P0-1 离线评估和样本治理

- 定义样本来源、样本标签、评估运行和报告输出。
- 支持 baseline vs hybrid 对比。
- 明确样本不足和 demo/mock 标记。

#### P0-2 向量召回和混合评分试算

- 建立可开关的向量召回分支。
- 输出 `vector_score`、`rule_score`、`profile_coverage_score`、`hybrid_score`。
- 支持异常降级。

#### P0-3 智能策略灰度实验

- 复用现有 rule experiment。
- control 使用规则 baseline，treatment 使用智能策略。
- 审计记录策略和分数组件。

#### P0-4 管理端观察和质量验证

- 策略页、评估报告页、审计扩展、Match Quality 过滤。
- 支持查看降级率、覆盖率和实验 bucket 表现。

### 10.2 PRD 验收标准

本 T003 文档验收：

- [OK] 明确产品目标、目标用户、使用场景、MVP 范围、非范围、风险和验收标准。
- [OK] 明确 P4 与 P3/R-P4-01 已完成能力边界，不把已完成事项重列为待开发。
- [OK] MVP 范围表覆盖向量召回、LLM 解释、混合评分、离线评估、灰度发布、招聘者侧候选人排序。

后续工程验收由 T004/T005 拆分，最低必须包括：

- 后端：策略、评估、审计、质量聚合相关测试通过。
- 前端：管理端策略/评估/审计/质量页面 build 通过。
- 浏览器：完整灰度观察路径有脚本或手工记录。
- 文档：接口契约、数据依赖、算法/规则边界、任务包均可追溯。

## 第十一章：开发者交接说明

你接下来要实现的不是“重做匹配”，而是在 P3 规则匹配治理闭环上增加可灰度、可审计、可降级的智能匹配 MVP。

后续 T004 请先产出接口契约和边界文档：

1. 定义智能策略、离线评估、向量召回、混合评分和审计扩展的数据契约。
2. 明确哪些接口复用现有 `/matches`、`/rule-experiments`、`/audits`、`/quality/summary`。
3. 明确算法边界：规则 baseline 仍是安全底座，vector/LLM/hybrid 都不能绕过审计和治理。

不要重新解释这些硬约束：

- P3 已完成规则驱动匹配治理闭环。
- R-P4-01 已完成 Match Quality P1，不属于 P4 智能匹配待开发范围。
- P0 不做 LLM 实时评分或 LLM 自动解释。
- P0 不做招聘者侧候选人排序正式上线。
- P0 所有智能能力必须可降级到规则 baseline。
- demo/mock 只能用于演示，不能作为上线证据。

可能涉及文件区域：

- `backend/job-platform/app/api/v1/matches.py`
- `backend/job-platform/app/modules/match/*`
- `backend/job-platform/tests/test_api/test_matches.py`
- `frontend/wechat-prototype/src/admin-ra/app/*`
- `frontend/wechat-prototype/src/admin-ra/resources/*`
- `frontend/wechat-prototype/output/playwright/*`
