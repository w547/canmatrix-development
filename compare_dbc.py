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

def collect_diffs(res, depth=0, parent_type="", parent_name=""):
    diffs = []
    if res.result and res.result != "equal":
        name = ""
        if hasattr(res.ref, 'name'):
            name = res.ref.name
        elif isinstance(res.ref, str):
            name = res.ref
        
        change_old = ""
        change_new = ""
        if res.changes is not None and len(res.changes) >= 2:
            change_old = str(res.changes[0]) if res.changes[0] is not None else ""
            change_new = str(res.changes[1]) if res.changes[1] is not None else ""
        
        diffs.append({
            'type': res.type or parent_type,
            'name': name,
            'result': res.result,
            'change_type': res.type or '',
            'old_value': change_old,
            'new_value': change_new,
            'depth': depth
        })
    
    for child in res.children:
        child_parent_name = ""
        if hasattr(res.ref, 'name'):
            child_parent_name = res.ref.name
        diffs.extend(collect_diffs(child, depth + 1, res.type or parent_type, child_parent_name))
    
    return diffs

diffs = collect_diffs(result)

frames_1 = set(f.name for f in db1.frames)
frames_2 = set(f.name for f in db2.frames)
signals_1 = set()
signals_2 = set()
for f in db1.frames:
    for s in f.signals:
        signals_1.add(f"{f.name}.{s.name}")
for f in db2.frames:
    for s in f.signals:
        signals_2.add(f"{f.name}.{s.name}")

print("=" * 100)
print("DBC 文件对比报告")
print("=" * 100)
print(f"文件1 (原始): {file1}")
print(f"文件2 (正确): {file2}")
print()
print("=" * 100)
print("一、基本统计信息")
print("=" * 100)
print(f"{'项目':<30} {'文件1':<20} {'文件2':<20} {'差异':<10}")
print("-" * 80)
print(f"{'ECU数量':<30} {len(db1.ecus):<20} {len(db2.ecus):<20} {len(db2.ecus)-len(db1.ecus):<+10}")
print(f"{'报文(Frame)数量':<30} {len(db1.frames):<20} {len(db2.frames):<20} {len(db2.frames)-len(db1.frames):<+10}")
print(f"{'信号(Signal)数量':<30} {len(signals_1):<20} {len(signals_2):<20} {len(signals_2)-len(signals_1):<+10}")
print()

added_frames = frames_2 - frames_1
deleted_frames = frames_1 - frames_2
common_frames = frames_1 & frames_2

print("=" * 100)
print("二、报文(Frame)差异")
print("=" * 100)
print(f"新增报文: {len(added_frames)} 个")
if added_frames:
    print(f"  {', '.join(sorted(added_frames))}")
print()
print(f"删除报文: {len(deleted_frames)} 个")
if deleted_frames:
    print(f"  {', '.join(sorted(deleted_frames))}")
print()
print(f"共有报文: {len(common_frames)} 个")
print()

frame_diffs = [d for d in diffs if d['type'] == 'FRAME' and d['result'] == 'changed']
if frame_diffs:
    print("=" * 100)
    print("三、共有报文属性差异")
    print("=" * 100)
    print(f"{'报文名称':<35} {'变化类型':<20} {'原值':<25} {'新值':<25}")
    print("-" * 105)
    
    for d in diffs:
        if d['type'] == 'FRAME' and d['result'] == 'changed' and d['change_type'] not in ['FRAME', 'ATTRIBUTES'] and d['old_value'] and d['new_value']:
            print(f"{d['name']:<35} {d['change_type']:<20} {d['old_value'][:25]:<25} {d['new_value'][:25]:<25}")
    print()

print("=" * 100)
print("四、信号(Signal)差异")
print("=" * 100)

added_signals = signals_2 - signals_1
deleted_signals = signals_1 - signals_2

print(f"新增信号: {len(added_signals)} 个")
if added_signals:
    for sig in sorted(added_signals)[:20]:
        print(f"  + {sig}")
    if len(added_signals) > 20:
        print(f"  ... 还有 {len(added_signals)-20} 个新增信号")
print()

print(f"删除信号: {len(deleted_signals)} 个")
if deleted_signals:
    for sig in sorted(deleted_signals)[:20]:
        print(f"  - {sig}")
    if len(deleted_signals) > 20:
        print(f"  ... 还有 {len(deleted_signals)-20} 个删除信号")
print()

signal_diffs = []
for d in diffs:
    if d['type'] == 'SIGNAL' and d['result'] == 'changed' and d['old_value'] and d['new_value']:
        signal_diffs.append(d)

if signal_diffs:
    print("=" * 100)
    print("五、共有信号属性差异")
    print("=" * 100)
    print(f"{'信号名称':<45} {'变化类型':<20} {'原值':<15} {'新值':<15}")
    print("-" * 95)
    
    current_frame = ""
    current_signal = ""
    for d in signal_diffs[:50]:
        print(f"{d['name']:<45} {d['change_type']:<20} {d['old_value'][:15]:<15} {d['new_value'][:15]:<15}")
    
    if len(signal_diffs) > 50:
        print(f"\n... 还有 {len(signal_diffs)-50} 个信号属性变化")
    print()

ecu_added = set(e.name for e in db2.ecus) - set(e.name for e in db1.ecus)
ecu_deleted = set(e.name for e in db1.ecus) - set(e.name for e in db2.ecus)

if ecu_added or ecu_deleted:
    print("=" * 100)
    print("六、ECU差异")
    print("=" * 100)
    if ecu_added:
        print(f"新增ECU: {', '.join(sorted(ecu_added))}")
    if ecu_deleted:
        print(f"删除ECU: {', '.join(sorted(ecu_deleted))}")
    print()

print("=" * 100)
print(f"总差异项数: {len(diffs)}")
print("=" * 100)
