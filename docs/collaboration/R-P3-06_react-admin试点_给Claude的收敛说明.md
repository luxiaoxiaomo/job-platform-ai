# R-P3-06 react-admin 试点收敛说明

> 给 Claude：当前任务不是继续扩展后台，而是把 `react-admin` 最小试点收敛到可验证状态。

## 1. 当前结论

`react-admin` 试点可以继续，但必须严格收窄范围。

Codex 已经修正了两个关键偏差：

1. `/admin-ra/*` 已经挂回主应用路由，不再通过 `main.jsx` 顶层 hash 分流。
2. MUI 依赖已经收敛到 `^7.3.11`，避免 MUI 9 与 react-admin 依赖不兼容。

当前前端 `npm run build` 已通过。

---

## 2. 你现在只允许处理的范围

只允许修改以下文件或目录：

```text
frontend/wechat-prototype/src/admin-ra/**
frontend/wechat-prototype/src/App.jsx
frontend/wechat-prototype/src/admin/AdminApp.jsx
frontend/wechat-prototype/src/services/api.js
```

其中：

- `src/admin-ra/**` 是主要工作区
- `App.jsx` 只允许维护 `/admin-ra/*` 路由
- `AdminApp.jsx` 只允许维护“react-admin 规则管理台（试运行）”入口
- `services/api.js` 只允许在接口基础地址或鉴权请求确实有问题时小改

---

## 3. 明确不要做

不要做以下事情：

1. 不要改 `frontend/wechat-prototype/src/main.jsx`
2. 不要改 `package.json`
3. 不要改 `package-lock.json`
4. 不要改后端接口
5. 不要改求职者端页面
6. 不要改招聘者端页面
7. 不要改聊天、消息、简历解析、企业认证、AI 配置
8. 不要替换现有 `/admin`
9. 不要重构现有 `AdminApp`
10. 不要新增新的大组件库

这次只做 `react-admin + match-rules` 的最小试点验证。

---

## 4. 当前目标

请验证并修正以下流程：

### 4.1 入口

从现有管理后台进入：

```text
/admin
  -> 基础数据
  -> react-admin 规则管理台（试运行）
  -> /admin-ra/match-rules
```

要求：

- 页面能打开
- 不出现空白页
- 不跳回首页
- 未登录时能按现有认证逻辑处理

### 4.2 规则列表

路径：

```text
/admin-ra/match-rules
```

接口：

```http
GET /api/v1/matches/rule-configs
```

要求：

- 列表能展示规则
- 至少展示 `name / scope / status / version / updated_at`
- 筛选项如果后端暂不支持，不要强行改后端
- 如果筛选参数与后端不兼容，前端先降级处理

### 4.3 规则详情

路径：

```text
/admin-ra/match-rules/:id/show
```

或 react-admin 实际生成的详情路径。

接口：

```http
GET /api/v1/matches/rule-configs/{id}
```

要求：

- 能展示基础信息
- 能展示权重概览
- 能展示维度表
- `logic` 用折叠 JSON 展示即可

### 4.4 规则编辑

路径：

```text
/admin-ra/match-rules/:id
```

或 react-admin 实际生成的 edit 路径。

关键接口：

```http
POST /api/v1/matches/rule-configs/{id}/versions
```

要求：

- 编辑保存不能用 `PUT`
- 编辑保存不能用 `PATCH`
- 编辑保存不能覆盖当前版本
- 必须调用 `/versions`
- 保存成功后要跳转到新版本详情页

这是本次试点最关键的点。

### 4.5 历史版本

路径：

```text
/admin-ra/match-rules/:id/history
```

接口：

```http
GET /api/v1/matches/rule-configs/{id}/history
```

要求：

- 能展示历史版本列表
- 能从历史版本跳回对应规则详情
- 第一版不要求做版本对比
- 第一版不要求做回滚

---

## 5. 重点检查点

请重点检查这几个文件：

```text
frontend/wechat-prototype/src/admin-ra/app/dataProvider.js
frontend/wechat-prototype/src/admin-ra/app/authProvider.js
frontend/wechat-prototype/src/admin-ra/resources/match-rules/list.jsx
frontend/wechat-prototype/src/admin-ra/resources/match-rules/show.jsx
frontend/wechat-prototype/src/admin-ra/resources/match-rules/edit.jsx
frontend/wechat-prototype/src/admin-ra/resources/match-rules/history.jsx
```

其中最容易出错的是：

```text
edit.jsx
```

请确认：

1. 保存时走 `dataProvider.update`
2. `dataProvider.update` 实际调用 `POST /versions`
3. 后端返回 `{ config: newConfig }` 时，前端拿到的是新版本对象
4. 成功后跳转到 `newConfig.id` 的详情页

---

## 6. 接口语义约束

本项目的规则编辑不是普通 CRUD。

正确语义：

```text
编辑规则 = 基于当前规则生成新版本
```

因此：

```text
react-admin update(resource, params)
  -> POST /api/v1/matches/rule-configs/{id}/versions
  -> 返回新版本 config
  -> 跳转新版本详情页
```

不要把它实现成：

```text
PUT /rule-configs/{id}
PATCH /rule-configs/{id}
直接覆盖当前规则
```

---

## 7. 验证命令

前端构建：

```bash
cd frontend/wechat-prototype
npm run build
```

期望：

```text
build 成功
```

如果出现 chunk size warning 可以先接受，因为 `react-admin` 本身较大，且当前已做懒加载。

---

## 8. 完成后请汇报

完成后请只汇报以下内容：

1. 改了哪些文件
2. `/admin-ra/match-rules` 是否能打开
3. 列表接口是否成功
4. 详情接口是否成功
5. 编辑保存是否调用 `/versions`
6. 保存后是否跳转到新版本详情页
7. 历史版本接口是否成功
8. `npm run build` 是否通过
9. 是否还有阻塞

不要汇报无关优化，不要继续扩展功能。

---

## 9. 当前建议

如果遇到问题，优先修前端适配层，不要改后端。

只有在确认后端接口响应结构无法满足 `react-admin` 最小试点时，才把问题记录下来交给 Codex 审核，不要自行新增后端接口。
