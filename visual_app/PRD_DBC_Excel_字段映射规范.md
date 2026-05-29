# DBC ↔ Excel 字段映射规范 (PRD)

> 版本: 1.1 | 日期: 2026-05-20 | 基于 canmatrix 代码库实际实现

---

## 1. 数据来源说明

### 1.1 DBC 数据库结构

DBC 文件是 CAN 总线描述的标准文本格式，由 Vector Informatik 定义。本系统支持的 DBC 关键段如下：

| 段 | 关键字 | 说明 |
|----|--------|------|
| 版本 | `VERSION` | DBC 文件版本标识 |
| 节点 | `BU_` | ECU 节点名称列表 |
| 值表 | `VAL_TABLE_` | 全局值表定义 |
| 帧 | `BO_` | 消息/帧定义（ID、名称、DLC、发送者） |
| 信号 | `SG_` | 信号定义（含起始位、长度、字节序、因子、偏移量、min/max、单位、接收者） |
| 发送者 | `BO_TX_BU_` | 帧的第二及后续发送者 |
| 注释 | `CM_` | 帧、信号、ECU 注释 |
| 属性定义 | `BA_DEF_` | 自定义属性类型定义（帧/信号/ECU/全局级别） |
| 属性默认 | `BA_DEF_DEF_` | 自定义属性默认值 |
| 属性值 | `BA_` | 自定义属性实例值 |
| 信号值表 | `VAL_` | 信号枚举值表 |
| 信号组 | `SIG_GROUP_` | 信号组定义 |
| 环境变量 | `EV_` | 环境变量定义 |

#### 信号行格式

```
SG_ <name> [M|m<N>] : <start_bit>|<size>@<byte_order><sign> (<factor>,<offset>) [<min>|<max>] "<unit>" <receivers>
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 信号名称 | `EngineSpeed` |
| `M` / `m<N>` | 复用模式（M=Multiplexor, mN=由复用值N触发） | `m0` |
| `start_bit` | 起始位（LSB0 编号） | `12` |
| `size` | 信号长度（bit） | `16` |
| `byte_order` | `0`=Motorola(大端), `1`=Intel(小端) | `1` |
| `sign` | `+`=无符号, `-`=有符号 | `+` |
| `factor` | 缩放因子（物理值 = 原始值 × factor + offset） | `0.125` |
| `offset` | 偏移量 | `0` |
| `min` / `max` | 物理范围 | `0\|8000` |
| `unit` | 物理单位 | `rpm` |

### 1.2 Excel 文件格式规范

Excel 文件（`.xls` 或 `.xlsx`）按以下列顺序组织数据：

#### 列结构布局

```
[帧信息列] [信号前半列] [ECU 列...] [信号后半列] [附加帧属性列...] [附加信号属性列...]
```

#### 完整列定义

| 列序号 | 列标题 | 分组 | 数据类型 |
|--------|--------|------|----------|
| 1 | `ID` | 帧信息 | 十六进制字符串（如 `3A1h`, `1A2xh`） |
| 2 | `Frame Name` | 帧信息 | 字符串 |
| 3 | `DLC` | 帧信息 | 整数 |
| 4 | `frame.comment` | 帧信息 | 字符串 |
| 5 | `Cycle Time [ms]` | 帧信息 | 整数（毫秒） |
| 6 | `Launch Type` | 帧信息 | 枚举字符串 |
| 7 | `Launch Parameter` | 帧信息 | 整数 |
| 8 | `DiagRequest` | 帧信息（Diagnostics） | STRING |
| 9 | `DiagResponse` | 帧信息（Diagnostics） | STRING |
| 10 | `DiagState` | 帧信息（Diagnostics） | STRING |
| 11 | `NmMessage` | 帧信息（Net Management） | STRING |
| 12 | `GenMsgILSupport` | 帧信息（Interaction Layer） | STRING |
| 13 | `GenMsgCycleTimeFast` | 帧信息（Interaction Layer） | INT 0..65535 |
| 14 | `GenMsgNoOfRepetitions` | 帧信息（Interaction Layer） | INT 0..65535 |
| 15 | `CANFD_BRS` | 帧信息 | STRING |
| 16 | `Signal Byte No.` | 信号前半 | 整数（1-based） |
| 17 | `Signal Bit No.` | 信号前半 | 整数（0-7） |
| 18 | `Signal Name` | 信号前半 | 字符串 |
| 19 | `Signal Function` | 信号前半 | 字符串（含 Multiplex 信息） |
| 20 | `Signal Length [Bit]` | 信号前半 | 整数 |
| 21 | `Signal Default` | 信号前半 | 数值 |
| 22 | `Signal Not Available` | 信号前半 | 字符串（`GenSigSNA` 属性值） |
| 23 | `Byteorder` | 信号前半 | `"i"`(Intel) 或 `"m"`(Motorola) |
| 24..N | `{ECU名称}` (每个ECU各占一列) | ECU | `"s"`/`"r"`/`"sr"`/`"rs"` |
| N+1 | `Value` | 信号后半 | 整数（值表键） |
| N+2 | `Name / Phys. Range` | 信号后半 | 字符串（值表项名 或 `min..max`） |
| N+3 | `Function / Increment Unit` | 信号后半 | 字符串（因子+单位 或 仅单位） |
| ... | `frame.{属性名}` | 附加帧属性 | 字符串/数值 |
| ... | `signal.{属性名}` | 附加信号属性 | 字符串/数值 |

> **条件列说明**：
> - `Signal Not Available`：仅当 DBC 的 `signal_defines` 中存在 `"GenSigSNA"` 时才生成
> - 帧级属性列（DiagRequest、DiagResponse、DiagState、NmMessage、GenMsgILSupport、GenMsgCycleTimeFast、GenMsgNoOfRepetitions、CANFD_BRS）：当 DBC 的 `frame_defines` 中存在对应定义时显示值，否则显示空值
> - ECU 列数量取决于数据库中 ECU 的数量
> - 附加属性列数量取决于是否有 `frame.*` 和 `signal.*` 前缀的属性

> **字体样式规范**：
> - 所有数据列统一使用黑色字体（`sty_norm` / `Font(color='000000')`）
> - 第一行使用玫瑰色背景表头（`sty_header`）
> - 每个 Frame 的第一行帧信息列使用粗体 + 上边框（`sty_first_frame`）

---

## 2. 字段映射关系表

### 2.1 帧（Frame）级映射

| DBC 字段 / 属性 | Excel 列标题 | 转换方向 | 数据类型 | 约束 |
|-----------------|-------------|----------|----------|------|
| `BO_` 的 CAN ID | `ID` | 双向 | Hex 字符串 | 标准帧: `3A1h`; 扩展帧: `1A2xh`（`xh` 后缀标识 extended） |
| `BO_` 的帧名称 | `Frame Name` | 双向 | String | DBC 导出时截断至 32 字符 |
| `frame.cycle_time` / `BA_ "GenMsgCycleTime"` | `Cycle Time [ms]` | 双向 | Integer | 0 = 未设置；范围 0-65535 |
| `BA_ "GenMsgSendType"` | `Launch Type` | 双向 | String (ENUM) | 如 `"Cyclic"`, `"Event"`；导入时自动注册 `GenMsgSendType` 定义为 ENUM |
| `BA_ "GenMsgDelayTime"` | `Launch Parameter` | 双向 | Integer | 条件出现：仅当 `GenMsgDelayTime` 在 `frame_defines` 中存在 |
| `frame.arbitration_id.id` | — | DBC only | Integer (HEX) | Excel 中通过 `ID` 列解析 |
| `frame.arbitration_id.extended` | — | DBC only | Boolean | Excel 中通过 `xh` 后缀推断 |
| `frame.size` (DLC) | — | 导入固定为 8 | Integer | 导入后通过 `calc_dlc()` 重新计算实际 DLC |
| `frame.transmitters` | ECU 列（`"s"`） | 双向 | List[String] | 每信号行的 ECU 列中标记 `s` 表示发送 |
| `CM_ BO_` | `frame.comment` 列 | 双向 | String | 帧注释 |
| `BA_ "DiagRequest"` | `DiagRequest` 列 | 双向 | STRING | 诊断请求属性 |
| `BA_ "DiagResponse"` | `DiagResponse` 列 | 双向 | STRING | 诊断响应属性 |
| `BA_ "DiagState"` | `DiagState` 列 | 双向 | STRING | 诊断状态属性 |
| `BA_ "NmMessage"` | `NmMessage` 列 | 双向 | STRING | 网络管理消息属性 |
| `BA_ "GenMsgILSupport"` | `GenMsgILSupport` 列 | 双向 | STRING | 交互层支持属性 |
| `BA_ "GenMsgCycleTimeFast"` | `GenMsgCycleTimeFast` 列 | 双向 | INT 0..65535 | 快速周期时间 |
| `BA_ "GenMsgNoOfRepetitions"` | `GenMsgNoOfRepetitions` 列 | 双向 | INT 0..65535 | 重复发送次数 |
| `BA_ "CANFD_BRS"` | `CANFD_BRS` 列 | 双向 | STRING | CAN FD 比特率切换属性 |

### 2.2 信号（Signal）级映射

| DBC 字段 / 属性 | Excel 列标题 | 转换方向 | 数据类型 | 约束 |
|-----------------|-------------|----------|----------|------|
| `sig.name` | `Signal Name` | 双向 | String | 信号唯一标识（帧内） |
| `sig.start_bit` | `Signal Byte No.` + `Signal Bit No.` | 双向 | Integer | Byte(1-based) + Bit(0-7) → 绝对起始位，根据 Motorola 格式转换 |
| `sig.size` | `Signal Length [Bit]` | 双向 | Integer | 范围 1-64 |
| `sig.is_little_endian` | `Byteorder` | 双向 | `"i"` / `"m"` | `"i"`=Intel(True), `"m"`=Motorola(False) |
| `sig.is_signed` | — | 导入固定 | Boolean | Excel 导入时固定为 `False`；DBC 中由 `SG_` 行的 `+/-` 标识 |
| `sig.factor` | `Function / Increment Unit` | 双向 | Numeric | 与 unit 在同一列，格式: `"{factor} {unit}"` 或仅 `"{unit}"` |
| `sig.offset` | `Name / Phys. Range` | 双向 | Numeric | 通过 `"min..max"` 解析；`offset = min` |
| `sig.unit` | `Function / Increment Unit` | 双向 | String | 与 factor 同列 |
| `sig.min` | `Name / Phys. Range` | 双向 | Numeric | 与 max 同列，格式: `"min..max"` |
| `sig.max` | `Name / Phys. Range` | 双向 | Numeric | 与 min 同列；未指定时自动计算为 `2^size - 1` |
| `sig.initial_value` | `Signal Default` | 双向 | Numeric | **物理值**（已缩放）；DBC 导出时反转为原始值 `raw = (initial - offset)/factor` 写入 `GenSigStartValue` |
| `sig.comment` | `Signal Function` | 双向 | String | 含 Multiplex 信息 |
| `sig.multiplex` | `Signal Function` | 双向 | String/Int | Multiplexor: `"Mode Signal:"` 前缀；Multiplexed: `"Mode N:"` 前缀 |
| `sig.values` | `Value` + `Name / Phys. Range` | 双向 | Dict[Int→String] | 值表：Value 列存键(Int)，Name/Phys.Range 列存值(String) |
| `sig.receivers` | ECU 列（`"r"`） | 双向 | List[String] | 每信号行 ECU 列中标记 `r` |
| `sig.cycle_time` / `BA_ "GenSigCycleTime"` | — | DBC only | Integer | Excel 无独立列 |
| `sig.attributes["GenSigSNA"]` | `Signal Not Available` | 双向 | String | 条件出现：仅当 DBC 定义了 `GenSigSNA` |
| `CM_ SG_` | `Signal Function` | 双向 | String | 信号注释与 Function 共用一列 |

### 2.3 DBC 属性映射

| DBC 属性名 | 级别 | DBC 类型 | Excel 表现 | 说明 |
|-----------|------|----------|-----------|------|
| `GenMsgCycleTime` | 帧属性 | INT 0 65535 | `Cycle Time [ms]` 列 | 帧发送周期，导入时自动注册 |
| `GenSigCycleTime` | 信号属性 | INT 0 65535 | 无独立列 | 信号周期，仅 DBC 内可见 |
| `GenMsgSendType` | 帧属性 | ENUM | `Launch Type` 列 | 帧发送类型（Cyclic/Event 等） |
| `GenMsgDelayTime` | Interaction Layer | INT 0 65535 | `Launch Parameter` 列 | 延迟参数 |
| `GenSigStartValue` | 信号属性 | FLOAT 0 100000000000 | `Signal Default` 列 | 信号初始值（导出时自动生成定义） |
| `GenSigSNA` | 信号属性 | STRING | `Signal Not Available` 列 | 信号不可用值标识 |
| `GenMsgCycleTimeActive` | Interaction Layer | INT 0 65535 | 无独立列 | 导入时自动注册 |
| `GenMsgNrOfRepetitions` | Interaction Layer | INT 0 65535 | `GenMsgNoOfRepetitions` 列 | 重复发送次数 |
| `DiagRequest` | Diagnostics | STRING | `DiagRequest` 列 | 诊断请求标识 |
| `DiagResponse` | Diagnostics | STRING | `DiagResponse` 列 | 诊断响应标识 |
| `DiagState` | Diagnostics | STRING | `DiagState` 列 | 诊断状态标识 |
| `NmMessage` | Net Management | STRING | `NmMessage` 列 | 网络管理消息标识 |
| `GenMsgILSupport` | Interaction Layer | STRING | `GenMsgILSupport` 列 | 交互层支持标识 |
| `GenMsgCycleTimeFast` | Interaction Layer | INT 0 65535 | `GenMsgCycleTimeFast` 列 | 快速周期时间 |
| `GenMsgNoOfRepetitions` | Interaction Layer | INT 0 65535 | `GenMsgNoOfRepetitions` 列 | 重复发送次数 |
| `CANFD_BRS` | — | STRING | `CANFD_BRS` 列 | CAN FD 比特率切换 |
| `VFrameFormat` | 帧属性 | ENUM | 无独立列 | CAN FD / J1939 格式标识 |

**分类说明**：
- **Interaction Layer**：交互层（IL）相关属性，用于控制报文发送行为（周期、延迟、重复次数、IL 支持等）
- **Diagnostics**：诊断相关属性（DiagRequest、DiagResponse、DiagState）
- **Net Management**：网络管理相关属性（NmMessage）
- **帧属性**：报文/帧级别的通用属性
- **信号属性**：信号级别的通用属性

---

## 3. 数据转换规则

### 3.1 起始位转换

**DBC LSB0 编号 ↔ Excel (Byte, Bit) 编号**

```
Excel → 内部:
  abs_start_bit = (byte_no - 1) × 8 + bit_no
  然后根据 is_little_endian 和 motorola_bit_format 通过 set_startbit() 转换

内部 → Excel:
  start_bit = sig.get_startbit(bit_numbering=1, start_little=True)
  byte_no   = int(start_bit / 8) + 1
  bit_no    = start_bit % 8
```

**Motorola 字节序的三种位编号模式**：

| 模式 | `motorola_bit_format` | 说明 |
|------|----------------------|------|
| MSB | `"msb"` | 以 MSB 为参考，`set_startbit(abs_start_bit, bitNumbering=1)` |
| MSB Reverse | `"msbreverse"` | 默认，`set_startbit(abs_start_bit)` |
| LSB | `"lsb"` | 以 LSB 为参考，`set_startbit(abs_start_bit, bitNumbering=1, startLittle=True)` |

### 3.2 物理值 ↔ 原始值转换

```
物理值 → 原始值:  raw = (physical_value - offset) / factor
原始值 → 物理值:  physical = raw × factor + offset
```

**重要规则**：
- `initial_value` 在内部始终以**物理值**形式存储
- Excel `Signal Default` 列存储的是**物理值**
- DBC `GenSigStartValue` 属性存储的是**原始值**
- 导出 DBC 时需执行物理值→原始值转换，且**绕过 `phys2raw()` 的 min/max 钳制**

### 3.3 CAN ID 转换

```
DBC → Excel:
  标准帧: f"{id}h"                       如 "3A1h"
  扩展帧: f"{id}xh"                      如 "1A2xh"

Excel → DBC:
  含 "xh" 后缀 → extended=True, id=int(value[:-2], 16)
  仅 "h" 后缀  → extended=False, id=int(value[:-1], 16)
```

### 3.4 Multiplex 信息编解码

| DBC 类型 | Excel `Signal Function` 列格式 |
|----------|------------------------------|
| 非复用 | 直接存放 signal comment |
| Multiplexor | `"Mode Signal: " + comment` |
| Multiplexed (值 N) | `"Mode " + N + ":" + comment` |
| 复杂复用 | `"Mode " + muxer_value + " = " + multiplex_value` |

**解析规则**：
1. 若以 `"Mode Signal:"` 开头 → Multiplexor
2. 若以 `"Mode "` 开头且含 `":"` → 提取 mux_value + comment
3. 否则 → 普通信号

### 3.5 值表（Value Table）映射

```
Excel → DBC:
  Value 列（整数键） + Name/Phys.Range 列（值名）
  → sig.add_values(int_key, string_value)

DBC → Excel:
  值表条目以多行 "key: value" 格式写入 Name/Phys.Range 列
  导入时通过 `_parse_inline_value_table()` 解析
```

### 3.6 ECU 发送/接收标记

| 标记 | 含义 |
|------|------|
| `"s"` | 发送者（Transmitter） |
| `"r"` | 接收者（Receiver） |
| `"sr"` 或 `"rs"` | 即是发送者又是接收者 |

### 3.7 Factor/Unit 列解析

```
列格式:
  "{factor}  {unit}"    → sig.factor = factor, sig.unit = unit
  "{unit}"              → sig.factor = 1, sig.unit = unit

解析规则：
  若含空格且首字符为数字 → 前半为factor，后半为unit
  否则 → 全部视为unit，factor = 1
```

---

## 4. 数据校验标准

### 4.1 帧级校验

| 字段 | 校验规则 | 异常处理 |
|------|----------|----------|
| `ID` | 必须为有效的十六进制数；后缀必须为 `h` 或 `xh` | 跳过该帧行，记录加载错误 |
| `Frame Name` | 非空字符串 | 跳过该帧行 |
| `Cycle Time` | 可转换为 int 的数值；若转换失败默认 0 | 警告 + 默认值 0 |
| `Launch Type` | 允许为 None；非空时注册为 ENUM 类型 | 静默处理 |
| 帧间分割 | 当 ID 或 Frame Name 变化时识别为新帧 | — |

### 4.2 信号级校验

| 字段 | 校验规则 | 异常处理 |
|------|----------|----------|
| `Signal Byte No.` | ≥1 的整数 | 转换失败则跳过信号 |
| `Signal Bit No.` | 0-7 的整数 | 转换失败则跳过信号 |
| `Signal Name` | 非空且不等于 `"-"`（表示为空信号占位） | 值为 `"-"` 时跳过该信号行 |
| `Signal Length` | 1-64 的整数 | 转换失败则使用 0 |
| `Signal Default` | `None` 或 空字符串时使用默认值 0.0 | 非数值字符串静默忽略 |
| `Byteorder` | `"i"` 或 `"m"` | `"i"`→Intel, 其他→Motorola；None→默认 Intel |
| `Factor` | 可转换的数值字符串或单位 | 转换失败则 factor=1, 原值作为 unit |
| `Min/Max` | 从 `"min..max"` 解析；单值视为 offset | 解析失败则自动计算 |

### 4.3 值表校验

| 字段 | 校验规则 | 异常处理 |
|------|----------|----------|
| `Value` | 整数 | 非整数跳过该条目 |
| `Name / Phys. Range` | 非空字符串 | 空值跳过该条目 |
| 值表键唯一性 | 同一信号的值表键不可重复 | 后者覆盖前者 |

---

## 5. 异常处理机制

### 5.1 文件级别异常

| 异常场景 | 处理方式 |
|----------|----------|
| 文件不存在 | 抛出 `FileNotFoundError` |
| 文件格式不正确（非 Excel/DBC） | 抛出格式错误，提示支持的格式列表 |
| Excel 工作表为空 | 返回空数据库对象 |
| 编码错误 | 使用 `dbcImportEncoding` / `dbcExportEncoding` 参数指定（默认 UTF-8） |

### 5.2 导入级异常

| 异常场景 | 处理方式 |
|----------|----------|
| 列标题不匹配 | 通过关键词精确匹配（如 `"Cycle Time"` 匹配 `"Cycle Time [ms]"` 列，避免 `"Cycle"` 过于宽泛误匹配 `"GenMsgCycleTimeFast"`） |
| 数据类型转换失败 | `try/except` 捕获转换异常，使用默认值继续 |
| ECU 列解析错误 | 跳过无法识别的标记，保留已识别的 s/r 信息 |
| Multiplex 解析失败 | 捕获 `ValueError: not enough values to unpack`，保留原始 comment，multiplex 设为 None |
| 附加属性 `exec()` 异常 | 静默忽略无法执行的附加属性赋值语句 |

### 5.3 导出级异常

| 异常场景 | 处理方式 |
|----------|----------|
| 信号名重复 | 自动添加数字后缀（如 `Signal_0`, `Signal_1`） |
| 信号名含特殊字符 | `compatibility` 模式下替换非 ASCII 字符 |
| GenSigStartValue 为 0 | **不写入** GenSigStartValue 属性（initial_value=0 时使用默认值） |
| Factor 与 Decimal 类型不匹配 | 统一使用 `float_factory` 转换后再进行算术运算 |
| ECU 名过长（>32 字符） | 截断并使用 `SystemNodeLongSymbol` 属性存储原名 |
| DLC 计算 | 导出后自动调用 `calc_dlc()` 计算最小所需 DLC |

### 5.4 往返一致性保证

为确保 `DBC → Excel → DBC` 往返转换的一致性，系统实施以下规则：

1. **initial_value 完整保留**：Excel `Signal Default` 列存储物理初始值，导出 DBC 时转换为原始值并写入 `GenSigStartValue`，使用直接公式计算绕过 min/max 钳制
2. **值表多行格式**：导出的值表信息在 Excel 中以换行分隔的多行格式存储，导入时解析
3. **附加属性持久化**：`frame.*` 和 `signal.*` 前缀的附加列保持属性名称前缀，导入时通过 `exec()` 语句恢复
4. **Signal Group 等高级结构**：仅在 DBC 格式中存在，Excel 中不体现

---

## 6. 附录：实现文件索引

| 文件 | 职责 |
|------|------|
| [canmatrix.py](file:///E:/BSW/wsq_ai/canmatrix-development/src/canmatrix/canmatrix.py) | Signal 和 Frame 数据模型定义（核心字段及默认值） |
| [xls_common.py](file:///E:/BSW/wsq_ai/canmatrix-development/src/canmatrix/formats/xls_common.py) | Excel 导出列构建逻辑（`get_frame_info()`, `get_signal()`） |
| [xls.py](file:///E:/BSW/wsq_ai/canmatrix-development/src/canmatrix/formats/xls.py) | `.xls` 格式导入/导出（关键词模糊匹配列索引） |
| [xlsx.py](file:///E:/BSW/wsq_ai/canmatrix-development/src/canmatrix/formats/xlsx.py) | `.xlsx` 格式导入/导出（精确列名匹配） |
| [dbc.py](file:///E:/BSW/wsq_ai/canmatrix-development/src/canmatrix/formats/dbc.py) | DBC 格式导入/导出（序列化/反序列化全部 DBC 段） |
| [convert.py](file:///E:/BSW/wsq_ai/canmatrix-development/src/canmatrix/convert.py) | 格式转换调度器（统一转换入口，处理参数传递） |
| [formats/__init__.py](file:///E:/BSW/wsq_ai/canmatrix-development/src/canmatrix/formats/__init__.py) | 格式模块注册与加载分发（`loadp()`, `dumpp()`） |