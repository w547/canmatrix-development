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

#
# this script exports xls-files from a canmatrix-object
# xls-files are the can-matrix-definitions displayed in Excel

import decimal
import logging
import typing
from builtins import *

import xlrd
import xlwt

import canmatrix
import canmatrix.formats.xls_common

logger = logging.getLogger(__name__)

# Font Size : 8pt * 20 = 160
# font = 'font: name Arial Narrow, height 160'
font = 'font: name Verdana, height 160'

if xlwt is not None:
    sty_header = xlwt.easyxf(font + ', bold on; align: vertical center, horizontal center',
                             'pattern: pattern solid, fore-colour rose')
    sty_norm = xlwt.easyxf(font + ', colour black')
    sty_first_frame = xlwt.easyxf(font + ', colour black; borders: top thin',
                                  'pattern: pattern solid, fore-colour light_turquoise')
    sty_white = xlwt.easyxf(font + ', colour white')

    # ECU Matrix-Styles
    sty_green = xlwt.easyxf('pattern: pattern solid, fore-colour light_green')
    sty_green_first_frame = xlwt.easyxf('pattern: pattern solid, fore-colour light_turquoise; borders: top thin')
    sty_sender = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25')
    sty_sender_first_frame = xlwt.easyxf('pattern: pattern solid, fore-colour light_turquoise; borders: top thin')
    sty_sender_green = xlwt.easyxf('pattern: pattern 0x04, fore-colour gray25, back-colour light_green')
    sty_sender_green_first_frame = xlwt.easyxf(
        'pattern: pattern solid, fore-colour light_turquoise; borders: top thin')


def write_ecu_matrix(ecus, sig, frame, worksheet, row, col, first_frame):
    # type: (typing.Sequence[str], typing.Optional[canmatrix.Signal], canmatrix.Frame, xlwt.Worksheet, int, int, xlwt.XFStyle) -> int
    # first-frame - style with borders:
    if first_frame == sty_first_frame:
        norm = sty_first_frame
        sender = sty_sender_first_frame
        norm_green = sty_green_first_frame
        sender_green = sty_sender_green_first_frame
    # consecutive-frame - style without borders:
    else:
        norm = sty_norm
        sender = sty_sender
        norm_green = sty_green
        sender_green = sty_sender_green

    # iterate over ECUs:
    for ecu_name in ecus:
        # every second ECU with other style
        if col % 2 == 0:
            loc_style = norm
            loc_style_sender = sender
        # every second ECU with other style
        else:
            loc_style = norm_green
            loc_style_sender = sender_green

        # write "s" "r" "r/s" if signal is sent, received or send and received by ECU
        if sig and ecu_name in sig.receivers and ecu_name in frame.transmitters:
            worksheet.write(row, col, label="r/s", style=loc_style_sender)
        elif sig and ecu_name in sig.receivers:
            worksheet.write(row, col, label="r", style=loc_style)
        elif sig:
            # For signal rows: don't fall through to frame receivers,
            # only check frame transmitters (to show "s" for sender ECU)
            if ecu_name in frame.transmitters:
                worksheet.write(row, col, label="s", style=loc_style_sender)
            else:
                worksheet.write(row, col, label="", style=loc_style)
        elif ecu_name in frame.receivers and ecu_name in frame.transmitters:
            worksheet.write(row, col, label="r/s", style=loc_style_sender)
        elif ecu_name in frame.receivers:
            worksheet.write(row, col, label="r", style=loc_style)
        elif ecu_name in frame.transmitters:
            worksheet.write(row, col, label="s", style=loc_style_sender)
        else:
            worksheet.write(row, col, label="", style=loc_style)
        col += 1
    # loop over ECUs ends here
    return col


def write_excel_line(worksheet, row, col, row_array, style):
    # type: (xlwt.Worksheet, int, int, typing.Sequence, xlwt.XFStyle) -> int
    for item in row_array:
        worksheet.write(row, col, label=item, style=style)
        col += 1
    return col


def dump(db, file, **options):
    # type: (canmatrix.CanMatrix, typing.IO, **typing.Any) -> None
    head_top = ['ID', 'Frame Name', 'DLC', 'frame.comment', 'Cycle Time [ms]', 'Launch Type', 'GenMsgDelayTime',
                'DiagRequest', 'DiagResponse', 'DiagState', 'NmMessage', 'GenMsgILSupport',
                'GenMsgCycleTimeFast', 'GenMsgNrOfRepetition', 'CANFD_BRS', 'ID-Format',
                'Signal Byte No.', 'Signal Bit No.', 'Signal Name', 'Signal Function', 'Signal Length [Bit]',
                'Signal Default', 'GenSigStartValue', 'GenSigInactiveValue', 'GenSigSendType',
                'EventCommandSignal', 'GatewayedSignals', 'GenSigInvalidValue', 'GenSigTimeoutValue',
                'Factor', 'Offset', 'Signal Not Available', 'Byteorder']
    head_tail = ['Value',   'Name / Phys. Range', 'Function / Increment Unit']

    if len(options.get("additionalSignalAttributes", "")) > 0:
        additional_signal_columns = options.get("additionalSignalAttributes").split(",")  # type: typing.List[str]
    else:
        additional_signal_columns = []  # ["attributes['DisplayDecimalPlaces']"]

    if len(options.get("additionalFrameAttributes", "")) > 0:
        additional_frame_columns = options.get("additionalFrameAttributes").split(",")  # type: typing.List[str]
    else:
        additional_frame_columns = []  # ["attributes['DisplayDecimalPlaces']"]

    motorola_bit_format = options.get("xlsMotorolaBitFormat", "msbreverse")

    workbook = xlwt.Workbook(encoding='utf8')
    workbook.set_colour_RGB(0x28, 0xDC, 0xE6, 0xF1)
#    ws_name = os.path.basename(filename).replace('.xls', '')
#    worksheet = workbook.add_sheet('K-Matrix ' + ws_name[0:22])
    worksheet = workbook.add_sheet('K-Matrix ')

    row_array = []  # type: typing.List[str]
    col = 0

    # write ECUs in first row:
    ecu_list = [ecu.name for ecu in db.ecus]

    row_array += head_top
    head_start = len(row_array)

    row_array += ecu_list
    for col in range(len(row_array)):
        worksheet.col(col).width = 1111
    tail_start = len(row_array)
    row_array += head_tail

    additional_frame_start = len(row_array)

    for col in range(tail_start, len(row_array)):
        worksheet.col(col).width = 3333

    for additionalCol in additional_frame_columns:
        row_array.append("frame." + additionalCol)
        col += 1

    for additionalCol in additional_signal_columns:
        row_array.append("signal." + additionalCol)
        col += 1

    write_excel_line(worksheet, 0, 0, row_array, sty_header)

    # set width of selected Cols
    worksheet.col(1).width = 5555
    worksheet.col(3).width = 3333
    worksheet.col(7).width = 5555
    worksheet.col(8).width = 7777
    worksheet.col(head_start).width = 1111
    worksheet.col(head_start + 1).width = 5555

    frame_hash = {}
    if db.type == canmatrix.matrix_class.CAN:
        logger.debug("Length of db.frames is %d", len(db.frames))
        for frame in db.frames:
            if frame.is_complex_multiplexed:
                logger.error("export complex multiplexers is not supported - ignoring frame %s", frame.name)
                continue
            frame_hash[int(frame.arbitration_id.id)] = frame
    else:
        frame_hash = {a.name:a for a in db.frames}


    # set row to first Frame (row = 0 is header)
    row = 1

    frame_col_count = len(canmatrix.formats.xls_common.get_frame_info(db, db.frames[0]) if db.frames else 16)


    # iterate over the frames
    for idx in sorted(frame_hash.keys()):

        frame = frame_hash[idx]

        # sort signals:
        sig_hash = {"{:02d}{}".format(sig.get_startbit(), sig.name): sig for sig in frame.signals}

        additional_frame_info = [frame.attribute(frameInfo, default="") for frameInfo in additional_frame_columns]

        # === Write frame row (frame-level columns only) ===
        frame_row = canmatrix.formats.xls_common.get_frame_info(db, frame)
        frame_row += ["" for _ in range(head_start - len(frame_row))]
        front_col = write_excel_line(worksheet, row, 0, frame_row, sty_first_frame)

        col = head_start
        col = write_ecu_matrix(ecu_list, None, frame, worksheet, row, col, sty_first_frame)

        tail_row = ["" for _ in range(len(head_tail))]
        tail_row += additional_frame_info
        tail_row += ["" for _ in additional_signal_columns]
        write_excel_line(worksheet, row, col, tail_row, sty_first_frame)
        row += 1

        if len(sig_hash) == 0:
            continue

        # === Write signal rows (signal-level columns only) ===
        empty_frame = ["" for _ in range(frame_col_count)]
        sig_style = sty_norm

        # iterate over signals
        for sig_idx in sorted(sig_hash.keys()):
            sig = sig_hash[sig_idx]

            worksheet.row(row).level = 1

            if sig.values.__len__() > 0:  # signals with value table
                val_style = sig_style
                # iterate over values in value table
                for val in sorted(sig.values.keys()):
                    write_excel_line(worksheet, row, 0, empty_frame, sig_style)

                    col = head_start
                    col = write_ecu_matrix(ecu_list, sig, frame, worksheet, row, col, sig_style)

                    # write Value
                    (frontRow, backRow) = canmatrix.formats.xls_common.get_signal(db, frame, sig, motorola_bit_format)
                    write_excel_line(worksheet, row, frame_col_count, frontRow, sig_style)
                    backRow += ["" for _ in additional_frame_columns]
                    for item in additional_signal_columns:
                        temp = getattr(sig, item, "")
                        backRow.append(temp)

                    write_excel_line(worksheet, row, col + 2, backRow, sig_style)
                    write_excel_line(worksheet, row, col, [val, sig.values[val]], val_style)

                    # no min/max here, because min/max has same col as values...
                    # next row
                    row += 1
                    sig_style = sty_norm
                    val_style = sty_norm
                # loop over values ends here
            # no value table available
            else:
                write_excel_line(worksheet, row, 0, empty_frame, sig_style)

                col = head_start
                col = write_ecu_matrix(
                    ecu_list, sig, frame, worksheet, row, col, sig_style)
                (frontRow, backRow) = canmatrix.formats.xls_common.get_signal(db, frame, sig, motorola_bit_format)
                write_excel_line(worksheet, row, frame_col_count, frontRow, sig_style)

                if float(sig.min) != 0 or float(sig.max) != 1.0:
                    backRow.insert(0, str(sig.min) + ".." + str(sig.max))  # type: ignore
                else:
                    backRow.insert(0, "")
                backRow.insert(0, "")

                backRow += ["" for _ in additional_frame_columns]
                for item in additional_signal_columns:
                    temp = getattr(sig, item, "")
                    backRow.append(temp)

                write_excel_line(worksheet, row, col, backRow, sig_style)

                # next row
                row += 1
                sig_style = sty_norm
        # loop over signals ends here
    # loop over frames ends here

    # frozen headings instead of split panes
    worksheet.set_panes_frozen(True)
    # in general, freeze after last heading row
    worksheet.set_horz_split_pos(1)
    worksheet.set_remove_splits(True)
    # save file
    workbook.save(file)


# ########################### load ###############################

def parse_value_name_column(value_name, value_str, signal_size, float_factory):
    # type: (str, str, int, typing.Callable) -> typing.Tuple
    mini = maxi = offset = None  # type: typing.Any
    value_table = dict()
    if ".." in value_name:
        (mini, maxi) = value_name.strip().split("..")
        mini = float_factory(mini)
        maxi = float_factory(maxi)
        offset = mini
        if len(value_str.strip()) > 0 and ':' in value_str:
            for line in value_str.strip().split('\n'):
                line = line.strip()
                if ':' in line:
                    key, val = line.split(':', 1)
                    try:
                        value_table[int(float(key.strip()))] = val.strip()
                    except (ValueError, TypeError):
                        pass

    elif len(value_name) > 0:
        if len(value_str.strip()) > 0:
            # Value Table
            value = int(float(value_str))
            value_table[value] = value_name
        maxi = pow(2, signal_size) - 1
        maxi = float_factory(maxi)
        mini = 0
        offset = 0
    return mini, maxi, offset, value_table


def read_additional_signal_attributes(signal, attribute_name, attribute_value):
    if not attribute_name.startswith("signal"):
        return
    if attribute_name.replace("signal.", "") in vars(signal):
        command_str = attribute_name + "="
        command_str += str(attribute_value)
        if len(str(attribute_value)) > 0:
            exec(command_str)
    else:
        pass


def load(file, **options):
    # type: (typing.IO, **typing.Any) -> canmatrix.CanMatrix
    motorola_bit_format = options.get("xlsMotorolaBitFormat", "msbreverse")
    float_factory = canmatrix.utils.FloatFactory.get_float_factory()

    additional_inputs = dict()
    wb = xlrd.open_workbook(file_contents=file.read())
    sh = wb.sheet_by_index(0)
    db = canmatrix.CanMatrix()

    # Defines not imported...
    # db.add_ecu_defines("NWM-Stationsadresse", 'HEX 0 63')
    # db.add_ecu_defines("NWM-Knoten", 'ENUM  "nein","ja"')

    canmatrix.formats.xls_common.initialize_excel_attribute_defines(db)

    launch_types = []  # type: typing.List[str]
    launch_type_default = None  # type: typing.Optional[str]
    sig_send_types = []  # type: typing.List[str]
    sig_send_type_default = None  # type: typing.Optional[str]

    # eval search for correct columns:
    index = {}
    for i in range(sh.ncols):
        value = sh.cell(0, i).value
        if value == "ID":
            index['ID'] = i
        elif "Frame Name" in value:
            index['frameName'] = i
        elif "DLC" in value:
            index['dlc'] = i
        elif "frame.comment" in value:
            index['frameComment'] = i
        elif "Cycle Time" in value:
            index['cycle'] = i
        elif "Launch Type" in value:
            index['launchType'] = i
        elif "GenMsgDelayTime" in value:
            index['launchParam'] = i
        elif "DiagRequest" in value:
            index['diagRequest'] = i
        elif "DiagResponse" in value:
            index['diagResponse'] = i
        elif "DiagState" in value:
            index['diagState'] = i
        elif "NmMessage" in value:
            index['nmMessage'] = i
        elif "GenMsgILSupport" in value:
            index['genMsgILSupport'] = i
        elif "GenMsgCycleTimeFast" in value:
            index['genMsgCycleTimeFast'] = i
        elif "GenMsgNrOfRepetition" in value:
            index['genMsgNrOfRepetition'] = i
        elif "CANFD_BRS" in value:
            index['canfdBrs'] = i
        elif "ID-Format" in value:
            index['idFormat'] = i
        elif "Signal Byte No." in value:
            index['startbyte'] = i
        elif "Signal Bit No." in value:
            index['startbit'] = i
        elif "Signal Name" in value:
            index['signalName'] = i
        elif "Signal Function" in value:
            index['signalComment'] = i
        elif "Signal Length" in value:
            index['signalLength'] = i
        elif "Signal Default" in value:
            index['signalDefault'] = i
        elif "GenSigStartValue" in value:
            index['genSigStartValue'] = i
        elif "GenSigInactiveValue" in value:
            index['genSigInactiveValue'] = i
        elif "GenSigSendType" in value:
            index['genSigSendType'] = i
        elif "EventCommandSignal" in value:
            index['eventCommandSignal'] = i
        elif "GatewayedSignals" in value:
            index['gatewayedSignals'] = i
        elif "GenSigInvalidValue" in value:
            index['genSigInvalidValue'] = i
        elif "GenSigTimeoutValue" in value:
            index['genSigTimeoutValue'] = i
        elif "Signal Not Ava" in value:
            index['signalSNA'] = i
        elif "Value" in value:
            index['Value'] = i
        elif "Name / Phys" in value:
            index['ValueName'] = i
        elif "Function /" in value:
            index['function'] = i
        elif "Factor" in value:
            index['explicitFactor'] = i
        elif "Offset" in value:
            index['explicitOffset'] = i
        elif "Byteorder" in value:
            index['byteorder'] = i
        else:
            if 'Value' in index and i > index['Value']:
                additional_inputs[i] = value

    if "byteorder" in index:
        index['ECUstart'] = index['byteorder'] + 1
    else:
        index['ECUstart'] = index['signalSNA'] + 1
    index['ECUend'] = index['Value']

    # ECUs:
    for x in range(index['ECUstart'], index['ECUend']):
        db.add_ecu(canmatrix.Ecu(sh.cell(0, x).value))

    # initialize:
    frame_id = None
    signal_name = ""
    new_frame = None

    def _cell(row_num, col_index):
        return sh.cell(row_num, col_index).value

    def _has_frame_id(row_num):
        if 'ID' not in index:
            return False
        val = _cell(row_num, index['ID'])
        return val is not None and len(str(val)) > 0

    def _has_signal_name(row_num):
        if 'signalName' not in index:
            return False
        val = _cell(row_num, index['signalName'])
        return val is not None and len(str(val)) > 0

    for row_num in range(1, sh.nrows):
        has_id = _has_frame_id(row_num)
        has_sig = _has_signal_name(row_num)

        if not has_id and not has_sig:
            continue

        is_new_format_frame_row = has_id and not has_sig

        if has_id:
            row_frame_id = _cell(row_num, index['ID'])
            if row_frame_id != frame_id:
                frame_id = row_frame_id
                frame_name = _cell(row_num, index['frameName'])
                cycle_time = _cell(row_num, index['cycle'])
                launch_type = _cell(row_num, index['launchType'])
                dlc = int(_cell(row_num, index['dlc'])) if 'dlc' in index else 8

                new_frame = canmatrix.Frame(frame_name, size=dlc)
                if frame_id.endswith("xh"):
                    new_frame.arbitration_id = canmatrix.ArbitrationId(int(frame_id[:-2], 16), extended=True)
                else:
                    new_frame.arbitration_id = canmatrix.ArbitrationId(int(frame_id[:-1], 16), extended=False)
                db.add_frame(new_frame)

                if 'launchType' in index:
                    result = canmatrix.formats.xls_common._import_attr_with_default(
                        new_frame, "GenMsgSendType", launch_type,
                        db=db, defines_dict=db.frame_defines, collect_list=launch_types)
                    if result is not None and launch_type_default is None:
                        launch_type_default = result

                if 'launchParam' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "GenMsgDelayTime", _cell(row_num, index['launchParam']), db=db, defines_dict=db.frame_defines)

                if 'diagRequest' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "DiagRequest", _cell(row_num, index['diagRequest']), db=db, defines_dict=db.frame_defines)

                if 'diagResponse' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "DiagResponse", _cell(row_num, index['diagResponse']), db=db, defines_dict=db.frame_defines)

                if 'diagState' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "DiagState", _cell(row_num, index['diagState']), db=db, defines_dict=db.frame_defines)

                if 'nmMessage' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "NmMessage", _cell(row_num, index['nmMessage']), db=db, defines_dict=db.frame_defines)

                if 'genMsgILSupport' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "GenMsgILSupport", _cell(row_num, index['genMsgILSupport']), db=db, defines_dict=db.frame_defines)

                if 'genMsgCycleTimeFast' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "GenMsgCycleTimeFast", _cell(row_num, index['genMsgCycleTimeFast']), db=db, defines_dict=db.frame_defines)

                if 'genMsgNrOfRepetition' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "GenMsgNrOfRepetition", _cell(row_num, index['genMsgNrOfRepetition']), db=db, defines_dict=db.frame_defines)

                if 'canfdBrs' in index:
                    canmatrix.formats.xls_common._import_attr_with_default(new_frame, "CANFD_BRS", _cell(row_num, index['canfdBrs']), db=db, defines_dict=db.frame_defines)

                if 'idFormat' in index:
                    id_format = _cell(row_num, index['idFormat'])
                    if id_format is not None and str(id_format).strip() != '':
                        id_format_str = str(id_format).strip()
                        if '_FD' in id_format_str:
                            new_frame.is_fd = True
                        new_frame.add_attribute("VFrameFormat", id_format_str)

                try:
                    cycle_time = int(cycle_time)
                except:
                    cycle_time = 0
                new_frame.cycle_time = cycle_time

                if 'frameComment' in index:
                    frame_comment = _cell(row_num, index['frameComment'])
                    if frame_comment:
                        new_frame.add_comment(str(frame_comment))

                for additional_index in additional_inputs:
                    if "frame" in additional_inputs[additional_index]:
                        command_str = additional_inputs[additional_index].replace("frame", "new_frame")
                        command_str += "="
                        command_str += str(_cell(row_num, additional_index))
                        exec(command_str)

            if is_new_format_frame_row:
                for x in range(index['ECUstart'], index['ECUend']):
                    ecu_val = _cell(row_num, x)
                    if ecu_val is not None:
                        ecu_str = str(ecu_val)
                        if 's' in ecu_str:
                            new_frame.add_transmitter(sh.cell(0, x).value.strip())
                        if 'r' in ecu_str:
                            new_frame.add_receiver(sh.cell(0, x).value.strip())
                signal_name = ""
                continue

        if not has_sig:
            continue

        # new signal detected
        if _cell(row_num, index['signalName']) != signal_name \
                and len(str(_cell(row_num, index['signalName']))) > 0:
            # new Signal
            receiver = []
            start_byte = int(_cell(row_num, index['startbyte']))
            start_bit = int(_cell(row_num, index['startbit']))
            raw_signal_name = _cell(row_num, index['signalName'])
            signal_name = str(raw_signal_name).strip() if raw_signal_name is not None else ""
            raw_signal_comment = _cell(row_num, index['signalComment'])
            signal_comment = str(raw_signal_comment).strip() if raw_signal_comment is not None else ""
            signal_length = int(_cell(row_num, index['signalLength']))
            signal_default = _cell(row_num, index['signalDefault'])
            signal_sna = _cell(row_num, index['signalSNA'])
            multiplex = None  # type: typing.Union[str, int, None]
            if signal_comment.startswith('Mode Signal:'):
                multiplex = 'Multiplexor'
                signal_comment = signal_comment[12:]
            elif signal_comment.startswith('Mode '):
                mux, signal_comment = signal_comment[4:].split(':', 1)
                multiplex = int(mux.strip())

            if index.get("byteorder", False):
                signal_byte_order = _cell(row_num, index['byteorder'])

                if 'i' in signal_byte_order:
                    is_little_endian = True
                else:
                    is_little_endian = False
            else:
                is_little_endian = True  # Default Intel

            is_signed = False

            if signal_name != "-":
                for x in range(index['ECUstart'], index['ECUend']):
                    ecu_val = _cell(row_num, x)
                    if ecu_val is not None and 's' in str(ecu_val):
                        new_frame.add_transmitter(sh.cell(0, x).value.strip())
                    if ecu_val is not None and 'r' in str(ecu_val):
                        receiver.append(sh.cell(0, x).value.strip())
                new_signal = canmatrix.Signal(
                    signal_name,
                    start_bit=(start_byte - 1) * 8 + start_bit,
                    size=int(signal_length),
                    is_little_endian=is_little_endian,
                    is_signed=is_signed,
                    receivers=receiver,
                    multiplex=multiplex)

                if not is_little_endian:
                    # motorola
                    if motorola_bit_format == "msb":
                        new_signal.set_startbit((start_byte - 1) * 8 + start_bit, bitNumbering=1)
                    elif motorola_bit_format == "msbreverse":
                        new_signal.set_startbit((start_byte - 1) * 8 + start_bit)
                    else:  # motorola_bit_format == "lsb"
                        new_signal.set_startbit(
                            (start_byte - 1) * 8 + start_bit,
                            bitNumbering=1,
                            startLittle=True)

                for additional_index in additional_inputs:  # todo explain this possibly dangerous code with eval
                    if "signal" in additional_inputs[additional_index]:
                        read_additional_signal_attributes(new_signal, additional_inputs[additional_index], _cell(row_num, additional_index))

                new_frame.add_signal(new_signal)
                new_signal.add_comment(signal_comment)
                if signal_default is not None and signal_default != '':
                    try:
                        new_signal.initial_value = float_factory(signal_default)
                    except (ValueError, decimal.InvalidOperation):
                        pass
                if 'genSigStartValue' in index:
                    gen_sig_start_value = _cell(row_num, index['genSigStartValue'])
                    if gen_sig_start_value is not None and str(gen_sig_start_value).strip() != '':
                        stripped, is_default = canmatrix.formats.xls_common._strip_default_mark(str(gen_sig_start_value).strip())
                        if not is_default:
                            new_signal.add_attribute("GenSigStartValue", stripped)

                if 'genSigInactiveValue' in index:
                    gen_sig_inactive_value = _cell(row_num, index['genSigInactiveValue'])
                    if gen_sig_inactive_value is not None and str(gen_sig_inactive_value).strip() != '':
                        new_signal.add_attribute("GenSigInactiveValue", str(gen_sig_inactive_value).strip())

                if 'genSigSendType' in index:
                    result = canmatrix.formats.xls_common._import_attr_with_default(new_signal, "GenSigSendType", _cell(row_num, index['genSigSendType']), db=db, defines_dict=db.signal_defines, collect_list=sig_send_types)
                    if result is not None and sig_send_type_default is None:
                        sig_send_type_default = result

                if 'eventCommandSignal' in index:
                    event_command_signal = _cell(row_num, index['eventCommandSignal'])
                    if event_command_signal is not None and str(event_command_signal).strip() != '':
                        new_signal.add_attribute("EventCommandSignal", str(event_command_signal).strip())

                if 'gatewayedSignals' in index:
                    gatewayed_signals = _cell(row_num, index['gatewayedSignals'])
                    if gatewayed_signals is not None and str(gatewayed_signals).strip() != '':
                        new_signal.add_attribute("GatewayedSignals", str(gatewayed_signals).strip())

                if 'genSigInvalidValue' in index:
                    gen_sig_invalid_value = _cell(row_num, index['genSigInvalidValue'])
                    if gen_sig_invalid_value is not None and str(gen_sig_invalid_value).strip() != '':
                        new_signal.add_attribute("GenSigInvalidValue", str(gen_sig_invalid_value).strip())

                if 'genSigTimeoutValue' in index:
                    gen_sig_timeout_value = _cell(row_num, index['genSigTimeoutValue'])
                    if gen_sig_timeout_value is not None and str(gen_sig_timeout_value).strip() != '':
                        new_signal.add_attribute("GenSigTimeoutValue", str(gen_sig_timeout_value).strip())
                function = _cell(row_num, index['function'])

        value = str(_cell(row_num, index['Value']))
        value_name = _cell(row_num, index['ValueName'])

        if value_name == 0:
            value_name = "0"
        elif value_name == 1:
            value_name = "1"
        # .encode('utf-8')

        unit = ""

        factor = _cell(row_num, index['function'])
        if isinstance(factor, str):
            factor = factor.strip()
            if " " in factor and factor[0].isdigit():
                (factor, unit) = factor.strip().split(" ", 1)
                factor = factor.strip()
                unit = unit.strip()
                new_signal.unit = unit
                try:
                    # if prevents overwriting explicit factor (if given)
                    if new_signal.factor in (1, 1.0):	
                        new_signal.factor = float_factory(factor)
                except:
                    logger.warning(
                        "Some error occurred while decoding scale of Signal %s: '%s'",
                        signal_name,
                        _cell(row_num, index['function']))
            else:
                unit = factor.strip()
                new_signal.unit = unit
                new_signal.factor = 1

        (mini, maxi, offset, value_table) = parse_value_name_column(value_name, value, new_signal.size, float_factory)
        if new_signal.min is None:
            new_signal.min = mini
        if new_signal.max is None:
            new_signal.max = maxi
        if new_signal.offset is None:
            new_signal.offset = offset
        if value_table is not None:
            for value, name in value_table.items():
                new_signal.add_values(value, name)

        if 'explicitFactor' in index:
            explicit_factor = _cell(row_num, index['explicitFactor'])
            if explicit_factor is not None and str(explicit_factor).strip() != '':
                try:
                    new_signal.factor = float_factory(str(explicit_factor).strip())
                except (ValueError, decimal.InvalidOperation):
                    pass

        if 'explicitOffset' in index:
            explicit_offset = _cell(row_num, index['explicitOffset'])
            if explicit_offset is not None and str(explicit_offset).strip() != '':
                try:
                    new_signal.offset = float_factory(str(explicit_offset).strip())
                except (ValueError, decimal.InvalidOperation):
                    pass

    for frame in db.frames:
        frame.update_receiver()
        frame.calc_dlc()

    launch_type_enum = "ENUM"
    launch_type_enum += ",".join([' "{}"'.format(launch_type) for launch_type in launch_types if launch_type])
    db.add_frame_defines("GenMsgSendType", launch_type_enum)
    if launch_type_default is not None:
        db.add_define_default("GenMsgSendType", launch_type_default)

    sig_send_type_enum = "ENUM"
    sig_send_type_enum += ",".join([' "{}"'.format(sig_send_type) for sig_send_type in sig_send_types if sig_send_type])
    db.add_signal_defines("GenSigSendType", sig_send_type_enum)
    if sig_send_type_default is not None:
        db.add_define_default("GenSigSendType", sig_send_type_default)

    db.set_fd_type()
    return db
