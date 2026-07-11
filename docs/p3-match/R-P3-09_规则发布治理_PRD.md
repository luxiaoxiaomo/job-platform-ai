# R-P3-09 规则发布治理 PRD

## AI 速读卡

- 产品目标：把已具备的规则编辑、版本、实验和审计能力收束成可控的发布治理流程。
- 目标用户：平台管理员，后续可扩展为规则运营、规则审核、只读观察者。
- P0 范围：发布前校验、规则升为 active、实验运行互斥校验、实验暂停/结束、发布操作审计、管理端发布治理页。
- 主要页面：规则发布治理页、规则详情发布面板、实验治理动作区。
- 关键状态：规则 `draft/testing/active/archived`，实验 `draft/running/paused/ended`。
- 关键接口：新增发布校验、规则发布、实验状态变更接口；复用规则列表、对比、实验效果、审计接口。
- 主要风险：误发布、同 scope/template 多 active、运行实验冲突、未来生效窗口误判、发布治理中的回滚入口不清晰。
- 验收摘要：后端测试覆盖阻断条件；前端可完成校验、发布、暂停/结束实验；浏览器流程可验证发布后运行时匹配使用新 active 规则。

## 第一章：背景与目标

### 1.1 当前背景

P3 人岗匹配主线截至 R-P3-07 已完成以下基础能力：

- 规则配置已落库，支持 `scope`、`template_key`、`version`、`status`。
- 管理端可以编辑规则维度并保存为新版本。
- 管理端可以查看历史、对比版本、回滚生成新版本。
- 可以创建规则实验，运行时支持 stable AB bucket。
- 匹配结果会记录审计，实验效果可以按 control/treatment 聚合查看。

当前缺口不在“能不能改规则”，而在“规则如何被可靠地发布到生产运行时”。现有接口允许创建 `active` 版本时自动归档旧 active，但缺少产品化的发布前检查、冲突解释、实验互斥、操作审计和前端发布入口。

### 1.2 产品目标

`硬约束` R-P3-09 的目标是建立规则发布治理闭环：

1. 管理员在发布规则前能看到校验结果，而不是直接提交后才发现问题。
2. 同一 `scope + template_key` 在生产运行时最多只有一个 `active` 规则。
3. 有运行中实验时，不能无提示地发布会影响同一 `scope + template_key` 的规则。
4. 实验可以被暂停或结束，暂停后运行时回落 active 规则，结束后保留审计和效果记录。
5. 每次发布、阻断、暂停、结束实验都能在管理端追踪到操作者、时间和原因。

### 1.3 设计原则

- `硬约束` 不重写 R-P3-01 至 R-P3-07 的能力，把它们视为基线。
- `硬约束` 不在 R-P3-09 引入复杂多角色审批流；当前代码只有 `admin/seeker/recruiter`，P0 只要求 `admin` 可操作。
- `推荐默认` 前端使用现有 react-admin 管理台承载发布治理，而不是新增一套独立后台。
- `推荐默认` 发布治理先做“同步检查 + 显式确认 + 审计记录”，不做定时发布和多级审批。
- `发挥空间` 实现可在页面文案、布局和字段命名上优化，但不得改变阻断规则和状态机。

## 第二章：用户角色与使用场景

### 2.1 用户角色

| 角色 | 当前系统对应 | P0 权限 | 后续扩展 |
| --- | --- | --- | --- |
| 平台管理员 | `admin` | 查看规则、编辑规则、发布规则、归档规则、暂停/结束实验、查看审计 | 可拆分为运营和审核 |
| 求职者 | `seeker` | 无规则治理权限 | 无 |
| 招聘者 | `recruiter` | 无规则治理权限 | 可查看部分岗位级效果，非 P0 |
| 规则运营 | 暂无代码角色 | 非 P0 | 起草/测试规则，不可发布 |
| 规则审核 | 暂无代码角色 | 非 P0 | 审核发布、强制回滚 |
| 只读观察者 | 暂无代码角色 | 非 P0 | 查看规则、实验、审计 |

`硬约束` R-P3-09 P0 所有写操作仅允许 `admin`。如果未来新增细分角色，不得降低当前 `admin` 能力。

### 2.2 使用场景

#### 场景 A：管理员发布测试过的新规则

- 入口：`/admin-ra/match-rules/:id/show` 或规则发布治理页。
- 前置：存在一个 `draft` 或 `testing` 规则版本。
- 流程：打开发布面板，运行发布检查，确认无阻断项，填写发布说明，点击发布。
- 结果：目标规则变为 `active`，同 scope/template 旧 active 变为 `archived` 并写入 `effective_to`。

#### 场景 B：运行中实验阻断直接发布

- 入口：规则发布面板。
- 前置：同一 `scope + template_key` 存在 `running` 实验。
- 流程：发布检查展示阻断项，说明实验 ID、名称、control/treatment、流量和开始时间。
- 结果：不允许直接发布；管理员必须先暂停或结束实验，再重新发布检查。

#### 场景 C：管理员暂停实验排查问题

- 入口：`/admin-ra/rule-experiments` 实验治理动作区。
- 前置：实验状态为 `running`。
- 流程：查看实验效果或收到异常反馈，点击暂停，填写原因，确认。
- 结果：实验状态变为 `paused`，运行时不再进行 AB 分流，回落当前 active 规则。

#### 场景 D：管理员结束实验并保留记录

- 入口：实验治理动作区。
- 前置：实验状态为 `running` 或 `paused`。
- 流程：点击结束，填写实验结论，确认。
- 结果：实验状态变为 `ended`，写入 `ended_at`，历史审计和效果查询仍可查看。

#### 场景 E：管理员尝试发布无效规则

- 入口：发布面板。
- 前置：目标规则维度权重全为 0、没有启用维度、`effective_from >= effective_to`，或状态不允许发布。
- 流程：发布检查展示阻断项。
- 结果：发布按钮禁用，接口返回结构化错误。

## 第三章：范围与非范围

### 3.1 P0 范围

`硬约束` P0 必须包含：

1. 规则发布前校验接口。
2. 规则发布接口：将指定规则版本升为 `active`。
3. 发布时归档同一 `scope + template_key + strategy` 下旧 active 规则。
4. 运行中实验互斥校验：同一 `scope + template_key` 有 `running` 实验时阻断发布。
5. 实验状态变更接口：支持 `running -> paused`、`paused -> running`、`running/paused/draft -> ended` 的受控流转。
6. 管理端发布治理页：展示候选规则、当前 active、运行中实验、发布检查结果和操作入口。
7. 管理端实验治理动作区：暂停、恢复、结束实验。
8. 操作审计：记录发布、发布阻断、实验暂停/恢复/结束的操作者、原因、前后状态、关联资源。
9. 后端测试、前端构建和浏览器手工流程验收。

### 3.2 P1 范围

`推荐默认` P1 可以排期到 R-P3-10 或后续：

1. 发布后质量看板和长期转化指标。
2. 按岗位、求职者、规则版本过滤审计详情的增强页。
3. 发布影响预估：用历史样本批量重算新旧规则差异。
4. 多角色审批流：规则运营提交、规则审核批准、管理员发布。
5. 定时发布和自动回滚。
6. 实验统计显著性分析。

### 3.3 非范围

`硬约束` 本 PRD 不做：

- 向量匹配、embedding、LLM 实时评分。
- LLM 自动生成规则或自动调权。
- 复杂权限体系改造。
- 规则 DSL 重构。
- 长周期离线重算。
- 招聘者侧规则配置入口。

## 第四章：核心流程与状态机

### 4.1 规则状态机

当前模型已支持：

```text
draft -> testing -> active -> archived
```

R-P3-09 P0 允许的状态流转：

| 当前状态 | 目标状态 | 是否允许 | 触发动作 | 说明 |
| --- | --- | --- | --- | --- |
| draft | testing | 允许 | 保存新版本或状态更新 | 进入可实验状态 |
| draft | active | 允许但需发布检查 | 发布规则 | 适合紧急修复或小范围规则 |
| testing | active | 允许但需发布检查 | 发布规则 | 推荐发布路径 |
| active | archived | 系统自动 | 发布同 scope/template 新 active | 旧 active 不可直接编辑 |
| archived | active | 不直接允许 | 回滚生成新版本后发布 | 保留历史不可变 |
| active | draft/testing | 不允许 | 无 | 避免生产版本被反向编辑 |
| archived | draft/testing | 不允许 | 无 | 历史只读 |

`硬约束` 运行时选择 active 规则的逻辑不能被破坏：无 running 实验时，按 R-P3-07 的选择顺序使用最新可用 active 规则，异常时继续 fallback。

### 4.2 实验状态机

当前模型已支持：

```text
draft -> running -> paused -> ended
```

R-P3-09 P0 允许的状态流转：

| 当前状态 | 目标状态 | 是否允许 | 触发动作 | 运行时行为 |
| --- | --- | --- | --- | --- |
| draft | running | 允许，需校验 | 启动实验 | AB 分流生效 |
| running | paused | 允许 | 暂停实验 | 回落 active 规则 |
| paused | running | 允许，需校验 | 恢复实验 | AB 分流恢复 |
| draft | ended | 允许 | 取消实验 | 不进入运行时 |
| running | ended | 允许 | 结束实验 | 停止分流，保留审计 |
| paused | ended | 允许 | 结束实验 | 保留审计 |
| ended | running/paused | 不允许 | 无 | 历史只读 |

`硬约束` 同一 `scope + template_key` 最多存在一个 `running` 实验。恢复 paused 实验时也必须检查互斥。

### 4.3 规则发布主流程

1. 管理员进入发布治理页或规则详情页发布面板。
2. 前端调用发布检查接口。
3. 后端返回 `blockers`、`warnings`、`summary` 和建议操作。
4. 若有 blocker，发布按钮禁用，管理员只能跳转处理冲突。
5. 若无 blocker，管理员填写发布原因和确认文本。
6. 前端调用发布接口。
7. 后端在事务中执行：
   - 锁定同一 `scope + template_key + strategy` 的规则集合。
   - 再次运行发布检查。
   - 将旧 active 置为 `archived`，写入 `effective_to`。
   - 将目标规则置为 `active`，写入 `effective_from`、`updated_by`。
   - 写入发布操作审计。
8. 前端展示发布成功，并刷新规则列表、详情和发布治理页。

### 4.4 发布检查规则

`硬约束` blocker：

| 编码 | 阻断条件 | 用户提示 |
| --- | --- | --- |
| `rule_not_found` | 目标规则不存在 | 规则版本不存在或已被删除 |
| `rule_archived` | 目标规则为 archived | 历史版本不能直接发布，请先回滚生成新版本 |
| `rule_already_active` | 目标规则已经 active | 当前规则已在生产生效 |
| `no_enabled_dimensions` | 没有启用维度 | 至少启用一个匹配维度 |
| `invalid_weight_total` | 启用维度权重总和 <= 0 | 启用维度权重总和必须大于 0 |
| `invalid_effective_window` | `effective_from >= effective_to` | 生效时间窗口不合法 |
| `running_experiment_conflict` | 同 scope/template 有 running 实验 | 请先暂停或结束运行中的实验 |
| `template_scope_mismatch` | 目标规则缺少 scope/template | 规则归属不完整 |
| `permission_denied` | 当前用户非 admin | 无权限发布规则 |

`推荐默认` warning：

| 编码 | 警告条件 | 用户提示 |
| --- | --- | --- |
| `publish_from_draft` | 从 draft 直接发布 | 建议先进入 testing 并通过实验验证 |
| `no_recent_audit` | 目标规则无实验或审计样本 | 当前规则缺少线上验证样本 |
| `large_weight_change` | 与当前 active 对比存在单维度权重变化 >= 30 | 变化较大，建议先灰度 |
| `disabled_major_dimension` | 关闭核心维度，如 skill/experience | 核心维度关闭可能影响匹配质量 |

`发挥空间` warning 不阻断发布，但前端必须展示，并要求管理员显式确认。

### 4.5 实验治理主流程

#### 暂停实验

1. 管理员在实验列表选择 running 实验。
2. 点击暂停，填写原因。
3. 后端校验状态为 running。
4. 实验状态更新为 paused。
5. 后续匹配请求不再使用该实验，按 active 规则执行。
6. 写入操作审计。

#### 恢复实验

1. 管理员在 paused 实验点击恢复。
2. 后端检查同 scope/template 是否已有其他 running 实验。
3. 后端检查 control/treatment 规则存在且未 archived。
4. 状态更新为 running。
5. 写入操作审计。

#### 结束实验

1. 管理员点击结束实验，填写结论。
2. 后端校验状态不为 ended。
3. 状态更新为 ended，写入 `ended_at`。
4. 审计记录和效果查询保留。
5. 写入操作审计。

## 第五章：页面与交互设计

### 5.1 规则发布治理页

- 路由：`/admin-ra/rule-releases`
- 入口：
  - react-admin 左侧菜单新增 `Rule Releases`。
  - 规则列表每行新增 `Release` 动作。
  - 规则详情页新增 `Release Check` 面板。

#### 用户目标

管理员快速判断哪些规则可以发布、哪些规则被实验或校验项阻断。

#### 展示字段

顶部概览：

- 当前 active 规则数。
- 可发布候选数：`draft/testing`。
- 运行中实验数。
- 阻断项数。

候选规则表：

- 规则 ID。
- 名称。
- `scope`。
- `template_key`。
- `version`。
- `status`。
- 当前 active 版本。
- 是否存在 running 实验。
- 最近更新时间。
- 创建人/更新人。
- 检查状态：未检查、可发布、有警告、已阻断。

#### 操作

- 运行发布检查。
- 查看与当前 active 的差异。
- 跳转实验治理。
- 发布规则。
- 查看操作审计。

#### 正常流程

1. 页面加载候选规则列表。
2. 管理员选择一个 testing 规则。
3. 点击发布检查。
4. 页面展示通过项、warning 和 blocker。
5. 无 blocker 时，管理员填写发布说明并确认发布。
6. 发布成功后候选表刷新，目标规则状态显示 active。

#### 失败路径

- 接口 403：页面展示无权限，不显示发布按钮。
- 发布检查失败：保留候选列表，检查面板展示错误原因和重试按钮。
- 发布接口返回 blocker：展示最新 blocker，提示“检查结果已过期，请按最新结果处理”。
- 发布成功但刷新失败：展示成功提示，并提供手动刷新按钮。

#### 状态

- `idle`：未选择规则。
- `checking`：发布检查中。
- `blocked`：存在 blocker。
- `warning`：无 blocker 但存在 warning。
- `ready`：可发布。
- `publishing`：发布中。
- `published`：发布完成。

#### 依赖

- `GET /api/v1/matches/rule-configs`
- `GET /api/v1/matches/rule-experiments`
- `GET /api/v1/matches/rule-configs/{config_id}/compare/{target_config_id}`
- 新增发布检查和发布接口。

#### 验收标准

- 管理员可以从页面完成一次 testing 规则发布。
- 有 running 实验冲突时发布按钮不可用。
- warning 不阻断发布，但必须展示并要求确认。
- 发布成功后同 scope/template 旧 active 显示 archived。

### 5.2 规则详情发布面板

- 路由：复用 `/admin-ra/match-rules/:id/show`。
- 放置位置：规则元信息和维度详情之间或详情页右侧动作区。

#### 用户目标

管理员在查看某个规则版本时直接完成校验、对比和发布。

#### 展示字段

- 当前规则状态。
- 当前 active 规则 ID 和版本。
- 目标规则与 active 的差异摘要。
- 发布检查结果。
- 最近 5 条相关操作审计。

#### 操作

- 运行检查。
- 与 active 对比。
- 发布。
- 回到版本历史。

#### 失败路径

- 当前规则为 archived：只显示“历史版本不可直接发布，请回滚生成新版本”。
- 当前规则为 active：显示“已发布”，不显示发布按钮。
- active 规则缺失：允许发布，但 warning 提示“当前无 active，发布后将成为默认生产规则”。

#### 验收标准

- 管理员无需离开规则详情页即可看见是否可发布。
- archived 和 active 状态下动作符合状态机。

### 5.3 实验治理动作区

- 路由：复用 `/admin-ra/rule-experiments`。

#### 用户目标

管理员可以管理实验状态，解除发布冲突或处理实验异常。

#### 展示字段

实验列表在现有字段基础上增加：

- 状态标签。
- 是否阻塞规则发布。
- 开始时间。
- 结束时间。
- control/treatment 规则状态。
- 最近匹配数。

#### 操作

- 启动实验。
- 暂停实验。
- 恢复实验。
- 结束实验。
- 查看效果。
- 查看关联审计。

#### 失败路径

- 恢复实验时已有其他 running 实验：阻断并展示冲突实验。
- control/treatment 规则不存在或 archived：阻断恢复。
- 结束实验重复提交：返回当前 ended 状态，不重复写入业务变更，但记录接口幂等结果。

#### 验收标准

- running 实验可以暂停，暂停后运行时匹配不再返回该 experiment_id。
- paused 实验可以恢复，恢复后运行时匹配重新返回 experiment_id 和 bucket。
- ended 实验不可恢复。

### 5.4 操作审计列表

- P0 可作为发布治理页内嵌表格。
- P1 可扩展成独立资源 `/admin-ra/rule-release-audits`。

#### 展示字段

- 审计 ID。
- 动作类型：`publish_rule`、`block_publish`、`pause_experiment`、`resume_experiment`、`end_experiment`。
- 资源类型：`rule_config` 或 `rule_experiment`。
- 资源 ID。
- `scope`。
- `template_key`。
- 操作人。
- 原因。
- 前状态。
- 后状态。
- 创建时间。

#### 验收标准

- 每次成功发布和实验状态变化都有审计记录。
- 发布被接口阻断时也记录阻断原因，便于排查。

## 第六章：数据模型与指标定义

### 6.1 新增数据表：`match_rule_operation_audits`

`硬约束` 需要新增规则操作审计表，不要复用 `match_rule_match_audits`。后者是匹配计算审计，前者是管理操作审计。

字段建议：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | int | 是 | 主键 |
| `action` | string(50) | 是 | 操作类型 |
| `resource_type` | string(50) | 是 | `rule_config` / `rule_experiment` |
| `resource_id` | int | 是 | 资源 ID |
| `scope` | string(80) | 是 | 规则范围 |
| `template_key` | string(80) | 是 | 模板 key |
| `before_status` | string(30) | 否 | 操作前状态 |
| `after_status` | string(30) | 否 | 操作后状态 |
| `actor_id` | int | 否 | 操作人 |
| `reason` | text | 否 | 操作说明 |
| `details` | JSON/JSONB | 否 | blocker、warning、关联 active、关联实验等 |
| `created_at` | datetime | 是 | 创建时间 |

索引：

- `idx_match_rule_operation_audits_resource`: `resource_type, resource_id`
- `idx_match_rule_operation_audits_scope_template`: `scope, template_key`
- `idx_match_rule_operation_audits_action`: `action`
- `idx_match_rule_operation_audits_created_at`: `created_at`

### 6.2 现有模型字段复用

规则配置复用 `match_rule_configs`：

- `status`
- `effective_from`
- `effective_to`
- `updated_by`
- `updated_at`
- `parent_version_id`

实验复用 `match_rule_experiments`：

- `status`
- `started_at`
- `ended_at`
- `updated_by`
- `updated_at`

`推荐默认` 不在 P0 新增 release request 表。原因是当前不做多级审批，发布动作可以由操作审计覆盖。

### 6.3 发布检查响应结构

```json
{
  "rule_config_id": 12,
  "scope": "global",
  "template_key": "default",
  "current_status": "testing",
  "current_active_config_id": 8,
  "can_publish": false,
  "blockers": [
    {
      "code": "running_experiment_conflict",
      "message": "同一 scope/template 存在运行中实验",
      "resource_type": "rule_experiment",
      "resource_id": 3
    }
  ],
  "warnings": [
    {
      "code": "large_weight_change",
      "message": "技能维度权重变化超过 30"
    }
  ],
  "summary": {
    "enabled_dimension_count": 4,
    "configured_total_weight": 100,
    "active_config_id": 8,
    "running_experiment_id": 3
  }
}
```

### 6.4 指标定义

`release_success_count`:

- business meaning: 规则发布成功次数，用于观察规则治理活跃度。
- numerator: `match_rule_operation_audits.action = publish_rule` 的记录数。
- denominator: 无。
- data source: `match_rule_operation_audits`。
- refresh cadence: 页面实时查询或按请求刷新。
- caveats: 同一规则多次发布会计多次。

`release_block_count`:

- business meaning: 发布被阻断次数，用于发现流程摩擦和规则质量问题。
- numerator: `match_rule_operation_audits.action = block_publish` 的记录数。
- denominator: 发布检查或发布请求次数。
- data source: `match_rule_operation_audits.details.blockers`。
- refresh cadence: 页面实时查询或按请求刷新。
- caveats: 前端只运行检查但不点击发布时，是否记为阻断由接口实现决定；P0 推荐发布接口阻断必须记录，纯检查阻断可不记录。

`running_experiment_count`:

- business meaning: 当前运行中实验数，用于判断发布冲突风险。
- numerator: `match_rule_experiments.status = running` 的记录数。
- denominator: 无。
- data source: `match_rule_experiments`。
- refresh cadence: 页面实时查询。
- caveats: 按全局计数和按 scope/template 计数要分别展示。

`active_rule_coverage_count`:

- business meaning: 有 active 规则覆盖的 scope/template 数。
- numerator: distinct `scope + template_key` where `match_rule_configs.status = active`。
- denominator: distinct `scope + template_key` where any rule config exists。
- data source: `match_rule_configs`。
- refresh cadence: 页面实时查询。
- caveats: 代码 fallback 不计入 active 规则覆盖。

`experiment_pause_count`:

- business meaning: 实验被暂停次数，用于发现异常实验或频繁干预。
- numerator: `match_rule_operation_audits.action = pause_experiment` 的记录数。
- denominator: running 实验总数。
- data source: `match_rule_operation_audits` 和 `match_rule_experiments`。
- refresh cadence: 页面实时查询。
- caveats: 同一实验多次暂停会计多次。

## 第七章：接口与系统行为

### 7.1 发布检查接口

```text
GET /api/v1/matches/rule-configs/{config_id}/release-check
```

Auth:

- `admin`

Response:

- 使用第六章 `发布检查响应结构`。

系统行为：

- 只读，不改变规则状态。
- 必须检查权限、目标规则、维度合法性、生效窗口、running 实验冲突。
- 可以返回 warning。
- 如果目标规则不存在返回 404。

### 7.2 发布规则接口

```text
POST /api/v1/matches/rule-configs/{config_id}/publish
```

Auth:

- `admin`

Request:

```json
{
  "reason": "完成 AB 验证，发布 V4 为生产规则",
  "confirm_warnings": true
}
```

Response:

```json
{
  "message": "match_rule_config_published",
  "config": {},
  "archived_config_ids": [8],
  "release_check": {}
}
```

系统行为：

- 在事务内重新执行发布检查。
- 若存在 blocker，返回 400，`detail = match_rule_publish_blocked`，并附带 release_check。
- 若只有 warning 且 `confirm_warnings != true`，返回 400，`detail = match_rule_publish_warning_unconfirmed`。
- 发布成功时：
  - 同一 `scope + template_key + strategy` 的旧 active 置为 archived。
  - 目标规则置为 active。
  - `effective_from` 默认写当前时间。
  - 旧 active 的 `effective_to` 写当前时间。
  - 写入操作审计。

`硬约束` 发布接口不能创建新规则版本；它只改变既有目标版本状态。编辑和回滚仍使用 R-P3-05/R-P3-06 的既有版本生成接口。

### 7.3 实验状态变更接口

```text
POST /api/v1/matches/rule-experiments/{experiment_id}/status
```

Auth:

- `admin`

Request:

```json
{
  "status": "paused",
  "reason": "发布新规则前暂停实验"
}
```

Allowed `status`:

- `running`
- `paused`
- `ended`

Response:

```json
{
  "message": "match_rule_experiment_status_updated",
  "experiment": {}
}
```

系统行为：

- `draft -> running`：校验 control/treatment 规则存在，scope/template 一致，且同 scope/template 无其他 running 实验。
- `running -> paused`：允许，运行时立即回落 active。
- `paused -> running`：按启动实验重新校验互斥。
- `running/paused/draft -> ended`：允许，写入 `ended_at`。
- `ended -> *`：不允许，返回 400。
- 每次成功状态变化写入操作审计。

### 7.4 操作审计查询接口

```text
GET /api/v1/matches/rule-operation-audits
```

Auth:

- `admin`

Query:

- `resource_type?: string`
- `resource_id?: int`
- `scope?: string`
- `template_key?: string`
- `action?: string`
- `skip?: int = 0`
- `limit?: int = 20`

Response:

```json
{
  "items": [
    {
      "id": 1,
      "action": "publish_rule",
      "resource_type": "rule_config",
      "resource_id": 12,
      "scope": "global",
      "template_key": "default",
      "before_status": "testing",
      "after_status": "active",
      "actor_id": 1,
      "reason": "完成验证后发布",
      "details": {
        "archived_config_ids": [8]
      },
      "created_at": "2026-06-21T10:00:00"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

### 7.5 运行时匹配行为

`硬约束` R-P3-09 不改变 R-P3-07 的运行时选择顺序：

1. `scope = job_id:{job_id}`, `template_key = default`
2. `scope = global`, `template_key = default`
3. 代码默认规则 fallback

变化点：

- running 实验继续优先于 active 规则。
- paused 和 ended 实验不得参与运行时分流。
- 发布新 active 后，未被 running 实验覆盖的匹配请求应使用新 active。
- 发布失败不得影响现有匹配结果。

## 第八章：权限、风控与审计

### 8.1 权限

P0 权限：

| 操作 | seeker | recruiter | admin |
| --- | --- | --- | --- |
| 查看规则列表 | 禁止 | 禁止 | 允许 |
| 发布检查 | 禁止 | 禁止 | 允许 |
| 发布规则 | 禁止 | 禁止 | 允许 |
| 暂停/恢复/结束实验 | 禁止 | 禁止 | 允许 |
| 查看操作审计 | 禁止 | 禁止 | 允许 |

`推荐默认` 后续权限模型：

- `rule_operator`：可创建 draft/testing，不可发布。
- `rule_reviewer`：可审批和发布。
- `viewer`：只读。

P0 不实现这些角色，但 PRD 和接口命名不得封死未来扩展。

### 8.2 风控

`硬约束` 风控规则：

- 发布接口必须服务端二次检查，不得只依赖前端检查结果。
- 发布和实验状态变更必须写审计。
- running 实验冲突必须阻断发布。
- 同 scope/template/strategy 最多一个 active，发布事务必须保证。
- archived 规则不能直接发布。
- ended 实验不能恢复。
- 接口失败不得改变运行时现有 active 或 experiment 状态。

`推荐默认` 风控规则：

- warning 发布需要 `confirm_warnings = true`。
- 发布 reason 必填，长度 5 至 500 字。
- 实验暂停/结束 reason 必填。
- 大权重变化 warning 阈值默认 30。

### 8.3 审计

操作审计必须覆盖：

- 谁操作：`actor_id`。
- 操作什么：`action/resource_type/resource_id`。
- 从什么状态到什么状态：`before_status/after_status`。
- 为什么操作：`reason`。
- 影响范围：`scope/template_key`。
- 关键细节：blocker、warning、archived config IDs、conflict experiment ID。

`硬约束` 匹配审计和操作审计要分表。匹配审计回答“某次匹配用了什么规则”，操作审计回答“管理员如何改变了规则治理状态”。

## 第九章：异常、空状态与边界场景

### 9.1 空状态

- 无候选规则：发布治理页显示“暂无 draft/testing 规则版本”，提供进入规则列表入口。
- 无 active 规则：显示 warning，允许发布第一个 active。
- 无实验：实验冲突区域显示“当前无运行中实验”。
- 无操作审计：显示“暂无发布操作记录”。

### 9.2 异常状态

- 规则版本不存在：返回 404，前端提示“规则版本不存在或已刷新”。
- 目标规则维度为空：阻断发布。
- 权重总和非法：阻断发布。
- running 实验指向不存在的 control/treatment：恢复实验阻断；发布检查也应提示存在异常实验。
- 发布过程中并发启动实验：发布接口二次检查阻断。
- 发布过程中并发发布另一规则：事务中只允许最终一个 active；失败请求返回冲突错误。

### 9.3 边界场景

- `traffic_percent = 0` 的 running 实验仍算 running，仍阻断发布。原因是运行时仍挂载实验对象，审计会记录 experiment_id。
- `traffic_percent = 100` 的 running 实验同样阻断发布。
- target rule 与 current active 是同一个 ID：不执行发布，返回 already active。
- 从 draft 直接发布：允许但 warning。
- active 规则被回滚：仍通过“回滚生成新版本 + 发布新版本”完成，不直接修改历史 active。
- `effective_from` 在未来：P0 不做定时生效；发布时如果设置未来 `effective_from`，作为 warning 或阻断由后端统一处理。推荐 P0 阻断未来 `effective_from`，避免运行时选择逻辑不一致。

## 第十章：开发优先级与验收标准

### 10.1 开发优先级

#### P0-1 后端发布检查和发布动作

- 新增 operation audit model、migration、schema、repository。
- 新增 release-check 接口。
- 新增 publish 接口。
- 后端测试覆盖 blocker、warning、发布成功、并发/冲突核心路径。

#### P0-2 实验状态治理

- 新增实验状态变更接口。
- 运行时确认只选择 running 实验。
- 后端测试覆盖 pause、resume、end 和 ended 不可恢复。

#### P0-3 前端发布治理

- react-admin 新增 `Rule Releases` 页面。
- 规则详情页增加发布检查面板。
- 实验列表增加暂停、恢复、结束动作。
- dataProvider 增加对应方法。

#### P0-4 联调验收

- 增加浏览器手工流程脚本。
- 保存关键截图。
- 更新 `docs/HANDOFF.json` 和 P3 协作计划。

### 10.2 后端验收标准

必须通过：

```text
.\.venv\Scripts\pytest.exe -q tests\test_api\test_matches.py
```

新增或更新测试至少覆盖：

- admin 可以对 testing 规则执行 release-check。
- 非 admin 不能执行 release-check/publish/status update。
- running 实验冲突时 publish 返回阻断。
- 无 blocker 时 publish 成功，目标规则 active，旧 active archived。
- publish 有 warning 且未确认时返回 `match_rule_publish_warning_unconfirmed`。
- pause running 实验后，匹配接口不再返回该 experiment_id。
- resume paused 实验后，匹配接口重新返回 experiment_id。
- end 实验后不能恢复。
- 操作审计可查询。

### 10.3 前端验收标准

必须通过：

```text
npm.cmd run build
```

前端行为：

- `/admin-ra/rule-releases` 可打开。
- 可从规则列表或详情进入发布动作。
- 发布检查结果正确展示 blocker/warning。
- blocker 存在时发布按钮禁用。
- warning 存在时需要确认后才能发布。
- 实验列表可暂停、恢复、结束实验。
- 操作成功后列表刷新。

### 10.4 浏览器/手工验收脚本

建议新增：

```text
frontend/wechat-prototype/output/playwright/manual-rp309-flow.cjs
```

流程：

1. 登录或获取 admin token。
2. 创建一个 testing 规则版本。
3. 创建同 scope/template 的 running 实验。
4. 打开 `/admin-ra/rule-releases`。
5. 对 testing 规则运行发布检查，确认展示 `running_experiment_conflict`。
6. 打开 `/admin-ra/rule-experiments`，暂停实验。
7. 回到发布治理页，重新检查，确认可发布或仅有 warning。
8. 确认发布。
9. 触发一次求职者匹配，确认 response `source.rule_config_id` 为新 active，且 `experiment_id` 为空。
10. 查询操作审计，确认有 pause 和 publish 记录。

截图建议：

- `frontend/wechat-prototype/output/playwright/rp309-release-blocked.png`
- `frontend/wechat-prototype/output/playwright/rp309-experiment-paused.png`
- `frontend/wechat-prototype/output/playwright/rp309-release-published.png`
- `frontend/wechat-prototype/output/playwright/rp309-operation-audits.png`

## 第十一章：开发者交接说明

你要实现的是 R-P3-09 规则发布治理，不是重做规则编辑、实验效果或质量看板。

先从后端做起：

1. 在 `backend/job-platform/app/modules/match/models.py` 增加 `MatchRuleOperationAuditModel`。
2. 增加 Alembic migration，创建 `match_rule_operation_audits`。
3. 在 `schemas.py` 增加 release-check、publish、experiment status update、operation audit 的 request/response。
4. 在 `writes.py` 或新的 governance service 中实现：
   - 发布检查。
   - 发布事务。
   - 实验状态变更。
   - 操作审计写入。
5. 在 `matches.py` 暴露接口：
   - `GET /rule-configs/{config_id}/release-check`
   - `POST /rule-configs/{config_id}/publish`
   - `POST /rule-experiments/{experiment_id}/status`
   - `GET /rule-operation-audits`

不要重新解释这些硬约束：

- 同一 `scope + template_key + strategy` 最多一个 active。
- 同一 `scope + template_key` 最多一个 running 实验。
- running 实验冲突必须阻断发布。
- archived 规则不能直接发布。
- ended 实验不能恢复。
- 发布和实验状态变更必须写操作审计。
- R-P3-07 的运行时匹配选择顺序不能改变。

前端优先改 react-admin：

1. 在 `frontend/wechat-prototype/src/admin-ra/app/dataProvider.js` 增加 release-check、publish、experiment status update、operation audit 方法。
2. 新增 `resources/rule-releases` 页面并挂到 `AdminRaApp.jsx` 菜单。
3. 在 `resources/match-rules/show.jsx` 增加发布检查面板。
4. 在 `resources/rule-experiments/list.jsx` 增加暂停、恢复、结束动作。
5. 保持现有 `/admin-ra/rule-experiments` 效果和审计面板可用。

验收时你必须跑：

```text
.\.venv\Scripts\pytest.exe -q tests\test_api\test_matches.py
npm.cmd run build
node frontend/wechat-prototype/output/playwright/manual-rp309-flow.cjs
```

已知未知：

- 当前系统只有 `admin/seeker/recruiter`，不要在 P0 强行落库新角色。
- 当前没有投递转化质量指标，R-P3-09 不要实现质量运营看板。
- 当前运行时未按 `effective_from/effective_to` 过滤 active 规则；P0 发布接口应避免未来生效窗口导致运行时语义不一致。

完成后更新：

- `docs/HANDOFF.json`
- `docs/p3-match/P3_人岗匹配与规则配置协作计划.md`
- 如有接口细节变更，新增或补充 R-P3-09 接口契约文档
