# Bug 修复日志

> 项目: canmatrix DBC ↔ Excel 双向转换

---

## Bug #6: Excel 转 DBC 时，无 CAN FD 帧情况下报 KeyError: 'VFrameFormat'

**严重程度**: 高 | **状态**: ✅ 已修复 | **日期**: 2026-06-22

### 问题描述

Excel 转 DBC 时，间歇性报错 `KeyError: 'VFrameFormat'`。当 Excel 中包含 CAN FD 帧时转换正常，不包含时失败。

### 触发条件

| 场景 | 是否报错 | 原因 |
|------|:-------:|------|
| Excel **包含**至少一个 CAN FD 帧（`ID-Format` 含 `_FD` 或 DLC > 8） | ❌ 不报错 | `dbc.py` 导出时 `contains_fd = True`，注册了 `VFrameFormat` 属性定义，写入正常 |
| Excel **不包含**任何 CAN FD 帧 | ✅ 报错 | `contains_fd = False`，`dbc.py` 不会注册 `VFrameFormat` 属性定义，但 Excel 导入时已给每个帧添加了 `VFrameFormat` 属性，写入 DBC 时直接访问 `db.frame_defines["VFrameFormat"]` → KeyError |

### 根因

`dbc.py` 写入帧属性时（L406），无条件访问 `db.frame_defines[attrib]`，未检查属性是否已注册。而信号属性写入处（L416）已有 `if attrib in db.signal_defines` 保护。

```python
# 帧属性写入（修复前）—— 缺少保护
for frame in db.frames:
    for attrib, val in sorted(frame.attributes.items()):
        f.write(create_attribute_string(attrib, "BO_", ..., val,
            db.frame_defines[attrib].type == "STRING"))  # ← KeyError

# 信号属性写入 —— 已有保护
for frame in db.frames:
    for signal in frame.signals:
        for attrib, val in sorted(signal.attributes.items()):
            if attrib in db.signal_defines:  # ← 有保护
                f.write(...)
```

### 修复内容

| 文件 | 修改 |
|------|------|
| [dbc.py](src/canmatrix/formats/dbc.py#L405-L407) | 帧属性写入处新增 `if attrib in db.frame_defines` 保护，跳过未注册的属性，与信号属性写入逻辑保持一致 |

### 验证

| 测试文件 | 修复前 | 修复后 |
|----------|--------|--------|
| `test_20260622_144647.xlsx`（2 帧，0 FD） | `KeyError: 'VFrameFormat'` | 转换成功，输出大小 1305 字节 |

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

| 文件 | Bug #1 | Bug #2 | Bug #3 | Bug #4 | Bug #5 | Bug #6 | 分类更新 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `src/canmatrix/formats/xls_common.py` | ✅ | | | | | | ✅ |
| `src/canmatrix/formats/xls.py` | ✅ | | ✅ | ✅ | ✅ | | ✅ |
| `src/canmatrix/formats/xlsx.py` | ✅ | | ✅ | | ✅ | | ✅ |
| `src/canmatrix/formats/dbc.py` | | ✅ | | | | ✅ | |
| `visual_app/PRD_DBC_Excel_字段映射规范.md` | ✅ | | | ✅ | ✅ | | ✅ |
| `tests/files/dbc/test_frame_attributes.dbc` | ✅ | | | | | | |
| `tests/test_frame_attr_roundtrip.py` | ✅ | | | | | | |

---

## 测试覆盖

| 测试套件 | 用例数 | 通过 | 失败 |
|----------|:-----:|:---:|:---:|
| `test_frame_attr_roundtrip.py` | 4 | 4 | 0 |
| `test_xls.py` | 1 | 1 | 0 |
| `test_dbc.py` | 65 | 64 | 1 (预存: kcd) |
| `test_cli_convert.py` | — | 全部 | 0 |
| `test_formats.py` | — | 全部 | 0 |
| Bug #6 手动验证 | 1 | 1 | 0 |