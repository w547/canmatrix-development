import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

path = os.path.join(os.path.dirname(__file__), 'visual_app', '测试集', '111.dbc')
with open(path, 'rb') as f:
    data = f.read()
text = data.decode('gbk', errors='replace')

for i, line in enumerate(text.split('\n')):
    if 'GenSigStartValue' in line or ('BA_DEF_ SG_' in line and 'GenSig' in line) or ('BA_DEF_DEF_' in line and 'GenSig' in line):
        print(f"L{i+1}: {line.strip()}")
