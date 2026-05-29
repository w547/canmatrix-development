# Bug 修复日志

> 项目: canmatrix DBC ↔ Excel 双向转换 | 日期: 2026-05-20

---

## Bug #1: DBC 转 Excel 时报文全局 attributes 丢失

**严重程度**: 高 | **状态**: ✅ 已修复

### 问题描述

DBC 文件中的报文级别（`BA_ BO_`）自定义属性在转换为 Excel 时，以下属性完全丢失：

| 属性 | 分类 |
|------|------|
| `DiagRequest` | Diagnostics |
| `DiagResponse` | Diagnostics |
| `DiagState` | Diagnostics |
| `NmMessage` | Net Management |
| `GenMsgILSupport` | Interaction Layer |
| `GenMsgCycleTimeFast` | Interaction Layer |
| `GenMsgNoOfRepetitions` | Interaction Layer |
| `CANFD_BRS` | — |

Excel 导出时仅保留了 `GenMsgSendType`（Launch Type 列）和 `GenMsgDelayTime`（Launch Parameter 列），其余帧属性无对应列。

### 根因

1. `xls_common.py` 的 `get_frame_info()` 函数仅输出 `GenMsgSendType` 和 `GenMsgDelayTime`
2. `head_top` 列定义中缺少对应列头
3. 导入侧无对应的列检测和属性读写逻辑

### 修复内容

| 文件 | 修改 |
|------|------|
| [xls_common.py](src/canmatrix/formats/xls_common.py) | `get_frame_info()` 新增 8 个属性输出，`GenMsgDelayTime` 与 `GenMsgSendType` 解耦为独立列 |
| [xls.py](src/canmatrix/formats/xls.py) | `head_top` 新增 8 列；`load()` 新增列检测、属性读取、defines 注册 |
| [xlsx.py](src/canmatrix/formats/xlsx.py) | 同 xls.py |

### 验证

- `test_frame_attr_roundtrip.py` 4 项测试全部通过
- DBC → XLS/XLSX → DBC 双向转换逐属性比对一致

---

## Bug #2: DBC 导入时 STRING 类型属性无条件引号剥离导致值损坏

**严重程度**: 中 | **状态**: ✅ 已修复

### 问题描述

`dbc.py` 的 `load()` 函数在导入完成后对 STRING 类型的属性值**无条件**执行 `[1:-1]` 切片操作，假设所有值都带外层双引号。当值不加引号时（如 `BA_ "DiagRequest" BO_ 256 1;`），会导致数据损坏：

| 原始值 | `[1:-1]` 后 | 结果 |
|--------|------------|------|
| `1` | `""` 空字符串 | **数据丢失** |
| `"DiagState_Default"` | `DiagState_Default` | 正常 |

### 根因

[dbc.py#L1005-L1024](src/canmatrix/formats/dbc.py#L1005-L1024) 中 global/ECU/frame/signal 四个层级均使用 `val[1:-1]` 无条件剥离。

### 修复内容

改为仅当值以 `"` 开头且以 `"` 结尾时才剥离：

```python
if val.startswith('"') and val.endswith('"'):
    val = val[1:-1]
```

影响范围：[dbc.py](src/canmatrix/formats/dbc.py) — global / ECU / frame / signal 四个层级的 `BA_` 后处理代码。

---

## Bug #3: Excel 导入时 GenMsgDelayTime 未存储

**严重程度**: 中 | **状态**: ✅ 已修复

### 问题描述

`xls.py` 和 `xlsx.py` 的 `load()` 函数从 "Launch Parameter" 列读取了 `launch_param` 值，但**从未调用 `add_attribute("GenMsgDelayTime", ...)` 将其存回帧属性**。导致 Excel 转 DBC 后 `GenMsgDelayTime` 丢失。

### 修复内容

在 `xls.py` 和 `xlsx.py` 的帧处理后加入：

```python
if launch_param is not None and str(launch_param).strip() != '':
    new_frame.add_attribute("GenMsgDelayTime", str(launch_param).strip())
```

---

## Bug #4: 列标题检测 `"Cycle"` 过于宽泛

**严重程度**: 中 | **状态**: ✅ 已修复

### 问题描述

`xls.py` `load()` 中列标题检测使用 `"Cycle" in value` 匹配 `"Cycle Time [ms]"` 列。但新增的 `"GenMsgCycleTimeFast"` 列头也包含 `"Cycle"`，导致 `index['cycle']` 被错误覆盖为后者的列索引，从而 "Cycle Time [ms]" 列读取失败。

### 修复内容

将 `"Cycle" in value` 改为 `"Cycle Time" in value`，精确匹配 `"Cycle Time [ms]"` 列，避免误匹配 `"GenMsgCycleTimeFast"`。

---

## Bug #5: Frame 信息列白色字体导致视觉不可见

**严重程度**: 低 | **状态**: ✅ 已修复

### 问题描述

Excel 导出时，同一 Frame 的第 2 个信号行开始，Frame 信息列（ID、Frame Name、DLC、comment、Cycle Time、Launch Type 及所有新增属性列）以白色字体（`sty_white` / `color='00ffffff'`）写入，在白色背景上视觉不可见。

### 根因

原设计用于模拟"合并单元格"效果——每个信号行结束后 `frame_style = sty_white`，导致下一行 Frame 信息以白色字体写入。

### 修复内容

将 `xls.py` 和 `xlsx.py` 共 4 处的 `frame_style = sty_white` 改为 `frame_style = sty_norm`，Frame 信息列与 Signal 列字体统一为黑色。

---

## 技术项分类更新: GenMsgCycleTimeActive / GenMsgNoOfRepetitions → Interaction Layer

**严重程度**: 信息 | **状态**: ✅ 已完成

### 变更内容

| 属性 | 原分类 | 新分类 |
|------|--------|--------|
| `GenMsgCycleTimeActive` | 帧属性 | Interaction Layer |
| `GenMsgNoOfRepetitions` / `GenMsgNrOfRepetitions` | 帧属性 | Interaction Layer |
| `GenMsgDelayTime` | 帧属性 | Interaction Layer |

### 影响文件

- [xls_common.py](src/canmatrix/formats/xls_common.py) — 导出函数注释新增分类标注
- [xls.py](src/canmatrix/formats/xls.py) — defines 注册区和导入侧属性读取区新增分类注释
- [xlsx.py](src/canmatrix/formats/xlsx.py) — 同上
- [PRD_DBC_Excel_字段映射规范.md](visual_app/PRD_DBC_Excel_字段映射规范.md) — 分类表更新 + 新增分类说明

---

## 修改文件汇总

| 文件 | Bug #1 | Bug #2 | Bug #3 | Bug #4 | Bug #5 | 分类更新 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| `src/canmatrix/formats/xls_common.py` | ✅ | | | | | ✅ |
| `src/canmatrix/formats/xls.py` | ✅ | | ✅ | ✅ | ✅ | ✅ |
| `src/canmatrix/formats/xlsx.py` | ✅ | | ✅ | | ✅ | ✅ |
| `src/canmatrix/formats/dbc.py` | | ✅ | | | | |
| `visual_app/PRD_DBC_Excel_字段映射规范.md` | ✅ | | | ✅ | ✅ | ✅ |
| `tests/files/dbc/test_frame_attributes.dbc` | ✅ | | | | | |
| `tests/test_frame_attr_roundtrip.py` | ✅ | | | | | |

---

## 测试覆盖

| 测试套件 | 用例数 | 通过 | 失败 |
|----------|:-----:|:---:|:---:|
| `test_frame_attr_roundtrip.py` | 4 | 4 | 0 |
| `test_xls.py` | 1 | 1 | 0 |
| `test_dbc.py` | 65 | 64 | 1 (预存: kcd) |
| `test_cli_convert.py` | — | 全部 | 0 |
| `test_formats.py` | — | 全部 | 0 |