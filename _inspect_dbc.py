import canmatrix, canmatrix.formats, tempfile

for dbc_name in ['test', 'test_frame_attributes', 'test_signal_attributes', 'aa', 'test_frame_decoding']:
    dbc_path = f'tests/files/dbc/{dbc_name}.dbc'
    print(f"\n{'='*60}")
    print(f"=== Original DBC: {dbc_name}.dbc ===")
    print(f"{'='*60}")
    with open(dbc_path, 'r', encoding='gb2312', errors='replace') as f:
        content = f.read()
    print(content[:3000])
    
    dbs = canmatrix.formats.loadp(dbc_path)
    db = dbs['']
    
    tmp_xlsx = tempfile.mktemp(suffix='.xlsx')
    with open(tmp_xlsx, 'wb') as f:
        canmatrix.formats.dump(db, f, export_type='xlsx')
    
    dbs2 = canmatrix.formats.loadp(tmp_xlsx)
    db2 = dbs2['']
    
    tmp_dbc = tempfile.mktemp(suffix='.dbc')
    with open(tmp_dbc, 'wb') as f:
        canmatrix.formats.dump(db2, f, export_type='dbc')
    
    print(f"\n--- Generated DBC ---")
    with open(tmp_dbc, 'r', encoding='gb2312', errors='replace') as f:
        content = f.read()
    print(content[:3000])
