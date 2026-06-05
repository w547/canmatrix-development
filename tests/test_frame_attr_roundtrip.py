# -*- coding: utf-8 -*-
import io
import os
import sys
import tempfile

import canmatrix
import canmatrix.formats.dbc
import canmatrix.formats.xls
import canmatrix.formats.xlsx


TEST_DBC = os.path.join(os.path.dirname(__file__), "files", "dbc", "test_frame_attributes.dbc")


def load_dbc(path):
    with open(path, "rb") as f:
        db = canmatrix.formats.dbc.load(f)
    return db


def dump_xls(db):
    f = io.BytesIO()
    canmatrix.formats.xls.dump(db, f)
    return f.getvalue()


def load_xls(data):
    f = io.BytesIO(data)
    db = canmatrix.formats.xls.load(f)
    return db


def dump_xlsx(db, path):
    canmatrix.formats.xlsx.dump(db, path)


def load_xlsx(path):
    with open(path, "rb") as f:
        db = canmatrix.formats.xlsx.load(f)
    return db


def get_frame_attrs(frame):
    return {
        "DiagRequest": frame.attribute("DiagRequest"),
        "DiagResponse": frame.attribute("DiagResponse"),
        "DiagState": frame.attribute("DiagState"),
        "NmMessage": frame.attribute("NmMessage"),
        "GenMsgILSupport": frame.attribute("GenMsgILSupport"),
        "GenMsgSendType": frame.attribute("GenMsgSendType"),
        "GenMsgDelayTime": frame.attribute("GenMsgDelayTime"),
        "GenMsgCycleTimeFast": frame.attribute("GenMsgCycleTimeFast"),
        "GenMsgNoOfRepetitions": frame.attribute("GenMsgNoOfRepetitions"),
        "CANFD_BRS": frame.attribute("CANFD_BRS"),
        "VFrameFormat": frame.attribute("VFrameFormat"),
        "is_fd": frame.is_fd,
    }


def attr_roundtrip_check(db_original, db_roundtrip):
    for orig_frame in db_original.frames:
        rt_frame = db_roundtrip.frame_by_id(orig_frame.arbitration_id)
        assert rt_frame is not None, f"Frame {orig_frame.name} not found after round-trip"

        orig_attrs = get_frame_attrs(orig_frame)
        rt_attrs = get_frame_attrs(rt_frame)

        for attr_name, orig_val in orig_attrs.items():
            rt_val = rt_attrs[attr_name]
            if attr_name == "is_fd":
                assert orig_val == rt_val, \
                    f"Frame {orig_frame.name}: is_fd mismatch: orig={orig_val} vs rt={rt_val}"
            elif orig_val is not None and rt_val is not None:
                assert str(orig_val) == str(rt_val), \
                    f"Frame {orig_frame.name}: attr '{attr_name}' mismatch: orig='{orig_val}' vs rt='{rt_val}'"
            elif orig_val is not None and rt_val is None:
                raise AssertionError(
                    f"Frame {orig_frame.name}: attr '{attr_name}' LOST in round-trip: orig='{orig_val}'"
                )


def test_xls_roundtrip():
    """Test DBC -> XLS -> DBC round-trip preserves all frame attributes."""
    db_original = load_dbc(TEST_DBC)
    xls_data = dump_xls(db_original)
    db_roundtrip = load_xls(xls_data)
    attr_roundtrip_check(db_original, db_roundtrip)
    print("PASS: XLS round-trip test - all frame attributes preserved")


def test_xlsx_roundtrip():
    """Test DBC -> XLSX -> DBC round-trip preserves all frame attributes."""
    db_original = load_dbc(TEST_DBC)

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        xlsx_path = tmp.name

    try:
        dump_xlsx(db_original, xlsx_path)
        db_roundtrip = load_xlsx(xlsx_path)
    finally:
        if os.path.exists(xlsx_path):
            os.unlink(xlsx_path)

    attr_roundtrip_check(db_original, db_roundtrip)
    print("PASS: XLSX round-trip test - all frame attributes preserved")


def test_xls_expected_values():
    """Verify specific attribute values are correct in generated XLS."""
    db = load_dbc(TEST_DBC)

    diag_frame = db.frame_by_id(canmatrix.ArbitrationId(256))
    assert diag_frame is not None
    assert str(diag_frame.attribute("DiagRequest")) == "1"
    assert str(diag_frame.attribute("DiagResponse")) == "1"
    assert str(diag_frame.attribute("DiagState")) == "DiagState_Default"
    assert str(diag_frame.attribute("GenMsgDelayTime")) == "10"

    nm_frame = db.frame_by_id(canmatrix.ArbitrationId(512))
    assert nm_frame is not None
    assert str(nm_frame.attribute("NmMessage")) == "NmActive"
    assert str(nm_frame.attribute("GenMsgDelayTime")) == "100"

    il_frame = db.frame_by_id(canmatrix.ArbitrationId(768))
    assert il_frame is not None
    assert str(il_frame.attribute("GenMsgILSupport")) == "Yes"
    assert str(il_frame.attribute("GenMsgCycleTimeFast")) == "20"
    assert str(il_frame.attribute("GenMsgNoOfRepetitions")) == "3"
    assert str(il_frame.attribute("GenMsgDelayTime")) == "50"

    fd_frame = db.frame_by_id(canmatrix.ArbitrationId(1024))
    assert fd_frame is not None
    assert str(fd_frame.attribute("CANFD_BRS")) == "On"
    assert str(fd_frame.attribute("GenMsgCycleTimeFast")) == "10"
    assert str(fd_frame.attribute("GenMsgNoOfRepetitions")) == "1"
    assert str(fd_frame.attribute("GenMsgDelayTime")) == "200"
    assert fd_frame.is_fd is True

    fd_small_frame = db.frame_by_id(canmatrix.ArbitrationId(1280))
    assert fd_small_frame is not None
    assert str(fd_small_frame.attribute("CANFD_BRS")) == "On"
    assert fd_small_frame.is_fd is True
    assert fd_small_frame.size == 8

    print("PASS: XLS expected values test - all specific attributes verified")


def test_xls_export_contains_columns():
    """Verify that the XLS export actually contains the new column headers and values."""
    db = load_dbc(TEST_DBC)
    xls_data = dump_xls(db)

    import xlrd
    wb = xlrd.open_workbook(file_contents=xls_data)
    sh = wb.sheet_by_index(0)

    headers = [sh.cell(0, i).value for i in range(sh.ncols)]

    expected_headers = [
        "DiagRequest", "DiagResponse", "DiagState", "NmMessage",
        "GenMsgILSupport", "GenMsgCycleTimeFast", "GenMsgNoOfRepetitions", "CANFD_BRS", "ID-Format"
    ]
    for h in expected_headers:
        assert h in headers, f"Column '{h}' not found in XLS headers: {headers}"

    found_diag = False
    found_nm = False
    found_il = False
    found_fd = False

    for row_num in range(1, sh.nrows):
        row_data = [sh.cell(row_num, i).value for i in range(sh.ncols)]
        if 256 in row_data or "DiagFrame" in str(row_data):
            diag_request_idx = headers.index("DiagRequest")
            if sh.cell(row_num, diag_request_idx).value:
                found_diag = True
        if 512 in row_data or "NmFrame" in str(row_data):
            nm_msg_idx = headers.index("NmMessage")
            if sh.cell(row_num, nm_msg_idx).value:
                found_nm = True
        if 768 in row_data or "InteractionFrame" in str(row_data):
            il_idx = headers.index("GenMsgILSupport")
            if sh.cell(row_num, il_idx).value:
                found_il = True
        if 1024 in row_data or "CanFDFrame" in str(row_data):
            brs_idx = headers.index("CANFD_BRS")
            if sh.cell(row_num, brs_idx).value:
                found_fd = True

    assert found_diag, "DiagRequest value not found in XLS data rows"
    assert found_nm, "NmMessage value not found in XLS data rows"
    assert found_il, "GenMsgILSupport value not found in XLS data rows"
    assert found_fd, "CANFD_BRS value not found in XLS data rows"

    print("PASS: XLS column headers and values verified")


def main():
    print("=" * 60)
    print("Frame Attribute Round-Trip Test Suite")
    print("=" * 60)

    test_xls_expected_values()
    test_xls_export_contains_columns()
    test_xls_roundtrip()
    test_xlsx_roundtrip()

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()