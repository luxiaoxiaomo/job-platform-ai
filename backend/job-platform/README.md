# 空岗信息发布对接平台 - 后端服务

## 📋 项目状态

- ✅ **审核问题修复**: 所有高风险和中风险问题已修复
- ✅ **数据库**: PostgreSQL + Redis (Docker)
- ✅ **测试覆盖**: 20个自动化测试用例
- ✅ **可交付状态**: 已达生产就绪

详细修复报告：[docs/审核问题修复报告.md](docs/审核问题修复报告.md)

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
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. 访问API文档
http://localhost:8000/docs

---

## 🧪 测试

### 运行所有测试
```bash
poetry run pytest tests/ -v
```

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
│   ├── modules/user/    # 用户模块
│   │   ├── models.py    # User数据模型
│   │   ├── schemas.py   # Pydantic Schema
│   │   ├── repository.py  # 数据访问层
│   │   └── service.py   # 业务逻辑层
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

详细API文档：http://localhost:8000/docs

---

## 🔧 技术栈

- **Web框架**: FastAPI 0.131.0
- **ORM**: SQLAlchemy 2.1.0 (Async)
- **数据库**: PostgreSQL 16 + pgvector
- **缓存**: Redis 7
- **认证**: JWT (PyJWT)
- **加密**: cryptography (Fernet + HMAC-SHA256)
- **测试**: pytest + pytest-asyncio
- **迁移**: Alembic
- **AI**: LangChain + OpenAI

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
   - 生产环境强制校验所有关键配置
   - Fail-fast原则，启动时检测错误

---

## 📚 相关文档

- [审核问题修复报告](docs/审核问题修复报告.md) - 详细修复记录
- [PRD产品需求文档](../../PRD_空岗信息发布对接平台v2.md)
- [需求清单](../../需求清单_语音记录20260603.md)

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

Copyright © 2026 空岗平台团队
