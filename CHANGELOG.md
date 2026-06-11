# Changelog

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
