# 基础数据新增与编辑抽屉实现计划

> **面向 AI 代理的工作者：** 使用 `superpowers:executing-plans` 在当前会话内逐任务执行。步骤使用复选框跟踪进度。

**目标：** 将标准职位库和标签库的内嵌新增、编辑表单改为右侧抽屉，并保持详情页、状态切换和列表刷新行为兼容。

**架构：** `BaseData` 保留列表查询、快捷状态切换和抽屉编排。新建 `AdminBaseDataDrawers.jsx`，集中实现抽屉壳、标准职位表单、标签表单、详情加载、校验和保存。浏览器回归验证新增、编辑、父级约束和详情页兼容。

**技术栈：** React 18、React Router、现有 services API、Vitest、Playwright、Vite、ESLint。

---

## 文件结构

- 新建：`frontend/wechat-prototype/src/admin/AdminBaseDataDrawers.jsx`，负责共享抽屉、两类表单、payload 转换和保存。
- 新建：`frontend/wechat-prototype/src/admin/AdminBaseDataDrawers.test.js`，覆盖 payload、校验和父级过滤。
- 修改：`frontend/wechat-prototype/src/admin/AdminApp.jsx`，移除内嵌表单，增加新增按钮和抽屉状态。
- 修改：`frontend/wechat-prototype/src/styles/admin.css`，增加遮罩、抽屉、表单和窄屏样式。
- 修改：`frontend/wechat-prototype/output/playwright/manual-base-data-detail-flow.cjs`，覆盖抽屉新增、编辑和详情页回归。
- 更新：`goal-005/tasks.md`、`goal-005/changelog.md`，记录 T007-P2 证据。

### 任务 1：建立失败的单元与浏览器回归

- [ ] 修改 `manual-base-data-detail-flow.cjs`：断言列表页不存在旧内嵌输入框，点击「新增标准职位」后出现抽屉。
- [ ] 新建 `AdminBaseDataDrawers.test.js`：断言标准职位别名转换、标签数字字段转换、必填校验和父级排除自身。
- [ ] 运行 `npm.cmd test -- AdminBaseDataDrawers.test.js`，预期因模块不存在而失败。
- [ ] 运行基础数据浏览器脚本，预期因新增按钮或抽屉不存在而失败。

### 任务 2：实现共享抽屉与表单

- [ ] 新建 `AdminBaseDataDrawers.jsx`，导出 `StandardPositionDrawer`、`TagLibraryDrawer`、`buildStandardPositionPayload`、`buildTagPayload` 和 `filterTagParentOptions`。
- [ ] 抽屉支持遮罩、关闭按钮、`Esc`、固定底部、保存中状态和错误展示。
- [ ] 编辑模式通过 `getStandardPosition(id)` 或 `getTagLibraryItem(id)` 加载最新详情。
- [ ] 保存分别调用 create/update API；成功回调 `onSaved`，失败保留表单。
- [ ] 实现脏数据关闭确认，保存成功关闭时跳过确认。
- [ ] 运行 `npm.cmd test -- AdminBaseDataDrawers.test.js`，预期通过。

### 任务 3：将列表页切换到抽屉编排

- [ ] 修改 `AdminApp.jsx`：移除标准职位和标签的表单 state、reset/edit/save 函数及内嵌 JSX。
- [ ] 增加 `positionDrawer`、`tagDrawer` 状态，右上角新增按钮打开 create 模式。
- [ ] 行内「编辑」打开 edit 模式并传入 ID。
- [ ] 保存成功后关闭抽屉、显示 toast 并调用对应列表刷新。
- [ ] 保留「查看详情」和「启用 / 停用」行为。
- [ ] 修改 `admin.css`：桌面宽 560 px，小于 768 px 时全屏。

### 任务 4：完成真实浏览器流程

- [ ] 扩展 `manual-base-data-detail-flow.cjs`：通过抽屉新增标准职位。
- [ ] 通过编辑抽屉修改标准职位说明并验证列表或详情。
- [ ] 通过抽屉新增带父级标签，并验证父级显示。
- [ ] 编辑标签时验证自身不在父级选项中。
- [ ] 修改字段后关闭，验证脏数据确认；取消确认后抽屉保持打开。
- [ ] 再次验证标准职位详情、标签列表和标签详情。
- [ ] 运行脚本，预期输出 `{"ok":true,...}`。

### 任务 5：全量验证、账本和提交

- [ ] 运行 `npm.cmd run lint`，预期 0 errors。
- [ ] 运行 `npm.cmd test`，预期全部通过。
- [ ] 运行 `npm.cmd run build`，预期 exit 0。
- [ ] 运行 `git diff --check`，预期 exit 0。
- [ ] 更新 Goal 账本，记录测试、浏览器和构建证据。
- [ ] 仅暂存产品代码、测试、设计和计划文件，排除生成截图与 manifest。
- [ ] 提交 `feat: move base data editing into drawers`。
- [ ] 推送 PR #9 并确认 Backend、Frontend Actions 全绿。
