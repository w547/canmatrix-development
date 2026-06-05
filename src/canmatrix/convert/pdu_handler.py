# -*- coding: utf-8 -*-
import copy
import logging
import typing

import canmatrix
from .base import ConvertHandler

logger = logging.getLogger(__name__)


def _convert_pdu_container_to_multiplexed(frame):
    # type: (canmatrix.Frame) -> canmatrix.Frame
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


class PduHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "PDU容器处理"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return True

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        frame_pdu_container_list = [
            frame
            for frame in db.frames
            if frame.is_pdu_container
        ]
        if options.get('ignorePduContainer'):
            for frame in frame_pdu_container_list:
                db.del_frame(frame)
        else:
            for frame in frame_pdu_container_list:
                logger.warning("%s converted to Multiplexed frame", frame.name)
                new_frame = _convert_pdu_container_to_multiplexed(frame)
                db.del_frame(frame)
                db.add_frame(new_frame)
