#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression test: verify that DBC -> Excel conversion preserves all signals.
Specifically verifies the 27 signals that were previously lost due to 
bare except: clause in dbc.py silently swallowing UnicodeDecodeError on 
non-ASCII unit strings (e.g., "℃").
"""
import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import canmatrix
import canmatrix.formats
import canmatrix.convert

# The 27 signals that were previously lost during DBC -> Excel conversion
CRITICAL_SIGNALS = [
    'MCUR_MotTemp', 'MCUR_RotorTemp', 'MCUR_IGBTTempA', 'MCUR_IGBTTempB', 'MCUR_IGBTTempC',
    'BMS_Cc2SngR',
    'DCDC_InpWtrTemp', 'DCDC_CopntTemp', 'DCDC_OutWtrTemp', 'DCDC_Oring_APS_Temp',
    'OBC_CCRes', 'OBC_CopntTemp', 'OBC_InsulationR',
    'MCUR_EOP_MOS_Temp', 'MCUR_PCBTemp',
    'Wpr_MotTemp', 'RSM_AirT', 'RSM_DewPointT', 'RSM_WinT', 'EMS_engCoolantTemp',
    'TDU_TDU_ChillerOutlT', 'TDU_BattInlT', 'TDU_BattOutlT', 'TDU_MotInletWaterT',
    'TDU_HEXInWtrT', 'TDU_LeBlowFaceAirOutlT_RHVAC', 'TDU_RiBlowFaceAirOutlT_RHVAC',
]


class TestDbcToExcelSignalPreservation(unittest.TestCase):
    """Verify all signals survive DBC -> Excel conversion."""

    def setUp(self):
        self.dbc_path = os.path.join(os.path.dirname(__file__), '测试集', 'org.dbc')

    def test_load_preserves_signals(self):
        """Step 1: Verify DBC loader parses all 27 signals."""
        db = canmatrix.formats.loadp_flat(self.dbc_path, dbcImportEncoding='utf-8')
        all_signals = set()
        for frame in db.frames:
            for sig in frame.signals:
                all_signals.add(sig.name)
        missing = [s for s in CRITICAL_SIGNALS if s not in all_signals]
        self.assertEqual(len(missing), 0,
                         f"DBC load missing signals: {missing}")

    def test_export_preserves_signals(self):
        """Step 2: Verify DBC -> XLSX export preserves all 27 signals."""
        import openpyxl

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            output_path = tmp.name

        try:
            canmatrix.convert.convert(
                self.dbc_path, output_path,
                dbcImportEncoding='utf-8',
                force_output='xlsx'
            )

            wb = openpyxl.open(output_path)
            ws = wb.active
            excel_signals = set()
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[7] and row[7] != 'Signal Name':
                    excel_signals.add(str(row[7]).strip())
            wb.close()

            missing = [s for s in CRITICAL_SIGNALS if s not in excel_signals]
            self.assertEqual(len(missing), 0,
                             f"XLSX export missing signals: {missing}")
            self.assertGreaterEqual(len(excel_signals), 1000,
                                    f"Expected 1000+ signals, got {len(excel_signals)}")
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_roundtrip_preserves_signals(self):
        """Step 3: Verify DBC -> XLSX -> DBC round-trip preserves signals."""
        import openpyxl

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_xlsx:
            xlsx_path = tmp_xlsx.name
        with tempfile.NamedTemporaryFile(suffix='.dbc', delete=False) as tmp_dbc:
            dbc_path = tmp_dbc.name

        try:
            # DBC -> XLSX
            canmatrix.convert.convert(
                self.dbc_path, xlsx_path,
                dbcImportEncoding='utf-8', force_output='xlsx'
            )
            # XLSX -> DBC
            canmatrix.convert.convert(
                xlsx_path, dbc_path,
                dbcImportEncoding='utf-8', force_output='dbc',
                dbcExportEncoding='utf-8'
            )
            # Load round-tripped DBC
            db = canmatrix.formats.loadp_flat(dbc_path, dbcImportEncoding='utf-8')
            all_signals = set()
            for frame in db.frames:
                for sig in frame.signals:
                    all_signals.add(sig.name)
            missing = [s for s in CRITICAL_SIGNALS if s not in all_signals]
            self.assertEqual(len(missing), 0,
                             f"Round-trip missing signals: {missing}")
        finally:
            for p in [xlsx_path, dbc_path]:
                if os.path.exists(p):
                    os.unlink(p)


if __name__ == '__main__':
    unittest.main(verbosity=2)
