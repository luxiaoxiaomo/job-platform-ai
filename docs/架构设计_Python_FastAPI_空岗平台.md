# 空岗信息发布对接平台 — Python/FastAPI 技术架构方案

| 项目 | 内容 |
|------|------|
| 产品名称 | 空岗信息发布对接平台 |
| 文档版本 | V1.0 Python/FastAPI 版 |
| 文档状态 | 待评审 |
| 替代基线 | 架构设计 V1.0（Java Spring Cloud 微服务） |
| 关联PRD | PRD_空岗信息发布对接平台v2.md |
| 创建日期 | 2026-06-05 |
| 核心原则 | **AI原生 · 单体优先 · Python全栈 · 渐进拆分** |
| 目标团队 | AI工程师团队（Python技术栈） |

---

## 文档摘要

### 为什么选择Python/FastAPI方案

**团队背景**：全AI工程师团队，Python技术栈，需要集成12+项AI能力。

**核心差异**：
- **技术栈**：Python 3.12 + FastAPI + SQLAlchemy + Celery + LangChain + PostgreSQL
- **架构**：单体优先（Modular Monolith），模块分层，内部Python函数调用，非HTTP/RPC
- **开发速度**：比Java微服务快 **3-4倍**
- **部署**：Docker Compose，一期1台2C4G（¥900/月），生产2台4C8G（¥2,330/月）
- **数据库**：PostgreSQL + pgvector（向量检索），替代MySQL + Milvus + ES组合
- **AI集成**：AI Gateway作为Python模块，LangChain管理Prompt + 模型路由 + 降级
- **成本**：月成本 ¥2,330（服务器） + ¥3,000-5,000（AI调用），比Java方案省 **50-70%**

**关键不变**：PRD需求、业务逻辑、API接口（50+）、数据库表结构、前端代码全部保持原设计，只技术实现层从Java微服务切换到Python单体。

---

## 目录

1. [架构设计概述](#1-架构设计概述)
2. [技术选型](#2-技术选型)
3. [整体架构设计](#3-整体架构设计)
4. [模块拆分设计](#4-模块拆分设计)
5. [数据库设计](#5-数据库设计)
6. [API接口设计](#6-api接口设计)
7. [AI能力架构专项](#7-ai能力架构专项)
8. [部署与运维](#8-部署与运维)
9. [开发排期与成本](#9-开发排期与成本)
10. [代码结构示例](#10-代码结构示例)
11. [渐进拆分路径](#11-渐进拆分路径)
12. [监控与告警](#12-监控与告警)
13. [数据安全方案](#13-数据安全方案)
14. [风险与应对](#14-风险与应对)
15. [附录](#15-附录)

---

## 1. 架构设计概述

### 1.1 设计目标

本平台采用**模块化单体架构**（Modular Monolith），以支撑"AI增强型空岗信息发布对接"核心链路。架构设计围绕以下目标展开：

- **快速迭代**：AI工程师团队，Python全栈，2-3个月上线MVP
- **AI原生**：12+项AI能力深度集成，LangChain + pgvector原生支持
- **成本优化**：单体架构，少中间件，月成本¥2,330（vs Java方案¥10,000）
- **渐进扩展**：模块边界清晰，按需拆分，避免过度设计
- **高可用**：系统可用率 >= 99.5%，AI降级保证核心流程不中断

### 1.2 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          客户端层 (Client Layer)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ 微信小程序    │  │ H5 Web       │  │ 管理后台      │                  │
│  │ (应聘者/招聘者)│  │              │  │ (Admin)      │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
└─────────┼──────────────────┼──────────────────┼──────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      接入层 (Gateway Layer)                              │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Nginx (SSL终止 + 反向代理 + 限流)                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     应用层 (Application Layer)                           │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │               FastAPI 主应用（单进程部署）                      │    │
│  │                                                                │    │
│  │  模块（内部Python函数调用）：                                    │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │    │
│  │  │ user    │ │ job     │ │ message │ │ talent  │             │    │
│  │  │ 模块     │ │ 模块     │ │ 模块     │ │ 模块     │             │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘             │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │    │
│  │  │ push    │ │ review  │ │ stats   │ │ admin   │             │    │
│  │  │ 模块     │ │ 模块     │ │ 模块     │ │ 模块     │             │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘             │    │
│  │                                                                │    │
│  │  ┌────────────────────────────────────────────────────────┐   │    │
│  │  │           AI Gateway 模块（核心）                       │   │    │
│  │  │  - LangChain 管理                                       │   │    │
│  │  │  - Prompt 版本化                                        │   │    │
│  │  │  - 模型路由与降级                                       │   │    │
│  │  │  - Token 计量                                           │   │    │
│  │  └────────────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │               Celery Workers（异步任务）                       │    │
│  │  - 推送任务（订阅匹配、模板消息）                             │    │
│  │  - AI批量调用（推送摘要生成、批量匹配）                       │    │
│  │  - 数据聚合（统计、报表）                                     │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     数据层 (Data Layer)                                  │
│                                                                         │
│  ┌────────────────┐ ┌────────────────┐ ┌──────────────────┐           │
│  │ PostgreSQL 16  │ │ Redis 7        │ │ MinIO / OSS      │           │
│  │ + pgvector     │ │ (缓存+队列)     │ │ (对象存储)        │           │
│  │                │ │                │ │                  │           │
│  │ • 业务数据      │ │ • Session      │ │ • 营业执照       │           │
│  │ • 向量检索      │ │ • 验证码       │ │ • 简历附件       │           │
│  │ • 全文搜索      │ │ • 缓存         │ │ • 头像图片       │           │
│  └────────────────┘ │ • Celery队列   │ └──────────────────┘           │
│                     └────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────┘

                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     外部服务 (External Services)                         │
│                                                                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────┐   │
│  │ OpenAI API │ │ 通义千问    │ │ 百度OCR    │ │ 微信开放平台      │   │
│  │ (GPT-4o)   │ │ (备用LLM)  │ │ (主OCR)    │ │ (OAuth/模板消息) │   │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 为什么是单体架构

**对比Java微服务方案的优势**：

| 维度 | Python单体 | Java微服务 | 差异 |
|------|-----------|-----------|------|
| **开发周期** | 2-3个月（1-2个AI工程师） | 4-6个月（3-4个后端） | **快2倍** |
| **部署复杂度** | Docker Compose | K8s + 12个服务 | **简单10倍** |
| **运维成本** | 开发兼任 | 需专职DevOps | **省1人** |
| **月服务器成本** | ¥2,330 | ¥10,000 | **省77%** |
| **AI集成成本** | LangChain原生（1周） | 封装Python服务（4周） | **快4倍** |
| **调试效率** | 单进程，堆栈连续 | 跨服务，链路复杂 | **快3倍** |
| **技能匹配** | AI工程师天然Python | 需学Spring Boot | **零学习成本** |

**单体的边界**：
- ✅ 一期：0-5万DAU，单体足够
- ⚠️ 二期：5-20万DAU，按瓶颈拆分（AI Gateway、Push服务）
- ❌ 三期：20万+DAU，考虑全面微服务化

---

## 2. 技术选型

### 2.1 技术栈总览

| 层次 | 技术选型 | 版本 | 选型理由 |
|------|---------|------|---------|
| **前端-用户端** | 微信小程序（原生） | - | PRD要求，与原Java方案一致 |
| **前端-管理后台** | React + Ant Design | React 18 + Antd 5 | 与原型一致 |
| **后端框架** | FastAPI | 0.110+ | 高性能异步框架，AI工程师友好 |
| **ORM** | SQLAlchemy | 2.0+ | 声明式API，支持异步，PostgreSQL完美集成 |
| **异步驱动** | asyncpg | 0.29+ | PostgreSQL异步驱动，性能是psycopg2的3倍 |
| **数据验证** | Pydantic | 2.0+ | FastAPI内置，类型安全 |
| **异步任务** | Celery + Redis | Celery 5.3+ | AI工程师熟悉的任务队列 |
| **数据库** | PostgreSQL 16 | 16.x | JSON/数组/向量/全文搜索原生支持 |
| **向量检索** | pgvector | 0.5+ | PostgreSQL扩展，替代Milvus |
| **缓存** | Redis | 7.x | 缓存 + Session + Celery队列 |
| **对象存储** | MinIO / 阿里云OSS | - | 文件存储 |
| **AI框架** | LangChain | 0.1+ | Prompt管理、模型路由、RAG |
| **LLM** | OpenAI API + 通义千问 | - | 主备模型 |
| **OCR** | 百度OCR + 腾讯OCR | - | 主备OCR |
| **Web服务器** | Uvicorn + Gunicorn | - | ASGI服务器 |
| **容器化** | Docker + Docker Compose | - | 一期部署方案 |
| **监控** | Prometheus + Grafana | - | 指标监控 |
| **日志** | Python logging + Loki | - | 结构化日志 |

### 2.2 为什么选FastAPI

**对比Django/Flask**：

| 特性 | FastAPI | Django | Flask |
|------|---------|--------|-------|
| **性能** | ⭐⭐⭐⭐⭐（异步，接近Go） | ⭐⭐（同步） | ⭐⭐⭐（同步） |
| **类型安全** | ⭐⭐⭐⭐⭐（Pydantic） | ⭐（无） | ⭐（无） |
| **API文档** | ⭐⭐⭐⭐⭐（自动生成Swagger） | ⭐⭐（需DRF） | ⭐（需扩展） |
| **异步支持** | ⭐⭐⭐⭐⭐（原生async/await） | ⭐⭐⭐（3.1+支持） | ⭐⭐（需扩展） |
| **学习曲线** | ⭐⭐⭐⭐（简单） | ⭐⭐（复杂） | ⭐⭐⭐⭐⭐（最简单） |
| **AI集成** | ⭐⭐⭐⭐⭐（与LangChain完美） | ⭐⭐⭐ | ⭐⭐⭐ |

**FastAPI特别适合AI应用**：
```python
from fastapi import FastAPI
from pydantic import BaseModel
from ai.chains import jd_writer

app = FastAPI()

class JDRequest(BaseModel):
    title: str
    city: str
    salary: str

@app.post("/api/ai/jd-generate")
async def generate_jd(req: JDRequest):
    # 类型自动验证，API文档自动生成
    result = await jd_writer.generate(req.title, req.city, req.salary)
    return result
```

### 2.3 为什么选PostgreSQL + pgvector

**对比MySQL + Milvus方案**：

| 能力 | PostgreSQL + pgvector | MySQL + Milvus |
|------|---------------------|----------------|
| **向量检索** | ✅ pgvector扩展（原生） | ✅ Milvus（独立部署） |
| **JSON查询** | ✅ JSONB（高性能） | ⚠️ JSON（性能差3倍） |
| **数组类型** | ✅ 原生ARRAY | ❌ 只能用JSON模拟 |
| **全文搜索** | ✅ 内置（中文支持） | ⚠️ 需外接ES |
| **部署复杂度** | ✅ 1个组件 | ⚠️ 3个组件（MySQL+Milvus+ES） |
| **月成本** | ✅ ¥800 | ⚠️ ¥3,300 |
| **LangChain集成** | ✅ PGVector（官方推荐） | ⚠️ 需配置多个连接 |

**pgvector性能**：
- 10万向量：检索 < 200ms
- 100万向量：需HNSW索引，检索 < 500ms
- 1000万+向量：建议迁移专业向量库（Milvus/Qdrant）

**结论**：一期用pgvector，省掉Milvus和ES，架构更简洁。

### 2.4 Python版本与依赖管理

**Python版本**：3.12+（性能比3.10提升15%）

**依赖管理**：Poetry（比pip更现代）

```toml
# pyproject.toml
[tool.poetry]
name = "job-platform"
version = "1.0.0"
python = "^3.12"

[tool.poetry.dependencies]
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
sqlalchemy = "^2.0.0"
asyncpg = "^0.29.0"
pydantic = "^2.0.0"
celery = "^5.3.0"
redis = "^5.0.0"
langchain = "^0.1.0"
openai = "^1.0.0"
pgvector = "^0.2.0"
python-jose = "^3.3.0"  # JWT
passlib = "^1.7.4"      # 密码哈希
python-multipart = "^0.0.9"  # 文件上传
httpx = "^0.27.0"       # 异步HTTP客户端
```

---

## 3. 整体架构设计

### 3.1 模块化单体架构

**核心设计原则**：
1. **模块边界清晰**：每个模块独立文件夹，禁止跨模块直接import
2. **接口层隔离**：模块间通过service层调用，不直接操作数据库
3. **数据库表前缀**：`user_*`, `job_*`, `msg_*`，为未来分库做准备
4. **依赖注入**：使用FastAPI的Depends机制，方便测试和替换

```
job-platform/
├── app/
│   ├── main.py                 # FastAPI应用入口
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理（环境变量）
│   │   ├── security.py         # JWT、密码加密
│   │   └── dependencies.py     # 全局依赖注入
│   │
│   ├── api/                    # API路由层
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证相关API
│   │   │   ├── user.py         # 用户管理API
│   │   │   ├── job.py          # 岗位管理API
│   │   │   ├── message.py      # 消息API
│   │   │   ├── talent.py       # 人才池API
│   │   │   └── admin.py        # 管理后台API
│   │
│   ├── modules/                # 业务模块（核心）
│   │   ├── user/
│   │   │   ├── service.py      # 业务逻辑
│   │   │   ├── models.py       # SQLAlchemy模型
│   │   │   ├── schemas.py      # Pydantic验证
│   │   │   └── repository.py   # 数据访问层
│   │   ├── job/
│   │   ├── message/
│   │   ├── talent/
│   │   ├── push/
│   │   ├── review/
│   │   ├── stats/
│   │   └── admin/
│   │
│   ├── ai/                     # AI能力层（独立）
│   │   ├── gateway.py          # AI Gateway统一入口
│   │   ├── chains/             # LangChain chains
│   │   │   ├── jd_writer.py
│   │   │   ├── content_review.py
│   │   │   ├── smart_reply.py
│   │   │   ├── matching.py
│   │   │   └── ocr.py
│   │   ├── prompts/            # Prompt模板
│   │   ├── embeddings/         # Embedding管理
│   │   ├── vectorstore.py      # pgvector封装
│   │   └── fallback.py         # 降级策略
│   │
│   ├── tasks/                  # Celery异步任务
│   │   ├── push_tasks.py
│   │   ├── ai_batch_tasks.py
│   │   └── stats_tasks.py
│   │
│   ├── db/                     # 数据库管理
│   │   ├── session.py          # 数据库会话
│   │   └── base.py             # Base模型
│   │
│   └── utils/                  # 工具函数
│       ├── logging.py
│       └── exceptions.py
│
├── alembic/                    # 数据库迁移
│   └── versions/
├── tests/                      # 测试
├── docker-compose.yml          # 开发环境
├── Dockerfile                  # 生产镜像
└── pyproject.toml              # 依赖管理
```

### 3.2 模块职责划分

| 模块 | 职责 | 依赖模块 | 对外接口数 |
|------|------|---------|-----------|
| **user** | 用户注册/登录、企业认证、资料管理、微信OAuth | ai（OCR） | 6 |
| **job** | 岗位CRUD、草稿管理、发布、状态机、批量导入 | ai（JD生成、内容审核）、review | 10 |
| **message** | 留言收发、对话管理、联系方式交换 | ai（智能回复、情感分析） | 5 |
| **talent** | 人才池、候选人聚合、团队协作备注、跟进提醒 | user、job、message、stats、ai（匹配） | 8 |
| **push** | 订阅管理、推送匹配、微信模板消息 | job、ai（推荐、摘要） | 5 |
| **review** | 企业认证审核、岗位内容审核、审核队列 | ai（内容安全） | 4 |
| **stats** | 数据统计、埋点采集、浏览穿透、漏斗分析 | job、message | 6 |
| **admin** | 管理后台聚合API、用户管理、基础数据维护 | 聚合所有模块 | 8 |
| **ai** | AI能力统一入口（LangChain、Prompt管理） | 外部AI服务 | 内部调用 |

**模块调用规则**：
```python
# ✅ 正确：通过service层调用
from modules.job.service import JobService
from modules.ai.gateway import ai_gateway

async def create_job_with_ai(data):
    # 调用AI生成JD
    jd_content = await ai_gateway.generate_jd(data.title, data.city)
    # 调用job模块保存
    job = await JobService.create(jd_content)
    return job

# ❌ 错误：直接跨模块访问models
from modules.job.models import Job  # 禁止！
```

### 3.3 数据流向

**典型请求链路（岗位发布）**：
```
1. 前端提交 → 
2. API层（job.py）接收并验证（Pydantic） → 
3. Service层（job/service.py）业务逻辑 → 
4. AI Gateway（ai/gateway.py）内容审核 → 
5. Repository层（job/repository.py）数据持久化 → 
6. Celery任务（tasks/push_tasks.py）异步推送 → 
7. 返回响应
```

---

## 4. 模块拆分设计

### 4.1 核心模块详细设计

#### User模块（用户管理）

**职责**：
- 微信OAuth登录/注册
- 用户资料管理（真名/虚拟名）
- 企业信息管理（OCR识别营业执照）
- 权限控制（RBAC）

**核心代码结构**：
```python
# modules/user/models.py
from sqlalchemy import Column, String, Enum, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    openid = Column(String(64), unique=True)
    role = Column(Enum('recruiter', 'seeker', 'admin'))
    display_name = Column(String(50))
    real_name_encrypted = Column(String(200))  # AES加密
    avatar_url = Column(String(500))
    info_completeness = Column(Integer, default=0)

class Enterprise(Base):
    __tablename__ = 'enterprises'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    real_name_encrypted = Column(String(300))
    virtual_name = Column(String(100))
    ocr_result = Column(JSONB)  # AI OCR识别结果
    verification_status = Column(Enum('pending', 'verified', 'rejected'))
```

```python
# modules/user/service.py
from ai.gateway import ai_gateway

class UserService:
    @staticmethod
    async def register_enterprise(user_id: int, license_image_url: str):
        # 调用AI OCR识别营业执照
        ocr_result = await ai_gateway.ocr_license(license_image_url)
        
        # 创建企业记录
        enterprise = Enterprise(
            user_id=user_id,
            real_name_encrypted=encrypt(ocr_result['company_name']),
            ocr_result=ocr_result,
            verification_status='pending'
        )
        await db.add(enterprise)
        return enterprise
```

#### Job模块（岗位管理）

**职责**：
- 岗位CRUD（草稿 → 提交 → 审核 → 上线）
- AI辅助（JD代写、润色、标准化）
- 批量导入（Excel解析）
- 岗位状态机

**状态机**：
```python
# job状态流转
draft → pending → online
          ↓         ↓
      rejected   closed
```

**核心代码**：
```python
# modules/job/models.py
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from pgvector.sqlalchemy import Vector

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), index=True)
    cities = Column(ARRAY(String))  # PostgreSQL原生数组
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    responsibility = Column(Text)
    requirement = Column(Text)
    status = Column(Enum('draft', 'pending', 'online', 'closed', 'rejected'))
    ai_review_detail = Column(JSONB)  # AI审核详情
    embedding = Column(Vector(768))   # pgvector向量字段
    search_vector = Column(TSVECTOR)  # 全文搜索向量
```

#### AI模块（AI能力层）

**职责**：
- 统一AI调用入口
- Prompt版本管理
- 模型路由与降级
- Token计量与成本统计
- 缓存策略

**核心设计**（详见第7章）

---

## 5. 数据库设计

### 5.1 PostgreSQL表结构

#### users表（用户）

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    openid VARCHAR(64) UNIQUE NOT NULL,
    unionid VARCHAR(64),
    role VARCHAR(20) NOT NULL CHECK (role IN ('recruiter', 'seeker', 'admin')),
    display_name VARCHAR(50) NOT NULL,
    real_name_encrypted VARCHAR(200),  -- AES-256-GCM加密
    name_type VARCHAR(20) DEFAULT 'real',
    avatar_url VARCHAR(500),
    phone_encrypted VARCHAR(100),
    email VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    info_completeness INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_openid ON users(openid);
CREATE INDEX idx_users_role ON users(role);
```

#### enterprises表（企业）

```sql
CREATE TABLE enterprises (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    real_name_encrypted VARCHAR(300) NOT NULL,
    virtual_name VARCHAR(100),
    credit_code_encrypted VARCHAR(50) UNIQUE,
    legal_person_encrypted VARCHAR(100),
    city VARCHAR(50),
    industry VARCHAR(50),
    business_license_url VARCHAR(500),
    ocr_result JSONB,  -- AI OCR识别结果
    ocr_confidence NUMERIC(3,2),
    verification_status VARCHAR(20) DEFAULT 'unverified',
    ai_risk_flag VARCHAR(20) DEFAULT 'normal',
    ai_risk_reason TEXT,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_enterprises_status ON enterprises(verification_status);
CREATE INDEX idx_enterprises_city ON enterprises(city);
-- GIN索引支持JSONB查询
CREATE INDEX idx_enterprises_ocr ON enterprises USING GIN (ocr_result);
```

#### jobs表（岗位）

```sql
-- 安装pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    enterprise_id INTEGER REFERENCES enterprises(id),
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(100) NOT NULL,
    title_standard VARCHAR(100),  -- AI标准化后的名称
    cities TEXT[],  -- PostgreSQL原生数组
    salary_min INTEGER NOT NULL,
    salary_max INTEGER NOT NULL,
    salary_type VARCHAR(20) DEFAULT 'monthly',
    responsibility TEXT NOT NULL,
    requirement TEXT NOT NULL,
    education VARCHAR(20),
    experience VARCHAR(50),
    status VARCHAR(20) DEFAULT 'draft',
    ai_review_detail JSONB,  -- AI审核详情
    embedding vector(768),   -- pgvector向量字段
    search_vector tsvector,  -- 全文搜索向量
    view_count INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    published_at TIMESTAMP,
    expired_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_cities ON jobs USING GIN (cities);  -- GIN索引支持数组查询
CREATE INDEX idx_jobs_search ON jobs USING GIN (search_vector);  -- 全文搜索索引
CREATE INDEX idx_jobs_embedding ON jobs USING hnsw (embedding vector_cosine_ops);  -- HNSW向量索引
CREATE INDEX idx_jobs_published ON jobs(published_at DESC) WHERE status = 'online';
```

**向量检索示例**：
```sql
-- 找出与给定向量最相似的10个岗位
SELECT id, title, 
       1 - (embedding <=> '[0.1, 0.2, ..., 0.9]'::vector) AS similarity
FROM jobs
WHERE status = 'online'
ORDER BY embedding <=> '[0.1, 0.2, ..., 0.9]'::vector
LIMIT 10;
```

#### conversations表（对话）

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    recruiter_id INTEGER REFERENCES users(id),
    seeker_id INTEGER REFERENCES users(id),
    last_message TEXT,
    last_message_at TIMESTAMP,
    recruiter_unread INTEGER DEFAULT 0,
    seeker_unread INTEGER DEFAULT 0,
    contact_exchanged BOOLEAN DEFAULT FALSE,
    ai_sentiment VARCHAR(20),  -- AI情感分析：high/medium/low
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conv_recruiter ON conversations(recruiter_id, last_message_at DESC);
CREATE INDEX idx_conv_seeker ON conversations(seeker_id, last_message_at DESC);
```

#### messages表（消息）

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    sender_id INTEGER REFERENCES users(id),
    sender_role VARCHAR(20),
    content TEXT NOT NULL,
    ai_reviewed BOOLEAN DEFAULT FALSE,
    ai_review_result VARCHAR(20),  -- pass/warning/block
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conv ON messages(conversation_id, created_at DESC);
```

#### talent_notes表（团队协作备注）

```sql
CREATE TABLE talent_notes (
    id SERIAL PRIMARY KEY,
    seeker_id INTEGER REFERENCES users(id),
    enterprise_id INTEGER REFERENCES enterprises(id),  -- 多租户隔离
    author_id INTEGER REFERENCES users(id),
    author_name VARCHAR(50),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notes_seeker ON talent_notes(seeker_id, enterprise_id);
```

### 5.2 Redis Key设计

| Key Pattern | 类型 | 用途 | TTL |
|-------------|------|------|-----|
| `session:{openid}` | String(JSON) | 用户Session | 30min |
| `sms:code:{phone}` | String | 短信验证码 | 5min |
| `job:views:{job_id}` | HyperLogLog | 岗位浏览UV | 永久 |
| `cache:job:{id}` | String(JSON) | 岗位详情缓存 | 10min |
| `cache:talent:{id}` | String(JSON) | 人才详情缓存 | 10min |
| `rate:ai:{user_id}:{feature}` | String(Int) | AI调用限流 | 1h |
| `celery:*` | List/Set | Celery队列 | - |

---

## 6. API接口设计

### 6.1 RESTful API规范

**统一响应格式**：
```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    code: int  # 200成功，400客户端错误，500服务端错误
    message: str
    data: Optional[T] = None
    
# 成功响应
{
  "code": 200,
  "message": "success",
  "data": {...}
}

# 错误响应
{
  "code": 400,
  "message": "参数验证失败",
  "data": {"field": "title", "error": "不能为空"}
}
```

### 6.2 核心接口列表

#### 用户模块（6个接口）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 微信登录 | POST | `/api/v1/auth/wechat-login` | 换取openid，返回JWT |
| 完善资料 | PUT | `/api/v1/users/profile` | 更新display_name等 |
| 企业认证 | POST | `/api/v1/enterprises/register` | 上传营业执照，AI OCR |
| 获取企业信息 | GET | `/api/v1/enterprises/{id}` | 含虚拟名/认证状态 |
| 设置虚拟名 | PUT | `/api/v1/enterprises/{id}/virtual-name` | 更新虚拟名 |
| 上传头像 | POST | `/api/v1/users/avatar` | 返回OSS URL |

**示例**：
```python
# POST /api/v1/enterprises/register
{
  "license_image_url": "https://oss.../license.jpg"
}

# 响应
{
  "code": 200,
  "data": {
    "enterprise_id": 123,
    "ocr_result": {
      "company_name": "星辰互联科技有限公司",
      "credit_code": "91110108...",
      "confidence": 0.98
    },
    "verification_status": "pending"
  }
}
```

#### 岗位模块（10个接口）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 创建岗位（AI辅助） | POST | `/api/v1/jobs` | 含AI JD生成 |
| 保存草稿 | PUT | `/api/v1/jobs/{id}/draft` | 状态=draft |
| 提交审核 | POST | `/api/v1/jobs/{id}/submit` | draft→pending |
| 岗位列表 | GET | `/api/v1/jobs` | 支持筛选/排序 |
| 岗位详情 | GET | `/api/v1/jobs/{id}` | 含AI画像 |
| AI生成JD | POST | `/api/v1/ai/job/generate` | 独立AI接口 |
| AI润色JD | POST | `/api/v1/ai/job/polish` | JD优化 |
| 批量导入 | POST | `/api/v1/jobs/batch-import` | Excel上传 |
| 岗位统计 | GET | `/api/v1/jobs/{id}/stats` | 浏览/留言/漏斗 |
| 浏览记录穿透 | GET | `/api/v1/jobs/{id}/visitors` | 按人聚合 |

**示例（AI生成JD）**：
```python
# POST /api/v1/ai/job/generate
{
  "title": "Python开发工程师",
  "city": "北京",
  "salary": "20-35K",
  "experience": "3-5年"
}

# 响应
{
  "code": 200,
  "data": {
    "title": "Python开发工程师",
    "responsibility": [
      "负责推荐系统后端开发",
      "优化算法性能，提升召回率"
    ],
    "requirement": [
      "3年以上Python开发经验",
      "熟悉Django/Flask/FastAPI"
    ],
    "ai_score": 85,  # AI评估吸引力
    "suggestions": ["建议补充技术栈要求"]
  }
}
```

#### 消息模块（5个接口）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 发送留言 | POST | `/api/v1/messages` | AI内容审核 |
| 对话列表 | GET | `/api/v1/conversations` | 按角色分组 |
| 对话详情 | GET | `/api/v1/conversations/{id}/messages` | 消息历史 |
| AI智能回复建议 | POST | `/api/v1/ai/reply-suggestions` | 生成3条候选 |
| 交换联系方式 | POST | `/api/v1/conversations/{id}/exchange-contact` | 解密真名/手机 |

#### 人才池模块（8个接口）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 人才池列表 | GET | `/api/v1/talent` | 按人聚合 |
| 人才详情 | GET | `/api/v1/talent/{seeker_id}` | 所有投递岗位+留言 |
| AI人岗匹配 | POST | `/api/v1/ai/match` | 计算匹配度 |
| 添加团队备注 | POST | `/api/v1/talent/{id}/notes` | 协作备注 |
| 设置跟进提醒 | POST | `/api/v1/talent/{id}/followup` | 定时提醒 |
| 人才统计 | GET | `/api/v1/talent/stats` | 总数/活跃/匹配 |
| 导出人才 | GET | `/api/v1/talent/export` | Excel导出 |
| 批量打标签 | POST | `/api/v1/talent/batch-tag` | 批量操作 |

#### 推送模块（5个接口）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 订阅管理 | POST | `/api/v1/subscriptions` | 关键词订阅 |
| 订阅列表 | GET | `/api/v1/subscriptions` | 当前用户订阅 |
| 推送历史 | GET | `/api/v1/push/history` | 收到的推送 |
| 推送统计 | GET | `/api/v1/push/stats` | 打开率/转化率 |
| 通知中心 | GET | `/api/v1/notifications` | 站内消息 |

#### 审核模块（4个接口）

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 审核队列 | GET | `/api/v1/admin/review/queue` | 待审核列表 |
| 审核详情 | GET | `/api/v1/admin/review/{id}` | 含AI预审结果 |
| 通过审核 | POST | `/api/v1/admin/review/{id}/approve` | pending→online |
| 驳回审核 | POST | `/api/v1/admin/review/{id}/reject` | 附驳回理由 |

### 6.3 鉴权方案

**JWT Bearer Token**：
```python
# 登录后返回
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 7200
}

# 后续请求Header
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**JWT Payload**：
```json
{
  "user_id": 123,
  "openid": "oX9Yw5...",
  "role": "recruiter",
  "enterprise_id": 456,
  "exp": 1717567890
}
```

---

## 7. AI能力架构专项

### 7.1 AI Gateway设计

**职责**：
1. 统一AI调用入口
2. Prompt版本管理（A/B测试）
3. 模型路由与降级
4. 缓存策略
5. Token计量与成本统计
6. 异常处理与重试

**核心代码**：
```python
# ai/gateway.py
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
import redis
import hashlib
import json

class AIGateway:
    def __init__(self):
        self.primary_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            timeout=30
        )
        self.fallback_llm = ChatOpenAI(
            model="qwen-max",  # 通义千问
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            timeout=30
        )
        self.redis = redis.Redis(decode_responses=True)
        self.cache_ttl = {
            'jd_generate': 3600,      # JD生成缓存1小时
            'content_review': 300,    # 内容审核缓存5分钟
            'smart_reply': 1800,      # 智能回复缓存30分钟
            'matching': 600,          # 匹配评分缓存10分钟
        }
    
    async def call_with_fallback(
        self, 
        chain,
        inputs: dict, 
        feature: str,
        user_id: int = None
    ):
        """统一AI调用入口"""
        
        # 1. 生成缓存key
        cache_key = self._gen_cache_key(feature, inputs)
        
        # 2. 检查缓存
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 3. 限流检查
        if user_id and not self._check_rate_limit(user_id, feature):
            raise Exception("AI调用频率超限，请稍后再试")
        
        # 4. 主模型调用（带计量）
        try:
            with get_openai_callback() as cb:
                result = await chain.arun(inputs)
                
                # 记录Token消耗
                await self._log_usage(
                    feature=feature,
                    user_id=user_id,
                    tokens=cb.total_tokens,
                    cost=cb.total_cost
                )
                
                # 写缓存
                ttl = self.cache_ttl.get(feature, 600)
                self.redis.setex(cache_key, ttl, json.dumps(result))
                
                return result
        
        except Exception as e:
            # 5. 降级到备用模型
            logger.warning(f"主模型失败，降级：{e}")
            return await self._fallback(chain, inputs, feature)
    
    def _gen_cache_key(self, feature: str, inputs: dict) -> str:
        """生成缓存key"""
        content = json.dumps(inputs, sort_keys=True)
        hash_val = hashlib.md5(content.encode()).hexdigest()
        return f"ai:cache:{feature}:{hash_val}"
    
    def _check_rate_limit(self, user_id: int, feature: str) -> bool:
        """限流检查（令牌桶算法）"""
        key = f"rate:ai:{user_id}:{feature}"
        limit = 100  # 每小时100次
        current = self.redis.get(key)
        
        if not current:
            self.redis.setex(key, 3600, 1)
            return True
        
        if int(current) >= limit:
            return False
        
        self.redis.incr(key)
        return True
    
    async def _fallback(self, chain, inputs, feature):
        """降级策略"""
        if feature == "jd_generate":
            # 返回模板JD
            return self._template_jd(inputs)
        elif feature == "smart_reply":
            # 返回预设短语
            return self._preset_replies()
        elif feature == "content_review":
            # 降级为关键词过滤
            return self._keyword_filter(inputs)
        else:
            # 尝试备用模型
            return await chain.arun(inputs, llm=self.fallback_llm)

# 全局单例
ai_gateway = AIGateway()
```

### 7.2 12项AI能力实现

#### 1. OCR识别（营业执照）

```python
# ai/chains/ocr.py
from langchain.chains import TransformChain
import httpx

async def ocr_license(image_url: str) -> dict:
    """调用百度OCR识别营业执照"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://aip.baidubce.com/rest/2.0/ocr/v1/business_license",
            data={"url": image_url},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        result = resp.json()
        
    return {
        "company_name": result['words_result']['单位名称']['words'],
        "credit_code": result['words_result']['社会信用代码']['words'],
        "legal_person": result['words_result']['法人']['words'],
        "address": result['words_result']['地址']['words'],
        "confidence": result['words_result']['单位名称']['probability']['average']
    }
```

#### 2. JD代写与润色

```python
# ai/chains/jd_writer.py
from langchain import PromptTemplate, LLMChain

JD_GENERATE_PROMPT = """你是资深HR，擅长撰写吸引人的职位描述。

岗位信息：
- 职位：{title}
- 城市：{city}
- 薪资：{salary}
- 经验要求：{experience}

请生成职位描述，包含：
1. 岗位职责（3-5条，每条20字左右）
2. 任职要求（5-7条，每条15字左右）
3. 加分项（2-3条）

返回JSON格式：
{{
  "responsibility": ["...", "..."],
  "requirement": ["...", "..."],
  "bonus": ["...", "..."]
}}
"""

async def generate_jd(title: str, city: str, salary: str, experience: str):
    prompt = PromptTemplate(
        template=JD_GENERATE_PROMPT,
        input_variables=["title", "city", "salary", "experience"]
    )
    chain = LLMChain(llm=ai_gateway.primary_llm, prompt=prompt)
    
    result = await ai_gateway.call_with_fallback(
        chain=chain,
        inputs={"title": title, "city": city, "salary": salary, "experience": experience},
        feature="jd_generate"
    )
    
    return json.loads(result)
```

#### 3. 内容审核

```python
# ai/chains/content_review.py
CONTENT_REVIEW_PROMPT = """你是内容审核专家，检查以下文本是否违规。

文本：{content}

审核维度：
1. 是否含歧视性内容（性别、年龄、地域）
2. 是否含违禁词（传销、赌博、色情）
3. 是否含虚假信息（夸大薪资、虚假承诺）
4. 语气是否专业

返回JSON：
{{
  "result": "pass/warning/block",
  "reason": "具体原因",
  "suggestions": ["修改建议1", "修改建议2"]
}}
"""

async def review_content(content: str):
    # 实现逻辑同上
    pass
```

#### 4. 智能回复建议

```python
# ai/chains/smart_reply.py
REPLY_SUGGESTION_PROMPT = """你是招聘HR助手，根据求职者的留言，生成3条专业回复建议。

求职者留言：{message}
岗位：{job_title}

生成3条回复，要求：
1. 第一条：热情欢迎型
2. 第二条：简洁询问型（询问简历/意向）
3. 第三条：详细介绍型（介绍岗位亮点）

每条30字左右。
"""
```

#### 5. 人岗匹配评分

```python
# ai/chains/matching.py
async def calculate_match_score(job_embedding: list, resume_embedding: list):
    """基于向量相似度计算匹配度"""
    from numpy import dot
    from numpy.linalg import norm
    
    # 余弦相似度
    cos_sim = dot(job_embedding, resume_embedding) / (norm(job_embedding) * norm(resume_embedding))
    
    # 归一化到0-100
    score = int((cos_sim + 1) * 50)
    
    return {
        "total_score": score,
        "dimensions": {
            "skill_match": score + 5,
            "experience_match": score - 3,
            "salary_match": score + 2
        }
    }
```

### 7.3 Prompt版本管理

```python
# ai/prompts/版本化管理
prompts/
├── jd_writer/
│   ├── v1.txt        # 基础版
│   ├── v2.txt        # 优化版（突出成长空间）
│   └── config.json   # A/B测试配置
└── content_review/
    ├── v1.txt
    └── v2.txt

# config.json
{
  "jd_writer": {
    "default": "v2",
    "ab_test": {
      "enabled": true,
      "v1_ratio": 0.3,
      "v2_ratio": 0.7
    }
  }
}
```

### 7.4 成本控制

**Token计量**：
```python
async def _log_usage(self, feature, user_id, tokens, cost):
    """记录AI调用成本"""
    key = f"ai:cost:{datetime.now().strftime('%Y%m%d')}"
    self.redis.hincrby(key, feature, tokens)
    
    # 用户维度
    user_key = f"ai:cost:user:{user_id}:{datetime.now().strftime('%Y%m')}"
    self.redis.hincrbyfloat(user_key, "cost", cost)
```

**月度预算控制**：
```python
# 配置月度预算
AI_MONTHLY_BUDGET = 5000  # 5000元

async def check_budget():
    month_key = f"ai:cost:{datetime.now().strftime('%Y%m')}"
    total_cost = sum([float(v) for v in redis.hvals(month_key)])
    
    if total_cost >= AI_MONTHLY_BUDGET * 0.9:
        # 触发告警，切换到低成本模型
        logger.warning("AI预算即将超限，切换降级策略")
        return False
    return True
```

---

## 8. 部署与运维

### 8.1 Docker Compose部署（一期）

**docker-compose.yml**：
```yaml
version: '3.8'

services:
  # FastAPI应用
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/jobplatform
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    command: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    restart: always
  
  # Celery Worker
  celery_worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/jobplatform
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    command: celery -A app.tasks worker --loglevel=info --concurrency=4
    restart: always
  
  # Celery Beat（定时任务）
  celery_beat:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    command: celery -A app.tasks beat --loglevel=info
    restart: always
  
  # PostgreSQL
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=jobplatform
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
  
  # Nginx
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

**Dockerfile**：
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装Python依赖
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# 复制应用代码
COPY . .

# 启动命令
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

**一键启动**：
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止
docker-compose down
```

### 8.2 生产环境部署方案

**架构**：
```
                  ┌─────────────┐
Internet ────────►│   Nginx     │ (SSL终止、负载均衡)
                  └──────┬──────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ FastAPI  │  │ FastAPI  │  │ Celery   │
    │ Instance │  │ Instance │  │ Workers  │
    │    1     │  │    2     │  │  (4个)   │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │
         └─────────────┼─────────────┘
                       ▼
              ┌────────────────┐
              │   PostgreSQL   │
              │   (RDS托管)    │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   Redis集群    │
              │   (3节点)      │
              └────────────────┘
```

**服务器配置（一期）**：
| 角色 | 配置 | 数量 | 月成本 |
|------|------|------|--------|
| FastAPI应用 | 4C8G | 2台 | ¥1,230 |
| PostgreSQL RDS | 4C8G | 1 | ¥800 |
| Redis | 4G | 1 | ¥300 |
| **总计** | - | - | **¥2,330** |

### 8.3 K8s部署（二期扩展）

**当满足以下条件时考虑K8s**：
- DAU > 5万
- 需要按模块独立扩展
- 有专职DevOps

**k8s-deployment.yaml**：
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: registry.cn-beijing.aliyuncs.com/yourorg/job-platform:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 9. 开发排期与成本

### 9.1 开发排期（AI工程师团队）

**假设**：2个AI工程师 + 1个前端开发

#### 第一阶段（Sprint 1-2，4周）：核心MVP

| 任务 | 负责人 | 工期 | 说明 |
|------|--------|------|------|
| 项目脚手架搭建 | AI工程师A | 2天 | FastAPI + SQLAlchemy + Docker |
| 数据库设计 + 迁移 | AI工程师A | 3天 | Alembic迁移脚本 |
| 用户模块（登录/注册） | AI工程师A | 3天 | 微信OAuth + JWT |
| AI Gateway基础框架 | AI工程师A | 3天 | LangChain + 缓存 + 降级 |
| OCR识别（营业执照） | AI工程师A | 2天 | 百度OCR接口 |
| 岗位模块（CRUD） | AI工程师B | 4天 | 含状态机 |
| AI JD生成 + 润色 | AI工程师B | 3天 | Prompt调优 |
| 内容审核 | AI工程师B | 2天 | AI + 关键词 |
| 前端对接 | 前端 | 10天 | 与原型对齐 |
| **Sprint 1-2总计** | - | **4周** | **可演示MVP** |

#### 第二阶段（Sprint 3-4，4周）：完善功能

| 任务 | 负责人 | 工期 | 说明 |
|------|--------|------|------|
| 消息模块 | AI工程师A | 4天 | 对话+智能回复 |
| 推送模块 | AI工程师A | 3天 | Celery + 订阅匹配 |
| 人才池模块 | AI工程师B | 5天 | 按人聚合 + 备注 |
| 人岗匹配（向量） | AI工程师B | 4天 | pgvector + 余弦相似度 |
| 统计模块 | AI工程师A | 3天 | 浏览穿透 + 漏斗 |
| 审核模块 | AI工程师B | 2天 | 审核队列 |
| 管理后台API | AI工程师A | 3天 | 聚合接口 |
| 前端完善 | 前端 | 10天 | 全功能覆盖 |
| **Sprint 3-4总计** | - | **4周** | **功能完整** |

#### 第三阶段（Sprint 5-6，4周）：测试与优化

| 任务 | 负责人 | 工期 | 说明 |
|------|--------|------|------|
| 单元测试 | 全员 | 5天 | 覆盖率>80% |
| 集成测试 | 全员 | 3天 | API契约测试 |
| 性能测试 | AI工程师A | 2天 | 压测+优化 |
| AI Prompt调优 | AI工程师B | 5天 | A/B测试 |
| 监控告警 | AI工程师A | 2天 | Prometheus |
| 生产部署 | AI工程师A | 3天 | Docker Compose |
| **Sprint 5-6总计** | - | **4周** | **生产就绪** |

**总计**：**12周（3个月）**上线生产环境

### 9.2 成本估算

#### 一次性成本

| 项目 | 金额 | 说明 |
|------|------|------|
| 开发人力 | ¥180,000 | 2个AI工程师 × 3个月 × ¥30k/月 |
| 前端人力 | ¥60,000 | 1个前端 × 3个月 × ¥20k/月 |
| 域名+SSL证书 | ¥500 | 一次性 |
| **总计** | **¥240,500** | - |

#### 月度运营成本

| 项目 | 一期（0-5万DAU） | 二期（5-20万DAU） |
|------|-----------------|------------------|
| **服务器** | | |
| FastAPI应用服务器 | ¥1,230 (2台4C8G) | ¥2,460 (4台) |
| PostgreSQL RDS | ¥800 | ¥1,600 (主从) |
| Redis | ¥300 | ¥900 (集群) |
| OSS存储 | ¥100 | ¥300 |
| CDN | ¥200 | ¥500 |
| **服务器小计** | **¥2,630** | **¥5,760** |
| **AI调用** | | |
| LLM (GPT-4o-mini) | ¥3,000 | ¥8,000 |
| OCR | ¥500 | ¥1,500 |
| 其他AI服务 | ¥500 | ¥1,000 |
| **AI小计** | **¥4,000** | **¥10,500** |
| **月度总计** | **¥6,630** | **¥16,260** |
| **年度总计** | **¥79,560** | **¥195,120** |

**对比Java方案**：
- Java微服务一期：¥10,000（服务器）+ ¥4,000（AI）= **¥14,000/月**
- Python单体一期：¥2,630（服务器）+ ¥4,000（AI）= **¥6,630/月**
- **节省**：53%

---

## 10. 代码结构示例

### 10.1 完整项目结构

```
job-platform/
├── README.md
├── pyproject.toml           # Poetry依赖
├── poetry.lock
├── .env.example             # 环境变量模板
├── docker-compose.yml
├── Dockerfile
├── alembic.ini              # 数据库迁移配置
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   │
│   ├── core/                # 核心配置
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   │
│   ├── api/                 # API路由
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── jobs.py
│   │       ├── messages.py
│   │       ├── talent.py
│   │       └── admin.py
│   │
│   ├── modules/             # 业务模块
│   │   ├── user/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   ├── job/
│   │   ├── message/
│   │   ├── talent/
│   │   ├── push/
│   │   ├── review/
│   │   ├── stats/
│   │   └── admin/
│   │
│   ├── ai/                  # AI能力层
│   │   ├── __init__.py
│   │   ├── gateway.py
│   │   ├── chains/
│   │   │   ├── jd_writer.py
│   │   │   ├── content_review.py
│   │   │   ├── smart_reply.py
│   │   │   ├── matching.py
│   │   │   └── ocr.py
│   │   ├── prompts/
│   │   │   ├── jd_writer_v1.txt
│   │   │   └── jd_writer_v2.txt
│   │   ├── embeddings.py
│   │   ├── vectorstore.py
│   │   └── fallback.py
│   │
│   ├── tasks/               # Celery任务
│   │   ├── __init__.py
│   │   ├── push_tasks.py
│   │   ├── ai_batch_tasks.py
│   │   └── stats_tasks.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   └── base.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       ├── exceptions.py
│       └── encryption.py
│
├── alembic/                 # 数据库迁移
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
│
├── tests/                   # 测试
│   ├── conftest.py
│   ├── test_api/
│   ├── test_modules/
│   └── test_ai/
│
└── scripts/                 # 脚本工具
    ├── init_db.py
    └── seed_data.py
```

### 10.2 main.py（应用入口）

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.session import engine
from app.api.v1 import auth, users, jobs, messages, talent, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("🚀 FastAPI应用启动")
    yield
    # 关闭时执行
    print("👋 FastAPI应用关闭")

app = FastAPI(
    title="空岗信息发布对接平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["岗位"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["消息"])
app.include_router(talent.router, prefix="/api/v1/talent", tags=["人才池"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理后台"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

### 10.3 典型模块示例（Job模块）

```python
# modules/job/models.py
from sqlalchemy import Column, Integer, String, Text, ARRAY, Enum
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    cities = Column(ARRAY(String))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    responsibility = Column(Text)
    requirement = Column(Text)
    status = Column(Enum('draft', 'pending', 'online', 'closed', name='job_status'))
    ai_review_detail = Column(JSONB)
    embedding = Column(Vector(768))
```

```python
# modules/job/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class JobCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    cities: List[str] = Field(..., min_items=1, max_items=10)
    salary_min: int = Field(..., gt=0)
    salary_max: int = Field(..., gt=0)
    responsibility: str
    requirement: str

class JobResponse(BaseModel):
    id: int
    title: str
    cities: List[str]
    salary_range: str
    status: str
    
    class Config:
        from_attributes = True
```

```python
# modules/job/service.py
from app.ai.gateway import ai_gateway
from app.modules.job.repository import JobRepository

class JobService:
    @staticmethod
    async def create_with_ai(data: JobCreate, user_id: int):
        # 1. AI生成JD（如果需要）
        if data.need_ai_generate:
            jd_content = await ai_gateway.generate_jd(
                title=data.title,
                city=data.cities[0],
                salary=f"{data.salary_min}-{data.salary_max}K"
            )
            data.responsibility = jd_content['responsibility']
            data.requirement = jd_content['requirement']
        
        # 2. AI内容审核
        review_result = await ai_gateway.review_content(
            content=f"{data.title} {data.responsibility} {data.requirement}"
        )
        
        # 3. 保存到数据库
        job = await JobRepository.create(data, user_id)
        job.ai_review_detail = review_result
        
        # 4. 生成Embedding（异步任务）
        from app.tasks.ai_batch_tasks import generate_job_embedding
        generate_job_embedding.delay(job.id)
        
        return job
```

```python
# api/v1/jobs.py
from fastapi import APIRouter, Depends
from app.modules.job.service import JobService
from app.modules.job.schemas import JobCreate, JobResponse
from app.core.dependencies import get_current_user

router = APIRouter()

@router.post("/", response_model=JobResponse)
async def create_job(
    data: JobCreate,
    current_user = Depends(get_current_user)
):
    job = await JobService.create_with_ai(data, current_user.id)
    return job
```

---

## 11. 渐进拆分路径

### 11.1 拆分时机判断

**何时拆分**？满足以下**任一条件**：
1. **性能瓶颈**：某模块响应时间P99 > 3秒
2. **并发瓶颈**：单进程CPU/内存达到80%
3. **开发冲突**：多人频繁改同一模块代码
4. **独立扩展需求**：某模块需要独立扩容（如AI Gateway）

**不拆分的信号**：
- DAU < 5万
- 开发团队 < 5人
- 没有明显性能问题

### 11.2 拆分优先级

**第一批拆分（6-12个月）**：
1. **AI Gateway** → 独立FastAPI服务（Python）
2. **Celery Workers** → 独立部署，按任务类型分组

**第二批拆分（12-18个月）**：
3. **Stats服务** → 独立服务 + ClickHouse
4. **Push服务** → 独立服务，专注推送

**第三批拆分（18个月+）**：
5. 按需拆分其他模块（job/message/talent）

### 11.3 拆分实施步骤（以AI Gateway为例）

**Step 1：代码隔离**
```python
# 原来：ai/gateway.py 在主应用内
# 改为：独立的 ai-gateway/ 项目
ai-gateway/
├── main.py
├── gateway.py
├── chains/
└── requirements.txt
```

**Step 2：接口定义**
```python
# 主应用调用AI Gateway
import httpx

async def call_ai_gateway(feature: str, inputs: dict):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://ai-gateway:8001/api/ai/call",
            json={"feature": feature, "inputs": inputs}
        )
        return resp.json()
```

**Step 3：数据迁移**
```sql
-- AI调用日志迁移到独立表
CREATE TABLE ai_call_logs (
    id SERIAL PRIMARY KEY,
    feature VARCHAR(50),
    user_id INTEGER,
    tokens INTEGER,
    cost NUMERIC(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Step 4：灰度发布**
```python
# 10%流量走新服务，90%走旧逻辑
if random.random() < 0.1:
    result = await call_ai_gateway(feature, inputs)
else:
    result = await ai_gateway_local.call(feature, inputs)
```

**Step 5：全量切换**
```python
# 全部流量切到新服务
result = await call_ai_gateway(feature, inputs)
```

---

## 12. 监控与告警

### 12.1 监控体系

**Prometheus + Grafana**：
```python
# 在FastAPI中暴露metrics
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# 定义指标
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('api_request_duration_seconds', 'API request duration')
ai_calls = Counter('ai_calls_total', 'Total AI calls', ['feature', 'status'])
ai_tokens = Counter('ai_tokens_total', 'Total AI tokens consumed', ['feature'])

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

# 在middleware中记录
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.observe(duration)
    return response
```

**Grafana Dashboard关键指标**：
```
1. 系统指标
   - API QPS（每秒请求数）
   - API延迟（P50/P90/P99）
   - 错误率（按endpoint）
   - 4xx/5xx状态码分布

2. 业务指标
   - DAU/MAU
   - 岗位发布量（日/周）
   - 消息互动量
   - 投递转化率

3. AI指标
   - AI调用次数（按功能）
   - AI响应延迟
   - AI降级触发率
   - Token消耗量（日/月）
   - AI成本（日/月）

4. 数据库指标
   - 连接池使用率
   - 慢查询数量（>1s）
   - 数据库CPU/内存
```

### 12.2 日志方案

**结构化日志**：
```python
# utils/logging.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": message,
            **kwargs
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def error(self, message: str, error: Exception = None, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": message,
            "error": str(error) if error else None,
            **kwargs
        }
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))

# 使用示例
logger = StructuredLogger(__name__)
logger.info("用户登录", user_id=123, ip="192.168.1.1")
logger.error("AI调用失败", error=e, feature="jd_generate", user_id=123)
```

**日志聚合（Loki）**：
```yaml
# docker-compose.yml中添加
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - ./loki-config.yaml:/etc/loki/local-config.yaml

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log
    - ./promtail-config.yaml:/etc/promtail/config.yaml
```

### 12.3 告警规则

**Prometheus Alert Rules**：
```yaml
# prometheus-alerts.yml
groups:
  - name: api_alerts
    rules:
      # P0告警：服务不可用
      - alert: APIDown
        expr: up{job="fastapi"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FastAPI服务不可用"
      
      # P1告警：错误率高
      - alert: HighErrorRate
        expr: rate(api_requests_total{status=~"5.."}[5m]) > 0.05
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "API错误率超过5%"
      
      # P1告警：AI调用失败率高
      - alert: AICallFailureRate
        expr: rate(ai_calls_total{status="error"}[10m]) > 0.3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "AI调用失败率超过30%"
      
      # P2告警：响应延迟高
      - alert: SlowAPIResponse
        expr: histogram_quantile(0.99, rate(api_request_duration_seconds_bucket[5m])) > 3
        for: 5m
        labels:
          severity: info
        annotations:
          summary: "API P99延迟超过3秒"
```

**告警通知（钉钉/飞书/企业微信）**：
```python
import httpx

async def send_alert(title: str, content: str):
    """发送钉钉告警"""
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=..."
    
    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": f"## {title}\n\n{content}\n\n时间：{datetime.now()}"
        }
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=message)
```

---

## 13. 数据安全方案

### 13.1 敏感数据加密

**AES-256-GCM加密**：
```python
# utils/encryption.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class Encryptor:
    def __init__(self, master_key: str):
        # 从主密钥派生加密密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"job-platform-salt",
            iterations=100000,
        )
        self.key = kdf.derive(master_key.encode())
        self.aesgcm = AESGCM(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """加密"""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        # 返回 base64(nonce + ciphertext)
        return base64.b64encode(nonce + ciphertext).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """解密"""
        data = base64.b64decode(encrypted)
        nonce = data[:12]
        ciphertext = data[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()

# 全局单例
encryptor = Encryptor(os.getenv("MASTER_KEY"))
```

**加密字段**：
- 真实姓名：`real_name_encrypted`
- 手机号：`phone_encrypted`
- 信用代码：`credit_code_encrypted`
- 微信号：`wechat_id_encrypted`

### 13.2 API安全

**JWT鉴权**：
```python
# core/security.py
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await UserRepository.get_by_id(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**限流**：
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# 使用
@app.post("/api/v1/ai/job/generate")
@limiter.limit("10/minute")  # 每分钟10次
async def generate_jd(request: Request, data: JDRequest):
    pass
```

### 13.3 SQL注入防护

**使用ORM参数化查询**：
```python
# ✅ 正确：参数化查询
async def get_jobs_by_city(city: str):
    query = select(Job).where(Job.cities.contains([city]))
    result = await session.execute(query)
    return result.scalars().all()

# ❌ 错误：字符串拼接（危险！）
async def get_jobs_by_city_unsafe(city: str):
    query = f"SELECT * FROM jobs WHERE '{city}' = ANY(cities)"  # SQL注入风险
    result = await session.execute(text(query))
```

### 13.4 数据脱敏

**AI调用前脱敏**：
```python
async def call_ai_with_privacy(content: str):
    """调用AI前脱敏敏感信息"""
    import re
    
    # 手机号脱敏
    content = re.sub(r'1[3-9]\d{9}', '138****1234', content)
    
    # 身份证号脱敏
    content = re.sub(r'\d{17}[\dXx]', '110***********1234', content)
    
    # 邮箱脱敏
    content = re.sub(r'[\w\.-]+@[\w\.-]+', 'user***@example.com', content)
    
    return await ai_gateway.call(content)
```

---

## 14. 风险与应对

### 14.1 技术风险

| 风险 | 等级 | 影响 | 应对措施 |
|------|------|------|---------|
| **PostgreSQL单库瓶颈** | 🔴高 | 5万DAU后性能下降 | 1. 一期优化索引和查询；2. 二期读写分离；3. 三期分库分表 |
| **Python GIL限制** | 🟡中 | 单进程CPU利用率低 | 多进程部署（Gunicorn workers=4） |
| **AI API不稳定** | 🔴高 | 核心功能不可用 | 1. 主备模型；2. 降级策略；3. 缓存；4. 重试机制 |
| **pgvector性能** | 🟡中 | 100万+向量检索慢 | 1. 一期够用（<50万）；2. 二期迁移Milvus |
| **Celery任务积压** | 🟡中 | 推送延迟 | 1. 增加worker数量；2. 按优先级分队列 |

### 14.2 业务风险

| 风险 | 等级 | 影响 | 应对措施 |
|------|------|------|---------|
| **AI幻觉** | 🔴高 | 生成不当内容 | 1. 内容审核双保险；2. "AI生成"标注；3. 用户反馈机制 |
| **AI成本超预算** | 🟡中 | 月成本失控 | 1. Token计量；2. 预算告警（90%触发）；3. 降级为便宜模型 |
| **数据泄露** | 🔴高 | 法律风险 | 1. 敏感字段加密；2. API鉴权；3. 审计日志；4. 定期安全审计 |
| **黑产刷量** | 🟡中 | AI成本浪费 | 1. 限流；2. 验证码；3. 行为分析；4. IP黑名单 |

### 14.3 团队风险

| 风险 | 等级 | 影响 | 应对措施 |
|------|------|------|---------|
| **核心开发离职** | 🔴高 | 项目停滞 | 1. 代码文档化；2. 结对编程；3. 知识分享会 |
| **技能单一** | 🟡中 | 只会Python，无法应对复杂场景 | 1. 学习异步编程；2. 学习数据库优化；3. 学习运维 |
| **过度依赖AI工具** | 🟢低 | 代码质量下降 | 1. Code Review；2. 单元测试覆盖 |

### 14.4 风险应对优先级

**立即行动（P0）**：
1. ✅ AI降级策略（主备模型 + 缓存）
2. ✅ 敏感数据加密（AES-256）
3. ✅ 监控告警（Prometheus + Grafana）

**近期完成（P1，1个月内）**：
4. ⏱ 数据库读写分离准备（预留配置）
5. ⏱ AI成本监控与预算告警
6. ⏱ 限流与防刷机制

**中期规划（P2，3个月内）**：
7. ⏱ 代码文档完善（Sphinx）
8. ⏱ 性能压测与优化
9. ⏱ 灾备演练

---

## 15. 附录

### 15.1 技术选型对比总结

| 维度 | Python/FastAPI | Java/Spring Cloud |
|------|---------------|-------------------|
| **开发速度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **运维复杂度** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **AI集成** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **性能** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **扩展性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **团队匹配** | ⭐⭐⭐⭐⭐（AI工程师） | ⭐⭐（需学习） |
| **成本** | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**结论**：对AI工程师团队，Python方案在**开发速度、AI集成、成本、团队匹配**4个维度全面领先。

### 15.2 关键指标监控

**一期上线后关注的核心指标**：
```
业务指标：
- DAU / MAU
- 岗位发布量（日均）
- 投递转化率（浏览→留言→沟通）
- 联系方式交换率

技术指标：
- API P99延迟 < 500ms
- 错误率 < 1%
- 可用率 > 99.5%
- 数据库CPU < 70%

AI指标：
- AI调用成功率 > 95%
- AI降级触发率 < 5%
- 月AI成本 < ¥5,000
- Token消耗量（日均）
```

### 15.3 里程碑与交付清单

| 里程碑 | 时间点 | 交付物 | 验收标准 |
|--------|--------|--------|---------|
| **M1: 核心MVP** | 第4周 | 用户/岗位/AI基础功能 | 可演示注册→发布→AI生成JD |
| **M2: 功能完整** | 第8周 | 消息/人才池/推送 | 覆盖PRD 80%功能点 |
| **M3: 生产就绪** | 第12周 | 测试/监控/部署 | 通过压测，可上线 |
| **M4: 数据积累** | 第16周 | 运营1个月 | DAU > 1000 |
| **M5: 按需拆分** | 第24周 | AI Gateway独立 | 支持5万DAU |

### 15.4 参考资料

**Python异步编程**：
- FastAPI官方文档：https://fastapi.tiangolo.com
- SQLAlchemy 2.0异步：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- asyncio最佳实践：https://docs.python.org/3/library/asyncio.html

**AI集成**：
- LangChain文档：https://python.langchain.com
- pgvector GitHub：https://github.com/pgvector/pgvector
- OpenAI API文档：https://platform.openai.com/docs

**部署与运维**：
- Docker Compose：https://docs.docker.com/compose/
- Prometheus监控：https://prometheus.io/docs/
- Grafana Dashboard：https://grafana.com/docs/

### 15.5 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| V1.0 | 2026-06-05 | 初稿，完整的Python/FastAPI技术架构方案，涵盖技术选型、模块设计、数据库、API、AI架构、部署、成本、排期、代码示例、监控、安全、风险应对 |

---

**文档结束**

**核心价值主张**：
- ✅ 为AI工程师团队量身定制
- ✅ 3个月上线生产环境
- ✅ 月成本节省50-70%
- ✅ AI能力深度集成（12+项）
- ✅ 渐进拆分，避免过度设计
- ✅ 完整的监控、安全、风险应对

**下一步行动**：
1. 评审本方案
2. 初始化项目脚手架
3. 第一个Sprint启动（用户模块 + AI Gateway）

**联系方式**：如有技术问题或需要调整方案，请与架构团队联系。

