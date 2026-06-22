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
| [P3_人岗匹配与规则配置协作计划.md](./p3-match/P3_人岗匹配与规则配置协作计划.md) | **P3 总纲** |
| [R-P3-01_人岗匹配规则版协作说明.md](./p3-match/R-P3-01_人岗匹配规则版协作说明.md) | 规则版匹配 API 起点 |
| [R-P3-03_匹配规则配置化协作计划.md](./p3-match/R-P3-03_匹配规则配置化协作计划.md) | 配置结构与解释字段 |
| [R-P3-04_规则配置落库与只读管理页协作计划.md](./p3-match/R-P3-04_规则配置落库与只读管理页协作计划.md) | 规则落库 + 只读管理页 |

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

- **进行中**：P3 — 真实画像 + 真实岗位 + 可解释匹配 + 可配置规则
- **下一步**：R-P3-04 联调 → R-P3-05 规则编辑与版本生成
- **真相源**：[`HANDOFF.json`](./HANDOFF.json)
