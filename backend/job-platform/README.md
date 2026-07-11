# 空岗信息发布对接平台 - 后端服务

## 📋 项目状态

- 后端核心业务闭环、P3 Match Quality 和 P4 本地智能匹配能力已实现。
- 2026-07-10 后端全量回归：`190 passed`。
- Alembic：`d9e1f2a3b409 (head)`，当前只有一个 head。
- GitHub Actions 已执行 Poetry lock、Ruff、主动配置一致性、Alembic 单 head 和完整 pytest 门禁。
- 当前状态适用于本地开发和 demo 验收；生产环境 E2E、发布治理与运行监控尚未完成。

## P4 智能匹配

当前后端已实现：

- 智能策略与离线评估表、迁移和持久化。
- 管理员策略列表、创建、详情、更新、克隆 API，以及操作审计。
- 离线评估 run/report API；demo/mock 样本只返回 dry-run 证据，不能形成上线决策。
- 求职者岗位匹配和招聘者投递匹配的运行时智能评分。当存在 `active` 智能策略时，运行 `intelligent_hybrid_v1`。
- 本地确定性向量 provider `local_profile_text`。provider 不可用或未配置时，记录降级原因并返回 `rule_baseline`。

当前边界：

- 管理 API 创建的是草稿，尚无正式激活/发布治理接口。
- 生产级外部向量召回和向量分数尚未接入。
- 规则实验的 treatment 尚未绑定智能策略。
- 本地自动化、前端构建和浏览器验收不是生产上线证据。

手动测试指南：[`../../docs/p4-intelligent-matching/P4_智能匹配_手动测试指南.md`](../../docs/p4-intelligent-matching/P4_智能匹配_手动测试指南.md)

主要接口：

```text
GET    /api/v1/matches/intelligent/strategies
POST   /api/v1/matches/intelligent/strategies
GET    /api/v1/matches/intelligent/strategies/{strategy_id}
PATCH  /api/v1/matches/intelligent/strategies/{strategy_id}
POST   /api/v1/matches/intelligent/strategies/{strategy_id}/clone
POST   /api/v1/matches/intelligent/strategies/{strategy_id}/evaluations
GET    /api/v1/matches/intelligent/evaluations/{evaluation_id}
```

---

## 🚀 快速启动

### 1. 启动数据库（Docker）
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 2. 安装依赖
```bash
poetry install
```

### 3. 执行数据库迁移
```bash
poetry run alembic upgrade head
```

### 4. 启动应用

**方式1 - 使用启动脚本（推荐）**:
```bash
# Windows
start_server.bat
```

**方式2 - 手动启动**:
```bash
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
```

### 5. 访问API文档
http://localhost:8003/docs

---

## 🧪 测试

### 运行所有测试
```powershell
poetry check --lock
poetry run ruff check app tests ..\..\scripts\check_project_consistency.py --no-cache
poetry run pytest -q --basetemp D:\AIposition\.tmp\job-platform-pytest -p no:cacheprovider
```

`D:\AIposition\.tmp\` 已被忽略，适合 Windows 上默认临时目录不可写时使用。

### 运行特定测试
```bash
# 工具测试（不依赖Redis）
poetry run pytest tests/test_utils/ -v

# API测试（需要Redis）
poetry run pytest tests/test_api/ -v
```

### API手动测试
```powershell
# Windows PowerShell
.\test_api.ps1
```

---

## 📊 项目结构

```
backend/job-platform/
├── app/
│   ├── api/v1/          # API路由
│   │   ├── auth.py      # 认证API（注册、登录、验证码）
│   │   └── users.py     # 用户API（获取、更新用户信息）
│   ├── core/            # 核心配置
│   │   ├── config.py    # 配置管理
│   │   ├── security.py  # JWT、密码哈希
│   │   └── dependencies.py  # 依赖注入
│   ├── db/              # 数据库
│   │   ├── base.py      # Base模型
│   │   └── session.py   # 会话管理
│   ├── modules/         # 业务模块
│   │   ├── user/                    # 用户、角色、登录态、个人信息
│   │   ├── company_certification/  # 企业认证，含营业执照 OCR
│   │   ├── resume/                  # 简历上传、解析、分块、画像
│   │   ├── job/                     # 岗位发布、JD 解析、薪资处理
│   │   ├── match/                   # 人岗匹配、规则配置、版本、实验、审计
│   │   ├── application/             # 投递流程与状态流转
│   │   ├── message/                 # 消息沟通
│   │   ├── notification/            # 通知中心，含微信 provider
│   │   ├── base_data/               # 基础数据与标签治理
│   │   ├── seeker_profile/          # 求职画像
│   │   ├── search/                  # 岗位/候选人搜索
│   │   ├── ai_prompt/               # AI 提示词管理
│   │   └── admin/review/stats/talent/push/
│   ├── utils/           # 工具函数
│   │   ├── encryption.py   # 字段加密（Fernet）
│   │   ├── phone_hash.py   # 手机号哈希（HMAC-SHA256）
│   │   ├── rate_limiter.py # 限流工具
│   │   └── redis_client.py # Redis客户端
│   └── main.py          # FastAPI应用入口
├── alembic/             # 数据库迁移
├── tests/               # 测试
│   ├── test_api/        # API测试
│   └── test_utils/      # 工具测试
├── docs/                # 文档
├── .env.example         # 环境变量示例
├── pyproject.toml       # Poetry配置
└── docker-compose.dev.yml  # Docker配置
```

---

## 🔐 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```bash
# 基础配置
ENV=dev
DEBUG=True

# 数据库配置
DATABASE_URL=postgresql+asyncpg://dev:dev123@localhost:5432/jobplatform_dev

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120

# 字段加密配置（生成方法见下方）
ENCRYPTION_KEY=your-fernet-key-here

# AI服务配置（可选）
OPENAI_API_KEY=
```

### 生成ENCRYPTION_KEY
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 📡 API端点

### 认证相关
- `POST /api/v1/auth/send-verification-code` - 发送验证码
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录

### 用户相关
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `GET /api/v1/users/{user_id}` - 获取指定用户信息（需权限）

### 系统
- `GET /` - 根路径
- `GET /health` - 健康检查

详细 API 文档：http://localhost:8003/docs

---

## 🔧 技术栈

- **Web 框架**：FastAPI 0.136.3
- **ORM**：SQLAlchemy 2.0.50（异步）
- **数据库**: PostgreSQL 16 + pgvector
- **缓存**：Redis 7（服务端）+ redis-py 8.0
- **认证**：JWT（PyJWT）
- **加密**：cryptography（Fernet + HMAC-SHA256）
- **测试**：pytest 9 + pytest-asyncio
- **迁移**：Alembic 1.18
- **AI**：LangChain + OpenAI

---

## 🛡️ 安全特性

1. **双重手机号保护**:
   - `phone_hash`: HMAC-SHA256确定性哈希，用于查询和唯一性检查
   - `phone_encrypted`: Fernet加密，仅用于展示

2. **权限控制**:
   - JWT Token认证
   - 基于角色的访问控制（seeker/recruiter/admin）
   - 防止横向越权

3. **限流保护**:
   - 验证码接口：每分钟1次、每小时3次、每天10次
   - 基于Redis实现

4. **配置校验**:
   - 生产环境强制校验关键密钥、加密配置和数据库连接
   - Fail-fast原则，启动时检测错误

---

## 📚 相关文档

- [审核问题修复报告](docs/审核问题修复报告.md) - 详细修复记录
- [PRD 产品需求文档](../../docs/product/PRD_空岗信息发布对接平台v2.md)
- [需求清单](../../docs/product/需求清单_语音记录20260603.md)

---

## 🤝 开发指南

### 添加新模块
1. 在 `app/modules/` 创建模块目录
2. 创建 `models.py`, `schemas.py`, `repository.py`, `service.py`
3. 在 `app/api/v1/` 创建路由文件
4. 在 `app/main.py` 注册路由

### 数据库迁移
```bash
# 自动生成迁移
poetry run alembic revision --autogenerate -m "描述"

# 执行迁移
poetry run alembic upgrade head

# 回滚
poetry run alembic downgrade -1
```

### 代码格式化
```bash
poetry run black app/ tests/
poetry run isort app/ tests/
```

---

## 📝 待办事项

- [ ] 完善测试覆盖率（目标80%+）
- [ ] 集成CI/CD
- [ ] 性能测试和优化
- [ ] API文档完善
- [ ] 部署文档

---

## 📄 License

最后更新：2026-07-10

Copyright © 2026 空岗平台团队
