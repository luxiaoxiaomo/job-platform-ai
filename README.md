# 空岗信息发布对接平台

AI 增强型空岗信息发布对接平台：面向中小企业的智能招聘解决方案


## 当前验证状态（2026-07-10）

- 后端全量回归：`190 passed`。
- 数据库迁移：`alembic heads` 返回 `d9e1f2a3b409 (head)`，当前只有一个 head。
- 前端生产构建：`npm.cmd run build` 成功；仍有大 chunk 告警。
- 最小 CI：`.github/workflows/ci.yml` 已覆盖 Poetry lock、Ruff、Alembic 单 head、后端全量测试、`npm ci`、前端构建、端口/配置一致性和工作树洁净性检查。
- Windows 本地运行 pytest 时，默认临时目录可能遇到权限问题。建议使用仓库已忽略的 `D:\AIposition\.tmp\...`，并设置 `-p no:cacheprovider`。

## P4 智能匹配状态

已实现：

- 智能策略与离线评估持久化、管理 API、操作审计及评估报告。
- 求职者岗位匹配和招聘者投递匹配已接入运行时智能评分。当数据库存在 `active` 智能策略时，返回 `intelligent_hybrid_v1` 结果并记录评分审计。
- 本地确定性向量 provider `local_profile_text` 可用于受控环境；provider 不可用或未配置时，会记录 `vector_store_unavailable` 并降级到 `rule_baseline`。
- react-admin 管理端已支持策略列表、创建、详情、编辑、克隆和离线评估报告。

尚未完成：

- 生产级外部向量召回和向量分数接入。
- 智能策略与规则实验 treatment 的绑定。
- 智能策略正式激活/发布治理流程。当前管理 API 创建的是草稿，不能完成生产发布闭环。
- 生产环境 E2E 证据、上线决策和回滚治理。

手动测试指南：`docs/p4-intelligent-matching/P4_智能匹配_手动测试指南.md`。

---

## 📋 当前状态

### ✅ 已完成
- **后端业务模块**：用户、企业认证、简历、岗位、投递、匹配、搜索、消息、通知、基础数据、求职画像、AI Prompt、管理审核、统计与人才库
- **核心业务闭环**：岗位发布、简历解析、人岗匹配、投递、消息、通知与后台治理
- **P3 Match Quality**：规则配置、版本、实验、审计、评分解释、分层质量分析与调优建议
- **P4 智能匹配**：策略管理、离线评估、运行时智能评分、本地向量 provider 和管理端页面已完成本地验证
- **前端原型**：`frontend/wechat-prototype` 为当前主前端
- **前后端联调**：本地/demo 业务闭环已有运行证据，生产环境验收尚未覆盖
- **测试覆盖**：2026-07-10 后端全量回归 190 passed

### 🔄 进行中
- 生产级外部向量 provider 接入
- 智能策略实验绑定、激活/发布治理设计

### ⏳ 待开发
- 生产环境 12 步 E2E 验收
- 生产级智能匹配上线与回滚治理
- 前端大 chunk 拆分与构建告警治理

---

## 🚀 快速启动

### 前置要求
- Python 3.12+
- Node.js 18+
- Docker Desktop（用于PostgreSQL + Redis）
- Poetry（Python包管理）

### 1. 启动数据库

```bash
cd D:\AIposition\backend\job-platform
docker-compose -f docker-compose.dev.yml up -d
```

### 2. 启动后端

**方法A：双击启动脚本（推荐）**
```
D:\AIposition\backend\job-platform\启动后端.bat
```

**方法B：手动启动**
```bash
cd D:\AIposition\backend\job-platform
poetry run uvicorn app.main:app --reload --port 8003
```

**验证**：访问 http://localhost:8003/docs

### 3. 启动前端

**方法A：双击启动脚本（推荐）**
```
D:\AIposition\frontend\wechat-prototype\启动前端.bat
```

**方法B：手动启动**
```bash
cd D:\AIposition\frontend\wechat-prototype
npm run dev
```

**验证**：访问 http://localhost:5174

---

## 📂 项目结构

```
D:\AIposition\
├── backend/              # 后端项目
│   └── job-platform/
│       ├── app/          # 应用代码
│       │   ├── api/v1/   # API路由
│       │   ├── core/     # 核心配置
│       │   ├── modules/  # 业务模块
│       │   │   ├── user/                    # 用户、角色、登录态、个人信息
│       │   │   ├── company_certification/  # 企业认证，含营业执照 OCR
│       │   │   ├── resume/                  # 简历上传、解析、分块、画像
│       │   │   ├── job/                     # 岗位发布、JD 解析、薪资处理
│       │   │   ├── match/                   # 人岗匹配、规则配置、版本、实验、审计
│       │   │   ├── application/             # 投递流程与状态流转
│       │   │   ├── message/                 # 消息沟通
│       │   │   ├── notification/            # 通知中心，含微信 provider
│       │   │   ├── base_data/               # 基础数据与标签治理
│       │   │   ├── seeker_profile/          # 求职画像
│       │   │   ├── search/                  # 岗位/候选人搜索
│       │   │   ├── ai_prompt/               # AI 提示词管理
│       │   │   └── admin/review/stats/talent/push/
│       │   ├── db/       # 数据库
│       │   └── utils/    # 工具函数
│       ├── alembic/      # 数据库迁移
│       ├── tests/        # 单元测试
│       └── docs/         # 后端文档
│
├── frontend/             # 前端项目
│   └── wechat-prototype/
│       └── src/
│           ├── services/ # API服务层
│           ├── common/   # 通用组件
│           ├── seeker/   # 应聘者端
│           ├── recruiter/# 招聘者端
│           └── admin/    # 管理后台
│
└── docs/                 # 项目文档
    ├── PRD_空岗信息发布对接平台v2.md
    ├── 架构设计_Python_FastAPI_空岗平台.md
    ├── 前后端联调实施方案.md
    └── 前后端联调最终完成报告.md
```

---

## 🔑 API端点

- `auth` / `users`：认证、登录态、用户资料
- `company-certifications`：企业认证，含营业执照 OCR 与审核
- `resumes`：简历上传、解析、结构化管理
- `jobs`：岗位发布、JD 解析、薪资处理、上下架
- `matches`：人岗匹配、Match Quality、规则配置、版本、实验、审计，以及 P4 智能策略、离线评估和运行时智能评分
- `applications`：投递与状态流转
- `messages` / `notifications`：消息、通知，含微信 provider
- `base-data`：基础数据与标签治理
- `seeker-profiles`：求职画像
- `search`：岗位/候选人搜索
- `ai-prompts`：AI 提示词管理

完整 API 文档：http://localhost:8003/docs

---

## 🔐 测试账号

完整本地联调账号见：[docs/collaboration/本地测试账号.md](docs/collaboration/本地测试账号.md)

### 应聘者
- 手机号：`13800138000`
- 密码：`Test1234`

### 招聘者
- 手机号：`13900139000`
- 密码：`Recruiter123`

### 管理员
- 手机号：`13700137001`
- 密码：`Admin1234`

---

## 📚 文档

- [文档索引](docs/INDEX.md)
- [PRD 产品需求文档](docs/product/PRD_空岗信息发布对接平台v2.md)
- [架构设计](docs/architecture/架构设计_Python_FastAPI_空岗平台.md)
- [本地联调测试手册](docs/acceptance/本地联调测试手册_2026-06-29.md)
- [P4 智能匹配手动测试指南](docs/p4-intelligent-matching/P4_智能匹配_手动测试指南.md)
- [交接状态](docs/HANDOFF.json)

---

## 🔧 技术栈

### 后端
- **框架**：FastAPI 0.136
- **数据库**：PostgreSQL 16 + pgvector
- **缓存**：Redis 7
- **ORM**：SQLAlchemy 2.0 (异步)
- **认证**：JWT + bcrypt
- **加密**：Fernet (字段加密) + HMAC-SHA256 (手机号哈希)
- **迁移**：Alembic

### 前端
- **框架**：React 18 + Vite 5
- **路由**：React Router 6 (HashRouter)
- **状态**：React Context
- **样式**：原生CSS（微信小程序风格）

### 开发工具
- **Python包管理**：Poetry
- **前端包管理**：npm
- **容器化**：Docker Compose
- **测试**：pytest + pytest-asyncio

---

## 🧪 运行测试

### 后端测试
```bash
cd D:\AIposition\backend\job-platform
poetry check --lock
poetry run ruff check app tests ..\..\scripts\check_project_consistency.py --no-cache
poetry run pytest -q --basetemp D:\AIposition\.tmp\job-platform-pytest -p no:cacheprovider
```

### 前端构建
```bash
cd D:\AIposition\frontend\wechat-prototype
npm ci
npm run build
```

### 主动配置一致性

```bash
cd D:\AIposition
python scripts\check_project_consistency.py
```

该检查固定当前本地开发入口：前端 `5174`，后端 `8003`。历史验收脚本使用的专用端口不在此检查范围内。

---

## 持续集成

GitHub Actions 在推送到 `main` 和 Pull Request 时运行：

- 后端：Python 3.12、Poetry 2.2.1、锁文件检查、Ruff、Alembic 单 head、完整 pytest。
- 前端：Node.js 22、`npm ci`、Vite 生产构建。
- 仓库：主动配置一致性检查，以及命令执行后无新增或修改文件。

CI 权限为只读，不包含部署、数据库迁移执行或生产密钥访问。

---

## 💡 开发模式切换

### 联调模式（连接真实后端）
```bash
# 修改前端 .env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8003
```

### 演示模式（使用Mock数据）
```bash
# 修改前端 .env
VITE_USE_MOCK=true
```

---

## 📝 开发规范

### 代码风格
- **Python**：black + ruff
- **JavaScript**：标准ES6+
- **命名**：snake_case (Python) / camelCase (JS)

### Git提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档
refactor: 重构
test: 测试
chore: 构建/工具
```

---

## 🤝 团队协作

### 角色分工
- **产品**：PRD、需求评审
- **后端**：FastAPI开发
- **前端**：React开发
- **审核**：Codex（代码审查）

### 联调流程
1. 后端开发API
2. 后端测试通过
3. 前端联调API
4. 端到端测试
5. 代码审查
6. 合并代码

---

## 📞 联系方式

如有问题请联系开发团队。

---

**最后更新**：2026-07-10
