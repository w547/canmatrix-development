# Canmatrix 工程结构与功能文档

> 版本: 1.2.0 | 许可证: BSD-2-Clause | 作者: Eduard Bröcker  
> 项目主页: https://github.com/ebroecker/canmatrix  
> 文档: https://canmatrix.readthedocs.io

---

## 一、项目概述

**Canmatrix** 是一个用 Python 编写的汽车通信矩阵处理库，能够读写多种 CAN (Controller Area Network) 数据库格式。它实现了一个统一的 "Python CAN Matrix Object"，用于描述 CAN 通信中所需的对象（ECU、Frame、Signal、Value 等），并提供格式转换和数据库对比两大核心工具。

支持的总线类型:
- **CAN / CAN-FD** (主要支持)
- **FlexRay** (实验性)
- **LIN** (通过 LDF 格式)
- **Ethernet / SOME/IP** (实验性)

---

## 二、工程目录结构

```
canmatrix-development/
├── src/
│   └── canmatrix/                  # 核心包
│       ├── __init__.py             # 包入口, 公开API导出, 版本号 1.2.0
│       ├── canmatrix.py            # ★ 核心数据模型 (Signal, Frame, CanMatrix, Ecu 等)
│       ├── cancluster.py           # 多矩阵集群管理
│       ├── types.py                # 类型别名 (RawValue, PhysicalValue)
│       ├── utils.py                # 工具函数 (字符串解析, FloatFactory, 进制转换)
│       ├── compare.py              # 数据库比较引擎
│       ├── convert.py              # 格式转换引擎 (含过滤/合并/处理逻辑)
│       ├── copy.py                 # ECU/Frame/Signal 拷贝工具
│       ├── join.py                 # J1939 多数据库拼接
│       ├── log.py                  # 日志配置
│       ├── j1939_decoder.py        # J1939 多帧传输协议解码器
│       ├── j1939.dbc               # J1939 标准参数组定义
│       ├── py.typed                # PEP 561 类型标记
│       ├── cli/                    # 命令行工具
│       │   ├── __init__.py
│       │   ├── compare.py          # cancompare CLI 命令
│       │   └── convert.py          # canconvert CLI 命令
│       └── formats/                # 格式导入/导出模块
│           ├── __init__.py         # 格式注册中心, load/dump 统一接口
│           ├── arxml.py            # AUTOSAR ARXML
│           ├── csv.py              # CSV
│           ├── dbc.py              # Vector DBC (CANdb)
│           ├── dbf.py              # Busmaster DBF
│           ├── eds.py              # CANopen EDS
│           ├── fibex.py            # FIBEX XML
│           ├── json.py             # JSON (支持 CANard 格式)
│           ├── kcd.py              # Kayak KCD
│           ├── ldf.py              # LIN Description File
│           ├── odx.py              # ODX 诊断文件
│           ├── scapy.py            # Scapy Python 输出
│           ├── sym.py              # Peak PCAN Symbolic
│           ├── wireshark.py        # Wireshark Lua 脚本
│           ├── xls.py              # Excel .xls (xlrd/xlwt)
│           ├── xlsx.py             # Excel .xlsx (openpyxl)
│           ├── xls_common.py       # Excel 格式公共处理
│           └── yaml.py             # YAML
├── tests/                          # 测试套件 (119 个文件)
│   ├── files/                      # 测试输入文件 (dbc, arxml, dbf, kcd, json)
│   ├── reference/                  # 参考/期望输出文件
│   ├── test_*.py                   # 各模块单元测试
│   └── createTestMatrix.py         # 测试矩阵生成工具
├── examples/                       # 使用示例
├── docs/                           # Sphinx 文档源
├── stubs/                          # 类型存根文件
├── pyproject.toml                  # 项目配置
└── tox.ini                         # 多版本测试配置
```

---

## 三、核心数据模型 (canmatrix.py)

整个项目的核心，定义了汽车通信矩阵的完整数据层次结构。

### 3.1 对象层次关系

```
CanCluster (多矩阵集合)
  └── CanMatrix (单个 CAN 矩阵/数据库)
        ├── Ecu (电子控制单元/节点)
        │     ├── name, comment
        │     └── attributes (自定义属性)
        ├── Frame (CAN 报文/消息)
        │     ├── arbitration_id (ArbitrationId)
        │     │     ├── id (标准 11-bit / 扩展 29-bit)
        │     │     ├── extended (是否为扩展帧)
        │     │     └── J1939 属性 (pgn, source, destination, priority)
        │     ├── Signal (信号)
        │     │     ├── name, start_bit, size
        │     │     ├── is_little_endian (Intel/Motorola 字节序)
        │     │     ├── is_signed, is_float, is_ascii
        │     │     ├── factor, offset, min, max (物理值转换)
        │     │     ├── unit, comment
        │     │     ├── receivers (接收者 ECU 列表)
        │     │     ├── multiplex (多路复用)
        │     │     ├── values (值表/枚举)
        │     │     └── attributes (自定义属性)
        │     ├── SignalGroup (信号组, 含 AUTOSAR E2E/SecOC 属性)
        │     ├── Pdu (PDU, 用于 FlexRay/Container-PDU)
        │     └── Endpoint (以太网端点)
        ├── Define (属性定义: INT/STRING/ENUM/HEX/FLOAT)
        └── value_tables (全局值表)
```

### 3.2 关键类说明

| 类 | 说明 |
|---|---|
| **`ArbitrationId`** | CAN 仲裁 ID。支持标准帧(11-bit)、扩展帧(29-bit)，以及 J1939 分解(PGN/DA/SA/Priority)。提供 `to_compound_integer()` 用于复合 ID 表示。 |
| **`Ecu`** | 代表一个 ECU 电子控制单元。包含名称、注释和自定义属性。 |
| **`Signal`** | 信号是最小数据单元。支持 Intel/Motorola 字节序、物理值换算(`phys2raw`/`raw2phys`)、多路复用、浮点数、ASCII 字符串、值表枚举等。 |
| **`SignalGroup`** | 信号组，可包含 AUTOSAR E2E 和 SecOC 安全属性。 |
| **`Frame`** | CAN 报文/消息。包含信号列表、收发 ECU、DLC 计算、**编码(`encode`)/解码(`decode`/`unpack`)**、信号压缩(`compress`)、多路复用处理。支持 PDU 容器、CAN-FD、J1939。 |
| **`Pdu`** | 协议数据单元。用于 FlexRay 总线（一个 Frame 包含多个 PDU）和 ARXML 的 Container-PDU。 |
| **`CanMatrix`** | 整个 CAN 数据库。管理所有 ECU、Frame、属性定义(Define)和值表。提供增删改查、合并、重命名、编码/解码等操作。 |
| **`CanCluster`** | 多矩阵集群，继承自 `dict`，key 为矩阵名。聚合所有矩阵的 frames/signals/ecus，支持 PDU Gateway 和 Signal Gateway 路由信息。 |
| **`DecodedSignal`** | 解码后的信号值对象，包含 `raw_value`、`phys_value`、`named_value`。 |
| **`Define`** | 属性定义。支持 INT(整型)、STRING(字符串)、ENUM(枚举)、HEX(十六进制)、FLOAT(浮点)类型。 |

### 3.3 自定义异常

| 异常 | 触发条件 |
|---|---|
| `StartbitLowerZero` | 信号起始位计算结果为负 |
| `EncodingComplexMultiplexed` | 尝试编码复杂多路复用帧 |
| `MissingMuxSignal` | 编码多路复用帧时缺少多路选择器信号 |
| `DecodingComplexMultiplexed` | 解码复杂多路复用帧 |
| `DecodingFrameLength` | 解码时数据长度与 DLC 不匹配 |
| `ArbitrationIdOutOfRange` | 仲裁 ID 超出范围 |
| `J1939NeedsExtendedIdentifier` | J1939 操作需要扩展帧 ID |
| `DecodingContainerPdu` / `EncodingContainerPdu` | 容器 PDU 编解码 |

---

## 四、格式系统 (formats/)

### 4.1 架构设计

格式系统采用**插件式架构**，通过 `formats/__init__.py` 中的格式注册中心统一管理。

```python
# 支持的操作类型
supportedFormats[module] = ["load", "dump", "clusterImporter", "clusterExporter", "extension"]
```

### 4.2 统一导入/导出 API

| API | 说明 |
|---|---|
| `load(fileObj, import_type, key, **options)` | 从文件对象导入，返回 `{key: CanMatrix}` 字典 |
| `loads(string, import_type, key, **options)` | 从字符串导入 |
| `loadp(path, import_type, key, **options)` | 从文件路径导入（自动识别扩展名） |
| `loadp_flat(path, ...)` | 从路径导入，返回单个 CanMatrix |
| `loads_flat(string, ...)` | 从字符串导入，返回单个 CanMatrix |
| `load_flat(fileObj, ...)` | 从文件对象导入，返回单个 CanMatrix |
| `dump(canMatrix, fileObj, export_type, **options)` | 导出到文件对象 |
| `dumpp(canCluster, path, export_type, **options)` | 导出到文件路径（自动识别扩展名） |

### 4.3 各格式支持矩阵

| 格式 | 扩展名 | 导入 | 导出 | 集群导入 | 集群导出 | 可选依赖 |
|---|---|---|---|---|---|---|
| **dbc** | .dbc | ✅ | ✅ | - | - | 无 |
| **dbf** | .dbf | ✅ | ✅ | - | - | 无 |
| **kcd** | .kcd | ✅ | ✅ | - | - | lxml |
| **arxml** | .arxml | ✅ | ✅ | ✅ | ✅ | lxml |
| **yaml** | .yaml | ✅ | ✅ | - | - | pyyaml |
| **xls** | .xls | ✅ | ✅ | - | - | xlrd, xlwt |
| **xlsx** | .xlsx | ✅ | ✅ | - | - | openpyxl |
| **json** | .json | ✅ | ✅ | - | - | 无 |
| **sym** | .sym | ✅ | ✅ | - | - | 无 |
| **fibex** | .xml | ✅ | ✅ | - | - | lxml |
| **csv** | .csv | - | ✅ | - | - | 无 |
| **scapy** | .py | - | ✅ | - | - | 无 |
| **wireshark** | .lua | - | ✅ | - | - | 无 |
| **ldf** | .ldf | ✅ | - | - | - | ldfparser |
| **odx** | .odx | ✅ | - | - | - | lxml |
| **eds** | .eds/xml | ✅ | - | - | - | canopen |

### 4.4 重点格式详解

#### DBC (Vector CANdb)
- **最核心格式**，汽车行业 CAN 通信的标准文件格式
- 支持编码设置（`iso-8859-1` / `utf-8`），分别对 units 和 comments 独立设置
- 支持唯一信号名检查 (`dbcUniqueSignalNames`)
- 见 `formats/dbc.py`

#### ARXML (AUTOSAR)
- 支持 AUTOSAR 3.2.3 和 4.1.0+ 版本的导入导出
- 支持**多集群**处理（每个 CAN Cluster 对应一个 CanMatrix）
- 支持 Container-PDU（可转换为多路复用帧）
- 支持 FlexRay 和 Ethernet 描述（实验性）
- 支持多语言注释 (`preferred-languages`) 和 Update-Bit 生成
- 信号组支持 AUTOSAR E2E 和 SecOC 安全属性
- 见 `formats/arxml.py`

#### KCD (Kayak)
- 开源 CAN 描述格式
- 使用 XML+lxml 解析
- 见 `formats/kcd.py`

#### Excel (xls/xlsx)
- 支持自定义列: `additionalFrameAttributes`, `additionalSignalAttributes`
- 支持 Motorola 信号起始位格式选择 (`msb`, `lsb`, `msbreverse`)
- 支持值表分离行显示(`xlsValuesInSeperateLines`)
- 提供 Excel 模板 (`examples/cmTemplate.xlsx`)
- 见 `formats/xls.py`, `formats/xlsx.py`, `formats/xls_common.py`

#### JSON
- 支持 CANard 兼容格式导出 (`jsonExportCanard`)
- 支持完整数据导出 (`jsonExportAll`)
- 支持 `jsonNativeTypes` 使用原生 JSON 类型而非字符串
- 见 `formats/json.py`

---

## 五、命令行工具 (CLI)

### 5.1 canconvert - 格式转换工具

```bash
canconvert [options] input-file output-file
```

**主要功能:**
- 任意支持格式之间的相互转换
- 支持格式自动识别（通过文件扩展名）或手动指定 (`-i`, `-f`)

**过滤与筛选:**
- `--ecus` : 仅复制指定 ECU
- `--frames` : 仅复制指定 Frame
- `--signals` : 仅复制指定 Signal（作为独立信号）
- `--merge` : 合并额外的 CAN 数据库
- `--deleteEcu`, `--deleteFrame`, `--deleteSignal` : 删除指定对象

**处理与转换:**
- `--renameEcu`, `--renameFrame`, `--renameSignal` : 重命名
- `--changeFrameId` : 修改 Frame ID
- `--compressFrame` : 压缩信号布局（移除空隙）
- `--recalcDLC` : 重新计算 DLC
- `--setFrameFd` / `--unsetFrameFd` : 设置/取消 CAN-FD
- `--convertToExtended` / `--convertToJ1939` : 协议类型转换
- `--ignorePduContainer` : 忽略或转换 Container-PDU
- `--signalNameFromAttrib` : 用属性值替换信号名
- `--deleteZeroSignals` : 删除零长度信号
- `--deleteFloatingSignals` : 删除未分配的信号
- `--recalcSignalMaximums` / `--recalcSignalMinimums` : 重新计算物理值范围

**检查与验证:**
- `--checkFloatingFrames` : 检查无发送者 Frame
- `--checkFloatingSignals` : 检查未分配信号
- `--checkSignalUnit` : 检查信号缺少单位或值表
- `--checkSignalReceiver` : 检查信号缺少接收者
- `--warnSignalMinMaxSame` : 检查 min/max 值相同

**格式特定选项:**
- DBC: 编码设置、唯一信号名检查
- ARXML: 版本选择、FlexRay/Ethernet 解码、多语言
- Excel: Motorola 位格式、附加属性列
- JSON: CANard 导出、原生类型

### 5.2 cancompare - 数据库对比工具

```bash
cancompare [options] matrix1 matrix2
```

**主要功能:**
- 对比两个 CAN 数据库的差异
- 支持所有可导入格式
- 结果以树状结构输出

**对比维度:**
- Frame 级别的增删改（包括 ID、DLC、收发 ECU）
- Signal 级别的增删改（起始位、长度、因子、偏移、字节序、符号等）
- ECU 级别的增删改
- 属性定义的增删改
- 全局定义的增删改
- 值表的增删改
- 注释变化检查 (`-c`)
- 属性变化检查 (`-a`)
- 值表变化忽略 (`-t`)
- 仅列出 Frame 列表差异 (`-f`)

---

## 六、辅助模块

### utils.py
- **`FloatFactory`**: 浮点数工厂类，默认使用 `Decimal`，可切换为 `float`
- **`quote_aware_space_split`**: 引号感知的空白分隔解析
- **`quote_aware_comma_split`**: 引号感知的逗号分隔解析
- **`decode_number`**: 智能进制解码（支持 0b/0x 前缀）
- **`guess_value`**: 字符串值转换（true/false/hex/bin）
- **`get_gcd`**: 最大公约数（兼容多 Python 版本）

### copy.py
- **`copy_ecu`**: 复制 ECU 及其属性定义到目标矩阵
- **`copy_ecu_with_frames`**: 复制 ECU 及其关联 Frame (rx/tx 过滤)
- **`copy_frame`**: 复制 Frame 及其 ECU、信号、属性定义
- **`copy_signal`**: 复制信号到目标矩阵（顶层独立信号）

### join.py
- **`join_frame_by_signal_start_bit`**: 通过 PGN 和起始位匹配合并信号
- **`join_frame_for_manufacturer`**: J1939 制造商帧拼接
- **`rename_frame_with_id`**: 用 PGN+SA 扩展 Frame 名称
- **`rename_frame_with_sae_acronym`**: 用 SAE 缩写重命名

### j1939_decoder.py
- 实现 J1939 **多帧传输协议**（BAM/CMDT）的解码器
- 支持 9-1785 字节长报文的拼接
- 可配合自定义矩阵使用（PGN 查找）

### compare.py - 比较引擎
- **`CompareResult`**: 对比结果的树状数据结构
- **`compare_db`**: 数据库级别对比
- **`compare_frame`**: Frame 级别对比（信号、信号组、收发 ECU、属性）
- **`compare_signal`**: Signal 级别对比（所有物理参数、值表、属性）
- **`compare_ecu`**: ECU 级别对比
- **`compare_attributes`**: 属性比较
- **`compare_define_list`**: 定义列表比较
- **`compare_value_table`**: 值表比较
- **`dump_result`**: 将对比结果格式化输出

### convert.py - 转换引擎
- **`convert`**: 主转换函数，串联导入→处理→导出全流程
- **`convert_pdu_container_to_multiplexed`**: PDU 容器转多路复用帧
- 支持多种处理操作的有序执行（筛选、合并、重命名、删除、计算）

---

## 七、测试体系

| 测试文件 | 说明 |
|---|---|
| `test_canmatrix.py` | 核心数据模型测试 |
| `test_dbc.py` | DBC 格式导入导出测试 |
| `test_arxml.py` | ARXML 格式测试 |
| `test_arxml_gw.py` | ARXML Gateway 路由测试 |
| `test_dbf.py` | DBF 格式测试 |
| `test_kcd.py` | KCD 格式测试 |
| `test_json.py` | JSON 格式测试 |
| `test_sym.py` | SYM 格式测试 |
| `test_xls.py` | Excel 格式测试 |
| `test_wireshark.py` | Wireshark Lua 导出测试 |
| `test_scapy.py` | Scapy 导出测试 |
| `test_formats.py` | 格式注册与统一接口测试 |
| `test_cli_compare.py` | CLI 对比命令测试 |
| `test_cli_convert.py` | CLI 转换命令测试 |
| `test_codec.py` | 信号编解码测试 |
| `test_frame_decoding.py` | Frame 解码测试 |
| `test_frame_encoding.py` | Frame 编码测试 |
| `test_j1939_decoder.py` | J1939 解码器测试 |
| `test_copy.py` | 复制功能测试 |
| `test_utils.py` | 工具函数测试 |

---

## 八、依赖关系

```
canmatrix
├── 核心依赖: attrs, click, importlib-metadata
├── 格式依赖 (可选):
│   ├── lxml       → arxml, fibex, kcd, odx
│   ├── xlrd/xlwt  → xls
│   ├── openpyxl   → xlsx
│   ├── pyyaml     → yaml
│   ├── ldfparser  → ldf (LIN)
│   └── canopen    → eds
├── 测试依赖: pytest
└── Python 版本: >= 3.8, 支持到 3.13
```

---

## 九、数据流示意

```
┌─────────────────────────────────────────────────────────────┐
│                     canconvert / cancompare                  │
│                     (CLI 命令行入口)                         │
└─────────────────┬───────────────────────────┬───────────────┘
                  │                           │
                  ▼                           ▼
┌─────────────────────────────┐  ┌────────────────────────────┐
│     canmatrix.convert       │  │    canmatrix.compare        │
│  (转换引擎: 筛选/合并/处理)  │  │   (比较引擎: 树状差异输出)  │
└─────────────┬───────────────┘  └─────────────┬──────────────┘
              │                                │
              ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│              canmatrix.formats (格式注册中心)                 │
│   loads/loadp/load → 导入  │  dump/dumpp → 导出              │
└───────┬─────────────────────────────────────────┬───────────┘
        │                                         │
        ▼                                         ▼
┌───────────────────┐                    ┌───────────────────┐
│  格式导入模块      │                    │  格式导出模块      │
│  dbc, dbf, arxml,  │                   │  dbc, dbf, arxml,  │
│  kcd, json, sym,   │                   │  kcd, json, sym,   │
│  xls, xlsx, yaml,  │                   │  xls, xlsx, yaml,  │
│  fibex, ldf, odx,  │                   │  csv, scapy,       │
│  eds               │                   │  wireshark, fibex  │
└────────┬───────────┘                   └────────┬──────────┘
         │                                        │
         └──────────────┬─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│             canmatrix.CanMatrix (核心数据模型)                │
│                                                             │
│  CanCluster ──► CanMatrix ──► Frame ──► Signal              │
│                               (多矩阵)  (消息)   (信号)      │
│                                           │                  │
│                               SignalGroup (信号组)           │
│                               Pdu (FlexRay)                  │
│                               Endpoint (Ethernet)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 十、使用示例

### 10.1 命令行使用

```bash
# DBC 转 Excel
canconvert input.dbc output.xlsx

# ARXML 转 DBC, 指定 AUTOSAR 版本
canconvert input.arxml output.dbc --arxmlExportVersion 4.1.0

# JSON 导出 (CANard 兼容)
canconvert input.dbc output.json --jsonExportCanard

# 对比两个 DBC 文件
cancompare v1.dbc v2.dbc -c -a

# 仅复制特定 ECU 的帧
canconvert input.dbc output.dbc --ecus MyECU

# 压缩帧信号布局
canconvert input.dbc output.dbc --compressFrame Frame1,Frame2

# 合并多个数据库
canconvert db1.dbc merged.dbc --merge db2.dbc,db3.dbc

# 重新计算 DLC
canconvert input.dbc output.dbc --recalcDLC force
```

### 10.2 Python API 使用

```python
import canmatrix

# 导入 DBC 文件
db = canmatrix.formats.loadp_flat("input.dbc")

# 遍历所有帧
for frame in db.frames:
    print(f"Frame: {frame.name}, ID: 0x{frame.arbitration_id.id:X}")
    for signal in frame.signals:
        print(f"  Signal: {signal.name}, Start: {signal.start_bit}, Size: {signal.size}")

# 编码信号
data = db.encode(frame_id, {"EngineSpeed": 3000, "VehicleSpeed": 120})

# 解码信号
decoded = db.decode(frame_id, data)
for name, dsig in decoded.items():
    print(f"{name} = {dsig.phys_value} ({dsig.raw_value} raw)")

# 导出为 JSON
with open("output.json", "w") as f:
    canmatrix.formats.dump(db, f, "json")
```

---

## 十一、架构亮点

1. **单一数据模型**: 所有格式统一映射到 `CanMatrix` → `Frame` → `Signal` 层次结构，实现格式无关的操作
2. **插件式格式系统**: 新格式只需实现 `load/dump` 接口，自动注册到格式中心
3. **灵活的属性系统**: 通过 `Define` 和 `attributes` dict，支持任意供应商扩展属性
4. **完整的编解码**: 支持 Intel/Motorola 字节序、多路复用、CAN-FD、J1939、Container-PDU
5. **丰富的 CLI 过滤**: 转换过程支持选择、过滤、合并、重命名、验证检查等操作
6. **多矩阵集群**: `CanCluster` 支持管理多个 CAN 总线矩阵，含 Gateway 路由信息
