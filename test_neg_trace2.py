import sys
import os
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from canmatrix.formats import dbc

# Simulate the exact scenario: DBC with INT 0 0 define and 4294967294 value
test_dbc = '''VERSION "test"

NS_ :

BS_:

BU_: ECU1

BO_ 862 TestFrame: 8 ECU1
 SG_ TestSig1 : 0|32@0+ (1,0) [0|4294970000] "" Tester

BA_DEF_ SG_ "GenSigStartValue" INT 0 0;
BA_DEF_DEF_ "GenSigStartValue" 0;

BA_ "GenSigStartValue" SG_ 862 TestSig1 4294967294;
'''

print("=" * 60)
print("STEP 1: Import DBC with 4294967294 + INT 0 0 define")
db = dbc.load(io.BytesIO(test_dbc.encode('utf-8')))

for frame in db.frames:
    for sig in frame.signals:
        print(f"  {sig.name}:")
        print(f"    attributes: {sig.attributes}")
        print(f"    initial_value: {sig.initial_value} (type={type(sig.initial_value).__name__})")
        print(f"    is_signed: {sig.is_signed}, size: {sig.size}")

# Trace: what happens to the value 4294967294?
print("\n" + "=" * 60)
print("STEP 2: Trace value transformation")
val = 4294967294
print(f"  Raw value: {val}")
print(f"  As signed 32-bit: {val - (1 << 32)}")
print(f"  As hex: {hex(val)}")

# Now test: what if we interpret GenSigStartValue as signed based on signal size?
print("\n" + "=" * 60)
print("STEP 3: What SHOULD happen (signed interpretation)")
for sig_size in [8, 16, 32]:
    max_signed = 1 << (sig_size - 1)
    max_unsigned = (1 << sig_size) - 1
    test_vals = [4294967294, 4294967295, 2147483648, 65534, 254, -2, -2147483648]
    for tv in test_vals:
        if tv >= 0 and tv <= max_unsigned:
            signed = tv
            if tv >= max_signed:
                signed = tv - (1 << sig_size)
            print(f"  {sig_size}-bit: {tv} -> signed={signed}")

# Now let's look at what happens with the actual 111.dbc 
print("\n" + "=" * 60)
print("STEP 4: What happens when DBC has NO GenSigStartValue for signal")
dbc_no_gsv = '''VERSION "test"

NS_ :

BS_:

BU_: ECU1

BO_ 862 TestFrame: 8 ECU1
 SG_ TestSig1 : 0|32@0+ (1,0) [0|4294970000] "" Tester

BA_DEF_ SG_ "GenSigStartValue" INT 0 0;
BA_DEF_DEF_ "GenSigStartValue" 0;
'''
db2 = dbc.load(io.BytesIO(dbc_no_gsv.encode('utf-8')))
for frame in db2.frames:
    for sig in frame.signals:
        print(f"  {sig.name}:")
        print(f"    attributes: {sig.attributes}")
        print(f"    initial_value: {sig.initial_value}")

# Export to DBC
out = io.BytesIO()
dbc.dump(db2, out)
out.seek(0)
for line in out.read().decode('utf-8').split('\n'):
    if 'GenSigStartValue' in line:
        print(f"  EXPORT: {line.strip()}")

# What if we take the exported DBC (with GenSigStartValue 0) and convert to Excel and back?
print("\n" + "=" * 60)
print("STEP 5: DBC->Excel->DBC with GenSigStartValue=0 from default")
from canmatrix.formats import xlsx

xlsx_out = io.BytesIO()
xlsx.dump(db2, xlsx_out)
xlsx_out.seek(0)

db3 = xlsx.load(xlsx_out)
for frame in db3.frames:
    for sig in frame.signals:
        print(f"  After XLSX roundtrip: {sig.name}: GenSigStartValue='{sig.attributes.get('GenSigStartValue')}', initial_value={sig.initial_value}")

# Export to DBC
out2 = io.BytesIO()
dbc.dump(db3, out2)
out2.seek(0)
for line in out2.read().decode('utf-8').split('\n'):
    if 'GenSigStartValue' in line:
        print(f"  DBC EXPORT: {line.strip()}")
