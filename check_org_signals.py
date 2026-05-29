import sys
import os
import io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import canmatrix
from canmatrix.formats import dbc

test_dir = os.path.join(os.path.dirname(__file__), 'visual_app', '测试集')

org_path = os.path.join(test_dir, 'org.dbc')
print(f"Loading: {org_path}")

# Load DBC - use BytesIO like the test that works
with open(org_path, 'rb') as f:
    content = f.read()
db = dbc.load(io.BytesIO(content))

print(f"\nAfter load:")
print(f"  signal_defines keys: {list(db.signal_defines.keys())}")
print(f"  frame_defines keys: {list(db.frame_defines.keys())}")

if 'GenSigStartValue' in db.signal_defines:
    sd = db.signal_defines['GenSigStartValue']
    print(f"  GenSigStartValue Define: type={sd.type}, min={sd.min}, max={sd.max}, defaultValue={repr(sd.defaultValue)}")
else:
    print("  GenSigStartValue NOT in signal_defines")

targets = ['CRM_ChargeNo', 'BRM_BatteryManufacture']
for frame in db.frames:
    for sig in frame.signals:
        if sig.name in targets:
            print(f"\n  {sig.name} (frame id={frame.arbitration_id}):")
            print(f"    attributes: {sig.attributes}")
            print(f"    initial_value: {sig.initial_value}")
            print(f"    factor={sig.factor}, offset={sig.offset}")
            print(f"    is_signed={sig.is_signed}")

# Now test: XLSX roundtrip from org.dbc
print("\n=== XLSX roundtrip from org.dbc ===")
import canmatrix.formats.xlsx as xlsx
import tempfile

tmp_xlsx = os.path.join(tempfile.gettempdir(), 'org_test.xlsx')
xlsx.dump(db, tmp_xlsx)

db2 = xlsx.load(tmp_xlsx)

for frame2 in db2.frames:
    for sig2 in frame2.signals:
        if sig2.name in targets:
            print(f"\n  {sig2.name} (after XLSX):")
            print(f"    attributes: {sig2.attributes}")
            print(f"    initial_value: {sig2.initial_value}")

# Check raw BA_ lines for target signals
print("\n=== Raw BA_ lines for target signals in org.dbc ===")
for line in content.split(b'\n'):
    decoded = line.decode('utf-8', errors='replace').strip()
    if decoded.startswith('BA_') and 'GenSigStartValue' in decoded:
        for t in targets:
            if t in decoded:
                print(f"  {decoded}")
