# 多 AI 协作开发指南

## 仓库信息

- **GitHub**: https://github.com/luxiaoxiaomo/job-platform-ai
- **分支策略**: main 主分支，功能分支开发
- **提交规范**: Conventional Commits (feat/fix/docs/refactor/test/chore)

---

## 快速开始（新 AI 加入）

### 1. 克隆仓库

```bash
git clone https://github.com/luxiaoxiaomo/job-platform-ai.git
cd job-platform-ai
```

### 2. 启动本地环境

**数据库（Docker）**
```bash
cd backend/job-platform
docker-compose -f docker-compose.dev.yml up -d
```

**后端（8003 端口）**
```bash
cd backend/job-platform
# Windows
启动后端.bat

# 或手动
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
```

**前端（5174 端口）**
```bash
cd frontend/wechat-prototype
# Windows
启动前端.bat

# 或手动
npm run dev
```

**验证**
- 后端 API 文档: http://localhost:8003/docs
- 前端应用: http://localhost:5174

---

## 协作工作流

### 场景 1：开发新功能

```bash
# 1. 确保在最新 main 分支
git checkout main
git pull origin main

# 2. 创建功能分支（命名规范：feature/功能名）
git checkout -b feature/message-chat

# 3. 开发并提交
git add .
git commit -m "feat: 实现应聘者-招聘者消息聊天

- WebSocket 实时通讯
- 消息历史记录
- 未读消息提示

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

# 4. 推送到远程
git push origin feature/message-chat

# 5. 创建 Pull Request
gh pr create --title "feat: 消息聊天功能" --body "实现应聘者与招聘者实时通讯"
```

### 场景 2：修复 Bug

```bash
git checkout -b fix/login-validation
# ... 开发修复 ...
git commit -m "fix: 修复登录验证码校验逻辑

- 验证码 6 位长度限制
- 过期时间从 5 分钟改为 10 分钟
- 添加重发冷却时间 60 秒

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
git push origin fix/login-validation
```

### 场景 3：更新文档

```bash
git checkout -b docs/api-guide
# ... 编写文档 ...
git commit -m "docs: 补充 API 调用示例

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
git push origin docs/api-guide
```

---

## 分支命名规范

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feature/` | 新功能 | `feature/resume-upload` |
| `fix/` | Bug 修复 | `fix/auth-token-expire` |
| `docs/` | 文档 | `docs/deployment-guide` |
| `refactor/` | 重构 | `refactor/user-service` |
| `test/` | 测试 | `test/job-api-coverage` |
| `chore/` | 构建/工具 | `chore/update-deps` |

---

## 提交消息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>: <简短描述>

<详细描述（可选）>

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

**Type 类型：**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档
- `refactor`: 重构（不改变功能）
- `test`: 测试
- `chore`: 构建/工具/依赖

**示例：**
```bash
git commit -m "feat: 添加简历上传功能

- 支持 PDF/Word 格式
- RapidOCR 解析简历内容
- AI 自动提取结构化信息

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 代码审查（PR 流程）

### 创建 PR

```bash
# 方式 1: gh CLI（推荐）
gh pr create --title "feat: 投递管理模块" --body "实现投递记录 CRUD 和状态流转"

# 方式 2: GitHub 网页
# 推送分支后，访问 https://github.com/luxiaoxiaomo/job-platform-ai/pulls
```

### PR 检查清单

提交 PR 前确认：
- [ ] 代码已通过本地测试（后端 `pytest`，前端 `npm run build`）
- [ ] 提交消息遵循规范
- [ ] 敏感信息已排除（`.env` 不在提交中）
- [ ] 有必要的注释和文档
- [ ] 数据库迁移已创建（如有表变更）

### 审查与合并

- 由项目 owner 或其他 AI 审查
- 通过后合并到 main
- 合并后删除远程分支：`gh pr merge --delete-branch`

---

## 常见任务

### 同步 main 最新代码

```bash
git checkout main
git pull origin main

# 更新功能分支
git checkout feature/your-feature
git merge main
# 或
git rebase main
```

### 解决合并冲突

```bash
# 1. 尝试合并 main
git merge main
# 如果有冲突，git 会提示冲突文件

# 2. 手动解决冲突（编辑文件，保留正确部分）

# 3. 标记已解决
git add <冲突文件>
git commit -m "chore: 解决与 main 的合并冲突"
```

### 撤销未推送的提交

```bash
# 撤销最后一次提交，保留修改
git reset --soft HEAD~1

# 撤销最后一次提交，丢弃修改
git reset --hard HEAD~1
```

### 查看其他 AI 的工作

```bash
# 查看所有远程分支
git fetch --all
git branch -r

# 切换到其他分支查看
git checkout feature/some-feature-by-another-ai
```

---

## 数据库迁移协作

**创建迁移**
```bash
cd backend/job-platform
# 修改 models 后
poetry run alembic revision --autogenerate -m "add_new_table"
poetry run alembic upgrade head
```

**同步他人的迁移**
```bash
git pull origin main
cd backend/job-platform
poetry run alembic upgrade head
```

---

## 环境隔离

### 后端环境变量

每个 AI 使用独立的 `.env`（不提交），参考 `.env.example`：

```bash
cd backend/job-platform
cp .env.example .env
# 编辑 .env，配置本地数据库/Redis/密钥
```

### 前端 Mock 开关

- **联调模式**（连真实后端）: `VITE_USE_MOCK=false`
- **演示模式**（纯 Mock）: `VITE_USE_MOCK=true`

修改 `frontend/wechat-prototype/.env`

---

## 测试约定

### 后端测试

```bash
cd backend/job-platform
poetry run pytest -v
```

- 单元测试放 `tests/test_modules/`
- API 测试放 `tests/test_api/`
- 覆盖率目标：核心模块 >80%

### 前端测试

```bash
cd frontend/wechat-prototype
npm run build  # 验证构建无误
```

---

## 沟通与协调

### 避免冲突的最佳实践

1. **领取任务前查看 Issues/Projects**
   - GitHub Issues: https://github.com/luxiaoxiaomo/job-platform-ai/issues
   - 在 Issue 下评论 "我来处理"，避免重复开发

2. **功能模块划分**
   - 应聘者端（`frontend/wechat-prototype/src/seeker/`）
   - 招聘者端（`frontend/wechat-prototype/src/recruiter/`）
   - 管理后台（`frontend/wechat-prototype/src/admin/`）
   - 后端模块（`backend/job-platform/app/modules/`）

3. **小步提交、频繁推送**
   - 功能拆小块（如"投递列表"和"投递详情"分两个 PR）
   - 每天至少推送一次，避免大量积压

4. **使用 Draft PR**
   ```bash
   gh pr create --draft --title "WIP: 消息聊天（开发中）"
   ```
   让其他 AI 看到你在做什么

---

## 项目当前状态（2026-06-12）

### ✅ 已完成
- 认证模块（注册/登录/验证码）
- 用户模块（用户信息 CRUD）
- 企业认证（营业执照 OCR + 审核流）
- 岗位管理（发布/列表/详情/AI 代写/批量导入）
- 前后端联调（认证闭环已打通）
- 28 个测试用例通过

### 🔄 进行中
无（待分配）

### ⏳ 待开发（可认领）
1. **投递管理** —— 应聘者投递记录、招聘者收到的简历
2. **消息聊天** —— 应聘者↔招聘者实时通讯
3. **通知中心** —— 系统通知、审核通知、消息提醒
4. **数据统计** —— 招聘者数据看板、应聘者投递统计
5. **简历解析** —— 上传 PDF/Word → AI 提取结构化
6. **画像匹配** —— 人岗匹配算法、相似度计算
7. **测评系统** —— 招聘者推送测评链接给应聘者
8. **学习课程** —— 应聘者技能提升课程

---

## 紧急联系

- **项目 Owner**: @luxiaoxiaomo
- **技术文档**: `docs/` 目录
- **PRD**: `docs/PRD_空岗信息发布对接平台v2.md`
- **架构设计**: `docs/架构设计_Python_FastAPI_空岗平台.md`

---

## FAQ

**Q: 如何查看其他 AI 正在开发的功能？**  
A: `git branch -r` 查看所有远程分支，或访问 https://github.com/luxiaoxiaomo/job-platform-ai/branches

**Q: 我改了 `poetry.lock`，要提交吗？**  
A: 是的，`poetry.lock` 应该提交（已从 `.gitignore` 移除），保证依赖一致性。

**Q: 前端 `node_modules` 要提交吗？**  
A: 不用，`.gitignore` 已排除。每个 AI clone 后自己 `npm install`。

**Q: 数据库容器冲突怎么办？**  
A: 本地测试可改 `docker-compose.dev.yml` 端口（如 5432→5433），但不要提交这个改动。

**Q: 如何运行他人的分支验证功能？**  
A:
```bash
git fetch origin
git checkout feature/some-feature
# 重启服务验证
```

---

**最后更新**: 2026-06-12  
**当前版本**: v0.1.0 (初始推送)
