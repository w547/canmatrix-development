# Changelog

## 2026-06-22 — 修复无 CAN FD 帧时 Excel 转 DBC 报 VFrameFormat KeyError

### 问题描述

Excel 转 DBC 时，有时候报错 `KeyError: 'VFrameFormat'`，有时候转换正常。**原因**：Excel 中没有 CAN FD 帧时触发，有 CAN FD 帧时不触发。

### 根因分析

| 场景 | 是否触发 | 原因 |
|------|:-------:|------|
| Excel **包含**至少一个 CAN FD 帧 | ❌ 不报错 | `dbc.py` 导出时因为 `contains_fd = True`，注册了 `VFrameFormat` 属性定义 → 写入正常 |
| Excel **不包含**任何 CAN FD 帧 | ✅ 报错 | `contains_fd = False` → `dbc.py` 不会注册 `VFrameFormat` 属性定义，但是 Excel 导入时已经给每个帧添加了 `VFrameFormat` 属性，写入 DBC 时遍历帧属性直接访问 `db.frame_defines[attrib]` → KeyError |

### 修复方案

| 文件 | 修改 |
|------|------|
| `src/canmatrix/formats/dbc.py` | 在写入帧属性处（L405-407）新增 `if attrib in db.frame_defines` 保护，跳过未注册的属性，和信号属性写入逻辑保持一致 |

### 验证

| 测试文件 | 修复前 | 修复后 |
|----------|--------|--------|
| `test_20260622_144647.xlsx`（2 帧，0 FD）| `KeyError: 'VFrameFormat'` | 转换成功，输出大小 1305 字节 |

## 2026-06-09 — 修复 CAN FD 帧类型在 DBC/Excel 互转中的丢失问题

### 问题描述
- DBC 与 Excel 互转时，DLC ≤ 8 字节的 CAN FD 帧被误判为 CAN 类型
- Excel 转 DBC 时，`VFrameFormat` 属性被错误统一设置为 `"can standard"`
- Excel 转 DBC 时，出现 `KeyError: 'VFrameFormat'` 报错

### 修改文件

#### `src/canmatrix/formats/dbc.py`
- **新增 VFrameFormat 属性同步逻辑**（L169-188）：导出 DBC 时，从帧的 `VFrameFormat` 属性中提取 `is_fd` / `is_j1939` 标志，并根据帧类型和扩展帧标志设置正确的 `VFrameFormat` 枚举值（`StandardCAN_FD` / `ExtendedCAN_FD` / `J1939PG` / `StandardCAN` / `ExtendedCAN`）
- **新增防御性属性检查**（L440-441）：写入帧属性时，跳过未在 `frame_defines` 中注册的属性，防止 `KeyError`

#### `src/canmatrix/formats/xlsx.py`
- **新增 `ID-Format` 列**（L134）：在 Excel 表头中新增 `ID-Format` 列，用于显式标识帧类型
- **新增 `ID-Format` 导入逻辑**（L517-523）：导入 Excel 时读取 `ID-Format` 列，若含 `_FD` 则设置 `is_fd = True`，并写入 `VFrameFormat` 属性

#### `src/canmatrix/formats/xls.py`
- **新增 `ID-Format` 列**（L112）：在 Excel 表头中新增 `ID-Format` 列
- **新增 `ID-Format` 导入逻辑**（L561-568）：导入 Excel 时读取 `ID-Format` 列，若含 `_FD` 则设置 `is_fd = True`，并写入 `VFrameFormat` 属性

#### `src/canmatrix/formats/xls_common.py`
- **新增 `ID-Format` 导出逻辑**（L118-128）：导出 Excel 时，根据 `frame.is_fd` 和 `frame.arbitration_id.extended` 生成 `ID-Format` 列内容（`StandardCAN_FD` / `ExtendedCAN_FD` / `StandardCAN` / `ExtendedCAN`）
