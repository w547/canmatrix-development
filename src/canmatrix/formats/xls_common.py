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

import typing
from builtins import *

import canmatrix


def _get_attr_with_default_mark(obj, attr_name, db, defines_dict):
    if attr_name in obj.attributes:
        return str(obj.attributes[attr_name])
    if attr_name in defines_dict:
        default_val = obj.attribute(attr_name, db=db)
        if default_val is not None and str(default_val).strip() != '':
            return str(default_val) + "*"
    return ""


def _get_attr_with_fallback(obj, attr_names, db, defines_dict):
    for name in attr_names:
        if name in obj.attributes:
            return str(obj.attributes[name])
    for name in attr_names:
        if name in defines_dict:
            default_val = obj.attribute(name, db=db)
            if default_val is not None and str(default_val).strip() != '':
                return str(default_val) + "*"
    return ""


def _strip_default_mark(value):
    if value is not None and str(value).endswith("*"):
        return str(value)[:-1], True
    return value, False


def _import_attr_with_default(obj, attr_name, cell_value, db=None, defines_dict=None, collect_list=None):
    if cell_value is None or str(cell_value).strip() == '':
        return None
    stripped, is_default = _strip_default_mark(str(cell_value).strip())
    if not is_default:
        obj.add_attribute(attr_name, stripped)
    else:
        if db is not None and defines_dict is not None and attr_name in defines_dict:
            defines_dict[attr_name].defaultValue = stripped
        # else:
        #     # Fallback: when the define is not yet registered (e.g. GenMsgSendType
        #     # is only created at the end of import), preserve the value as an
        #     # explicit attribute on the object.
        #     obj.add_attribute(attr_name, stripped)
    if collect_list is not None and stripped not in collect_list:
        collect_list.append(stripped)
    return stripped if is_default else None


def initialize_excel_attribute_defines(db):
    # type: (canmatrix.CanMatrix) -> None
    # ---- Interaction Layer attributes ----
    db.add_frame_defines("GenMsgDelayTime", 'INT 0 65535')
    db.add_frame_defines("GenMsgCycleTimeActive", 'INT 0 65535')

    # ---- Diagnostics attributes ----
    db.add_frame_defines("DiagRequest", 'STRING')
    db.add_frame_defines("DiagResponse", 'STRING')
    db.add_frame_defines("DiagState", 'STRING')

    # ---- Net Management attributes ----
    db.add_frame_defines("NmMessage", 'STRING')

    # ---- Interaction Layer attributes ----
    db.add_frame_defines("GenMsgILSupport", 'STRING')
    db.add_frame_defines("GenMsgCycleTimeFast", 'INT 0 65535')
    db.add_frame_defines("GenMsgNrOfRepetition", 'INT 0 65535')

    # ---- CAN FD attributes ----
    db.add_frame_defines("CANFD_BRS", 'STRING')

    # ---- Signal attributes ----
    db.add_signal_defines("GenSigSNA", 'STRING')
    db.add_signal_defines("GenSigInactiveValue", 'STRING')
    db.add_signal_defines("EventCommandSignal", 'STRING')
    db.add_signal_defines("GatewayedSignals", 'STRING')
    db.add_signal_defines("GenSigInvalidValue", 'STRING')
    db.add_signal_defines("GenSigTimeoutValue", 'STRING')


def get_frame_info(db, frame):
    # type: (canmatrix.CanMatrix, canmatrix.Frame) -> typing.List[str]
    ret_array = []  # type: typing.List[str]

    if db.type == canmatrix.matrix_class.CAN:
        # frame-id
        if frame.arbitration_id.extended:
            ret_array.append("%3Xxh" % frame.arbitration_id.id)
        else:
            ret_array.append("%3Xh" % frame.arbitration_id.id)
    elif db.type == canmatrix.matrix_class.FLEXRAY:
        ret_array.append("TODO")
    elif db.type == canmatrix.matrix_class.SOMEIP:
        ret_array.append("%3Xh" % frame.header_id)

    # frame-Name
    ret_array.append(frame.name)

    ret_array.append(str(frame.size))

    ret_array.append(frame.comment if frame.comment else "")

    ret_array.append(frame.effective_cycle_time)

    # ---- Interaction Layer attributes ----
    # Launch Type (GenMsgSendType)
    ret_array.append(_get_attr_with_default_mark(frame, "GenMsgSendType", db, db.frame_defines))

    # GenMsgDelayTime
    ret_array.append(_get_attr_with_default_mark(frame, "GenMsgDelayTime", db, db.frame_defines))

    # ---- Diagnostics attributes ----
    # DiagRequest
    ret_array.append(_get_attr_with_default_mark(frame, "DiagRequest", db, db.frame_defines))

    # DiagResponse
    ret_array.append(_get_attr_with_default_mark(frame, "DiagResponse", db, db.frame_defines))

    # DiagState
    ret_array.append(_get_attr_with_default_mark(frame, "DiagState", db, db.frame_defines))

    # ---- Net Management attributes ----
    # NmMessage
    ret_array.append(_get_attr_with_default_mark(frame, "NmMessage", db, db.frame_defines))

    # ---- Interaction Layer attributes ----
    # GenMsgILSupport
    ret_array.append(_get_attr_with_default_mark(frame, "GenMsgILSupport", db, db.frame_defines))

    # GenMsgCycleTimeFast
    ret_array.append(_get_attr_with_default_mark(frame, "GenMsgCycleTimeFast", db, db.frame_defines))

    # GenMsgNrOfRepetition
    ret_array.append(_get_attr_with_fallback(frame, ["GenMsgNrOfRepetition", "GenMsgNoOfRepetitions"], db, db.frame_defines))

    # ---- CAN FD attributes ----
    # CANFD_BRS
    ret_array.append(_get_attr_with_default_mark(frame, "CANFD_BRS", db, db.frame_defines))

    # ID-Format
    if frame.is_fd:
        if frame.arbitration_id.extended:
            ret_array.append("ExtendedCAN_FD")
        else:
            ret_array.append("StandardCAN_FD")
    else:
        if frame.arbitration_id.extended:
            ret_array.append("ExtendedCAN")
        else:
            ret_array.append("StandardCAN")

    return ret_array


def get_signal(db, frame, sig, motorola_bit_format):
    # type: (canmatrix.CanMatrix, canmatrix.Frame, canmatrix.Signal, str) -> typing.Tuple[typing.List, typing.List]
    front_array = []  # type: typing.List[typing.Union[str, float]]
    back_array = []
    if motorola_bit_format == "msb":
        start_bit = sig.get_startbit(bit_numbering=1)
    elif motorola_bit_format == "msbreverse":
        start_bit = sig.get_startbit()
    else:  # motorolaBitFormat == "lsb"
        start_bit = sig.get_startbit(bit_numbering=1, start_little=True)

    # start byte
    front_array.append(int(start_bit / 8) + 1)
    # start bit
    front_array.append(start_bit % 8)
    # signal name
    front_array.append(sig.name)

    # eval comment:
    comment = sig.comment if sig.comment else ""

    # eval multiplex-info
    if frame.is_complex_multiplexed:
        for signal in frame.signals:
            if signal.muxer_for_signal is not None:
                comment = "Mode {} = {}".format(sig.muxer_for_signal, sig.multiplex)
    else:
        if sig.multiplex == 'Multiplexor':
            comment = "Mode Signal: " + comment
        elif sig.multiplex is not None:
            comment = "Mode " + str(sig.multiplex) + ":" + comment

    # write comment and size of signal in sheet
    front_array.append(comment)
    front_array.append(sig.size)

    # start-value of signal available
    front_array.append(sig.initial_value)

    # GenSigStartValue from attributes
    front_array.append(_get_attr_with_default_mark(sig, "GenSigStartValue", db, db.signal_defines))

    # ---- Interaction Layer signal attributes ----
    gen_sig_inactive_value = sig.attributes.get("GenSigInactiveValue", "")
    front_array.append(gen_sig_inactive_value)

    front_array.append(_get_attr_with_default_mark(sig, "GenSigSendType", db, db.signal_defines))

    # ---- No category assigned signal attributes ----
    event_command_signal = sig.attributes.get("EventCommandSignal", "")
    front_array.append(event_command_signal)

    gatewayed_signals = sig.attributes.get("GatewayedSignals", "")
    front_array.append(gatewayed_signals)

    gen_sig_invalid_value = sig.attributes.get("GenSigInvalidValue", "")
    front_array.append(gen_sig_invalid_value)

    gen_sig_timeout_value = sig.attributes.get("GenSigTimeoutValue", "")
    front_array.append(gen_sig_timeout_value)

    front_array.append(str(sig.factor))
    front_array.append(str(sig.offset))

    # SNA-value of signal available
    if "GenSigSNA" in db.signal_defines:
        sna = sig.attribute("GenSigSNA", db=db)
        if sna is not None:
            sna = sna[1:-1]
        front_array.append(sna)
    # no SNA-value of signal available / just for correct style:
    else:
        front_array.append(" ")

    # eval byteorder (little_endian: intel == True / motorola == 0)
    if sig.is_little_endian:
        front_array.append("i")
    else:
        front_array.append("m")

    # is a unit defined for signal?
    signal_unit = str(sig.unit) if sig.unit is not None else ""
    if signal_unit.strip():
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            back_array.append("%g" % float(sig.factor) + "  " + signal_unit)
        # factor == 1.0
        else:
            back_array.append(signal_unit)
    # no unit defined
    else:
        # factor not 1.0 ?
        if float(sig.factor) != 1:
            back_array.append("%g -" % float(sig.factor))
        # factor == 1.0
        else:
            back_array.append("")

    return front_array, back_array
