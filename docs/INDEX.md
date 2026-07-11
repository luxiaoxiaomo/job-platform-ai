# 📚 文档索引

> 本文件是 docs/ 的导航总览。按主题分子目录，每个文档附一句话说明。
> 当前真相源见 [`HANDOFF.json`](./HANDOFF.json)（机读交接状态）。

## 🗂 目录结构

```
docs/
├── HANDOFF.json              # 机读交接状态（单一真相源，驱动自动推进）
├── INDEX.md                  # 本文件
├── product/                  # 产品与需求
├── architecture/             # 架构与设计
├── resume-foundation/        # 简历解析底座（P2）
├── p3-match/                 # 人岗匹配与规则配置（P3）
├── p4-intelligent-matching/  # 智能匹配（P4）
├── acceptance/               # 本地联调与业务验收
├── audit/                    # 上线前技术体检
├── demo/                     # 演示环境与样例数据
├── operations/               # 运营治理流程
├── collaboration/            # 多 AI 协作机制
└── archive/                  # 历史归档（旧联调报告、原始记录、原型文件）
```

---

## product/ — 产品与需求

| 文档 | 说明 |
| --- | --- |
| [PRD_空岗信息发布对接平台v2.md](./product/PRD_空岗信息发布对接平台v2.md) | 产品需求文档 V2（主文档） |
| [PRD评审报告_空岗信息发布对接平台v2.md](./product/PRD评审报告_空岗信息发布对接平台v2.md) | PRD 评审结论 |
| [产品脑暴_空岗信息发布对接平台.md](./product/产品脑暴_空岗信息发布对接平台.md) | 早期产品构思 |
| [需求优先级排序_空岗信息发布对接平台.md](./product/需求优先级排序_空岗信息发布对接平台.md) | 需求优先级 |
| [用户故事拆解_空岗信息发布对接平台.md](./product/用户故事拆解_空岗信息发布对接平台.md) | 用户故事 |
| [用户反馈分析_空岗信息发布对接平台.md](./product/用户反馈分析_空岗信息发布对接平台.md) | 用户反馈 |
| [竞品分析_空岗信息发布对接平台.md](./product/竞品分析_空岗信息发布对接平台.md) | 竞品对标 |
| [路线图_空岗信息发布对接平台.md](./product/路线图_空岗信息发布对接平台.md) | 产品路线图 |
| [成本估算_空岗信息发布对接平台.md](./product/成本估算_空岗信息发布对接平台.md) | 成本估算 |
| [实施方案_29条需求_20260603.md](./product/实施方案_29条需求_20260603.md) | 29 条需求实施方案 |
| [需求清单_语音记录20260603.md](./product/需求清单_语音记录20260603.md) | 语音需求记录 |

## architecture/ — 架构与设计

| 文档 | 说明 |
| --- | --- |
| [架构设计_Python_FastAPI_空岗平台.md](./architecture/架构设计_Python_FastAPI_空岗平台.md) | FastAPI 技术架构（主设计） |
| [开发设计文档_空岗平台.md](./architecture/开发设计文档_空岗平台.md) | 开发设计 |
| [实现架构_本轮需求_20260604.md](./architecture/实现架构_本轮需求_20260604.md) | 本轮需求实现架构 |
| [AI能力矩阵_参考文档.md](./architecture/AI能力矩阵_参考文档.md) | AI 能力规划 |
| [设计遗漏检查清单.md](./architecture/设计遗漏检查清单.md) | 设计自查清单 |

## resume-foundation/ — 简历解析底座（P2）

| 文档 | 说明 |
| --- | --- |
| [简历解析底座技术设计.md](./resume-foundation/简历解析底座技术设计.md) | 技术方案（Codex 维护，最终依据） |
| [简历解析底座_协作看板.md](./resume-foundation/简历解析底座_协作看板.md) | 全量协作看板（人读记录） |
| [简历解析底座_多AI协作计划.md](./resume-foundation/简历解析底座_多AI协作计划.md) | 多 AI 协作计划 |
| [简历解析底座_技术评审清单.md](./resume-foundation/简历解析底座_技术评审清单.md) | 技术评审清单 |
| [R-P2-02_字段映射文档.md](./resume-foundation/R-P2-02_字段映射文档.md) | STIC 字段到明细表映射 |
| [结构化简历解析方案_讨论稿.md](./resume-foundation/结构化简历解析方案_讨论稿.md) | 结构化解析讨论 |
| [简历画像能力梳理.md](./resume-foundation/简历画像能力梳理.md) | 画像能力边界 |
| [Claude_P2任务安排.md](./resume-foundation/Claude_P2任务安排.md) | Claude P2 任务安排 |
| [P2阶段完成总结.md](./resume-foundation/P2阶段完成总结.md) | P2 总结 |
| [联调测试方案_P1简历.md](./resume-foundation/联调测试方案_P1简历.md) | P1 联调方案 |
| [联调测试方案_P2画像.md](./resume-foundation/联调测试方案_P2画像.md) | P2 画像联调方案 |
| [STIC_表设计_核心表结构摘要.md](./resume-foundation/STIC_表设计_核心表结构摘要.md) | STIC 表设计摘要 |

## p3-match/ — 人岗匹配与规则配置（P3）

| 文档 | 说明 |
| --- | --- |
| [P3_人岗匹配与规则配置产品化收尾.md](./p3-match/P3_人岗匹配与规则配置产品化收尾.md) | P3 完成范围与剩余边界 |
| [P3_人岗匹配与规则配置协作计划.md](./p3-match/P3_人岗匹配与规则配置协作计划.md) | P3 总纲 |
| [R-P3-10_匹配质量运营看板_PRD.md](./p3-match/R-P3-10_匹配质量运营看板_PRD.md) | Match Quality 管理端能力 |
| [R-P4-01_Match_Quality_P1_分层质量分析与调优建议_PRD.md](./p3-match/R-P4-01_Match_Quality_P1_分层质量分析与调优建议_PRD.md) | 分层质量分析与调优建议 |

## p4-intelligent-matching/ — 智能匹配（P4）

| 文档 | 说明 |
| --- | --- |
| [P4_智能匹配_MVP_PRD.md](./p4-intelligent-matching/P4_智能匹配_MVP_PRD.md) | P4 产品范围与业务边界 |
| [P4_智能匹配_接口契约与算法边界.md](./p4-intelligent-matching/P4_智能匹配_接口契约与算法边界.md) | API、评分和降级边界 |
| [P4_智能匹配_代码实现入口计划.md](./p4-intelligent-matching/P4_智能匹配_代码实现入口计划.md) | 当前实现入口 |
| [P4_智能匹配_手动测试指南.md](./p4-intelligent-matching/P4_智能匹配_手动测试指南.md) | 策略、评估、管理端与运行时验收 |
| [P4_人岗匹配评分模型_v0.2_PRD_技术方案.md](./p4-intelligent-matching/P4_人岗匹配评分模型_v0.2_PRD_技术方案.md) | 评分模型技术方案 |

## demo/ — 演示环境

| 文档 | 说明 |
| --- | --- |
| [演示环境与样例数据方案.md](./demo/演示环境与样例数据方案.md) | 演示数据边界、准备、清理和证据要求 |
| [全链路演示文档.md](./demo/全链路演示文档.md) | 20 分钟全链路演示脚本、话术、账号、兜底和验收清单 |

## acceptance/ — 验收

| 文档 | 说明 |
| --- | --- |
| [本地联调测试手册_2026-06-29.md](./acceptance/本地联调测试手册_2026-06-29.md) | 当前本地启动、账号和主要业务流程 |
| [核心业务闭环验收_空岗发布平台.md](./acceptance/核心业务闭环验收_空岗发布平台.md) | 核心业务闭环验收范围 |

## collaboration/ — 多 AI 协作机制

| 文档 | 说明 |
| --- | --- |
| [AI协作机制_自动推进协议.md](./collaboration/AI协作机制_自动推进协议.md) | **自动推进协议**（HANDOFF 驱动） |
| [多AI协作约定.md](./collaboration/多AI协作约定.md) | 协作基础约定 |
| [多AI协作指南.md](./collaboration/多AI协作指南.md) | 协作操作指南 |
| [下一阶段多AI分工_投递管理.md](./collaboration/下一阶段多AI分工_投递管理.md) | 投递模块分工 |
| [本地测试账号.md](./collaboration/本地测试账号.md) | 测试账号速查 |

## archive/ — 历史归档

> 旧联调报告、原始语音记录、进度同步、原型交付物。保留备查，不再主动维护。

包含：原始语音记录、前后端联调方案/完成/最终报告、联调阻断修复、项目审核报告、Codex 进度同步、技术讨论邮件草稿、原型 zip/html/xmind 等。

---

## 当前阶段

- **已完成基线**：P3 规则配置、实验、审计、发布治理和 Match Quality。
- **当前状态**：P4 策略管理、离线评估、运行时智能评分、本地 `local_profile_text` provider 和管理端页面已完成本地验证。
- **运行时边界**：存在 `active` 智能策略时启用智能评分；否则使用规则基线。当前管理 API/UI 不提供正式激活/发布治理。
- **下一步**：生产级外部向量 provider、实验 treatment 绑定、生产 E2E 与上线治理。
- **真相源**：[`HANDOFF.json`](./HANDOFF.json)
