import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import tempfile
import io
import canmatrix
import canmatrix.formats.dbc as dbc
import canmatrix.formats.xlsx as xlsx

# Test with INT 0 0 define (matching user's actual scenario)
dbc_content = '''VERSION ""

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
 SG_ TestSignal : 0|32@1- (1,0) [0|0] "" Node1

BA_DEF_ SG_ "GenSigStartValue" INT 0 0;
BA_DEF_DEF_ "GenSigStartValue" 0;
BA_ "GenSigStartValue" SG_ 256 TestSignal -2147483648;
'''

print("=== STEP 1: Parse DBC (INT 0 0) ===")
db = dbc.load(io.BytesIO(dbc_content.encode('utf-8')))

frame = db.frames[0]
sig = frame.signals[0]
print(f"Signal: {sig.name}")
print(f"  attributes={sig.attributes}")
print(f"  GenSigStartValue in attributes: '{sig.attributes.get('GenSigStartValue')}'")
print(f"  initial_value={sig.initial_value}")
if 'GenSigStartValue' in db.signal_defines:
    sd = db.signal_defines['GenSigStartValue']
    print(f"  signal_defines: type={sd.type}, min={sd.min}, max={sd.max}, defaultValue={repr(sd.defaultValue)}")

print("\n=== STEP 2: Dump DBC directly to see what dbc.dump produces ===")
dbc_bytes = io.BytesIO()
dbc.dump(db, dbc_bytes)
dbc_out = dbc_bytes.getvalue().decode('utf-8')
print(dbc_out)

print("\n=== STEP 3: XLSX roundtrip ===")
tmp_xlsx = os.path.join(tempfile.gettempdir(), 'test_neg_int00.xlsx')
xlsx.dump(db, tmp_xlsx)

db2 = xlsx.load(tmp_xlsx)
frame2 = db2.frames[0]
sig2 = frame2.signals[0]
print(f"Signal: {sig2.name}")
print(f"  attributes={sig2.attributes}")
print(f"  GenSigStartValue in attributes: '{sig2.attributes.get('GenSigStartValue')}'")
print(f"  initial_value={sig2.initial_value}")

print("\n=== STEP 4: Dump DBC after XLSX roundtrip ===")
dbc_bytes2 = io.BytesIO()
dbc.dump(db2, dbc_bytes2)
dbc_out2 = dbc_bytes2.getvalue().decode('utf-8')
print(dbc_out2)

print("\n=== STEP 5: Test with -2 and INT 0 0 ===")
dbc_content2 = '''VERSION ""

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
 SG_ TestSignal : 0|32@1- (1,0) [0|0] "" Node1

BA_DEF_ SG_ "GenSigStartValue" INT 0 0;
BA_DEF_DEF_ "GenSigStartValue" 0;
BA_ "GenSigStartValue" SG_ 256 TestSignal -2;
'''

db3 = dbc.load(io.BytesIO(dbc_content2.encode('utf-8')))
sig3 = db3.frames[0].signals[0]
print(f"Signal: {sig3.name}")
print(f"  GenSigStartValue: '{sig3.attributes.get('GenSigStartValue')}'")
print(f"  initial_value={sig3.initial_value}")

tmp_xlsx2 = os.path.join(tempfile.gettempdir(), 'test_neg2_int00.xlsx')
xlsx.dump(db3, tmp_xlsx2)
db4 = xlsx.load(tmp_xlsx2)
sig4 = db4.frames[0].signals[0]
print(f"After XLSX roundtrip:")
print(f"  GenSigStartValue: '{sig4.attributes.get('GenSigStartValue')}'")
print(f"  initial_value={sig4.initial_value}")

dbc_bytes3 = io.BytesIO()
dbc.dump(db4, dbc_bytes3)
print(dbc_bytes3.getvalue().decode('utf-8'))
