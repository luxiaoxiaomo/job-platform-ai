# 空岗信息发布对接平台

AI增强型空岗信息发布对接平台 - 面向中小企业的智能招聘解决方案

---

## 📋 当前状态

### ✅ 已完成
- **后端核心模块**：认证、用户、企业认证
- **前端原型**：完整的UI界面
- **前后端联调**：认证闭环（注册、登录、用户信息）
- **测试覆盖**：pytest 28 passed

### 🔄 进行中
- 管理后台审核功能联调
- 岗位管理模块开发

### ⏳ 待开发
- 投递管理
- 消息聊天
- 通知中心
- 数据统计

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
poetry run uvicorn app.main:app --reload --port 8001
```

**验证**：访问 http://localhost:8001/docs

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
│       │   │   ├── user/                    # 用户模块
│       │   │   └── company_certification/  # 企业认证
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

### 认证模块
- `POST /api/v1/auth/send-verification-code?phone=xxx` - 发送验证码
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录

### 用户模块
- `GET /api/v1/users/me` - 获取当前用户
- `PUT /api/v1/users/me` - 更新当前用户
- `GET /api/v1/users/{user_id}` - 获取指定用户

### 企业认证模块
- `GET /api/v1/company-certifications/me` - 获取我的认证状态
- `POST /api/v1/company-certifications/me` - 提交认证申请
- `GET /api/v1/company-certifications/admin` - 管理员审核列表
- `POST /api/v1/company-certifications/admin/{id}/review` - 审核操作

完整API文档：http://localhost:8001/docs

---

## 🔐 测试账号

### 应聘者
- 手机号：`13800138000`
- 密码：`Test1234`

### 招聘者
（待创建）

### 管理员
（待创建）

---

## 📚 文档

### 产品文档
- [PRD产品需求文档](docs/PRD_空岗信息发布对接平台v2.md)
- [需求清单](docs/需求清单_语音记录20260603.md)

### 技术文档
- [架构设计](docs/架构设计_Python_FastAPI_空岗平台.md)
- [开发设计](docs/开发设计文档_空岗平台.md)
- [项目审核报告](docs/项目审核报告_空岗平台_20260605.md)

### 联调文档
- [联调实施方案](docs/前后端联调实施方案.md)
- [联调完成报告](docs/前后端联调最终完成报告.md)
- [联调问题修复](docs/联调阻断问题修复报告.md)

---

## 🔧 技术栈

### 后端
- **框架**：FastAPI 0.131
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
poetry run pytest -q
```

### 前端构建
```bash
cd D:\AIposition\frontend\wechat-prototype
npm run build
```

---

## 💡 开发模式切换

### 联调模式（连接真实后端）
```bash
# 修改前端 .env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8001
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

**最后更新**：2026-06-08
