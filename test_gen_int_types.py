import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import canmatrix
from decimal import Decimal
import openpyxl

# Test INT type BA_DEF and unsigned signals
configs = [
    # (signal_signed, ba_def_type, gen_sig_val, desc)
    (True, 'FLOAT', '-2147483648', 'signed+FLOAT+INT32_MIN'),
    (True, 'INT', '-2147483648', 'signed+INT+INT32_MIN'),
    (False, 'FLOAT', '-2147483648', 'unsigned+FLOAT+INT32_MIN'),
    (False, 'INT', '-2147483648', 'unsigned+INT+INT32_MIN'),
    (True, 'INT', '-2', 'signed+INT+-2'),
    (False, 'INT', '-2', 'unsigned+INT+-2'),
]

for sig_signed, ba_type, gen_val, desc in configs:
    sign = '-' if sig_signed else '+'
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

BO_ 100 TestFrame: 8 Vector__XXX
 SG_ TestSignal : 0|32@1{sign} (1,0) [{gen_val}|2147483647] "" Vector__XXX

BA_DEF_ SG_ "GenSigStartValue" {ba_type} {gen_val} 2147483647;

BA_ "GenSigStartValue" SG_ 100 TestSignal {gen_val};

BA_DEF_DEF_ "GenSigStartValue" 0;
'''

    dbc_path = f'test_{desc.replace("+","_").replace("-","n")}.dbc'
    with open(dbc_path, 'w') as f:
        f.write(dbc_content)
    
    try:
        dbs = canmatrix.formats.loadp(dbc_path)
        for db_name, db in dbs.items():
            for frame in db.frames:
                for sig in frame.signals:
                    gsv = sig.attributes.get("GenSigStartValue")
                    iv = sig.initial_value
                    print(f"{desc:>25s} | GSV={str(gsv):>15s} | IV={str(iv):>15s} | signed={sig.is_signed}")
    except Exception as e:
        print(f"{desc:>25s} | ERROR: {e}")
    
    try:
        os.remove(dbc_path)
    except:
        pass