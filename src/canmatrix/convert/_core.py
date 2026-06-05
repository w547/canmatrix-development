# -*- coding: utf-8 -*-
# Copyright (c) 2013, Eduard Broecker
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that
# the following conditions are met:
#
#    Redistributions of source code must retain the above copyright notice, this list of conditions and the
#    following disclaimer.
#    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

import copy
import logging
import typing

import canmatrix
import canmatrix.copy
import canmatrix.formats

logger = logging.getLogger(__name__)


def fix_mojibake_gbk(text):  # type: (str) -> str
    """Fix double-encoded Chinese text (GBK bytes interpreted as Latin-1).

    When Chinese text is encoded as GBK bytes, and those bytes are then
    misinterpreted as Latin-1/ISO-8859-1 characters, the result is mojibake.
    This function reverses that: text.encode('latin-1').decode('gbk')

    Example: 'ºóµç»ú¹¤×÷Ä£Ê½ÇëÇó' -> '后电机工作模式请求'

    :param text: The potentially double-encoded text
    :return: Fixed text if double-encoding is detected, otherwise original text
    """
    if not text or not isinstance(text, str):
        return text
    try:
        fixed = text.encode('latin-1').decode('gbk')
        cjk_orig = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        cjk_fixed = sum(1 for c in fixed if '\u4e00' <= c <= '\u9fff')
        if cjk_fixed > cjk_orig:
            return fixed
        return text
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def apply_mojibake_fix_to_db(db):  # type: (canmatrix.CanMatrix) -> None
    """Fix double-encoded Chinese in all text fields of a CanMatrix database.

    Applies fix_mojibake_gbk to: signal comments, frame comments, ECU comments,
    signal units, and value table entries.
    """
    for frame in db.frames:
        if frame.comment:
            frame.comment = fix_mojibake_gbk(frame.comment)
        for sig in frame.signals:
            if sig.comment:
                sig.comment = fix_mojibake_gbk(sig.comment)
            if sig.unit:
                sig.unit = fix_mojibake_gbk(sig.unit)
            for key, val in list(sig.values.items()):
                if isinstance(val, str):
                    sig.values[key] = fix_mojibake_gbk(val)

    for ecu in db.ecus:
        if ecu.comment:
            ecu.comment = fix_mojibake_gbk(ecu.comment)

    for name, table in db.value_tables.items():
        for key, val in list(table.items()):
            if isinstance(val, str):
                db.value_tables[name][key] = fix_mojibake_gbk(val)


def convert_pdu_container_to_multiplexed(frame):  # type: (canmatrix.Frame) -> canmatrix.Frame
    new_frame = copy.deepcopy(frame)
    if not frame.is_pdu_container:
        return new_frame
    header_id_signal = new_frame.signal_by_name("Header_ID")
    header_dlc_signal = new_frame.signal_by_name("Header_DLC")
    if header_id_signal is not None and header_dlc_signal is not None:
        header_id_signal.multiplex_setter("Multiplexor")
        bit_offset = header_id_signal.size + header_dlc_signal.size
    else:
        bit_offset = 0
    for sg_id, pdu in enumerate(new_frame.pdus):
        mux_val = pdu.id
        signal_group = []
        for signal in pdu.signals:
            signal.multiplex_setter(mux_val)
            signal.start_bit += bit_offset
            signal_group.append(signal.name)
            new_frame.add_signal(signal)
        signal_group_name = pdu.name
        if len(signal_group_name) == 0:
            signal_group_name = "HEARDER_ID_" + str(mux_val)
        new_frame.add_signal_group(signal_group_name, sg_id + 1, signal_group)
    new_frame.pdus = []
    return new_frame


def _extract_items(source_db, options):
    db = None

    if options.get('ecus', False):
        ecu_list = options['ecus'].split(',')
        db = canmatrix.CanMatrix()
        for ecu in ecu_list:
            direction = None
            if ":" in ecu:
                ecu, direction = ecu.split(":")
            canmatrix.copy.copy_ecu_with_frames(ecu, source_db, db, rx=(direction != "tx"), tx=(direction != "rx"))
    if options.get('frames', False):
        frame_list = options['frames'].split(',')
        db = canmatrix.CanMatrix() if db is None else db
        for frame_name in frame_list:
            frame_to_copy = source_db.frame_by_name(frame_name)
            canmatrix.copy.copy_frame(frame_to_copy.arbitration_id, source_db, db)
    if options.get('signals', False):
        signal_list = options['signals'].split(',')
        db = canmatrix.CanMatrix() if db is None else db
        for signal_name in signal_list:
            canmatrix.copy.copy_signal(signal_name, source_db, db)

    if db is None:
        db = source_db
    return db


def convert(infile, out_file_name, **options):  # type: (str, str, **str) -> None
    logger.info(f"Importing " + infile + " ...")
    dbs = canmatrix.formats.loadp(infile, **options)
    logger.info("Import Done")

    if options.get('fixMojibake'):
        for name in dbs:
            apply_mojibake_fix_to_db(dbs[name])
        logger.info("Mojibake fix applied")

    from canmatrix.convert import create_default_handler_registry
    registry = create_default_handler_registry()

    logger.info("Exporting " + out_file_name + " ...")
    out_dbs = {}  # type: typing.Dict[str, canmatrix.CanMatrix]
    for name in dbs:
        db = _extract_items(dbs[name], options)

        registry.execute_all(db, options)

        logger.debug(f"{name}")
        logger.info("%d Frames found" % (db.frames.__len__()))

        out_dbs[name] = db

    if 'force_output' in options and options['force_output'] is not None:
        canmatrix.formats.dumpp(out_dbs, out_file_name, export_type=options[
                                'force_output'], **options)
    else:
        canmatrix.formats.dumpp(out_dbs, out_file_name, **options)
    logger.info("Export Done")
