# React-Admin 最小迁移方案

> **适用范围**：仅用于 `admin` 管理后台，不涉及求职者端、招聘者端和简历解析业务流页面。

**目标：** 在不打断现有联调、不重构整站前端的前提下，为管理后台引入 `react-admin`，先完成 `人岗匹配规则管理` 的试点迁移，验证其在资源型后台场景中的适配性和收益。

**核心原则：**
- 只迁管理后台，不迁业务端
- 只做最小试点，不替换现有 `/admin`
- 复用现有认证、接口和路由体系
- 通过适配层接入，不要求后端为 `react-admin` 重写 API

---

## 1. 背景与问题

当前项目的前端已经具备可运行的 React + Router 基础，但管理后台最初是按演示型页面快速搭建的，存在以下问题：

1. 后台页面缺少统一的信息架构
2. 列表、详情、编辑页的模式没有抽象成可复用结构
3. 新增配置类页面时，需要重复写筛选、表格、表单、状态处理逻辑
4. 当规则版本、scope、history、权限等能力继续扩展时，维护成本会持续升高

在 `R-P3-05` 完成人岗匹配规则编辑后，这个问题已经开始显现。继续沿用纯手写页面不是不能做，但会让后续 `R-P3-06` 及之后的后台扩展效率越来越低。

因此，需要评估并试点引入一个更适合后台资源管理场景的前端框架。综合当前项目现状，`react-admin` 是较合适的候选。

---

## 2. 为什么选 react-admin

本项目当前的痛点主要集中在“资源型管理后台”，例如：

- 匹配规则管理
- 企业认证审核
- AI 配置管理
- 基础数据配置

这些页面具备明显的后台资源特征：

- 列表页
- 详情页
- 编辑页
- 状态过滤
- 权限和认证
- 版本/历史入口

`react-admin` 对上述能力有较成熟的默认模型，因此适合用于管理后台增强。

但同时，本项目还有大量不适合 `react-admin` 的业务型页面，例如：

- 求职者上传简历
- 简历解析确认
- 人岗匹配结果展示
- 招聘者发布职位流程
- 聊天、通知、投递链路

这些页面交互更强、流程更重，不适合用资源型后台框架承载。

因此，本方案的结论不是“全站迁移到 react-admin”，而是：

**只在管理后台资源层试点引入 react-admin。**

---

## 3. 迁移范围

### 3.1 第一阶段纳入范围

仅迁移 `人岗匹配规则管理`：

- 规则列表
- 规则详情
- 规则编辑
- 历史版本入口

### 3.2 第一阶段明确不纳入范围

以下内容保持现状，不进入本次迁移：

- 求职者端所有页面
- 招聘者端所有页面
- 简历上传/解析/确认页面
- 人岗匹配结果展示页
- 企业认证审核页面
- AI 提示词管理页面
- 现有 `/admin` 主入口替换

这样做的目的是把迁移风险严格限制在一个小范围内，避免影响正在推进的 P2/P3 联调。

---

## 4. 接入策略

本次采用“并存式接入”，而不是“替换式接入”。

### 4.1 路由策略

保留现有路由：

- `/admin`
- `/admin/match-rules/:id`
- `/admin/match-rules/:id/edit`

新增一套试运行入口：

- `/admin-ra/*`

建议路由结构：

```text
/admin                  现有手写管理后台
/admin-ra               react-admin 试点后台入口
/admin-ra/match-rules   react-admin 规则列表
```

这样可以做到：

1. 现有后台继续可用
2. 联调不被新框架打断
3. 可并行比较新旧两套管理页
4. 如果试点效果不好，可以低成本回退

---

## 5. 目录结构建议

建议在现有前端内增加一个独立的 `admin-ra` 目录，避免和现有 `src/admin` 混杂。

```text
frontend/wechat-prototype/src/
  admin-ra/
    app/
      AdminRaApp.jsx
      authProvider.js
      dataProvider.js
      layout.jsx
    resources/
      match-rules/
        list.jsx
        show.jsx
        edit.jsx
        history.jsx
        fields.jsx
        inputs.jsx
    shared/
      http.js
      adapters.js
```

现有目录保持不动：

```text
frontend/wechat-prototype/src/admin/
  AdminApp.jsx
  AdminMatchRules.jsx
  AdminCompanyCertification.jsx
```

这个拆法的好处是：

- 新旧共存清晰
- 试点失败也不会污染现有后台实现
- 后续如果继续迁企业认证、AI 配置，也有明确扩展位

---

## 6. 依赖方案

当前前端依赖较轻，仅包含 React、React Router 和 Vite。为了引入 `react-admin`，需要增加以下依赖：

```bash
npm install react-admin @mui/material @emotion/react @emotion/styled
```

### 说明

1. `react-admin` 本身依赖 MUI
2. 不建议第一阶段直接引入复杂的数据 provider 套件
3. 推荐自己实现一个轻量 `dataProvider`

原因是本项目后端 API 并不完全符合 `react-admin` 默认的 REST 约定，直接套现成 provider 会增加适配复杂度，收益不高。

---

## 7. 认证接入方案

本项目已有前端认证逻辑：

- `src/services/auth.js`
- `src/services/index.js`

第一阶段不重写登录逻辑，只给 `react-admin` 包一层 `authProvider`。

### 7.1 authProvider 职责

- `checkAuth`：检查当前用户是否已登录
- `logout`：复用现有 `logout()`
- `getIdentity`：复用现有 `getCurrentUser()`
- `checkError`：统一处理 401/403

### 7.2 管理员权限约束

第一阶段默认沿用当前 `admin` 身份机制，不引入新的 RBAC 模型。

换句话说：

- `react-admin` 不负责重新定义权限系统
- 它只消费现有登录状态与管理员身份

---

## 8. 数据接入方案

### 8.1 为什么不能直接用默认 CRUD

本项目的规则接口是：

- `GET /api/v1/matches/rule-configs`
- `GET /api/v1/matches/rule-configs/{id}`
- `GET /api/v1/matches/rule-configs/{id}/history`
- `POST /api/v1/matches/rule-configs/{id}/versions`

这里最大的差异是：

**“编辑规则”不是覆盖更新，而是生成新版本。**

这意味着 `react-admin` 默认的 `update(resource, params)` 语义并不直接适用。

### 8.2 dataProvider 设计原则

`dataProvider` 不应试图把后端改造成标准 CRUD，而应在前端做语义映射。

建议映射如下：

- `getList('match-rules')`
  - 调 `GET /api/v1/matches/rule-configs`
- `getOne('match-rules', { id })`
  - 调 `GET /api/v1/matches/rule-configs/{id}`
- `update('match-rules', { id, data })`
  - 实际调 `POST /api/v1/matches/rule-configs/{id}/versions`
  - 语义是“保存为新版本”
- `getManyReference` 或自定义 history loader
  - 调 `GET /api/v1/matches/rule-configs/{id}/history`

### 8.3 关键约束

`react-admin` 页面层必须明确知道：

- Edit 页不是原地更新
- 保存成功后返回的是“新版本”
- 成功后要跳转到新版本详情页，而不是停留在原记录上

这是本项目最重要的适配点。

---

## 9. 第一阶段页面设计

### 9.1 规则列表页

资源：`match-rules`

展示字段建议：

- `name`
- `scope`
- `status`
- `strategy`
- `version`
- `updated_at`

顶部筛选建议：

- `scope`
- `status`
- `strategy`
- 关键字搜索（规则名称）

操作建议：

- 查看详情
- 编辑配置
- 查看历史（可先作为按钮占位）

### 9.2 规则详情页

分区建议：

1. 基础信息
   - name
   - scope
   - strategy
   - status
   - version
   - description
   - created_by / updated_by
   - effective_from / effective_to

2. 权重概览
   - configured_total_weight
   - effective_total_weight
   - 启用维度数
   - 归一化说明

3. 维度表
   - label
   - key
   - enabled
   - configured_weight
   - effective_weight
   - description
   - logic_json 折叠展示

### 9.3 规则编辑页

编辑字段：

- name
- description
- status
- scope
- dimensions

每个 dimension 编辑项：

- label
- enabled
- weight
- description
- scoring_method
- logic_json
- sort_order

保存行为：

- 点击保存
- 调 `POST /versions`
- 成功后跳转到新版本详情页

### 9.4 历史版本页

第一阶段不要求做成完整独立页面，可以先做：

- 详情页中的历史版本区块
或
- 独立轻量列表页

优先目标是“能查看版本链”，不是把版本管理做满。

---

## 10. 与现有实现的共存关系

本阶段不删除以下现有实现：

- `src/admin/AdminApp.jsx`
- `src/admin/AdminMatchRules.jsx`

建议在现有 `AdminApp` 的“基础数据”区域新增试运行入口：

- `新规则管理台（试运行）`

点击跳转：

- `/admin-ra/match-rules`

这样做有三个好处：

1. 不影响当前使用者
2. 便于内部对比新旧页面
3. Claude 和 Codex 可分别基于不同入口联调

---

## 11. 分阶段实施计划

### Phase 1：基础接入

目标：先让 `react-admin` 跑起来

- 安装依赖
- 新建 `admin-ra/app/AdminRaApp.jsx`
- 新建 `authProvider.js`
- 新建 `dataProvider.js`
- 在 `App.jsx` 增加 `/admin-ra/*` 路由

### Phase 2：规则列表与详情

目标：能看规则，不改规则

- 实现 `match-rules/list.jsx`
- 实现 `match-rules/show.jsx`
- 跑通列表、详情、筛选

### Phase 3：规则编辑

目标：完成版本化保存

- 实现 `match-rules/edit.jsx`
- 对接 `/versions`
- 保存成功后跳转新版本详情页

### Phase 4：历史版本入口

目标：补齐版本链路

- 接 `/history`
- 详情页展示历史版本入口或历史列表

### Phase 5：试点评估

目标：决定是否继续扩展

评估维度：

- 开发速度是否提升
- 页面结构是否更清晰
- 后续扩展是否更顺
- 是否值得继续迁企业认证和 AI 配置

---

## 12. 风险与控制

### 风险 1：UI 风格与现有后台不一致

`react-admin` 基于 MUI，视觉风格会和现有手写后台不同。

控制方式：

- 第一阶段只作为试运行入口
- 不要求立即统一全部后台视觉

### 风险 2：默认 CRUD 模型与版本化编辑不匹配

控制方式：

- 明确在 `dataProvider.update()` 中做语义转换
- 不把后端强行改造成 PUT 更新

### 风险 3：引入依赖后复杂度上升

控制方式：

- 只引入 `react-admin + MUI` 的必要依赖
- 不一开始叠加更多生态包

### 风险 4：试点收益不足

控制方式：

- 第一阶段只迁一个资源
- 如果收益不明显，可停止扩展，不影响现有后台

---

## 13. 成功标准

完成本方案后，满足以下标准可视为试点成功：

1. `/admin-ra/match-rules` 可正常访问
2. 可查看规则列表
3. 可查看规则详情
4. 可编辑并保存为新版本
5. 保存后能跳转到新版本详情页
6. 不影响现有 `/admin` 页面功能
7. 前后端联调成本低于继续纯手写页面扩展

---

## 14. 最终建议

本项目**不适合**做“全站迁移到 react-admin”。
本项目**适合**做“管理后台资源层最小试点迁移”。

最推荐的落地方式是：

1. 新增 `/admin-ra` 试运行入口
2. 首批只迁 `人岗匹配规则管理`
3. 保留现有后台并行运行
4. 试点成功后再决定是否继续迁企业认证、AI 配置等资源页

这条路径的优点是：

- 风险小
- 回退容易
- 不打断现有开发
- 能真实验证 react-admin 是否适合你们的后台演进方向

---

## 15. 后续建议

如果确认按本方案推进，下一步建议补两份文档：

1. `React-Admin 接入实施计划`
   - 精确到文件路径、依赖、路由、provider、资源页拆分

2. `R-P3-06 规则管理台交互与字段映射说明`
   - 把规则列表、详情、编辑页的字段和接口映射说清楚

这样 Claude 就可以直接基于文档继续实现，而不需要重新整理上下文。
