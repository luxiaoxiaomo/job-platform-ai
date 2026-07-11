# docs 目录整理说明（给 Codex）

> 由 Claude 在 2026-06-17 完成 docs/ 重构。本文档说明改了什么、你需要同步什么。
> **请 Codex 在下次开工前读一遍。**

## 一、做了什么

把 docs/ 根目录下散落的 50+ 文件，按主题归到 6 个子目录，并修复了所有内部交叉引用。

### 新结构

```
docs/
├── HANDOFF.json              # 机读交接状态（单一真相源，路径未变，仍在根目录）
├── INDEX.md                  # 新增：文档导航总览
├── product/                  # 产品与需求（PRD、路线图、竞品、成本等，13 个）
├── architecture/             # 架构与设计（FastAPI 架构、开发设计等，7 个）
├── resume-foundation/        # 简历解析底座 P2（看板、技术设计、联调方案等，14 个）
├── p3-match/                 # 人岗匹配 P3（总纲 + R-P3-01/03/04，4 个）
├── collaboration/            # 多 AI 协作机制（协作约定、自动推进协议等，5 个）
└── archive/                  # 历史归档（旧联调报告、原始记录、原型文件，13 个）
```

根目录现在只剩 `HANDOFF.json` 和 `INDEX.md` 两个入口。

## 二、关键路径迁移对照（你最常引用的）

| 旧路径 | 新路径 |
| --- | --- |
| `docs/简历解析底座_协作看板.md` | `docs/resume-foundation/简历解析底座_协作看板.md` |
| `docs/简历解析底座技术设计.md` | `docs/resume-foundation/简历解析底座技术设计.md` |
| `docs/P3_人岗匹配与规则配置协作计划.md` | `docs/p3-match/P3_人岗匹配与规则配置协作计划.md` |
| `docs/R-P3-01_人岗匹配规则版协作说明.md` | `docs/p3-match/R-P3-01_人岗匹配规则版协作说明.md` |
| `docs/R-P3-03_匹配规则配置化协作计划.md` | `docs/p3-match/R-P3-03_匹配规则配置化协作计划.md` |
| `docs/R-P3-04_规则配置落库与只读管理页协作计划.md` | `docs/p3-match/R-P3-04_规则配置落库与只读管理页协作计划.md` |
| `docs/多AI协作约定.md` | `docs/collaboration/多AI协作约定.md` |
| `docs/本地测试账号.md` | `docs/collaboration/本地测试账号.md` |

`docs/HANDOFF.json` **路径不变**，仍在根目录。

## 三、已经做的事

- ✅ 所有 docs 内部 markdown 交叉引用已批量更新（`docs/X.md` → `docs/<主题>/X.md`）。
- ✅ `HANDOFF.json` 内的 `kanban_doc` / `protocol_doc` 字段已更新到新路径。
- ✅ 用 `mv` 而非删除，git 会识别为重命名，历史保留。
- ✅ 新增 `docs/INDEX.md` 作为导航总览。

## 四、需要你（Codex）同步的事项

1. **如果你有硬编码的文档路径**（例如 thread automation、脚本、或同步流程里写死了 `docs/简历解析底座_协作看板.md` 这类旧路径），请改为上表的新路径。
2. **后续写同步/看板时，引用其他文档请用新路径**。不确定路径时，先查 `docs/INDEX.md`。
3. **新文档归位规则**：
   - 后端 API 契约 / 表设计 → `docs/resume-foundation/` 或 `docs/p3-match/`（按阶段）
   - 联调方案、测试方案 → 对应阶段目录
   - 一次性进度同步、旧报告 → `docs/archive/`
4. **HANDOFF.json 维护方式不变**：仍是机读交接真相源，路径引用已更新。

## 五、当前未变的协作约定

- 多 AI 协作约定本身没变，只是文件位置挪了：`docs/collaboration/多AI协作约定.md`。
- 文件锁规则不变：Alembic 永远由你建，seeker 前端页面默认 Claude 改。
- 接口契约优先、字段只增不改。

## 六、当前任务状态（R-P3-04）

R-P3-04 前后端代码都已完成，唯一阻塞点在你这边：

- `signals.pending_for_codex` = `["R-P3-04A:backend-restart-and-migrate"]`
- 需要 `alembic upgrade head` + 重启后端服务，新路由 `/api/v1/matches/rule-configs/*` 才会生效（当前返回 404）。
- 完成后 R-P3-04B 即可联调。

详见 `docs/HANDOFF.json`。
