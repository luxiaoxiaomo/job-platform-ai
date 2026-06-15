/**
 * P1 阶段 Mock 数据
 * 对应 docs/简历解析底座_多AI协作计划.md 的 P1 API Contract
 */

// GET /api/v1/resumes/me 的 mock 返回
export const mockResumeStatusP1 = {
  has_resume: true,
  resume: {
    id: 12,
    seeker_id: 1,
    file_url: "/uploads/resumes/1_20260615_100000.docx",
    file_name: "王明简历.docx",
    content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    file_size: 36212,
    parsed_snapshot: "已上传简历文件，当前生成规则快照；后续可接入 AI 精细解析。",
    created_at: "2026-06-15T10:00:00",
    updated_at: "2026-06-15T10:00:00"
  },
  latest_upload: {
    id: 45,
    status: "parsed",  // uploaded | processing | parsed | failed
    original_file_name: "王明简历.docx",
    file_ext: ".docx",
    file_size: 36212,
    created_at: "2026-06-15T10:00:00"
  },
  latest_parse_run: {
    id: 81,
    status: "succeeded",  // pending | running | succeeded | completed_with_errors | failed
    parser_version: "resume-parser-v1",
    extractor: "docx",
    error_message: null,
    created_at: "2026-06-15T10:00:00",
    finished_at: "2026-06-15T10:00:03"
  }
}

// POST /api/v1/resumes/me/upload 的 mock 返回
export const mockUploadResponseP1 = {
  resume: {
    id: 12,
    seeker_id: 1,
    file_url: "/uploads/resumes/1_20260615_100000.docx",
    file_name: "王明简历.docx",
    content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    file_size: 36212,
    parsed_snapshot: "已上传简历文件，当前生成规则快照；后续可接入 AI 精细解析。",
    created_at: "2026-06-15T10:00:00",
    updated_at: "2026-06-15T10:00:00"
  },
  upload: {
    id: 45,
    status: "processing",  // 刚上传，解析中
    original_file_name: "王明简历.docx",
    file_ext: ".docx",
    file_size: 36212,
    created_at: "2026-06-15T10:00:00"
  },
  parse_run: {
    id: 81,
    status: "running",  // 解析任务正在执行
    parser_version: "resume-parser-v1",
    extractor: "docx",
    error_message: null,
    created_at: "2026-06-15T10:00:00"
  }
}

// 解析历史列表 mock 数据（假设有多次上传）
export const mockParseHistoryP1 = [
  {
    upload_id: 45,
    file_name: "王明简历.docx",
    file_size: 36212,
    upload_time: "2026-06-15T10:00:00",
    upload_status: "parsed",
    parse_run_id: 81,
    parse_status: "succeeded",
    extracted_text_preview: "王明 | 男 | 本科 | 5年工作经验\n\n工作经历：\n2021-2024 某互联网公司 高级前端工程师\n负责公司核心业务系统前端开发...",
    error_message: null
  },
  {
    upload_id: 44,
    file_name: "王明简历_v2.docx",
    file_size: 35180,
    upload_time: "2026-06-14T15:30:00",
    upload_status: "parsed",
    parse_run_id: 80,
    parse_status: "completed_with_errors",
    extracted_text_preview: "王明 | 男 | 本科\n\n工作经历：\n某互联网公司 前端工程师\n部分字段解析失败",
    error_message: "部分字段置信度过低"
  },
  {
    upload_id: 43,
    file_name: "旧版简历.doc",
    file_size: 28900,
    upload_time: "2026-06-10T09:15:00",
    upload_status: "failed",
    parse_run_id: 79,
    parse_status: "failed",
    extracted_text_preview: null,
    error_message: "不支持 .doc 格式，请使用 .docx"
  }
]

// 原文预览 mock 数据
export const mockExtractedTextP1 = {
  upload_id: 45,
  parse_run_id: 81,
  full_text: `王明 | 男 | 本科 | 5年工作经验
联系方式：138****5678 | wangming@example.com
期望岗位：高级前端工程师 | 期望薪资：20-30K

工作经历
───────────────────────────────────
2021.03 - 2024.06  某互联网公司  高级前端工程师
• 负责公司核心业务系统前端开发，使用 React + TypeScript 技术栈
• 主导前端架构升级，引入微前端方案，提升团队开发效率 30%
• 优化首屏加载性能，使用代码分割和懒加载，首屏时间从 3s 降至 1.2s
• 带领 5 人前端团队，负责技术选型和代码 Review

2019.07 - 2021.02  某创业公司  前端工程师
• 从 0 到 1 搭建公司官网和管理后台，独立完成前端架构设计
• 使用 Vue.js 开发 SPA 应用，配合 Element UI 快速迭代产品
• 参与产品需求评审，与设计师、后端工程师紧密协作

教育经历
───────────────────────────────────
2015.09 - 2019.06  某大学  计算机科学与技术  本科

技能特长
───────────────────────────────────
• 前端框架：React、Vue.js、Angular（熟练）
• 语言：JavaScript、TypeScript、HTML5、CSS3
• 工程化：Webpack、Vite、Babel、ESLint
• 状态管理：Redux、Mobx、Pinia
• UI 框架：Ant Design、Element UI、Material-UI
• 其他：微前端（qiankun）、性能优化、前端安全

项目经历
───────────────────────────────────
【某企业级管理系统】2022.06 - 2024.06
项目描述：面向企业内部的综合管理平台，包含 HR、财务、OA 等多个子系统
技术栈：React 18 + TypeScript + Ant Design + qiankun
我的职责：
• 担任前端技术负责人，主导微前端架构设计
• 封装 30+ 业务组件库，提升开发效率
• 建立前端规范和 CI/CD 流程

【某电商平台前台】2020.03 - 2021.02
项目描述：面向 C 端用户的电商平台，包含商品展示、购物车、订单管理等功能
技术栈：Vue 2 + Vuex + Element UI
我的职责：
• 负责首页、商品详情页、购物车等核心页面开发
• 优化移动端适配，实现响应式布局
• 对接后端 API，处理复杂业务逻辑

自我评价
───────────────────────────────────
5 年前端开发经验，熟练掌握 React/Vue 等主流框架，有丰富的企业级项目经验。
注重代码质量和用户体验，善于解决复杂技术问题。
具备良好的团队协作能力和技术分享精神，曾多次在团队内部做技术分享。
对新技术保持好奇心，持续学习前端领域最新技术动态。`,
  quality_score: 85,
  page_count: 2,
  word_count: 1250
}
