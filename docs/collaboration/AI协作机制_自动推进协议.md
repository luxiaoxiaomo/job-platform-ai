# AI 协作自动推进协议

> 让 Claude 与 Codex 在同一工作目录下协作，减少人工传话。核心：用一份机器可读的交接状态文件驱动自动推进。

## 一、复盘：当前协作的痛点

走过 P2 / P3-01 ~ P3-04，当前的协作模式是：

1. Codex 完成后端，在 `docs/resume-foundation/简历解析底座_协作看板.md` 写一段散文同步。
2. 用户读懂后，把"交接重点"转述给 Claude。
3. Claude 做完前端，再写一段散文同步。
4. 用户再转述给 Codex。

痛点很明确：

- **交接信号埋在散文里**：下一个 AI 要"读一段话"才能知道该不该开工。判断成本高、易漏。
- **触发依赖人**：所有推进都需要用户开口说"推进 R-P3-04"，AI 不会自己判断是否就绪。
- **状态分散**：任务状态、依赖、就绪标志散落在看板的多个同步段里，没有单一真相源。
- **契约对齐靠口头**：接口字段谁新增、谁破坏，靠人记忆，没有强约束。

目标不是消灭沟通，而是把**机械的"判断是否就绪 + 认领推进"**自动化，把人的精力留给真正的决策。

## 二、核心机制：单一交接状态文件

新增一份**始终最新**的交接文件，作为两个 AI 的"握手点"：

```
docs/HANDOFF.json
```

它是机器可读的（JSON），人也容易看懂。**任何一个 AI 启动 / 完成任务时，第一件事就是读写这个文件**。

### 文件结构

```json
{
  "schema_version": 1,
  "last_updated_by": "claude",
  "last_updated_at": "2026-06-17T16:00:00",
  "current_focus": "R-P3-04 规则配置落库 + 只读管理页",

  "tasks": [
    {
      "id": "R-P3-04A",
      "owner": "codex",
      "role": "backend",
      "status": "done",
      "ready_for_next": true,
      "files": ["backend/job-platform/app/modules/match/*", "backend/job-platform/app/api/v1/matches.py"],
      "summary": "match_rule_configs / dimensions 表已落库，查询 API 完成，迁移已执行",
      "unblocks": ["R-P3-04B"],
      "notes": "后端服务需重启 + alembic upgrade head 才生效"
    },
    {
      "id": "R-P3-04B",
      "owner": "claude",
      "role": "frontend",
      "status": "blocked",
      "ready": false,
      "blocked_by": ["R-P3-04A:backend-restart"],
      "files": ["frontend/wechat-prototype/src/admin/AdminMatchRules.jsx"],
      "summary": "规则详情只读页已实现，等后端服务重启后联调"
    }
  ],

  "signals": {
    "pending_for_claude": [],
    "pending_for_codex": ["R-P3-04A:backend-restart"]
  }
}
```

### 关键字段约定

| 字段 | 含义 | 取值 |
| --- | --- | --- |
| `status` | 任务状态 | `todo` / `in_progress` / `blocked` / `review` / `done` |
| `ready` / `ready_for_next` | 下游是否可开工 | `true` / `false` |
| `owner` | 负责的 AI | `claude` / `codex` / `both` |
| `blocked_by` | 被什么阻塞 | 任务 ID 列表，可带后缀 `:reason` |
| `unblocks` | 完成后解锁哪些任务 | 任务 ID 列表 |
| `signals.pending_for_*` | 谁有活可干 | 任务 ID 或 `id:reason` |

**最重要的一条**：`signals.pending_for_claude` 和 `signals.pending_for_codex` 是**每个 AI 启动时只需看这一个字段**，就知道自己有没有事做。这是把"读一段话判断"压缩成"读一个字段判断"。

## 三、自动推进的工作流

### 每个 AI 的开机动作

无论谁被唤醒（用户叫、cron 触发、loop 触发），第一步固定：

```
1. 读 docs/HANDOFF.json
2. 看 signals.pending_for_<自己>
3. 如果有就绪任务 → 认领、把 status 改 in_progress、推进
4. 如果没有 → 报告"无待推进任务"，退出
```

### 完成任务后的动作

```
1. 把自己任务 status 改 done，ready_for_next = true
2. 找 unblocks 指向的下游任务，把它们的 blocked_by 移除、ready = true
3. 更新 signals.pending_for_<对方>，把解锁的任务放进去
4. last_updated_by / last_updated_at 更新
5. 写回 docs/HANDOFF.json
```

这样**交接是自动发生的**：Codex 完成后端，文件里立刻出现 `pending_for_claude: ["R-P3-04B"]`，Claude 下次被唤醒就直接认领，不需要人传话。

## 四、契约优先：先写接口再写实现

所有涉及前后端的任务，**先在 HANDOFF.json 或独立 contract 文件里固化接口契约，再各自实现**。字段只新增、不破坏、不改名，破坏必须先做兼容期。

每个跨端任务在 `tasks[].files` 里同时写明：

- `contract`：契约文档路径
- `backend`：后端实现文件边界
- `frontend`：前端实现文件边界

文件锁规则不变（看板里已有）：Alembic 永远 Codex 建，seeker 前端页面默认 Claude 改，越界先在对话里说明。

## 五、定时触发（可选，按需开启）

用 Claude Code 的 cron 能力做轻量巡检。**注意**：cron 只是"提醒 + 巡检"，不强制自动改代码；是否真推进仍以文件状态为准。

```
每 30 分钟巡检一次：
1. 读 HANDOFF.json
2. 如果 signals.pending_for_claude 非空 → 推进第一个就绪任务
3. 如果为空 → 静默退出，不打扰用户
```

建议用偏移的分钟数（如 `*/23 * * * *` 或 `7,37 * * * *`），避免整点撞车。Codex 那边如有类似的 Thread Automation，约定**两边都只在文件状态为 ready 时才动手**，避免同时改同一文件。

## 六、与现有看板的关系

- `docs/resume-foundation/简历解析底座_协作看板.md`：**人读**的全量记录、复盘、同步散文。继续保留。
- `docs/HANDOFF.json`：**机读**的当前状态、就绪信号。单一真相源，驱动自动推进。
- `docs/p3-match/R-P3-XX_*.md`：**契约与设计**文档。不变。

看板负责"发生了什么"，HANDOFF 负责"接下来该谁做什么"。

## 七、落地步骤

1. 建一个初始 `docs/HANDOFF.json`（见结构示例）。
2. 我和 Codex 约定：每次开工先读它，每次收工先写它。
3. 用户不再需要传话，只需定时说一句"巡检 HANDOFF，有就绪任务就推进"，或挂一个 cron。
4. 跑两轮 P3-04 / P3-05 验证流程顺不顺，再迭代字段。

## 八、为什么是 JSON 而不是更多 markdown

- 解析可靠：AI 读 JSON 不会误判"就绪 / 未就绪"。
- 字段强制：`ready` / `owner` / `blocked_by` 是布尔 / 枚举，不会像散文那样含糊。
- diff 清晰：状态变更只动几个字段，git diff 一眼看出谁解锁了谁。

散文同步仍有价值（解释为什么），但放在看板的同步段，不承担"触发推进"的职责。
