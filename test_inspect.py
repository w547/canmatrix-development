import sys, os, logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from canmatrix.formats import dbc
import tempfile

test_dbc = '''VERSION ""

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

BU_: Tester

BO_ 862 BMS_FastChgInfo: 48 BMS
 SG_ CRM_ChargeNo : 39|32@0+ (1,0) [0|4.29497E+009] "" Tester

BA_DEF_ SG_ "GenSigStartValue" INT 0 0;
BA_DEF_DEF_ "GenSigStartValue" 0;
BA_ "GenSigStartValue" SG_ 862 CRM_ChargeNo -2;
'''

tmpdir = tempfile.mkdtemp()
dbc_in = os.path.join(tmpdir, 'test.dbc')

with open(dbc_in, 'w') as f:
    f.write(test_dbc)

with open(dbc_in, 'r') as f:
    print("=== DBC file content ===")
    print(f.read())

print("\n=== Loading DBC ===")
db = dbc.load(dbc_in)
print(f"Frames: {len(db.frames)}")
print(f"ECUs: {len(db.ecus)}")
if db.frames:
    for f in db.frames:
        print(f"  Frame: {f.name}, signals: {len(f.signals)}")
        for s in f.signals:
            print(f"    Signal: {s.name}, iv={s.initial_value}, attrs={dict(s.attributes)}")

import shutil
shutil.rmtree(tmpdir)
