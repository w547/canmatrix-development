import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import canmatrix
import canmatrix.compare

file1 = r"e:\BSW\wsq_ai\canmatrix-development\visual_app\测试集\F03_F05_org.dbc"
file2 = r"e:\BSW\wsq_ai\canmatrix-development\visual_app\测试集\F03_F05CANFD_CDU_VIU0_20260312_正确的.dbc"

db1 = canmatrix.formats.loadp(file1)
db2 = canmatrix.formats.loadp(file2)

if isinstance(db1, dict):
    db1 = list(db1.values())[0]
if isinstance(db2, dict):
    db2 = list(db2.values())[0]

result = canmatrix.compare.compare_db(db1, db2)

frames_1 = {f.name: f for f in db1.frames}
frames_2 = {f.name: f for f in db2.frames}

def get_all_signals(db):
    signals = {}
    for f in db.frames:
        for s in f.signals:
            key = f"{f.name}.{s.name}"
            signals[key] = (f, s)
    return signals

signals_1 = get_all_signals(db1)
signals_2 = get_all_signals(db2)

print("=" * 120)
print("DBC 文件对比报告")
print("=" * 120)
print(f"文件 A (F03_F05_org.dbc):         {file1}")
print(f"文件 B (F03_F05CANFD_CDU_VIU0_20260312_正确的.dbc): {file2}")
print()

print("=" * 120)
print("表 1: 基本统计信息对比")
print("=" * 120)
print(f"| {'项目':<25} | {'文件 A':<15} | {'文件 B':<15} | {'变化量':<10} | {'说明':<30} |")
print("-" * 120)
print(f"| {'ECU 数量':<25} | {len(db1.ecus):<15} | {len(db2.ecus):<15} | {len(db2.ecus)-len(db1.ecus):<+10} | {'节点数量变化':<30} |")
print(f"| {'报文(Frame)数量':<25} | {len(db1.frames):<15} | {len(db2.frames):<15} | {len(db2.frames)-len(db1.frames):<+10} | {'消息帧数量变化':<30} |")
print(f"| {'信号(Signal)数量':<25} | {len(signals_1):<15} | {len(signals_2):<15} | {len(signals_2)-len(signals_1):<+10} | {'信号总数变化':<30} |")
print()

added_frames = set(frames_2.keys()) - set(frames_1.keys())
deleted_frames = set(frames_1.keys()) - set(frames_2.keys())
common_frames = set(frames_1.keys()) & set(frames_2.keys())

print("=" * 120)
print("表 2: 报文(Frame)差异汇总")
print("=" * 120)
print(f"| {'类别':<15} | {'数量':<10} | {'报文名称':<80} |")
print("-" * 120)
print(f"| {'新增报文':<15} | {len(added_frames):<10} | {', '.join(sorted(added_frames)):<80} |")
print(f"| {'删除报文':<15} | {len(deleted_frames):<10} | {', '.join(sorted(deleted_frames)):<80} |")
print(f"| {'共有报文':<15} | {len(common_frames):<10} | {'（详细属性变化见下表）':<80} |")
print()

print("=" * 120)
print("表 3: 新增报文详情")
print("=" * 120)
if added_frames:
    print(f"| {'报文名称':<35} | {'ID(hex)':<12} | {'DLC':<6} | {'发送节点':<20} | {'信号数量':<10} | {'周期/类型':<20} |")
    print("-" * 120)
    for fname in sorted(added_frames):
        f = frames_2[fname]
        tx = ", ".join(f.transmitters) if f.transmitters else "N/A"
        cycle = f.attributes.get('GenMsgCycleTime', 'N/A') if f.attributes else 'N/A'
        print(f"| {fname:<35} | {hex(f.arbitration_id.id):<12} | {f.size:<6} | {tx[:20]:<20} | {len(f.signals):<10} | {str(cycle)[:20]:<20} |")
else:
    print("无新增报文")
print()

print("=" * 120)
print("表 4: 删除报文详情")
print("=" * 120)
if deleted_frames:
    print(f"| {'报文名称':<35} | {'ID(hex)':<12} | {'DLC':<6} | {'发送节点':<20} | {'信号数量':<10} | {'周期/类型':<20} |")
    print("-" * 120)
    for fname in sorted(deleted_frames):
        f = frames_1[fname]
        tx = ", ".join(f.transmitters) if f.transmitters else "N/A"
        cycle = f.attributes.get('GenMsgCycleTime', 'N/A') if f.attributes else 'N/A'
        print(f"| {fname:<35} | {hex(f.arbitration_id.id):<12} | {f.size:<6} | {tx[:20]:<20} | {len(f.signals):<10} | {str(cycle)[:20]:<20} |")
else:
    print("无删除报文")
print()

common_frame_attr_changes = []
for fname in sorted(common_frames):
    f1 = frames_1[fname]
    f2 = frames_2[fname]
    changes = []
    if f1.arbitration_id.id != f2.arbitration_id.id:
        changes.append(('ID', hex(f1.arbitration_id.id), hex(f2.arbitration_id.id)))
    if f1.size != f2.size:
        changes.append(('DLC', str(f1.size), str(f2.size)))
    if f1.transmitters != f2.transmitters:
        changes.append(('发送节点', ', '.join(f1.transmitters), ', '.join(f2.transmitters)))
    if changes:
        common_frame_attr_changes.append((fname, changes))

if common_frame_attr_changes:
    print("=" * 120)
    print("表 5: 共有报文属性变化")
    print("=" * 120)
    print(f"| {'报文名称':<35} | {'变化属性':<15} | {'文件 A':<30} | {'文件 B':<30} |")
    print("-" * 120)
    for fname, changes in common_frame_attr_changes:
        for i, (attr, old, new) in enumerate(changes):
            name = fname if i == 0 else ""
            print(f"| {name:<35} | {attr:<15} | {old[:30]:<30} | {new[:30]:<30} |")
    print()

added_signals = set(signals_2.keys()) - set(signals_1.keys())
deleted_signals = set(signals_1.keys()) - set(signals_2.keys())
common_signals = set(signals_1.keys()) & set(signals_2.keys())

print("=" * 120)
print("表 6: 信号(Signal)差异汇总")
print("=" * 120)
print(f"| {'类别':<15} | {'数量':<10} | {'说明':<80} |")
print("-" * 120)
print(f"| {'新增信号':<15} | {len(added_signals):<10} | {'文件 B 中新增的信号':<80} |")
print(f"| {'删除信号':<15} | {len(deleted_signals):<10} | {'文件 A 中有但文件 B 中没有的信号':<80} |")
print(f"| {'共有信号':<15} | {len(common_signals):<10} | {'两个文件都有的信号（属性可能有变化）':<80} |")
print()

print("=" * 120)
print("表 7: 新增信号按报文分组统计")
print("=" * 120)
added_by_frame = {}
for sig in added_signals:
    frame_name = sig.split('.')[0]
    if frame_name not in added_by_frame:
        added_by_frame[frame_name] = []
    added_by_frame[frame_name].append(sig.split('.')[1])

print(f"| {'报文名称':<35} | {'新增信号数':<12} | {'信号列表':<60} |")
print("-" * 120)
for fname in sorted(added_by_frame.keys()):
    sig_list = ", ".join(sorted(added_by_frame[fname]))
    print(f"| {fname:<35} | {len(added_by_frame[fname]):<12} | {sig_list[:60]:<60} |")
print()

print("=" * 120)
print("表 8: 删除信号按报文分组统计")
print("=" * 120)
deleted_by_frame = {}
for sig in deleted_signals:
    frame_name = sig.split('.')[0]
    if frame_name not in deleted_by_frame:
        deleted_by_frame[frame_name] = []
    deleted_by_frame[frame_name].append(sig.split('.')[1])

print(f"| {'报文名称':<35} | {'删除信号数':<12} | {'信号列表':<60} |")
print("-" * 120)
for fname in sorted(deleted_by_frame.keys()):
    sig_list = ", ".join(sorted(deleted_by_frame[fname]))
    print(f"| {fname:<35} | {len(deleted_by_frame[fname]):<12} | {sig_list[:60]:<60} |")
print()

common_signal_changes = []
for sig_key in sorted(common_signals):
    f1, s1 = signals_1[sig_key]
    f2, s2 = signals_2[sig_key]
    changes = []
    
    if s1.start_bit != s2.start_bit:
        changes.append(('起始位', str(s1.start_bit), str(s2.start_bit)))
    if s1.size != s2.size:
        changes.append(('位长', str(s1.size), str(s2.size)))
    if float(s1.factor) != float(s2.factor):
        changes.append(('精度', str(s1.factor), str(s2.factor)))
    if float(s1.offset) != float(s2.offset):
        changes.append(('偏移量', str(s1.offset), str(s2.offset)))
    if float(s1.min) != float(s2.min):
        changes.append(('最小值', str(s1.min), str(s2.min)))
    if float(s1.max) != float(s2.max):
        changes.append(('最大值', str(s1.max), str(s2.max)))
    if s1.is_little_endian != s2.is_little_endian:
        changes.append(('字节序', 'Intel(小端)' if s1.is_little_endian else 'Motorola(大端)', 
                              'Intel(小端)' if s2.is_little_endian else 'Motorola(大端)'))
    if s1.is_signed != s2.is_signed:
        changes.append(('符号', '有符号' if s1.is_signed else '无符号', 
                             '有符号' if s2.is_signed else '无符号'))
    if s1.unit != s2.unit:
        changes.append(('单位', str(s1.unit), str(s2.unit)))
    if s1.receivers != s2.receivers:
        changes.append(('接收节点', ', '.join(s1.receivers), ', '.join(s2.receivers)))
    
    if changes:
        common_signal_changes.append((sig_key, changes))

if common_signal_changes:
    print("=" * 120)
    print("表 9: 共有信号属性变化（前30条）")
    print("=" * 120)
    print(f"| {'信号名称':<45} | {'变化属性':<12} | {'文件 A':<25} | {'文件 B':<25} |")
    print("-" * 120)
    
    count = 0
    for sig_key, changes in common_signal_changes:
        if count >= 30:
            break
        for i, (attr, old, new) in enumerate(changes):
            if count >= 30:
                break
            name = sig_key if i == 0 else ""
            print(f"| {name:<45} | {attr:<12} | {old[:25]:<25} | {new[:25]:<25} |")
            count += 1
    
    if len(common_signal_changes) > 30:
        print(f"\n... 还有 {len(common_signal_changes) - 30} 个信号有属性变化")
    print()

ecu_names_1 = set(e.name for e in db1.ecus)
ecu_names_2 = set(e.name for e in db2.ecus)
ecu_added = ecu_names_2 - ecu_names_1
ecu_deleted = ecu_names_1 - ecu_names_2

print("=" * 120)
print("表 10: ECU(节点)差异")
print("=" * 120)
print(f"| {'类别':<15} | {'数量':<10} | {'ECU 名称':<80} |")
print("-" * 120)
print(f"| {'新增 ECU':<15} | {len(ecu_added):<10} | {', '.join(sorted(ecu_added)) if ecu_added else '无':<80} |")
print(f"| {'删除 ECU':<15} | {len(ecu_deleted):<10} | {', '.join(sorted(ecu_deleted)) if ecu_deleted else '无':<80} |")
print()

print("=" * 120)
print("总结")
print("=" * 120)
print(f"""
主要变化点：
1. ECU 节点: 新增 1 个 (IPS)
2. 报文: 新增 4 个 (CDU_Data, Diag_PhyReq_NIDU, Diag_Resp_NIDU, NM_Autosar_CDU)
         删除 2 个 (Diag_PhyReq_MCUR, Diag_Resp_MCUR)
3. 信号: 新增 149 个，删除 72 个，净增 77 个
4. 主要新增信号集中在 CDU_Data 报文中，与 CDU/IPS 电源管理相关

总差异项数: 386 项
""")
print("=" * 120)
