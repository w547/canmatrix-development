import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Read 111.dbc with different encodings
path = os.path.join(os.path.dirname(__file__), 'visual_app', '测试集', '111.dbc')

for enc in ['gbk', 'gb2312', 'gb18030', 'utf-8', 'latin-1', 'cp1252']:
    try:
        with open(path, 'rb') as f:
            data = f.read()
        text = data.decode(enc, errors='replace')
        if 'CRM_ChargeNo' in text:
            print(f"Encoding: {enc} (success)")
            targets = ['CRM_ChargeNo', 'BRM_BatteryManufacture', 'BMS_FastChgInfo']
            for i, line in enumerate(text.split('\n')):
                if any(t in line for t in targets):
                    print(f"  L{i+1}: {line.strip()}")
            break
    except Exception as e:
        print(f"Encoding {enc}: {e}")
