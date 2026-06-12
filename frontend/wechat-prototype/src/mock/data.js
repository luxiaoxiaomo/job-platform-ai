/* ============================================================
   Mock 数据模型（迁移自 react-vite-prototype，补齐双端字段）
   对齐 PRD V2.1：AI 摘要、情感标签、面试识别、审核三级、对接闭环
   ============================================================ */

const logoColors = ['#07C160', '#10AEFF', '#FA9D3B', '#7C5CFC', '#FF6B6B', '#36C5C5']
export const pickColor = (i) => logoColors[i % logoColors.length]

/* ---------- 招聘者：我发布的岗位 ---------- */
export const myJobs = [
  { id: 1, name: '前端开发工程师', city: '深圳·南山区', salary: '15K-25K', status: 'online', views: 328, uv: 246, msgs: 12, date: '2026-05-28',
    insight: '浏览量高但留言偏少（互动率3.6%）。可能原因：薪资略低于同区域均值。建议：参考同类岗位上调至 17K-28K，或用 AI 润色突出团队亮点。' },
  { id: 2, name: 'Java开发工程师', city: '深圳·福田区', salary: '18K-30K', status: 'online', views: 256, uv: 198, msgs: 8, date: '2026-05-25' },
  { id: 3, name: 'UI设计师', city: '广州·天河区', salary: '10K-18K', status: 'online', views: 189, uv: 152, msgs: 6, date: '2026-05-22' },
  { id: 4, name: '产品经理', city: '深圳·南山区', salary: '20K-35K', status: 'pending', views: 0, uv: 0, msgs: 0, date: '2026-06-01' },
  { id: 5, name: '数据分析师', city: '深圳·南山区', salary: '15K-25K', status: 'pending', views: 0, uv: 0, msgs: 0, date: '2026-06-02' },
  { id: 6, name: '运维工程师', city: '深圳·南山区', salary: '12K-20K', status: 'closed', views: 98, uv: 80, msgs: 2, date: '2026-04-10' },
]

/* ---------- 应聘者：岗位流（含 AI 一句话亮点） ---------- */
export const feedJobs = [
  { id: 1, name: '高级前端开发工程师', companyShow: '星辰互联（认证企业）', virtual: false, city: '深圳·南山区', salary: '20K-35K',
    tags: ['React', 'TypeScript', 'B端SaaS'], exp: '5年以上', edu: '本科', status: 'viewed',
    aiHighlight: '双休五险一金 · React 资深岗 · 团队技术氛围强', matchScore: 92, logoIdx: 1,
    duty: '1. 负责公司核心 SaaS 产品的前端架构设计与开发；\n2. 主导前端工程化体系建设，提升团队研发效率；\n3. 攻克复杂交互与性能优化难题；\n4. 指导初级工程师，参与技术方案评审；\n5. 与产品、设计协作，保障产品体验落地。',
    require: '1. 本科及以上学历，5年以上前端开发经验；\n2. 精通 React + TypeScript，熟悉前端工程化；\n3. 有大型 B端/SaaS 项目经验者优先；\n4. 良好的沟通能力与团队协作意识；\n5. 持续学习，关注前端技术演进。',
    contactMethod: '企业邮箱（认证后可见）' },
  { id: 2, name: 'Java后端开发工程师', companyShow: '云创数据', virtual: false, city: '深圳·福田区', salary: '18K-30K',
    tags: ['Spring Boot', 'MySQL', '微服务'], exp: '3年以上', edu: '本科', status: 'new',
    aiHighlight: '微服务架构 · 弹性工作 · 技术栈主流', matchScore: 85, logoIdx: 2,
    duty: '1. 负责后端服务的设计、开发与维护；\n2. 参与微服务架构演进；\n3. 保障系统稳定性与性能。',
    require: '1. 3年以上 Java 开发经验；\n2. 熟悉 Spring Boot、MySQL、Redis；\n3. 了解 Kafka 等消息中间件。',
    contactMethod: '微信（认证后可见）' },
  { id: 3, name: 'UI设计师', companyShow: '某互联网公司', virtual: true, city: '广州·天河区', salary: '10K-18K',
    tags: ['Figma', 'B端设计', '设计系统'], exp: '3年以上', edu: '专科', status: 'chatted',
    aiHighlight: '远程友好 · B端设计岗 · 成长空间大', matchScore: 78, logoIdx: 3,
    duty: '1. 负责 B端产品的界面设计；\n2. 维护并迭代设计系统；\n3. 与前端协作还原设计。',
    require: '1. 3年以上 UI 设计经验；\n2. 精通 Figma；\n3. 有 B端设计经验者优先。',
    contactMethod: '企业邮箱（认证后可见）' },
  { id: 4, name: '产品经理（B端）', companyShow: '智链科技（认证企业）', virtual: false, city: '深圳·南山区', salary: '20K-35K',
    tags: ['B端', 'SaaS', '需求分析'], exp: '5年以上', edu: '本科', status: 'starred',
    aiHighlight: '高薪 B端产品岗 · 直管核心业务线', matchScore: 73, logoIdx: 4,
    duty: '1. 负责 B端 SaaS 产品的规划与迭代；\n2. 输出 PRD、协调研发落地；\n3. 跟踪数据，持续优化产品。',
    require: '1. 5年以上 B端产品经验；\n2. 较强的逻辑与沟通能力；\n3. 熟悉 SaaS 商业模式。',
    contactMethod: '手机号（认证后可见）' },
]

/* ---------- 招聘者收到的对话 ---------- */
export const recruiterChats = [
  { id: 1, name: '张伟', virtual: false, job: '前端开发工程师', preview: '请问什么时候方便面试？', time: '10:23', unread: 2, emotion: 'high', logoIdx: 0,
    messages: [
      { from: 'them', text: '您好，我对贵公司的前端开发工程师岗位非常感兴趣。我有5年React开发经验，目前担任前端技术负责人。', time: '10:15', emotion: 'high' },
      { from: 'me', text: '张伟您好！感谢关注。我们团队使用 React + TypeScript，服务于 B端 SaaS 产品，团队8人。', time: '10:20' },
      { from: 'them', text: '听起来很不错！请问什么时候方便安排一次深入沟通？', time: '10:23', emotion: 'high', isInterview: true },
    ] },
  { id: 2, name: '王丽华', virtual: false, job: '前端开发工程师', preview: '想了解更多团队技术栈...', time: '09:45', unread: 1, emotion: 'high', logoIdx: 5,
    messages: [
      { from: 'them', text: '您好，看到前端开发岗位觉得很匹配。我有3年 Vue 和 React 经验。', time: '09:30', emotion: 'high' },
      { from: 'me', text: '王丽华您好！双栈经验很受欢迎。您对 B端产品有了解吗？', time: '09:38' },
      { from: 'them', text: '感谢回复，我想了解更多团队技术栈的细节。', time: '09:45', emotion: 'high' },
    ] },
  { id: 3, name: '陈思', virtual: true, job: 'Java开发工程师', preview: '请问支持远程办公吗？', time: '昨天', unread: 0, emotion: 'medium', logoIdx: 2,
    messages: [
      { from: 'them', text: '您好，我目前在成都，请问深圳的 Java 岗位支持远程吗？', time: '昨天 14:20', emotion: 'medium' },
    ] },
  { id: 5, name: '赵敏', virtual: true, job: '数据分析师', preview: '底薪和提成比例是怎样的？', time: '2天前', unread: 0, emotion: 'low', logoIdx: 4,
    messages: [
      { from: 'them', text: '你好，请问这个岗位的薪资结构是怎样的？', time: '2天前 11:00', emotion: 'low' },
    ] },
]

/* ---------- 应聘者的对话 ---------- */
export const seekerChats = [
  { id: 101, name: '李明辉（星辰互联）', job: '高级前端开发工程师', jobId: 1, preview: '可以安排本周四下午2点线上面试...', time: '10:20', unread: 1, isInterview: true, logoIdx: 1,
    messages: [
      { from: 'me', text: '您好，我对高级前端开发工程师岗位非常感兴趣，有5年React开发经验。', time: '昨天 15:00' },
      { from: 'them', text: '您好！您的背景很匹配。我们团队使用 React + TypeScript，有兴趣进一步了解吗？', time: '昨天 15:30' },
      { from: 'me', text: '非常感兴趣！请问什么时候方便安排一次深入沟通？', time: '昨天 16:00' },
      { from: 'them', text: '可以安排本周四下午2点线上面试，时长约45分钟，请确认时间是否方便。', time: '10:20', isInterview: true },
    ] },
  { id: 102, name: '王经理（云创数据）', job: 'Java后端开发工程师', jobId: 2, preview: '我们的技术栈主要是 Spring Boot...', time: '昨天', unread: 0, isInterview: false, logoIdx: 2,
    messages: [
      { from: 'me', text: '您好，我对 Java 后端岗位感兴趣，请问团队技术栈是什么？', time: '前天 10:00' },
      { from: 'them', text: '感谢留言，我们主要是 Spring Boot + MySQL + Redis + Kafka，团队20人左右。', time: '昨天 09:00' },
    ] },
]

/* ---------- 应聘者订阅 ---------- */
export const initialSubs = [
  { id: 1, keywords: ['前端开发', 'React', 'Web开发'], city: '深圳', salary: '15K+', active: true },
  { id: 2, keywords: ['UI设计', 'Figma', 'B端设计'], city: '深圳, 广州', salary: '10K+', active: true },
  { id: 3, keywords: ['产品经理', 'B端', 'SaaS'], city: '不限', salary: '15K-25K', active: false },
]

/* AI 推荐订阅 */
export const aiRecommendSubs = [
  { keywords: ['高级前端', 'React', 'TypeScript'], city: '深圳', salary: '20K+' },
  { keywords: ['前端架构师', 'Node.js'], city: '深圳, 广州', salary: '30K+' },
]

/* ---------- AI mock 文案 ---------- */
export const aiMock = {
  // OCR 识别营业执照
  ocrLicense: {
    creditCode: '91440300MA5XXXXX1A',
    company: '深圳市星辰互联科技有限公司',
    legal: '王晓明',
    address: '深圳市南山区科技园南区T3栋10层',
    capital: '500万元',
    setupDate: '2018-03-12',
  },
  // JD 代写
  jdDuty: '1. 负责公司核心产品的前端开发与维护；\n2. 参与前端架构设计与技术选型；\n3. 与产品、设计、后端紧密协作，保障需求高质量落地；\n4. 持续优化前端性能与用户体验；\n5. 参与代码评审，沉淀团队技术规范。',
  jdRequire: '1. 本科及以上学历，3年以上前端开发经验；\n2. 精通 HTML/CSS/JavaScript，熟练使用 React 或 Vue；\n3. 熟悉前端工程化与主流构建工具；\n4. 良好的沟通能力与责任心；\n5. 有大型项目或 B端产品经验者优先。',
  salarySuggest: { low: 17, high: 28, marketMedian: 22, benchmarkMedian: 24, benchmarkCompanies: ['星辰互联', '智链科技', '云创数据'], note: '基于「前端开发工程师 + 深圳 + 互联网」的市场数据分析' },
  // 虚拟名候选
  virtualNames: ['李然', '陈默', '周晴'],
  // 智能回复建议（招聘者视角）
  recruiterReplies: [
    { style: '专业正式', text: '您好，感谢您对该岗位的关注。我们可以安排一次线上沟通，您看本周四下午是否方便？届时会详细介绍团队与项目情况。' },
    { style: '热情友好', text: '您好呀～很高兴收到您的留言！您的经验和我们很匹配，要不要约个时间深入聊聊？期待和您交流～' },
    { style: '简洁高效', text: '您好，您的背景符合要求。方便的话本周四下午2点线上面试，请确认时间。' },
  ],
  // 智能回复建议（应聘者视角，润色）
  seekerPolish: '您好，非常感谢您的回复！我对贵公司的技术方向很感兴趣，本周四下午2点的安排我可以准时参加，期待进一步沟通。请问需要我提前准备哪些材料？',
}

export const getFeedJob = (id) => feedJobs.find(j => String(j.id) === String(id))
export const getRecruiterChat = (id) => recruiterChats.find(c => String(c.id) === String(id))
export const getSeekerChat = (id) => seekerChats.find(c => String(c.id) === String(id))

/* ---------- 人岗匹配分析（应聘者视角：我 vs 岗位） ---------- */
export const matchAnalysis = {
  // 默认对岗位1（高级前端）的匹配
  score: 92,
  summary: '你与该岗位高度匹配。核心技能与经验项满分，仅薪资期望略高于岗位上限，建议沟通时灵活表达。',
  dims: [
    { key: '技能匹配', score: 95, note: 'React/TS 完全命中岗位要求' },
    { key: '经验年限', score: 90, note: '5年 ≥ 要求5年' },
    { key: '学历匹配', score: 100, note: '本科 满足要求' },
    { key: '薪资匹配', score: 78, note: '期望22-30K，岗位20-35K，区间重叠' },
    { key: '城市匹配', score: 100, note: '同城（深圳）' },
    { key: '行业相关', score: 88, note: 'B端SaaS 经验高度相关' },
  ],
  gaps: [
    '薪资期望上限略高，建议沟通时强调能力与产出',
    '可补充「项目经历」中量化成果，进一步提升匹配说服力',
  ],
}

/* ---------- 候选人匹配度（招聘者视角：候选人 vs 岗位） ---------- */
export const candidateMatch = {
  name: '张伟', job: '前端开发工程师', score: 88,
  dims: [
    { key: '技能匹配', score: 92 },
    { key: '经验相关', score: 90 },
    { key: '薪资匹配', score: 82 },
    { key: '信息完整', score: 85 },
    { key: '互动积极', score: 95 },
    { key: '稳定性', score: 80 },
  ],
  highlights: ['5年以上相关经验', 'React 技术负责人', '响应及时'],
}

/* 候选人横向对比 */
export const candidateCompare = [
  { name: '张伟', skill: 92, exp: 90, salary: 82, complete: 85, active: 95, best: true },
  { name: '王丽华', skill: 85, exp: 78, salary: 90, complete: 70, active: 88, best: false },
  { name: '陈思', skill: 80, exp: 82, salary: 75, complete: 60, active: 65, best: false },
]

/* ---------- 投递记录（应聘者，含状态时间线） ---------- */
export const myApplications = [
  { id: 1, job: '高级前端开发工程师', company: '星辰互联', salary: '20K-35K', date: '今天 10:30', status: 'viewed', statusText: '已被查看',
    timeline: [
      { node: '已投递', time: '今天 10:30', done: true },
      { node: '招聘者已查看', time: '今天 11:05', done: true },
      { node: '沟通中', time: '今天 14:20', done: true },
      { node: '邀约面试', time: '', done: false },
      { node: '面试结果', time: '', done: false },
    ] },
  { id: 2, job: 'Java后端开发工程师', company: '云创数据', salary: '18K-30K', date: '昨天', status: 'pending', statusText: '待查看',
    timeline: [
      { node: '已投递', time: '昨天 16:00', done: true },
      { node: '招聘者已查看', time: '', done: false },
      { node: '沟通中', time: '', done: false },
      { node: '邀约面试', time: '', done: false },
      { node: '面试结果', time: '', done: false },
    ] },
  { id: 3, job: 'UI设计师', company: '某互联网公司', salary: '10K-18K', date: '3天前', status: 'invited', statusText: '邀面试',
    timeline: [
      { node: '已投递', time: '3天前', done: true },
      { node: '招聘者已查看', time: '3天前', done: true },
      { node: '沟通中', time: '2天前', done: true },
      { node: '邀约面试', time: '今天 09:00', done: true },
      { node: '面试结果', time: '待面试（本周四 14:00）', done: false },
    ] },
]

/* ---------- 收藏的职位 ---------- */
export const favoriteJobs = [
  { id: 1, name: '高级前端开发工程师', company: '星辰互联', city: '深圳·南山区', salary: '20K-35K', offline: false },
  { id: 4, name: '产品经理（B端）', company: '智链科技', city: '深圳·南山区', salary: '20K-35K', offline: false },
  { id: 9, name: '测试工程师', company: '某科技公司', city: '广州·天河区', salary: '12K-20K', offline: true },
]

/* ---------- 数据统计趋势（招聘者） ---------- */
export const statTrend = {
  views: [42, 58, 51, 73, 66, 88, 95],
  msgs: [2, 3, 2, 5, 4, 6, 8],
  days: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
  insights: [
    { phen: '浏览量持续上升', cause: '岗位标准名称 + AI亮点摘要提升了曝光', advice: '保持，可考虑工作日上午置顶' },
    { phen: '留言转化率 8.4%', cause: '高于平台均值（6%）', advice: 'AI智能回复保持快速响应可进一步提升' },
  ],
}

/* ---------- AI 客服 FAQ ---------- */
export const chatbotFAQ = [
  '如何发布岗位？',
  '审核需要多久？',
  '虚拟名怎么用？',
  '联系方式如何交换？',
]
export const chatbotAnswers = {
  '如何发布岗位？': '发布岗位分4步：① 完成企业认证（上传营业执照，AI自动识别）；② 在「我的岗位」点「＋发布」；③ 填写岗位名称/城市/薪资/职责（可用 AI 一键代写）；④ 提交后经 AI 预审+人工审核，通过即上线。',
  '审核需要多久？': '首次提交 48 小时内完成，修改重审 24 小时内完成。AI 预审通过率达标的岗位会更快上线。审核结果会通过微信通知你。',
  '虚拟名怎么用？': '注册时可选「虚拟名」模式，AI 会生成候选虚拟名保护你的隐私。前台仅展示虚拟名，平台后台保留真实信息用于可追溯。虚拟名设定后 30 天内不可更改。',
  '联系方式如何交换？': '为保护双方隐私，留言中禁止手打联系方式。双方互发消息后，任一方可点「请求交换联系方式」，对方确认后即可互见彼此授权公开的联系方式。',
}

/* ---------- 管理后台数据 ---------- */
export const adminStats = {
  kpis: [
    { label: '注册招聘者', value: '2,134', delta: '+128', up: true },
    { label: '注册应聘者', value: '21,580', delta: '+1,043', up: true },
    { label: '在线岗位', value: '5,267', delta: '+312', up: true },
    { label: '今日待审核', value: '38', delta: '紧急', up: false },
  ],
  userTrend: [120, 180, 165, 230, 280, 320, 410],
  jobTrend: [80, 110, 95, 160, 190, 210, 260],
}

export const adminReviewQueue = [
  { id: 1, type: '企业资质', company: '深圳市创新科技有限公司', submitter: '王晓明', time: '10:35', aiResult: 'pass', aiNote: 'AI预审通过，OCR验证一致', risk: 'low' },
  { id: 2, type: '岗位内容', company: '广州云创数据', job: '高薪诚聘全栈工程师', submitter: '张经理', time: '09:48', aiResult: 'warning', aiNote: 'AI检测到歧视性用语：「仅限男性」', risk: 'mid' },
  { id: 3, type: '企业资质', company: '深圳XX金融集团', submitter: '陈某', time: '09:12', aiResult: 'block', aiNote: 'AI初筛命中假冒企业风险：信用代码与企业名不匹配', risk: 'high' },
  { id: 4, type: '岗位内容', company: '杭州灵感设计科技', job: 'UI设计师', submitter: '李芳', time: '昨天', aiResult: 'pass', aiNote: 'AI预审通过，内容合规', risk: 'low' },
  { id: 5, type: '岗位内容', company: '深圳星辰互联', job: '高级前端开发工程师', submitter: '王晓明', time: '昨天', aiResult: 'pass', aiNote: 'AI预审通过', risk: 'low' },
]

export const adminUsers = [
  { id: 1, name: '星辰互联科技', role: '招聘者', verified: true, status: '正常', jobs: 5, date: '2026-03-12' },
  { id: 2, name: '云创数据', role: '招聘者', verified: true, status: '正常', jobs: 3, date: '2026-04-01' },
  { id: 3, name: '李然（虚拟名）', role: '应聘者', verified: true, status: '正常', jobs: '-', date: '2026-05-20' },
  { id: 4, name: '深圳XX金融集团', role: '招聘者', verified: false, status: '风险', jobs: 0, date: '2026-06-01' },
  { id: 5, name: '张伟', role: '应聘者', verified: true, status: '正常', jobs: '-', date: '2026-05-28' },
]

export const adminAIMetrics = [
  { name: 'AI OCR 识别', calls: '1,284', accuracy: '96.2%', avgTime: '2.1s', status: 'good' },
  { name: 'AI 内容审核', calls: '3,572', accuracy: '98.5%', avgTime: '1.3s', status: 'good' },
  { name: 'AI-JD 代写', calls: '892', accuracy: '采纳率 43%', avgTime: '3.4s', status: 'good' },
  { name: 'AI 智能回复', calls: '2,108', accuracy: '采纳率 38%', avgTime: '2.8s', status: 'good' },
  { name: 'AI 语义匹配', calls: '15,620', accuracy: '召回率 82%', avgTime: '0.4s', status: 'warn' },
  { name: 'AI 智能客服', calls: '648', accuracy: '解决率 51%', avgTime: '2.2s', status: 'good' },
]

export const adminJobLib = [
  { id: 1, name: '前端开发工程师', category: '技术/研发', alias: '前端工程师, Web前端', status: '启用' },
  { id: 2, name: '软件开发工程师', category: '技术/研发', alias: '程序员, 开发', status: '启用' },
  { id: 3, name: 'UI设计师', category: '设计', alias: '美工, 界面设计师', status: '启用' },
  { id: 4, name: '产品经理', category: '产品', alias: 'PM, 产品', status: '启用' },
  { id: 5, name: '销售经理', category: '销售', alias: '销售, 业务经理', status: '启用' },
]

export const getMatchAnalysis = (id) => matchAnalysis

/* ---------- 简历解析结果（上传后 AI 解析预填） ---------- */
export const resumeParsed = {
  name: '李然', gender: '男', age: 28, edu: '本科 · 计算机科学与技术',
  exp: '5 年', phone: '138****6677', email: 'liran****@mail.com',
  school: '华南理工大学', major: '软件工程',
  work: [
    { company: '某互联网公司', role: '前端技术负责人', period: '2021-至今', desc: '主导 React + TS 架构升级' },
    { company: '某科技公司', role: '前端工程师', period: '2019-2021', desc: 'B端 SaaS 产品开发' },
  ],
  skills: ['React', 'TypeScript', 'Node.js', 'Webpack', '前端工程化', '性能优化', '团队管理'],
}

/* ---------- 简历画像（应聘者） ---------- */
export const seekerProfile = {
  oneline: '5 年经验的资深前端工程师，技术深度突出、具备团队管理经验，适配中高级前端/前端负责人岗位。',
  level: '中高级',
  tags: [
    { t: 'React 专家', w: 'high' }, { t: 'TypeScript', w: 'high' }, { t: '前端工程化', w: 'high' },
    { t: '团队管理', w: 'mid' }, { t: 'B端 SaaS', w: 'mid' }, { t: '性能优化', w: 'mid' },
    { t: 'Node.js', w: 'low' }, { t: '5年经验', w: 'low' }, { t: '本科', w: 'low' },
  ],
  dims: [
    { key: '技术深度', score: 92 },
    { key: '经验广度', score: 80 },
    { key: '管理能力', score: 75 },
    { key: '学习成长', score: 88 },
    { key: '稳定性', score: 82 },
    { key: '沟通协作', score: 85 },
  ],
  suggest: '可补充开源项目或技术影响力（如技术分享、博客），进一步提升「技术影响力」维度评分。',
  salaryEstimate: { low: 18, high: 28, basis: '深圳·前端开发·5年经验·本科' },
}

/* ---------- 企业画像（招聘者） ---------- */
export const companyProfile = {
  name: '星辰互联科技',
  oneline: '深圳南山的 B端 SaaS 中型科技企业，技术氛围浓厚、福利完善，适合追求技术成长的求职者。',
  tags: [
    { t: '互联网/SaaS', c: 'green' }, { t: '51-200人', c: 'blue' }, { t: '已认证', c: 'green' },
    { t: '双休', c: 'orange' }, { t: '五险一金', c: 'orange' }, { t: '弹性工作', c: 'orange' },
    { t: '技术驱动', c: 'green' }, { t: '扁平管理', c: 'blue' },
  ],
  dims: [
    { key: '规模实力', score: 75 },
    { key: '福利待遇', score: 88 },
    { key: '成长空间', score: 90 },
    { key: '技术氛围', score: 92 },
    { key: '稳定性', score: 80 },
    { key: '雇主口碑', score: 85 },
  ],
}

/* ---------- 岗位画像（招聘者） ---------- */
export const jobProfile = {
  name: '前端开发工程师',
  oneline: '中高级前端岗位，技能要求聚焦 React 生态，薪资处于深圳市场中上水平，适合 3-5 年经验候选人。',
  tags: ['前端开发', 'React', 'TypeScript', '前端工程化', 'B端', '3-5年', '本科'],
  dims: [
    { key: '技能要求', score: 85 },
    { key: '经验门槛', score: 75 },
    { key: '薪资竞争力', score: 80 },
    { key: '学历要求', score: 60 },
    { key: '岗位热度', score: 88 },
    { key: '招聘紧急度', score: 70 },
  ],
}

/* ---------- AI 自动生成的岗位标签（发布时） ---------- */
export const aiJobTags = ['前端开发', 'React', 'TypeScript', '前端工程化', 'B端SaaS', '中高级', '本科', '深圳']

/* ---------- 批量导入岗位（AI 从 Excel 解析） ---------- */
export const batchParsedJobs = [
  { id: 1, name: '前端开发工程师', city: '深圳·南山区', salary: '15K-25K', valid: true, tags: ['React', '本科'] },
  { id: 2, name: 'Java开发工程师', city: '深圳·福田区', salary: '18K-30K', valid: true, tags: ['Spring Boot', '3年+'] },
  { id: 3, name: 'UI设计师', city: '广州·天河区', salary: '10K-18K', valid: true, tags: ['Figma'] },
  { id: 4, name: '产品经理', city: '深圳·南山区', salary: '20K-35K', valid: true, tags: ['B端', '5年+'] },
  { id: 5, name: '销售代表', city: '广州', salary: '面议', valid: false, warn: '薪资为"面议"，建议补充区间以提升曝光' },
  { id: 6, name: '运营专员', city: '深圳', salary: '8K-12K', valid: true, tags: ['新媒体'] },
]

/* ---------- 候选人批量列表（招聘者-所有曾互动的应聘者） ---------- */
export const candidateList = [
  { id: 1, name: '张伟', virtual: false, job: '前端开发工程师', jobId: 1, matchScore: 88, tags: ['5年+React', '技术负责人', '响应快'], lastMsg: '10:23', lastMsgTime: '今天', emotion: 'high', logoIdx: 0, hasResume: true },
  { id: 2, name: '王丽华', virtual: false, job: '前端开发工程师', jobId: 1, matchScore: 82, tags: ['3年Vue+React', '双栈'], lastMsg: '09:45', lastMsgTime: '今天', emotion: 'high', logoIdx: 5, hasResume: true },
  { id: 3, name: '陈思', virtual: true, job: 'Java开发工程师', jobId: 2, matchScore: 76, tags: ['Spring Boot', '远程'], lastMsg: '昨天', lastMsgTime: '昨天', emotion: 'medium', logoIdx: 2, hasResume: false },
  { id: 4, name: '赵敏', virtual: true, job: '数据分析师', jobId: 5, matchScore: 65, tags: ['数据分析', '咨询背景'], lastMsg: '2天前', lastMsgTime: '2天前', emotion: 'low', logoIdx: 4, hasResume: false },
  { id: 5, name: '李然', virtual: true, job: '高级前端开发工程师', jobId: 1, matchScore: 92, tags: ['5年React', 'TS专家', 'B端SaaS'], lastMsg: '昨天', lastMsgTime: '昨天', emotion: 'high', logoIdx: 1, hasResume: true },
  { id: 6, name: '刘洋', virtual: false, job: '产品经理（B端）', jobId: 4, matchScore: 71, tags: ['B端产品', '5年经验'], lastMsg: '3天前', lastMsgTime: '3天前', emotion: 'medium', logoIdx: 3, hasResume: true },
  { id: 7, name: '周晴', virtual: true, job: 'UI设计师', jobId: 3, matchScore: 80, tags: ['Figma专家', 'B端设计'], lastMsg: '1小时前', lastMsgTime: '今天', emotion: 'high', logoIdx: 1, hasResume: true },
  { id: 8, name: '孙磊', virtual: true, job: '运维工程师', jobId: 6, matchScore: 58, tags: ['Linux', '3年经验'], lastMsg: '5天前', lastMsgTime: '5天前', emotion: 'low', logoIdx: 5, hasResume: false },
]

export const getCandidate = (id) => candidateList.find(c => String(c.id) === String(id))

/* ---------- 浏览量穿透：某岗位的访客列表 ---------- */
export const jobVisitors = {
  1: [ // 前端开发工程师 - 328浏览/246人
    { id: 1, name: '张伟', virtual: false, views: 8, lastView: '今天 10:15', matchScore: 88, tags: ['5年+React'], hasChatted: true },
    { id: 2, name: '王丽华', virtual: false, views: 5, lastView: '今天 09:30', matchScore: 82, tags: ['Vue+React'], hasChatted: true },
    { id: 5, name: '李然', virtual: true, views: 12, lastView: '今天 08:22', matchScore: 92, tags: ['React专家'], hasChatted: true },
    { id: 10, name: '陈默', virtual: true, views: 4, lastView: '今天 07:45', matchScore: 85, tags: ['前端5年'], hasChatted: false },
    { id: 11, name: '吴芳', virtual: true, views: 3, lastView: '昨天 22:10', matchScore: 79, tags: ['全栈'], hasChatted: false },
    { id: 12, name: '郑强', virtual: false, views: 6, lastView: '昨天 18:30', matchScore: 72, tags: ['Angular'], hasChatted: false },
    { id: 13, name: '黄丽', virtual: true, views: 2, lastView: '昨天 14:20', matchScore: 68, tags: ['初级前端'], hasChatted: false },
    { id: 14, name: '许杰', virtual: true, views: 1, lastView: '昨天 11:00', matchScore: 55, tags: ['转行中'], hasChatted: false },
    { id: 15, name: '冯敏', virtual: true, views: 7, lastView: '前天 16:45', matchScore: 81, tags: ['React+Node'], hasChatted: false },
  ],
  2: [ // Java后端 - 256浏览/198人
    { id: 3, name: '陈思', virtual: true, views: 6, lastView: '昨天 14:20', matchScore: 76, tags: ['Spring Boot', '远程'], hasChatted: true },
    { id: 16, name: '赵鹏', virtual: false, views: 4, lastView: '今天 11:30', matchScore: 83, tags: ['Java', '微服务'], hasChatted: false },
    { id: 17, name: '钱敏', virtual: true, views: 3, lastView: '昨天 16:00', matchScore: 71, tags: ['后端3年'], hasChatted: false },
    { id: 18, name: '孙洋', virtual: false, views: 5, lastView: '今天 09:00', matchScore: 78, tags: ['Spring Cloud'], hasChatted: false },
  ],
  3: [ // UI设计师 - 189浏览/152人
    { id: 7, name: '周晴', virtual: true, views: 5, lastView: '今天 14:30', matchScore: 80, tags: ['Figma专家'], hasChatted: true },
    { id: 19, name: '吴莉', virtual: true, views: 3, lastView: '昨天 10:00', matchScore: 67, tags: ['UI设计'], hasChatted: false },
    { id: 20, name: '郑美', virtual: false, views: 4, lastView: '今天 08:50', matchScore: 74, tags: ['B端设计'], hasChatted: false },
  ],
  4: [ // 产品经理 - 0浏览 (pending)
  ],
  5: [ // 数据分析师 - 0浏览 (pending)
  ],
  6: [ // 运维工程师 - 98浏览/80人 (closed)
    { id: 8, name: '孙磊', virtual: true, views: 3, lastView: '5天前', matchScore: 58, tags: ['Linux'], hasChatted: false },
    { id: 21, name: '王浩', virtual: false, views: 2, lastView: '4天前', matchScore: 63, tags: ['运维3年'], hasChatted: false },
  ],
}
export const getJobVisitors = (jobId) => jobVisitors[jobId] || []

/* ---------- 人才池：应聘者为中心的全量数据 ---------- */
export const talentPool = [
  { id: 1, name: '张伟', virtual: false, matchAvg: 88, status: 'active', tags: ['5年+React', '技术负责人', '高意向'], appliedJobs: [
    { jobId: 1, jobName: '前端开发工程师', status: 'chatted', date: '2026-06-01' },
    { jobId: 4, jobName: '产品经理（B端）', status: 'viewed', date: '2026-06-02' },
  ], lastActive: '今天 10:23', emotion: 'high', logoIdx: 0, viewed: 18 },
  { id: 5, name: '李然', virtual: true, matchAvg: 92, status: 'active', tags: ['React专家', 'TS', 'B端SaaS'], appliedJobs: [
    { jobId: 1, jobName: '前端开发工程师', status: 'chatted', date: '2026-05-30' },
  ], lastActive: '昨天 16:00', emotion: 'high', logoIdx: 1, viewed: 24 },
  { id: 2, name: '王丽华', virtual: false, matchAvg: 82, status: 'active', tags: ['双栈', 'Vue+React'], appliedJobs: [
    { jobId: 1, jobName: '前端开发工程师', status: 'chatted', date: '2026-06-02' },
  ], lastActive: '今天 09:45', emotion: 'high', logoIdx: 5, viewed: 10 },
  { id: 7, name: '周晴', virtual: true, matchAvg: 80, status: 'active', tags: ['Figma专家', 'B端设计'], appliedJobs: [
    { jobId: 3, jobName: 'UI设计师', status: 'chatted', date: '2026-06-03' },
  ], lastActive: '今天 14:30', emotion: 'high', logoIdx: 1, viewed: 8 },
  { id: 3, name: '陈思', virtual: true, matchAvg: 76, status: 'passive', tags: ['Spring Boot', '远程'], appliedJobs: [
    { jobId: 2, jobName: 'Java开发工程师', status: 'chatted', date: '2026-05-28' },
  ], lastActive: '昨天', emotion: 'medium', logoIdx: 2, viewed: 6 },
  { id: 6, name: '刘洋', virtual: false, matchAvg: 71, status: 'passive', tags: ['B端产品', '5年经验'], appliedJobs: [
    { jobId: 4, jobName: '产品经理（B端）', status: 'chatted', date: '2026-05-29' },
  ], lastActive: '3天前', emotion: 'medium', logoIdx: 3, viewed: 4 },
  { id: 4, name: '赵敏', virtual: true, matchAvg: 65, status: 'passive', tags: ['数据分析'], appliedJobs: [
    { jobId: 5, jobName: '数据分析师', status: 'chatted', date: '2026-05-25' },
  ], lastActive: '2天前', emotion: 'low', logoIdx: 4, viewed: 3 },
  { id: 8, name: '孙磊', virtual: true, matchAvg: 58, status: 'archived', tags: ['Linux'], appliedJobs: [
    { jobId: 6, jobName: '运维工程师', status: 'viewed', date: '2026-05-20' },
  ], lastActive: '5天前', emotion: 'low', logoIdx: 5, viewed: 2 },
  { id: 10, name: '陈默', virtual: true, matchAvg: 85, status: 'active', tags: ['前端5年', '全栈'], appliedJobs: [
    { jobId: 1, jobName: '前端开发工程师', status: 'viewed', date: '2026-06-03' },
  ], lastActive: '今天 07:45', emotion: 'high', logoIdx: 3, viewed: 12 },
  { id: 11, name: '吴芳', virtual: true, matchAvg: 79, status: 'passive', tags: ['全栈', 'Node.js'], appliedJobs: [
    { jobId: 1, jobName: '前端开发工程师', status: 'viewed', date: '2026-06-02' },
  ], lastActive: '昨天 22:10', emotion: 'medium', logoIdx: 2, viewed: 5 },
]

export const talentStats = {
  total: 21,
  newThisMonth: 8,
  activeChatting: 5,
  starred: 3,
}

export const getTalent = (id) => talentPool.find(t => String(t.id) === String(id))

/* ---------- 总体统计（招聘者-全岗位聚合，与 myJobs 对齐） ---------- */
export const aggregateStats = {
  totalViews: 871,     // 328+256+189+0+0+98
  totalUV: 676,         // 246+198+152+0+0+80
  totalMsgs: 28,        // 12+8+6+0+0+2
  totalExchanges: 7,    // 模拟对接成功数
  avgMatch: 78,
  topJobs: [
    { id: 1, name: '前端开发工程师', views: 328 },
    { id: 2, name: 'Java开发工程师', views: 256 },
    { id: 3, name: 'UI设计师', views: 189 },
    { id: 6, name: '运维工程师', views: 98 },
    { id: 4, name: '产品经理（B端）', views: 0 },
  ],
}

/* ---------- 跟进提醒（招聘者，B-补4） ---------- */
export const followUpReminders = [
  { id: 1, name: '张伟', virtual: false, job: '前端开发工程师', logoIdx: 0, matchScore: 88,
    reason: '高意向候选人，已 2 天未跟进', level: 'urgent', lastActive: '2天前' },
  { id: 2, name: '王丽华', virtual: false, job: '前端开发工程师', logoIdx: 5, matchScore: 82,
    reason: '已读未回复，建议主动沟通', level: 'normal', lastActive: '今天 09:45' },
  { id: 7, name: '周晴', virtual: true, job: 'UI设计师', logoIdx: 1, matchScore: 80,
    reason: '面试邀约待对方确认', level: 'normal', lastActive: '今天 14:30' },
]

/* ---------- JD 吸引力分析（招聘者，B-补7） ---------- */
export const jdAttractiveness = {
  score: 72,
  level: '中等',
  factors: [
    { key: '薪资竞争力', score: 65, note: '略低于同区域同岗位中位值（22K）', good: false },
    { key: '职责清晰度', score: 88, note: 'JD 结构化、要点清晰', good: true },
    { key: '亮点突出度', score: 70, note: '可强化"双休/技术氛围"等吸引点', good: false },
    { key: '门槛合理性', score: 85, note: '学历经验要求适中，候选池较大', good: true },
  ],
  suggestions: [
    '薪资上调至 17K-28K 可提升约 35% 浏览转化',
    'JD 开头增加一句团队/项目亮点，提升点击率',
    '"任职要求"中"5年经验"可放宽至"3-5年"，扩大候选池',
  ],
  benchmark: { myConversion: 3.6, avgConversion: 6.2 }, // 浏览→留言转化率%
}

/* ---------- AI 面试准备（应聘者，A-补9） ---------- */
export const interviewPrep = {
  job: '高级前端开发工程师',
  company: '星辰互联',
  time: '本周四 14:00（线上）',
  companyBrief: '星辰互联是深圳南山的 B端 SaaS 中型科技企业（51-200人），技术氛围浓厚、双休五险一金，主营企业级数据中台产品。',
  commonQuestions: [
    { q: 'React 性能优化你做过哪些实践？', tip: '准备 2-3 个具体案例：useMemo/虚拟列表/打包优化，最好有量化数据' },
    { q: '如何设计一个可复用的组件库？', tip: '从 API 设计、主题定制、文档、版本管理几个维度展开' },
    { q: '描述一次你主导的技术攻关', tip: '用 STAR 法则：背景-任务-行动-结果，突出你的角色和量化成果' },
    { q: '为什么离开上一家？为什么选我们？', tip: '正向表达，结合公司 B端 SaaS 方向谈你的兴趣和匹配' },
  ],
  tips: [
    '提前 5 分钟进入会议，检查网络和摄像头',
    '准备 2-3 个反问问题（团队规模、技术栈演进、成长路径）',
    '基于你的简历画像，重点突出 React/TS 深度和团队管理经验',
  ],
}

/* ---------- 团队协作备注（招聘者内部，按候选人 id 索引） ---------- */
export const teamNotes = {
  1: [ // 张伟
    { id: 1, author: '王晓明（HR）', text: '电话初筛通过，技术背景扎实，约了周四面试', time: '今天 11:20' },
    { id: 2, author: '李总（用人部门）', text: '简历看了，重点考察架构能力和团队管理', time: '今天 14:05' },
  ],
  5: [ // 李然
    { id: 1, author: '王晓明（HR）', text: '匹配度最高的候选人，已优先沟通', time: '昨天 16:30' },
  ],
}
export const getTeamNotes = (id) => teamNotes[id] || []

/* 当前操作人（mock 登录身份） */
export const currentRecruiter = '王晓明（HR）'

/* ---------- 通知中心 ---------- */
export const recruiterNotifications = [
  { id: 1, type: 'application', title: '张伟投递了「前端开发工程师」', detail: '匹配度 85%，建议优先沟通', time: '10分钟前', read: false },
  { id: 2, type: 'message', title: '李娜回复了你的消息', detail: '关于薪资待遇的问题...', time: '1小时前', read: false },
  { id: 3, type: 'review', title: '岗位「UI设计师」审核通过', detail: '已自动上线，开始接收应聘', time: '今天 09:20', read: true },
  { id: 4, type: 'system', title: '「Java后端」浏览量突破100', detail: '已有 12 人留言互动', time: '昨天 16:30', read: true },
  { id: 5, type: 'reminder', title: '3天未跟进张伟', detail: '高意向候选人，建议及时联系', time: '昨天 14:00', read: true },
]

export const seekerNotifications = [
  { id: 1, type: 'match', title: '为你推荐3个新岗位', detail: '前端开发、UI设计、产品经理', time: '5分钟前', read: false },
  { id: 2, type: 'message', title: '阿里巴巴-HR 回复了你', detail: '我们对你的简历很感兴趣...', time: '30分钟前', read: false },
  { id: 3, type: 'interview', title: '字节跳动邀请你面试', detail: '前端开发工程师，本周四下午2点', time: '今天 10:15', read: true },
  { id: 4, type: 'system', title: '简历完整度提升至90%', detail: '再补充项目经历可达100%', time: '今天 08:00', read: true },
  { id: 5, type: 'review', title: '你投递的岗位已被查看', detail: '腾讯-前端开发，招聘者已查看简历', time: '昨天 18:20', read: true },
]

export const notificationTypes = {
  application: { icon: '📩', color: 'var(--wx-blue)' },
  message: { icon: '💬', color: 'var(--wx-green)' },
  review: { icon: '✅', color: 'var(--wx-green-dark)' },
  system: { icon: '📊', color: 'var(--wx-orange)' },
  reminder: { icon: '⏰', color: 'var(--wx-red)' },
  match: { icon: '🎯', color: 'var(--wx-blue)' },
  interview: { icon: '📅', color: 'var(--wx-red)' },
}

/* ---------- 招聘漏斗数据 ---------- */
export const recruitmentFunnel = [
  { stage: '浏览', count: 871, rate: 100, color: '#E8F5FF' },
  { stage: '留言', count: 146, rate: 16.8, color: '#D0EBFF' },
  { stage: '深度沟通', count: 52, rate: 6.0, color: '#A8D5FF' },
  { stage: '邀约面试', count: 18, rate: 2.1, color: '#6BB6FF' },
  { stage: '已录用', count: 5, rate: 0.6, color: '#2E8CFF' },
]

// 各岗位漏斗对比
export const funnelByJob = {
  1: [ // 前端开发
    { stage: '浏览', count: 328, rate: 100 },
    { stage: '留言', count: 62, rate: 18.9 },
    { stage: '深度沟通', count: 24, rate: 7.3 },
    { stage: '邀约面试', count: 9, rate: 2.7 },
    { stage: '已录用', count: 2, rate: 0.6 },
  ],
  2: [ // UI设计师
    { stage: '浏览', count: 256, rate: 100 },
    { stage: '留言', count: 38, rate: 14.8 },
    { stage: '深度沟通', count: 14, rate: 5.5 },
    { stage: '邀约面试', count: 5, rate: 2.0 },
    { stage: '已录用', count: 2, rate: 0.8 },
  ],
}

/* ---------- 管理后台审核 ---------- */
export const reviewQueue = [
  {
    id: 1,
    type: 'enterprise',
    targetId: 101,
    company: '杭州XX科技有限公司',
    submitter: '张伟',
    submittedAt: '2024-06-04 09:15',
    aiResult: 'pass',
    aiConfidence: 0.92,
    aiDetail: {
      riskFlags: [],
      ocrMatch: 0.95,
      creditCodeValid: true,
    },
    status: 'pending',
    businessLicense: 'https://via.placeholder.com/600x400?text=营业执照',
    creditCode: '91330100MA2XXXXX1A',
    legalPerson: '张伟',
    registeredCapital: '100万元',
  },
  {
    id: 2,
    type: 'job',
    targetId: 201,
    jobTitle: '前端开发工程师',
    company: '阿里巴巴',
    submitter: '李娜',
    submittedAt: '2024-06-04 10:30',
    aiResult: 'warning',
    aiConfidence: 0.78,
    aiDetail: {
      riskFlags: ['薪资范围过大'],
      contentSafe: true,
      discriminationCheck: 'pass',
    },
    status: 'pending',
    jobContent: {
      title: '前端开发工程师',
      salary: '15-50K',
      cities: ['杭州', '北京'],
      responsibility: '负责公司核心产品前端开发...',
      requirement: '3年以上前端开发经验，精通 React/Vue...',
    },
  },
  {
    id: 3,
    type: 'job',
    targetId: 202,
    jobTitle: 'UI设计师',
    company: '字节跳动',
    submitter: '王强',
    submittedAt: '2024-06-03 16:20',
    aiResult: 'block',
    aiConfidence: 0.95,
    aiDetail: {
      riskFlags: ['检测到性别歧视用语："限女性"'],
      contentSafe: false,
      discriminationCheck: 'fail',
    },
    status: 'pending',
    jobContent: {
      title: 'UI设计师（限女性）',
      salary: '12-20K',
      cities: ['北京'],
      responsibility: '负责产品界面设计...',
      requirement: '限女性，形象气质佳，熟练使用 Figma...',
    },
  },
]

/* ---------- 面试管理 ---------- */
export const interviews = [
  {
    id: 1,
    seekerId: 1,
    seekerName: '张伟',
    jobId: 1,
    jobTitle: '前端开发工程师',
    scheduledAt: '2024-06-10 14:00',
    location: '杭州市西湖区文三路 XX 大厦 8 楼',
    interviewer: '李经理',
    status: 'scheduled', // scheduled, completed, cancelled
    round: 1,
    type: '技术面试',
    notes: '',
    result: null, // pass, fail, pending
    feedback: '',
  },
  {
    id: 2,
    seekerId: 2,
    seekerName: '李娜',
    jobId: 1,
    jobTitle: '前端开发工程师',
    scheduledAt: '2024-06-05 10:00',
    location: '线上视频面试',
    interviewer: '王总监',
    status: 'completed',
    round: 2,
    type: '终面',
    notes: '技术能力强，沟通顺畅',
    result: 'pass',
    feedback: '技术栈匹配，项目经验丰富，建议发 offer',
  },
]
