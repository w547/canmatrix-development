import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import canmatrix
from canmatrix.utils import FloatFactory
from decimal import Decimal
import openpyxl

# Test various GenSigStartValue values through the full pipeline
test_values = [
    '-2147483648',  # INT32_MIN
    '-2',           # small negative
    '-1',           # smallest negative
    '0',            # zero
    '1',            # small positive
    '2147483647',   # INT32_MAX
    '4294967294',   # near UINT32_MAX
]

dbcs = []
for val in test_values:
    dbc_content = f'''VERSION ""

NS_ : 
	NS_DESC_
	CM_
	BA_DEF_
	BA_
	VAL_
	CAT_DEF_
	CAT_
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

BS_:

BU_:

BO_ 100 Frame_{val.replace('-','n')}: 8 Vector__XXX
 SG_ SigValid : 0|32@1- (1,0) [{val}|{val}] "" Vector__XXX

BA_DEF_ SG_ "GenSigStartValue" FLOAT {val} 2147483647;

BA_ "GenSigStartValue" SG_ 100 SigValid {val};

BA_DEF_DEF_ "GenSigStartValue" 0;
'''

    dbc_path = f'test_gen_{val.replace("-","n")}.dbc'
    with open(dbc_path, 'w') as f:
        f.write(dbc_content)
    dbcs.append((dbc_path, val))

for dbc_path, expected_val in dbcs:
    try:
        dbs = canmatrix.formats.loadp(dbc_path)
        for db_name, db in dbs.items():
            for frame in db.frames:
                for sig in frame.signals:
                    gsv = sig.attributes.get("GenSigStartValue")
                    iv = sig.initial_value
                    print(f"Value={expected_val:>15s} | GSV={str(gsv):>15s} | IV={str(iv):>15s} | attr_type={type(gsv).__name__}")
    except Exception as e:
        print(f"Value={expected_val:>15s} | ERROR: {e}")

# Cleanup
for dbc_path, _ in dbcs:
    try:
        os.remove(dbc_path)
    except:
        pass