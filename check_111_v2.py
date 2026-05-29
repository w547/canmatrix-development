import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

path = os.path.join(os.path.dirname(__file__), 'visual_app', '测试集', '111.dbc')
with open(path, 'rb') as f:
    data = f.read()
text = data.decode('gbk', errors='replace')

# Find GenSigStartValue definition and BA_ lines
for i, line in enumerate(text.split('\n')):
    if 'GenSigStartValue' in line:
        print(f"L{i+1}: {line.strip()}")
    if 'BA_DEF_ SG_' in line and 'GenSig' in line:
        print(f"L{i+1}: {line.strip()}")
    if 'BA_DEF_DEF_' in line and 'GenSig' in line:
        print(f"L{i+1}: {line.strip()}")

# Also check what BA_DEF_ lines exist
print("\n--- All signal BA_DEF_ lines ---")
for i, line in enumerate(text.split('\n')):
    if line.startswith('BA_DEF_ SG_'):
        print(f"L{i+1}: {line.strip()}")

# Check GenSigStartValue BA_ lines for target signals
print("\n--- GenSigStartValue BA_ for target signals ---")
frame_id = None
for i, line in enumerate(text.split('\n')):
    if line.startswith('BO_ 862 '):
        frame_id = '862'
    if 'GenSigStartValue' in line and 'SG_' in line and line.startswith('BA_'):
        if 'CRM_ChargeNo' in line or 'BRM_BatteryManufacture' in line:
            print(f"L{i+1}: {line.strip()}")
