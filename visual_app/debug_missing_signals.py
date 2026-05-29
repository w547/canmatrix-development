# -*- coding: utf-8 -*-
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import canmatrix
import canmatrix.formats
import canmatrix.convert

targets = [
    'MCUR_MotTemp', 'MCUR_RotorTemp', 'MCUR_IGBTTempA', 'MCUR_IGBTTempB', 'MCUR_IGBTTempC',
    'BMS_Cc2SngR', 'DCDC_InpWtrTemp', 'DCDC_CopntTemp', 'DCDC_OutWtrTemp', 'DCDC_Oring_APS_Temp',
    'OBC_CCRes', 'OBC_CopntTemp', 'OBC_InsulationR', 'MCUR_EOP_MOS_Temp', 'MCUR_PCBTemp',
    'Wpr_MotTemp', 'RSM_AirT', 'RSM_DewPointT', 'RSM_WinT', 'EMS_engCoolantTemp',
    'TDU_TDU_ChillerOutlT', 'TDU_BattInlT', 'TDU_BattOutlT', 'TDU_MotInletWaterT',
    'TDU_HEXInWtrT', 'TDU_LeBlowFaceAirOutlT_RHVAC', 'TDU_RiBlowFaceAirOutlT_RHVAC'
]

src_dbc = os.path.join(os.path.dirname(__file__), u'测试集', 'org.dbc')

print("=" * 60)
print("Step 1: 加载 DBC")
print("=" * 60)
db = canmatrix.formats.loadp_flat(src_dbc)
print(f"总帧数: {len(db.frames)}, 总信号数: {sum(len(f.signals) for f in db.frames)}")

found = sum(1 for f in db.frames for s in f.signals if s.name in targets)
print(f"目标信号: {found}/{len(targets)} found")

if found < 27:
    missing = [t for t in targets if not any(s.name == t for f in db.frames for s in f.signals)]
    print(f"  缺失: {missing}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Step 2: 导出 XLSX 并重新导入验证")
print("=" * 60)

tmp_xlsx = os.path.join(tempfile.gettempdir(), 'verify_org.xlsx')
canmatrix.convert.convert(src_dbc, tmp_xlsx)

db2 = canmatrix.formats.loadp_flat(tmp_xlsx)
print(f"XLSX re-import: {len(db2.frames)} frames, {sum(len(f.signals) for f in db2.frames)} signals")

found2 = sum(1 for f in db2.frames for s in f.signals if s.name in targets)
print(f"目标信号: {found2}/{len(targets)} found in XLSX export")

if found2 < 27:
    missing2 = [t for t in targets if not any(s.name == t for f in db2.frames for s in f.signals)]
    print(f"  缺失: {missing2}")
else:
    print("  ALL 27 signals present!")

os.unlink(tmp_xlsx)
print("\nDone.")