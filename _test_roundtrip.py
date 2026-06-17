import canmatrix
import canmatrix.formats
import os, tempfile

for dbc_name in ['test_frame_attributes', 'test_signal_attributes', 'test']:
    dbc_path = f'tests/files/dbc/{dbc_name}.dbc'
    if not os.path.exists(dbc_path):
        print(f'SKIP {dbc_path} (not found)')
        continue
    print(f'\n=== Testing {dbc_name}.dbc ===')
    
    dbs = canmatrix.formats.loadp(dbc_path)
    db = dbs['']
    print(f'Original: {len(db.frames)} frames, {sum(len(f.signals) for f in db.frames)} signals')
    for f in db.frames:
        print(f'  Frame: {f.name}, ID={f.arbitration_id}, signals={len(f.signals)}, transmitters={f.transmitters}')

    tmp_xlsx = tempfile.mktemp(suffix='.xlsx')
    with open(tmp_xlsx, 'wb') as f:
        canmatrix.formats.dump(db, f, export_type='xlsx')
    
    dbs2 = canmatrix.formats.loadp(tmp_xlsx)
    db2 = dbs2['']
    print(f'After XLSX load: {len(db2.frames)} frames, {sum(len(f.signals) for f in db2.frames)} signals')
    for f in db2.frames:
        print(f'  Frame: {f.name}, ID={f.arbitration_id}, signals={len(f.signals)}, transmitters={f.transmitters}')

    tmp_dbc = tempfile.mktemp(suffix='.dbc')
    with open(tmp_dbc, 'wb') as f:
        canmatrix.formats.dump(db2, f, export_type='dbc')
    
    try:
        dbs3 = canmatrix.formats.loadp(tmp_dbc)
        db3 = dbs3['']
        print(f'DBC reload OK: {len(db3.frames)} frames, {sum(len(f.signals) for f in db3.frames)} signals')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'DBC reload FAILED: {e}')
        print('DBC content:')
        with open(tmp_dbc, 'r') as f:
            print(f.read())
