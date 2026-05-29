# -*- coding: utf-8 -*-
import sys
import os
import io
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import canmatrix
import canmatrix.formats
import canmatrix.convert

def test_excel_to_dbc_initial_value():
    """验证 Excel Signal Default → DBC initial value 映射"""
    print('=' * 60)
    print('验证: Excel Signal Default → DBC initial value')
    print('=' * 60)

    src_dbc = os.path.join(os.path.dirname(__file__), u'测试集',
                           u'A8R_DCU_IPStoCCU_org.dbc')

    db_orig = canmatrix.formats.loadp_flat(src_dbc)
    print(f'\n原始 DBC: {len(db_orig.frames)} frames')

    orig_values = {}
    for frame in db_orig.frames:
        for sig in frame.signals:
            key = f'{frame.name}::{sig.name}'
            orig_values[key] = sig.initial_value

    for fmt in ['xlsx', 'xls']:
        print(f'\n--- {fmt} 往返测试 ---')

        fd_x, tmp_x = tempfile.mkstemp(suffix=f'.{fmt}')
        fd_d, tmp_d = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_x)
        os.close(fd_d)

        try:
            canmatrix.convert.convert(src_dbc, tmp_x)

            try:
                db_mid = canmatrix.formats.loadp_flat(tmp_x)
            except Exception as e:
                print(f'  SKIP ({fmt} load): {e}')
                continue

            canmatrix.convert.convert(tmp_x, tmp_d,
                                      force_output='dbc',
                                      dbcExportEncoding='utf-8')

            db_final = canmatrix.formats.loadp_flat(tmp_d)

            mismatches = []
            for frame in db_final.frames:
                for sig in frame.signals:
                    key = f'{frame.name}::{sig.name}'
                    if key in orig_values:
                        o, g = orig_values[key], sig.initial_value
                        if o != g:
                            mismatches.append((key, o, g))

            if mismatches:
                print(f'  FAIL: {len(mismatches)} mismatches')
                for k, o, g in mismatches[:5]:
                    print(f'    {k}: {o} -> {g}')
            else:
                print(f'  PASS: 所有 initial_value 一致')

        finally:
            for p in [tmp_x, tmp_d]:
                if os.path.exists(p):
                    os.unlink(p)

    print('\n完成')

if __name__ == '__main__':
    test_excel_to_dbc_initial_value()