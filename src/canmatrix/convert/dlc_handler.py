# -*- coding: utf-8 -*-
import typing

import canmatrix
from .base import ConvertHandler


class DlcHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "DLC操作"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return ('recalcDLC' in options and options['recalcDLC']) or \
               ('skipLongDlc' in options and options['skipLongDlc'] is not None) or \
               ('cutLongFrames' in options and options['cutLongFrames'] is not None)

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        if 'recalcDLC' in options and options['recalcDLC']:
            db.recalc_dlc(options['recalcDLC'])

        if 'skipLongDlc' in options and options['skipLongDlc'] is not None:
            delete_frame_list = [
                frame
                for frame in db.frames
                if frame.size > int(options['skipLongDlc'])
            ]
            for frame in delete_frame_list:
                db.del_frame(frame)

        if 'cutLongFrames' in options and options['cutLongFrames'] is not None:
            for frame in db.frames:
                if frame.size > int(options['cutLongFrames']):
                    delete_signal_list = [
                        sig
                        for sig in frame.signals
                        if sig.get_startbit() + int(sig.size) > int(options['cutLongFrames']) * 8
                    ]
                    for sig in delete_signal_list:
                        frame.signals.remove(sig)
                    frame.size = 0
                    frame.calc_dlc()
