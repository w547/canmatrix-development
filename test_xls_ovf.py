import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import canmatrix
import canmatrix.formats
import xlrd

gen_val = '-2147483648'
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

BU_: ECU1

BO_ 100 TestFrame: 8 ECU1
 SG_ Sig1 : 0|32@1- (1,0) [{gen_val}|2147483647] "" ECU1

BA_DEF_ SG_ "GenSigStartValue" INT -2147483648 2147483647;

BA_ "GenSigStartValue" SG_ 100 Sig1 {gen_val};

BA_DEF_DEF_ "GenSigStartValue" 0;
'''

dbc_path = 'test_xls_ovf.dbc'
xls_path = 'test_xls_ovf.xls'

with open(dbc_path, 'w') as f:
    f.write(dbc_content)

dbs = canmatrix.formats.loadp(dbc_path)
canmatrix.formats.dumpp(dbs, xls_path)

# Read back with xlrd
wb = xlrd.open_workbook(xls_path)
sh = wb.sheet_by_index(0)
headers = [sh.cell_value(0, i) for i in range(sh.ncols)]

gsv_idx = headers.index('GenSigStartValue')
sname_idx = headers.index('Signal Name')
sdefault_idx = headers.index('Signal Default')

for r in range(1, sh.nrows):
    print(f"Signal: {sh.cell_value(r, sname_idx)}")
    gsv = sh.cell_value(r, gsv_idx)
    sd = sh.cell_value(r, sdefault_idx)
    ctype_gsv = sh.cell_type(r, gsv_idx)
    ctype_sd = sh.cell_type(r, sdefault_idx)
    print(f"  GenSigStartValue: {repr(gsv)} (xlrd type: {ctype_gsv})")
    print(f"  Signal Default:   {repr(sd)} (xlrd type: {ctype_sd})")
    # xlrd types: 0=empty, 1=text, 2=number, 3=date, 4=bool, 5=error

for f in [dbc_path, xls_path]:
    try:
        os.remove(f)
    except:
        pass