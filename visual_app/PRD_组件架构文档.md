# DbcTool 前端组件架构文档 (PRD)

> 版本: 2.0  
> 日期: 2026-06-08  
> 状态: 已实施  

---

## 1. 概述

本文档描述了 DbcTool Web 前端应用的组件化架构。将原有的单文件 `index.html` (1085 行) 拆分为模块化的组件结构，提升代码可维护性、可测试性和可扩展性。

### 1.1 架构目标

- **高内聚低耦合**: 每个组件封装完整的功能、样式和交互逻辑
- **清晰的通信机制**: 通过全局命名空间 `DbcTool` 实现组件间通信
- **可测试性**: 每个组件可独立进行单元测试
- **性能优化**: 外部 CSS/JS 可被浏览器缓存，减少重复加载

### 1.2 文件结构

```
visual_app/
├── static/
│   ├── css/
│   │   └── style.css          # 全局样式（从 index.html 内联提取）
│   └── js/
│       ├── utils.js            # 通用工具函数
│       ├── convert.js          # 文件转换组件
│       ├── compare.js          # DBC比较组件
│       └── app.js              # 应用入口 & 初始化
├── templates/
│   └── index.html              # 精简后的 HTML 模板（~158 行）
└── app.py                      # Flask 后端（新增 static 目录配置）
```

---

## 2. 组件详细说明

### 2.1 全局命名空间: `DbcTool`

所有组件挂载在全局命名空间 `DbcTool` 下，避免全局变量污染。

```
DbcTool
├── escapeHtml()          # HTML 转义
├── getExt()              # 获取文件扩展名
├── fmtFromExt()          # 扩展名 → 格式映射
├── findFmtKey()          # 在格式列表中查找匹配
├── clearAllMsgs()        # 清除所有消息
├── msg()                 # 显示消息
├── toggleAdv()           # 切换高级选项展开/折叠
├── setupUpload()         # 配置文件上传区域
├── formatFileSize()      # 格式化文件大小
├── ICONS                 # 节点类型图标映射
├── Convert               # 文件转换组件
├── Compare               # DBC比较组件
└── App                   # 应用入口
```

---

### 2.2 文件: `utils.js` — 通用工具模块

**职责**: 提供跨组件共享的纯函数和常量。

**导出接口**:

| 方法/属性 | 类型 | 参数 | 返回值 | 说明 |
|-----------|------|------|--------|------|
| `escapeHtml(s)` | Function | `s: string` | `string` | HTML 特殊字符转义 |
| `getExt(name)` | Function | `name: string` | `string` | 从文件名提取扩展名 |
| `fmtFromExt(ext)` | Function | `ext: string` | `string` | 扩展名到格式 key 的映射 |
| `findFmtKey(ext, fmtMap)` | Function | `ext: string, fmtMap: Array` | `string` | 在格式列表中查找匹配的 key |
| `clearAllMsgs()` | Function | — | — | 清除页面上所有消息提示 |
| `msg(t, x)` | Function | `t: 'err'\|'ok'\|'inf', x: string` | — | 显示消息提示（8秒自动消失） |
| `toggleAdv(hdrId, bodyId)` | Function | `hdrId: string, bodyId: string` | — | 切换高级选项面板展开/折叠 |
| `setupUpload(zoneId, inpId, handler)` | Function | `zoneId: string, inpId: string, handler: Function` | — | 配置文件上传拖拽区域 |
| `formatFileSize(size)` | Function | `size: number` | `string` | 格式化文件大小为可读字符串 |
| `ICONS` | Object | — | `Object` | 节点类型到 Emoji 图标的映射 |

**依赖**: 无外部依赖。

**使用示例**:
```javascript
var safe = DbcTool.escapeHtml('<script>alert("xss")</script>');
var ext = DbcTool.getExt('example.dbc'); // 'dbc'
DbcTool.msg('err', '文件上传失败');
```

---

### 2.3 文件: `convert.js` — 文件转换组件

**职责**: 管理文件格式转换的完整流程，包括文件上传、格式选择、选项配置、API 调用和结果展示。

**命名空间**: `DbcTool.Convert`

**导出接口**:

| 方法 | 参数 | 说明 |
|------|------|------|
| `init(fmtMap)` | `fmtMap: Array` | 初始化组件，接收格式映射列表 |
| `fileInCvt(file)` | `file: File` | 处理文件上传，自动识别格式 |
| `updBtnCvt()` | — | 更新转换按钮状态 |
| `doConvert()` | — | 执行格式转换（异步） |
| `hideResCvt()` | — | 隐藏转换结果区域 |

**内部状态**:
- `cvFile`: 当前上传的文件对象
- `fmtMap`: 支持的格式列表

**交互流程**:
1. 用户拖拽/选择文件 → `fileInCvt()` 自动识别格式并设置默认输出格式
2. 用户选择输出格式 → `updBtnCvt()` 启用转换按钮
3. 用户点击"开始转换" → `doConvert()` 收集所有参数，调用 `/api/convert`
4. 转换完成 → `showResCvt()` 展示统计信息和下载链接

**DOM 依赖**:
- `#zoneCvt` / `#fileInpCvt` / `#fnameCvt` — 文件上传区
- `#inFmtCvt` / `#outFmtCvt` — 格式选择器
- `#autoBadge` / `#fmtHint` — 自动识别提示
- `#cO0` ~ `#cO3` — 基本转换选项
- `#cDlc` / `#cAr` / `#cEncI` / `#cEncO` / `#cMot` — 高级选项
- `#cUniq` / `#cCanard` / `#cMojibake` — 额外选项
- `#cFAttr` / `#cSAttr` — 额外属性
- `#btnGoCvt` — 转换按钮
- `#resCardCvt` / `#statsGridCvt` / `#btnDlCvt` — 结果展示

**依赖**: `DbcTool.escapeHtml`, `DbcTool.getExt`, `DbcTool.findFmtKey`, `DbcTool.formatFileSize`, `DbcTool.msg`

---

### 2.4 文件: `compare.js` — DBC比较组件

**职责**: 管理 DBC 文件比较的完整流程，包括双文件上传、维度设置、API 调用、树形结果渲染、悬浮提示、同步滚动和分栏拖拽。

**命名空间**: `DbcTool.Compare`

**导出接口**:

| 方法 | 参数 | 说明 |
|------|------|------|
| `init()` | — | 初始化组件（创建 tooltip DOM） |
| `fileInCmp1(file)` | `file: File` | 处理基准文件上传 |
| `fileInCmp2(file)` | `file: File` | 处理对比文件上传 |
| `updBtnCmp()` | — | 更新比较按钮状态 |
| `doCompare()` | — | 执行 DBC 比较（异步） |
| `hideResCmp()` | — | 隐藏比较结果区域 |
| `toggleDiffOnly()` | — | 切换"只显示差异"过滤模式 |
| `toggleTreeNode(rowEl)` | `rowEl: Element` | 切换树节点展开/折叠 |

**内部状态**:
- `cmpFile1` / `cmpFile2`: 上传的两个文件
- `diffMap`: 差异映射数据
- `diffOnlyActive`: "只显示差异"开关状态
- `tooltipEl` / `tooltipTimer`: Tooltip DOM 和定时器

**交互流程**:
1. 用户上传两个文件 → `fileInCmp1()` / `fileInCmp2()` 更新 UI
2. 用户设置比较维度 → 勾选/取消勾选复选框
3. 用户点击"开始比较" → `doCompare()` 调用 `/api/compare`
4. 比较完成 → `showResCmp()` 渲染左右分栏树形结构
5. 用户可拖拽分栏分隔线调整宽度比例
6. 用户可拖拽同步滚动条同步两侧滚动
7. 用户可点击"只显示差异"过滤显示
8. 鼠标悬停 CHANGED 节点 → 显示详细变更 Tooltip

**子功能模块**:

| 内部函数 | 说明 |
|----------|------|
| `renderSideTree()` | 渲染单侧树形结构 |
| `renderTreeNode()` | 递归渲染树节点 |
| `updateSideStats()` | 更新两侧统计栏 |
| `initDivider()` | 初始化分栏拖拽分隔线 |
| `initSyncScrollbar()` | 初始化同步滚动条 |
| `initTooltip()` | 初始化 Tooltip DOM |
| `attachTooltipListeners()` | 绑定 Tooltip 事件 |
| `onTooltipOver/Out/Enter/Leave/Click()` | Tooltip 交互处理 |

**DOM 依赖**:
- `#zoneCmp1` / `#zoneCmp2` / `#fileInpCmp1` / `#fileInpCmp2` / `#fnameCmp1` / `#fnameCmp2` — 双文件上传区
- `#pComments` / `#pAttrs` / `#pValTabs` / `#pDefs` — 比较维度设置
- `#btnGoCmp` — 比较按钮
- `#resCardCmp` / `#statsGridCmp` / `#diffSummary` — 结果展示
- `#cmpSplit` / `#cmpPanelLeft` / `#cmpPanelRight` / `#cmpDivider` — 分栏布局
- `#cmpBodyLeft` / `#cmpBodyRight` — 树形内容区
- `#cmpStatsLeft` / `#cmpStatsRight` — 统计栏
- `#cmpSyncScrollbar` / `#cmpSyncThumb` — 同步滚动条
- `#btnDiffOnly` — 差异过滤按钮
- `#pNameLeft` / `#pNameRight` — 文件名显示

**依赖**: `DbcTool.escapeHtml`, `DbcTool.ICONS`, `DbcTool.formatFileSize`, `DbcTool.msg`

---

### 2.5 文件: `app.js` — 应用入口

**职责**: 应用初始化、模块切换、全局事件绑定。

**命名空间**: `DbcTool.App`

**导出接口**:

| 方法 | 参数 | 说明 |
|------|------|------|
| `init()` | — | 初始化应用（获取格式列表、绑定上传、设置全局函数） |
| `switchModule(name)` | `name: 'convert'\|'compare'` | 切换功能模块 |

**初始化流程**:
1. 调用 `/api/formats` 获取支持的格式列表
2. 填充输入/输出格式下拉框
3. 初始化 `DbcTool.Convert` 和 `DbcTool.Compare` 组件
4. 配置文件上传区域
5. 绑定输出格式选择器的 change 事件
6. 将核心函数挂载到 `window` 全局作用域（供 HTML onclick 调用）

**依赖**: `DbcTool.Convert`, `DbcTool.Compare`, `DbcTool.setupUpload`, `DbcTool.clearAllMsgs`

---

## 3. 组件间通信机制

### 3.1 通信架构

```
┌─────────────────────────────────────────────┐
│                  DbcTool (全局命名空间)        │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  utils   │  │ Convert  │  │ Compare  │  │
│  │  (纯函数)  │  │ (组件)   │  │ (组件)   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │        │
│       └──────────────┼──────────────┘        │
│                      │                       │
│               ┌──────┴──────┐               │
│               │     App     │               │
│               │  (入口/调度)  │               │
│               └─────────────┘               │
└─────────────────────────────────────────────┘
```

### 3.2 通信方式

1. **命名空间引用**: 组件通过 `DbcTool.xxx` 访问其他组件的公开方法
2. **函数参数传递**: `App.init()` 将格式数据通过 `Convert.init(fmtMap)` 传递给转换组件
3. **全局函数挂载**: `App.init()` 将核心函数挂载到 `window` 供 HTML onclick 调用
4. **DOM 事件**: 组件通过 `addEventListener` 绑定 DOM 事件
5. **无直接耦合**: Convert 和 Compare 组件之间无直接依赖

---

## 4. 样式管理

### 4.1 CSS 文件: `style.css`

所有样式从 `index.html` 内联 `<style>` 标签提取到独立的 `style.css` 文件。

**优势**:
- 浏览器可缓存 CSS 文件，减少重复传输
- HTML 文件体积从 1085 行缩减至 158 行
- 样式修改不影响 HTML 结构

**CSS 变量体系**:
```css
:root {
    --bg: #0f172a;        /* 页面背景 */
    --surface: #1e293b;   /* 卡片背景 */
    --surface2: #334155;  /* 次要背景 */
    --border: #475569;    /* 边框颜色 */
    --text: #e2e8f0;      /* 主文字 */
    --text2: #94a3b8;     /* 次要文字 */
    --accent: #38bdf8;    /* 强调色（蓝） */
    --accent2: #818cf8;   /* 强调色（紫） */
    --green: #4ade80;     /* 成功色 */
    --red: #f87171;       /* 错误色 */
    --yellow: #fbbf24;    /* 警告色 */
    --orange: #fb923c;    /* 橙色 */
    --radius: 12px;       /* 圆角 */
}
```

---

## 5. 性能优化

### 5.1 优化措施

| 措施 | 说明 |
|------|------|
| CSS 外部化 | 浏览器缓存 style.css，后续访问无需重复下载 |
| JS 模块化 | 按需加载，utils.js 可被所有组件共享 |
| HTML 精简 | 移除内联样式和脚本，减少 HTML 体积约 85% |
| 无额外依赖 | 不引入任何第三方库，保持零依赖 |
| 事件委托 | Tooltip 使用事件委托减少监听器数量 |

### 5.2 加载顺序

```
1. style.css        (渲染阻塞，需优先加载)
2. utils.js         (基础工具，其他模块依赖)
3. convert.js       (转换组件)
4. compare.js       (比较组件)
5. app.js           (入口，初始化所有组件)
```

---

## 6. 测试指南

### 6.1 测试文件: `tests/test_components.html`

在 `visual_app/tests/` 目录下提供了组件单元测试页面，可通过浏览器直接打开运行。

### 6.2 测试覆盖

| 测试项 | 覆盖内容 |
|--------|----------|
| `DbcTool.escapeHtml()` | HTML 特殊字符转义正确性 |
| `DbcTool.getExt()` | 各种文件名的扩展名提取 |
| `DbcTool.fmtFromExt()` | 扩展名到格式的映射 |
| `DbcTool.formatFileSize()` | 文件大小格式化 |
| `DbcTool.findFmtKey()` | 格式列表查找 |
| `DbcTool.ICONS` | 图标映射完整性 |
| `DbcTool.Convert` 接口 | 所有公开方法存在性 |
| `DbcTool.Compare` 接口 | 所有公开方法存在性 |
| `DbcTool.App` 接口 | 所有公开方法存在性 |

---

## 7. 向后兼容

### 7.1 保留的全局函数

为保持与原有 HTML onclick 属性的兼容，以下函数挂载到 `window`:

| 全局函数 | 实际调用 |
|----------|----------|
| `switchModule(name)` | `DbcTool.App.switchModule(name)` |
| `doConvert()` | `DbcTool.Convert.doConvert()` |
| `doCompare()` | `DbcTool.Compare.doCompare()` |
| `toggleAdv(hdrId, bodyId)` | `DbcTool.toggleAdv(hdrId, bodyId)` |
| `toggleDiffOnly()` | `DbcTool.Compare.toggleDiffOnly()` |

### 7.2 历史版本

原有 `index.html` 的历史版本保留在 `templates/` 目录下:
- `indexV0.html` — 原始版本
- `indexV1外观大修改.html` — 外观大修改版
- `indexV2修改对比框悬浮窗位置.html` — 对比框悬浮窗位置调整版

---

## 8. 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 2.0 | 2026-06-08 | 初始组件化拆分：提取 CSS 到 style.css，JS 拆分为 utils/convert/compare/app 四个模块 |
