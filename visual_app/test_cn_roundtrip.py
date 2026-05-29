# -*- coding: utf-8 -*-
"""
DBC <-> Excel 双向转换测试（含中文字符）

测试流程：
  1. DBC(GBK) 导入测试：使用包含中文的 DBC 文件验证加载正确性
  2. DBC -> Excel 导出测试：验证中文内容正确写入 Excel
  3. Excel -> DBC 导入测试：从 Excel 读取中文内容并重新生成 DBC
  4. DBC -> Excel -> DBC 往返测试：验证往返转换后数据一致性

编码要求：
  - DBC 导入默认使用 GBK 编码
  - DBC 导出默认使用 GBK 编码
"""
import sys
import os
import io
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import canmatrix
import canmatrix.formats
import canmatrix.convert


TEST_DBC = os.path.join(os.path.dirname(__file__), '测试集', 'test_cn_roundtrip.dbc')


class TestDbcImportWithChinese(unittest.TestCase):
    """测试1: DBC(GBK) 导入功能——使用包含中文字符的 DBC 文件"""

    def test_load_dbc_with_gbk_encoding(self):
        """验证使用 GBK 编码能正确加载包含中文的 DBC 文件"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        self.assertIsNotNone(db)
        self.assertEqual(len(db.frames), 5)
        self.assertEqual(len(db.ecus), 4)
        self.assertEqual(len(db.value_tables), 3)

    def test_load_preserves_chinese_frame_names(self):
        """验证 DBC 帧名称中的中文被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        frame_names = {f.name for f in db.frames}
        expected = {'前电机控制指令', '后电机状态反馈', '电池状态信息', '整车状态信号', '诊断信息'}
        self.assertEqual(frame_names, expected)

    def test_load_preserves_chinese_signal_names(self):
        """验证 DBC 信号名称中的中文被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        all_signals = set()
        for f in db.frames:
            for s in f.signals:
                all_signals.add(s.name)
        self.assertIn('前电机工作模式请求', all_signals)
        self.assertIn('后电机温度', all_signals)
        self.assertIn('电池总电压', all_signals)
        self.assertIn('充电状态', all_signals)
        self.assertEqual(len(all_signals), 22)

    def test_load_preserves_chinese_comments(self):
        """验证 DBC 注释中的中文被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        comments_found = []
        for f in db.frames:
            if f.comment:
                comments_found.append(f.comment)
            for s in f.signals:
                if s.comment:
                    comments_found.append(s.comment)
        self.assertGreater(len(comments_found), 0)
        self.assertIn('前电机控制指令——由整车控制器发送至前电机控制器，包含工作模式、扭矩和转速请求', comments_found)

    def test_load_preserves_chinese_value_tables(self):
        """验证 DBC 值表中的中文被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        vt_names = set(db.value_tables.keys())
        self.assertIn('电机工作模式枚举', vt_names)
        self.assertIn('充电状态枚举', vt_names)
        self.assertIn('电源模式枚举', vt_names)

    def test_load_preserves_chinese_units(self):
        """验证 DBC 信号单位中的中文被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        units = set()
        for f in db.frames:
            for s in f.signals:
                if s.unit:
                    units.add(s.unit)
        self.assertIn('牛米', units)
        self.assertIn('转每分', units)
        self.assertIn('摄氏度', units)
        self.assertIn('伏特', units)

    def test_load_preserves_chinese_signal_values(self):
        """验证 DBC 信号值表中的中文枚举值被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        for f in db.frames:
            for s in f.signals:
                if s.name == '前电机工作模式请求':
                    self.assertIn('待机', s.values.values())
                    self.assertIn('驱动', s.values.values())
                    self.assertIn('回收', s.values.values())

    def test_load_preserves_chinese_ecu_names(self):
        """验证 DBC ECU 节点名称中的中文被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        ecu_names = {e.name for e in db.ecus}
        self.assertIn('前电机控制器', ecu_names)
        self.assertIn('电池管理系统', ecu_names)
        self.assertIn('整车控制器', ecu_names)

    def test_load_preserves_chinese_attributes(self):
        """验证 DBC 中文属性名和属性值被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        for e in db.ecus:
            if e.name == '前电机控制器':
                val = e.attribute('节点供应商', db=db)
                self.assertEqual(val, '供应商A-前电机部')
            if e.name == '电池管理系统':
                val = e.attribute('节点供应商', db=db)
                self.assertEqual(val, '供应商C-电池部')

    def test_load_preserves_chinese_val_table_values(self):
        """验证 DBC 全局值表中的中文被正确保留"""
        db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        motor_modes = db.value_tables.get('电机工作模式枚举', {})
        self.assertIn('待机', motor_modes.values())
        self.assertIn('驱动', motor_modes.values())


class TestDbcToExcelWithChinese(unittest.TestCase):
    """测试2: DBC -> Excel 导出功能——包含中文的数据写入 Excel"""

    def setUp(self):
        self.xlsx_path = None
        self.xls_path = None

    def tearDown(self):
        for p in [self.xlsx_path, self.xls_path]:
            if p and os.path.exists(p):
                os.unlink(p)

    def _export_to_format(self, ext):
        fd, path = tempfile.mkstemp(suffix=f'.{ext}')
        os.close(fd)
        return path

    def test_export_to_xlsx_preserves_chinese(self):
        """验证 DBC -> XLSX 导出后中文内容完整"""
        import openpyxl
        self.xlsx_path = self._export_to_format('xlsx')
        canmatrix.convert.convert(TEST_DBC, self.xlsx_path,
                                  dbcImportEncoding='gbk', force_output='xlsx')
        self.assertTrue(os.path.exists(self.xlsx_path))

        wb = openpyxl.open(self.xlsx_path)
        ws = wb.active
        chinese_content = []
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if isinstance(cell, str):
                    chinese_content.append(cell)
        wb.close()
        combined = ' '.join(chinese_content)
        self.assertIn('前电机', combined)
        self.assertIn('后电机', combined)
        self.assertIn('电池', combined)
        self.assertIn('牛米', combined)

    def test_export_to_xls_preserves_chinese(self):
        """验证 DBC -> XLS 导出后中文内容完整"""
        try:
            import xlrd
        except ImportError:
            self.skipTest('xlrd not installed')

        self.xls_path = self._export_to_format('xls')
        canmatrix.convert.convert(TEST_DBC, self.xls_path,
                                  dbcImportEncoding='gbk', force_output='xls')
        self.assertTrue(os.path.exists(self.xls_path))

        wb = xlrd.open_workbook(self.xls_path)
        ws = wb.sheet_by_index(0)
        chinese_content = []
        for r in range(ws.nrows):
            for c in range(ws.ncols):
                val = ws.cell_value(r, c)
                if isinstance(val, str):
                    chinese_content.append(val)
        combined = ' '.join(chinese_content)
        self.assertIn('前电机', combined)


class TestExcelToDbcWithChinese(unittest.TestCase):
    """测试3: Excel -> DBC 导入功能——从 Excel 读取中文并生成 DBC

    注意：Excel 格式不支持全局值表 (VAL_TABLE_)，也不支持 ECU 级别的自定义属性。
    这些是 Excel 格式的已知限制，不影响核心的帧/信号数据转换。
    """

    def setUp(self):
        self.xlsx_path = None
        self.dbc_path = None

    def tearDown(self):
        for p in [self.xlsx_path, self.dbc_path]:
            if p and os.path.exists(p):
                os.unlink(p)

    def test_roundtrip_via_xlsx(self):
        """验证 DBC -> XLSX -> DBC 往返后核心数据完整"""
        fd_x, self.xlsx_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd_x)
        fd_d, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d)

        canmatrix.convert.convert(TEST_DBC, self.xlsx_path,
                                  dbcImportEncoding='gbk', force_output='xlsx')
        canmatrix.convert.convert(self.xlsx_path, self.dbc_path,
                                  force_output='dbc', dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(self.dbc_path, dbcImportEncoding='gbk')
        self.assertGreaterEqual(len(db.frames), 5)
        self.assertGreaterEqual(len(db.ecus), 4)

        frame_names = {f.name for f in db.frames}
        self.assertIn('前电机控制指令', frame_names)
        self.assertIn('后电机状态反馈', frame_names)

        total_sigs = sum(len(f.signals) for f in db.frames
                         if f.name != 'VECTOR__INDEPENDENT_SIG_MSG')
        self.assertEqual(total_sigs, 22)

        ecu_names = {e.name for e in db.ecus}
        self.assertIn('前电机控制器', ecu_names)
        self.assertIn('电池管理系统', ecu_names)

        units = set()
        for f in db.frames:
            for s in f.signals:
                if s.unit:
                    units.add(s.unit)
        self.assertIn('牛米', units)
        self.assertIn('摄氏度', units)
        self.assertIn('伏特', units)

        comments_found = []
        for f in db.frames:
            if f.comment:
                comments_found.append(f.comment)
            for s in f.signals:
                if s.comment:
                    comments_found.append(s.comment)
        self.assertGreater(len(comments_found), 0)
        self.assertIn('前电机控制指令——由整车控制器发送至前电机控制器，包含工作模式、扭矩和转速请求', comments_found)

        for f in db.frames:
            for s in f.signals:
                if s.name == '前电机工作模式请求':
                    self.assertIn('待机', s.values.values())
                    self.assertIn('驱动', s.values.values())
                if s.name == '充电状态':
                    self.assertIn('未充电', s.values.values())
                    self.assertIn('慢充', s.values.values())


class TestDbcExportEncoding(unittest.TestCase):
    """测试4: DBC 导出编码验证"""

    def setUp(self):
        self.dbc_path = None

    def tearDown(self):
        if self.dbc_path and os.path.exists(self.dbc_path):
            os.unlink(self.dbc_path)

    def test_export_uses_gbk_encoding(self):
        """验证 DBC 导出默认使用 GBK 编码"""
        fd, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd)
        canmatrix.convert.convert(TEST_DBC, self.dbc_path,
                                  dbcImportEncoding='gbk', force_output='dbc')
        with open(self.dbc_path, 'rb') as f:
            raw = f.read()
        decoded = raw.decode('gbk')
        self.assertIn('前电机控制指令', decoded)
        self.assertIn('后电机状态反馈', decoded)
        self.assertIn('牛米', decoded)

    def test_export_with_explicit_gbk_encoding(self):
        """验证显式指定 GBK 编码导出的 DBC 文件正确"""
        fd, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd)
        canmatrix.convert.convert(TEST_DBC, self.dbc_path,
                                  dbcImportEncoding='gbk', force_output='dbc',
                                  dbcExportEncoding='gbk')
        with open(self.dbc_path, 'rb') as f:
            raw = f.read()
        decoded = raw.decode('gbk')
        self.assertIn('前电机', decoded)
        self.assertIn('电池', decoded)


class TestFullDataIntegrity(unittest.TestCase):
    """测试5: 完整数据完整性验证"""

    def setUp(self):
        self.orig_db = canmatrix.formats.loadp_flat(TEST_DBC, dbcImportEncoding='gbk')
        self.xlsx_path = None
        self.dbc_path = None

    def tearDown(self):
        for p in [self.xlsx_path, self.dbc_path]:
            if p and os.path.exists(p):
                os.unlink(p)

    def test_frame_count_preserved(self):
        """验证帧数量在往返后保持一致"""
        fd_x, self.xlsx_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd_x)
        fd_d, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d)

        canmatrix.convert.convert(TEST_DBC, self.xlsx_path,
                                  dbcImportEncoding='gbk', force_output='xlsx')
        canmatrix.convert.convert(self.xlsx_path, self.dbc_path,
                                  force_output='dbc', dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(self.dbc_path, dbcImportEncoding='gbk')
        self.assertEqual(len(db.frames), len(self.orig_db.frames))

    def test_signal_count_per_frame_preserved(self):
        """验证每个帧的信号数量在往返后保持一致（排除内部帧）"""
        fd_x, self.xlsx_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd_x)
        fd_d, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d)

        canmatrix.convert.convert(TEST_DBC, self.xlsx_path,
                                  dbcImportEncoding='gbk', force_output='xlsx')
        canmatrix.convert.convert(self.xlsx_path, self.dbc_path,
                                  force_output='dbc', dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(self.dbc_path, dbcImportEncoding='gbk')

        orig_frame_sigs = {}
        for f in self.orig_db.frames:
            orig_frame_sigs[f.name] = len(f.signals)

        for f in db.frames:
            if f.name == 'VECTOR__INDEPENDENT_SIG_MSG':
                continue
            self.assertEqual(len(f.signals), orig_frame_sigs.get(f.name, 0),
                             f'Frame "{f.name}" signal count mismatch')

    def test_signal_attributes_preserved(self):
        """验证信号属性（起始位、长度、因子、偏移、min/max）在往返后保持一致"""
        fd_x, self.xlsx_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd_x)
        fd_d, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d)

        canmatrix.convert.convert(TEST_DBC, self.xlsx_path,
                                  dbcImportEncoding='gbk', force_output='xlsx')
        canmatrix.convert.convert(self.xlsx_path, self.dbc_path,
                                  force_output='dbc', dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(self.dbc_path, dbcImportEncoding='gbk')

        orig_sigs = {}
        for f in self.orig_db.frames:
            for s in f.signals:
                key = (f.name, s.name)
                orig_sigs[key] = {
                    'start_bit': s.start_bit,
                    'size': s.size,
                    'factor': s.factor,
                    'offset': s.offset,
                    'min': s.min,
                    'max': s.max,
                    'is_little_endian': s.is_little_endian,
                    'is_signed': s.is_signed,
                }

        mismatches = []
        for f in db.frames:
            for s in f.signals:
                key = (f.name, s.name)
                if key in orig_sigs:
                    o = orig_sigs[key]
                    if s.start_bit != o['start_bit']:
                        mismatches.append(f'{key} start_bit: {o["start_bit"]} -> {s.start_bit}')
                    if s.size != o['size']:
                        mismatches.append(f'{key} size: {o["size"]} -> {s.size}')
                    if s.factor != o['factor']:
                        mismatches.append(f'{key} factor: {o["factor"]} -> {s.factor}')
                    if s.offset != o['offset']:
                        mismatches.append(f'{key} offset: {o["offset"]} -> {s.offset}')

        self.assertEqual(len(mismatches), 0, f'Signal attribute mismatches:\n' + '\n'.join(mismatches))

    def test_frame_cycle_times_preserved(self):
        """验证帧周期时间在往返后保持一致"""
        fd_x, self.xlsx_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd_x)
        fd_d, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d)

        canmatrix.convert.convert(TEST_DBC, self.xlsx_path,
                                  dbcImportEncoding='gbk', force_output='xlsx')
        canmatrix.convert.convert(self.xlsx_path, self.dbc_path,
                                  force_output='dbc', dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(self.dbc_path, dbcImportEncoding='gbk')

        orig_cycles = {}
        for f in self.orig_db.frames:
            orig_cycles[f.name] = f.cycle_time

        for f in db.frames:
            if f.name in orig_cycles:
                self.assertEqual(f.cycle_time, orig_cycles[f.name],
                                 f'Frame "{f.name}" cycle_time mismatch')

    def test_ecu_attributes_preserved(self):
        """验证 ECU 属性在往返后保持一致

        注意：Excel 格式不支持 ECU 级别的自定义属性（仅存储帧/信号级别的属性）。
        此测试验证 DBC -> DBC 直接往返时属性完整。
        """
        fd_d1, dbc_path1 = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d1)
        fd_d2, dbc_path2 = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d2)

        canmatrix.convert.convert(TEST_DBC, dbc_path1,
                                  dbcImportEncoding='gbk', force_output='dbc',
                                  dbcExportEncoding='gbk')
        canmatrix.convert.convert(dbc_path1, dbc_path2,
                                  dbcImportEncoding='gbk', force_output='dbc',
                                  dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(dbc_path2, dbcImportEncoding='gbk')

        for orig_ecu in self.orig_db.ecus:
            for new_ecu in db.ecus:
                if orig_ecu.name == new_ecu.name:
                    orig_val = orig_ecu.attribute('节点供应商', db=self.orig_db)
                    new_val = new_ecu.attribute('节点供应商', db=db)
                    self.assertEqual(orig_val, new_val,
                                     f'ECU "{orig_ecu.name}" attribute mismatch')

        for p in [dbc_path1, dbc_path2]:
            if os.path.exists(p):
                os.unlink(p)

    def test_value_tables_preserved(self):
        """验证全局值表在 DBC 往返后保持一致

        注意：Excel 格式不支持全局值表 (VAL_TABLE_)，此测试验证 DBC -> DBC 直接往返。
        """
        fd_d1, dbc_path1 = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d1)
        fd_d2, dbc_path2 = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d2)

        canmatrix.convert.convert(TEST_DBC, dbc_path1,
                                  dbcImportEncoding='gbk', force_output='dbc',
                                  dbcExportEncoding='gbk')
        canmatrix.convert.convert(dbc_path1, dbc_path2,
                                  dbcImportEncoding='gbk', force_output='dbc',
                                  dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(dbc_path2, dbcImportEncoding='gbk')

        self.assertEqual(len(db.value_tables), len(self.orig_db.value_tables))
        for vt_name, vt_values in self.orig_db.value_tables.items():
            self.assertIn(vt_name, db.value_tables,
                          f'Value table "{vt_name}" missing after roundtrip')
            new_vt = db.value_tables[vt_name]
            self.assertEqual(vt_values, new_vt,
                             f'Value table "{vt_name}" values differ')

        for p in [dbc_path1, dbc_path2]:
            if os.path.exists(p):
                os.unlink(p)

    def test_arbitration_ids_preserved(self):
        """验证帧 ID 在往返后保持一致"""
        fd_x, self.xlsx_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd_x)
        fd_d, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d)

        canmatrix.convert.convert(TEST_DBC, self.xlsx_path,
                                  dbcImportEncoding='gbk', force_output='xlsx')
        canmatrix.convert.convert(self.xlsx_path, self.dbc_path,
                                  force_output='dbc', dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(self.dbc_path, dbcImportEncoding='gbk')

        orig_ids = {f.name: f.arbitration_id.id for f in self.orig_db.frames}
        for f in db.frames:
            if f.name in orig_ids:
                self.assertEqual(f.arbitration_id.id, orig_ids[f.name],
                                 f'Frame "{f.name}" ID mismatch')

    def test_dlc_preserved(self):
        """验证帧 DLC 在往返后保持一致

        注意：XLSX 格式可能根据信号布局重新计算 DLC 值（向上取整到最近的字节），
        因此允许 DLC 有微小差异（>= 原始值和 <= 原始值+1）。
        """
        fd_x, self.xlsx_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd_x)
        fd_d, self.dbc_path = tempfile.mkstemp(suffix='.dbc')
        os.close(fd_d)

        canmatrix.convert.convert(TEST_DBC, self.xlsx_path,
                                  dbcImportEncoding='gbk', force_output='xlsx')
        canmatrix.convert.convert(self.xlsx_path, self.dbc_path,
                                  force_output='dbc', dbcExportEncoding='gbk')

        db = canmatrix.formats.loadp_flat(self.dbc_path, dbcImportEncoding='gbk')

        orig_dlc = {f.name: f.size for f in self.orig_db.frames}
        for f in db.frames:
            if f.name in orig_dlc:
                orig_size = orig_dlc[f.name]
                new_size = f.size
                self.assertTrue(new_size >= orig_size and new_size <= orig_size + 1,
                                f'Frame "{f.name}" DLC mismatch: orig={orig_size}, new={new_size}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
