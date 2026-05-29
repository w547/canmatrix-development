import sys
import os
import io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import canmatrix
from canmatrix.formats import dbc
import decimal

# Test: What happens with INT 0 0 define + signal that has no explicit BA_ line
# but has non-zero initial_value set from SG_ line?
# This tests if the defaultValue is None check causes data loss

print("=== Test 1: INT 0 0 define, signal with GenSigStartValue=4294967294 via BA_ ===")
dbc1 = '''VERSION ""

NS_ :
    NS_DESC_
    CM_
    BA_DEF_
    BA_
    VAL_
    CAT_DEF_
    CAT_
    FILTER
    BA_DEF_DEF_
    EV_DATA_
    ENVVAR_DATA_
    SGTYPE_
    SGTYPE_VAL_
    BA_DEF_SGTYPE_
    BA_SGTYPE_
    SIG_TYPE_REF_
    VAL_TABLE_
    SIG_GROUP_
    SIG_VALTYPE_
    SIGTYPE_VALTYPE_
    BO_TX_BU_
    BA_DEF_REL_
    BA_REL_
    BA_DEF_DEF_REL_
    BU_SG_REL_
    BU_EV_REL_
    BU_BO_REL_
    SG_MUL_VAL_

BS_:

BU_: Node1

BO_ 256 TestFrame: 8 Node1
 SG_ TestSignal : 0|32@0+ (1,0) [0|0] "" Node1

BA_DEF_ SG_ "GenSigStartValue" INT 0 0;
BA_DEF_DEF_ "GenSigStartValue" 0;
BA_ "GenSigStartValue" SG_ 256 TestSignal 4294967294;
'''

d1 = dbc.load(io.BytesIO(dbc1.encode('utf-8')))
s1 = d1.frames[0].signals[0]
print(f"  GenSigStartValue in attributes: '{s1.attributes.get('GenSigStartValue')}'")
print(f"  initial_value: {s1.initial_value}")
print(f"  is_signed: {s1.is_signed}")

# Dump to DBC - check if BA_ line is written
out1 = io.BytesIO()
dbc.dump(d1, out1)
out1_str = out1.getvalue().decode('utf-8')
ba_lines = [l for l in out1_str.split('\n') if 'GenSigStartValue' in l and 'BA_' in l and 'DEF_' not in l]
print(f"  BA_ lines in output: {ba_lines}")

print("\n=== Test 2: INT 0 0 define, signal WITHOUT explicit BA_ line, initial_value from post-processing ===")
# This tests if the defaultValue is None check prevents writing GenSigStartValue
dbc2 = '''VERSION ""

NS_ :
    NS_DESC_
    CM_
    BA_DEF_
    BA_
    VAL_
    CAT_DEF_
    CAT_
    FILTER
    BA_DEF_DEF_
    EV_DATA_
    ENVVAR_DATA_
    SGTYPE_
    SGTYPE_VAL_
    BA_DEF_SGTYPE_
    BA_SGTYPE_
    SIG_TYPE_REF_
    VAL_TABLE_
    SIG_GROUP_
    SIG_VALTYPE_
    SIGTYPE_VALTYPE_
    BO_TX_BU_
    BA_DEF_REL_
    BA_REL_
    BA_DEF_DEF_REL_
    BU_SG_REL_
    BU_EV_REL_
    BU_BO_REL_
    SG_MUL_VAL_

BS_:

BU_: Node1

BO_ 256 TestFrame: 8 Node1
 SG_ TestSignal : 0|32@0+ (1,0) [0|0] "" Node1

BA_DEF_ SG_ "GenSigStartValue" INT 0 0;
BA_DEF_DEF_ "GenSigStartValue" 0;
'''

d2 = dbc.load(io.BytesIO(dbc2.encode('utf-8')))
s2 = d2.frames[0].signals[0]
print(f"  GenSigStartValue in attributes: '{s2.attributes.get('GenSigStartValue')}'")
print(f"  initial_value: {s2.initial_value}")

# Now manually set initial_value to a non-zero value and delete GenSigStartValue
s2.initial_value = decimal.Decimal('-2147483648')
if 'GenSigStartValue' in s2.attributes:
    del s2.attributes['GenSigStartValue']
print(f"  After manual change:")
print(f"    GenSigStartValue in attributes: '{s2.attributes.get('GenSigStartValue')}'")
print(f"    initial_value: {s2.initial_value}")
print(f"    defaultValue: {repr(d2.signal_defines['GenSigStartValue'].defaultValue)}")

# Dump to DBC - this is the KEY test: will GenSigStartValue be written?
out2 = io.BytesIO()
dbc.dump(d2, out2)
out2_str = out2.getvalue().decode('utf-8')
ba_lines2 = [l for l in out2_str.split('\n') if 'GenSigStartValue' in l]
print(f"  GenSigStartValue lines in output:")
for l in ba_lines2:
    print(f"    {l}")

print("\n=== Test 3: FLOAT 0 100000000000 define (like 111.dbc), no BA_, non-zero initial_value ===")
dbc3 = '''VERSION ""

NS_ :
    NS_DESC_
    CM_
    BA_DEF_
    BA_
    VAL_
    CAT_DEF_
    CAT_
    FILTER
    BA_DEF_DEF_
    EV_DATA_
    ENVVAR_DATA_
    SGTYPE_
    SGTYPE_VAL_
    BA_DEF_SGTYPE_
    BA_SGTYPE_
    SIG_TYPE_REF_
    VAL_TABLE_
    SIG_GROUP_
    SIG_VALTYPE_
    SIGTYPE_VALTYPE_
    BO_TX_BU_
    BA_DEF_REL_
    BA_REL_
    BA_DEF_DEF_REL_
    BU_SG_REL_
    BU_EV_REL_
    BU_BO_REL_
    SG_MUL_VAL_

BS_:

BU_: Node1

BO_ 256 TestFrame: 8 Node1
 SG_ TestSignal : 0|32@0+ (1,0) [0|0] "" Node1

BA_DEF_ SG_ "GenSigStartValue" FLOAT 0 100000000000;
'''

d3 = dbc.load(io.BytesIO(dbc3.encode('utf-8')))
s3 = d3.frames[0].signals[0]
print(f"  GenSigStartValue in attributes: '{s3.attributes.get('GenSigStartValue')}'")
print(f"  initial_value: {s3.initial_value}")

s3.initial_value = decimal.Decimal('-2147483648')
if 'GenSigStartValue' in s3.attributes:
    del s3.attributes['GenSigStartValue']
print(f"  After manual change:")
print(f"    GenSigStartValue in attributes: '{s3.attributes.get('GenSigStartValue')}'")
print(f"    initial_value: {s3.initial_value}")
print(f"    defaultValue: {repr(d3.signal_defines['GenSigStartValue'].defaultValue)}")

out3 = io.BytesIO()
dbc.dump(d3, out3)
out3_str = out3.getvalue().decode('utf-8')
ba_lines3 = [l for l in out3_str.split('\n') if 'GenSigStartValue' in l]
print(f"  GenSigStartValue lines in output:")
for l in ba_lines3:
    print(f"    {l}")
