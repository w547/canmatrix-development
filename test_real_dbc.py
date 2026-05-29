import sys
import os
import io
import decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import canmatrix
from canmatrix.formats import dbc, xls, xlsx, xls_common

test_dir = os.path.join(os.path.dirname(__file__), 'visual_app', '测试集')

# ===== Test 1: Load the "new document" which has INT 0 0 define and 4294967294 values =====
print("=" * 60)
print("TEST 1: Load new_text_file.txt (INT 0 0 define)")
txt_path = os.path.join(test_dir, '新建文本文档.txt')
with open(txt_path, 'rb') as f:
    content = f.read()
db1 = dbc.load(io.BytesIO(content))
print(f"Loaded {len(db1.frames)} frames")

targets = ['CRM_ChargeNo', 'BRM_BatteryManufacture']
for frame in db1.frames:
    for sig in frame.signals:
        if sig.name in targets:
            print(f"\n  {sig.name}:")
            print(f"    attributes: {sig.attributes}")
            gsv = sig.attributes.get('GenSigStartValue', 'N/A')
            print(f"    GenSigStartValue attr: '{gsv}' (type={type(gsv).__name__})")
            print(f"    initial_value: {sig.initial_value} (type={type(sig.initial_value).__name__})")
            print(f"    factor={sig.factor}, offset={sig.offset}, is_signed={sig.is_signed}")

if 'GenSigStartValue' in db1.signal_defines:
    sd = db1.signal_defines['GenSigStartValue']
    print(f"\n  GenSigStartValue Define: type={sd.type}, min={sd.min}, max={sd.max}, default={sd.defaultValue}")

# ===== Test 2: Export db1 to DBC and check output =====
print("\n" + "=" * 60)
print("TEST 2: Export to DBC (from new_text_file)")
dbc_out = io.BytesIO()
dbc.dump(db1, dbc_out)
dbc_out.seek(0)
dbc_text = dbc_out.read().decode('utf-8', errors='replace')

for line in dbc_text.split('\n'):
    if 'GenSigStartValue' in line:
        if any(s in line for s in targets) or 'BA_DEF_' in line or 'BA_DEF_DEF_' in line:
            print(f"  {line.strip()}")

# ===== Test 3: Re-import and check =====
print("\n" + "=" * 60)
print("TEST 3: Re-import exported DBC")
dbc_out.seek(0)
db2 = dbc.load(dbc_out)
for frame in db2.frames:
    for sig in frame.signals:
        if sig.name in targets:
            gsv = sig.attributes.get('GenSigStartValue', 'N/A')
            print(f"  {sig.name}: GenSigStartValue='{gsv}', initial_value={sig.initial_value}")

if 'GenSigStartValue' in db2.signal_defines:
    sd = db2.signal_defines['GenSigStartValue']
    print(f"\n  GenSigStartValue Define after re-import: type={sd.type}, min={sd.min}, max={sd.max}, default={sd.defaultValue}")

# ===== Test 4: Export to XLSX and check =====
print("\n" + "=" * 60)
print("TEST 4: Export to XLSX")
xlsx_out = io.BytesIO()
xlsx.dump(db1, xlsx_out)
xlsx_out.seek(0)

# Re-import from XLSX
print("  Re-import from XLSX:")
db3 = xlsx.load(xlsx_out)
for frame in db3.frames:
    for sig in frame.signals:
        if sig.name in targets:
            gsv = sig.attributes.get('GenSigStartValue', 'N/A')
            print(f"  {sig.name}: GenSigStartValue='{gsv}', initial_value={sig.initial_value}")

# ===== Test 5: What is 4294967294 as a signed 32-bit int? =====
print("\n" + "=" * 60)
print("TEST 5: Value analysis")
val = 4294967294
print(f"  4294967294 as signed 32-bit: {val - (1 << 32)}")
print(f"  4294967294 as hex: {hex(val)}")
print(f"  -2 as unsigned 32-bit: {-2 & 0xFFFFFFFF}")
print(f"  -2147483648 as unsigned 32-bit: {-2147483648 & 0xFFFFFFFF}")

# ===== Test 6: Trace the exact conversion path =====
print("\n" + "=" * 60)
print("TEST 6: Trace DBC->Excel->DBC with org.dbc (INT 0 0 define)")
org_path = os.path.join(test_dir, 'org.dbc')
with open(org_path, 'rb') as f:
    content = f.read()
db_org = dbc.load(io.BytesIO(content))

for frame in db_org.frames:
    for sig in frame.signals:
        if sig.name in targets:
            gsv = sig.attributes.get('GenSigStartValue', 'N/A')
            print(f"  ORG {sig.name}: GenSigStartValue='{gsv}', initial_value={sig.initial_value}")

# Export org to DBC
org_out = io.BytesIO()
dbc.dump(db_org, org_out)
org_out.seek(0)
org_text = org_out.read().decode('utf-8', errors='replace')
for line in org_text.split('\n'):
    if 'GenSigStartValue' in line and any(s in line for s in targets):
        print(f"  ORG export: {line.strip()}")

# ===== Test 7: Check what happens when GenSigStartValue is 0 in Excel =====
print("\n" + "=" * 60)
print("TEST 7: Test with 111.dbc (no explicit GenSigStartValue for targets)")
dbc_111_path = os.path.join(test_dir, '111.dbc')
with open(dbc_111_path, 'rb') as f:
    content = f.read()
db_111 = dbc.load(io.BytesIO(content))

for frame in db_111.frames:
    for sig in frame.signals:
        if sig.name in targets:
            gsv = sig.attributes.get('GenSigStartValue', 'N/A')
            print(f"  111 {sig.name}: GenSigStartValue='{gsv}', initial_value={sig.initial_value}")

# Export 111 to Excel
xlsx_111_out = io.BytesIO()
xlsx.dump(db_111, xlsx_111_out)
xlsx_111_out.seek(0)

# Re-import from XLSX
db_111_from_xlsx = xlsx.load(xlsx_111_out)
for frame in db_111_from_xlsx.frames:
    for sig in frame.signals:
        if sig.name in targets:
            gsv = sig.attributes.get('GenSigStartValue', 'N/A')
            print(f"  111 from XLSX {sig.name}: GenSigStartValue='{gsv}', initial_value={sig.initial_value}")

# Export 111 to DBC
dbc_111_out = io.BytesIO()
dbc.dump(db_111, dbc_111_out)
dbc_111_out.seek(0)
dbc_111_text = dbc_111_out.read().decode('utf-8', errors='replace')
for line in dbc_111_text.split('\n'):
    if 'GenSigStartValue' in line and any(s in line for s in targets):
        print(f"  111 DBC export: {line.strip()}")
