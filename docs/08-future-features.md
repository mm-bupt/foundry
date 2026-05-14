# 08 — 后续功能规划

> TUI 已对齐 opencode 架构（context providers、dialog 系统、主题系统、leader key 等），以下功能需后端 API 支持后逐步实现。

---

## 高优先级

### SSE 事件流（实时数据同步）

- **现状**: 仅 WebSocket 单通道
- **所需 API**: `GET /api/events` SSE 端点，推送 session/message/part CRUD 事件
- **影响**: `context/sync.tsx` 数据同步、多客户端实时更新
- **参考**: opencode `context/sdk.tsx` + `context/sync.tsx`

### Prompt 自动补全（Slash Command）

- **现状**: `component/dialog-command.tsx` 已有命令注册框架，但无实时补全 UI
- **所需**: 前端 autocomplete 组件（输入 `/` 时弹出候选列表）
- **参考**: opencode `component/prompt/autocomplete.tsx`

---

## 中优先级

### 多 Agent 支持

- **所需 API**: Agent 列表 / 切换 / 配置 API
- **影响**: `context/local.tsx` agent 管理、Header 显示、Prompt 元数据
- **参考**: opencode `context/local.tsx` agent color/cycle

### Plugin 系统

- **所需 API**: 插件发现 / 加载 / 生命周期管理
- **影响**: 所有路由和组件的 Slot 注入点（`home_logo`, `sidebar_content`, `session_prompt` 等）
- **参考**: opencode `plugin/` 目录

### LSP 集成

- **所需 API**: LSP 服务端（诊断、补全、跳转）
- **影响**: Footer LSP 状态显示、Session 内联诊断
- **参考**: opencode `routes/session/footer.tsx` LSP 计数、`feature-plugins/sidebar/lsp.tsx`

### MCP（Model Context Protocol）集成

- **所需 API**: MCP 服务端管理（连接、工具发现）
- **影响**: Footer MCP 状态、Sidebar MCP 面板
- **参考**: opencode `feature-plugins/sidebar/mcp.tsx`、`component/dialog-mcp.tsx`

### Provider 连接管理

- **所需 API**: Provider 配置 / 连接状态 API
- **影响**: 模型选择对话框的 Provider 分组显示、未连接提示
- **参考**: opencode `component/dialog-provider.tsx`、`component/dialog-model.tsx` `useConnected()`

### Permission / Question 提示

- **所需 API**: 权限请求 / 确认提示 WebSocket 事件类型
- **影响**: `routes/session/permission.tsx`、`routes/session/question.tsx` 内联弹窗
- **参考**: opencode `routes/session/permission.tsx`、`question.tsx`

### Diff 查看（文件变更）

- **所需 API**: 文件读写 / 编辑 API、diff 生成
- **影响**: Sidebar 文件 diff 面板、Session 内联 diff 渲染
- **参考**: opencode `feature-plugins/sidebar/files.tsx`、Session 内 Edit/Write tool 渲染

### Prompt 历史持久化

- **所需**: 本地 KV 存储（类似 opencode 的 `kv.json`）
- **影响**: Prompt 上下导航、stash/pop 功能
- **参考**: opencode `component/prompt/history.tsx`、`stash.tsx`

---

## 低优先级

### VCS（版本控制）集成

- **所需 API**: Git 操作 API（status、diff、branch）
- **影响**: Footer VCS 状态
- **参考**: opencode `context/sync.tsx` vcs 字段

### 会话分享

- **所需 API**: 分享 URL 生成端点
- **影响**: Sidebar 分享链接显示
- **参考**: opencode `routes/session/sidebar.tsx` shareURL

### 会话 Fork

- **所需 API**: `POST /api/sessions/{id}/fork`
- **影响**: Session timeline 对话框、fork 操作
- **参考**: opencode `routes/session/dialog-fork-from-timeline.tsx`

### 会话导出

- **所需 API**: 导出端点（Markdown / JSON）
- **影响**: 命令面板 export 命令
- **参考**: opencode `ui/dialog-export-options.tsx`

### 会话时间线

- **所需 API**: 消息历史版本 API
- **影响**: Timeline 对话框、undo/redo
- **参考**: opencode `routes/session/dialog-timeline.tsx`

### Todo 管理

- **所需 API**: Todo CRUD + WebSocket 事件
- **影响**: Sidebar Todo 面板
- **参考**: opencode `feature-plugins/sidebar/todo.tsx`、`component/todo-item.tsx`

### 多工作区

- **所需 API**: Workspace 管理 API
- **影响**: Session 列表工作区标签、工作区切换
- **参考**: opencode `component/dialog-workspace-create.tsx`

---

## 实现建议

1. **SSE 优先**: 这是 `context/sync.tsx` 完整运作的基础，完成后 TUI 即可实时响应所有后端变更
2. **前端先行**: 主题系统、dialog 系统、键绑定等纯前端功能已就绪，可直接完善细节
3. **渐进式接入**: 每个 API 就绪后，对应 TUI 功能只需少量代码即可启用（架构已预留）
