# -*- coding: utf-8 -*-
import typing

import canmatrix
from .base import ConvertHandler


class SignalHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "Signal操作"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return ('renameSignal' in options and options['renameSignal'] is not None) or \
               ('deleteSignal' in options and options['deleteSignal'] is not None) or \
               ('deleteZeroSignals' in options and options['deleteZeroSignals']) or \
               ('deleteSignalAttributes' in options and options['deleteSignalAttributes']) or \
               ('deleteFloatingSignals' in options and options['deleteFloatingSignals']) or \
               (options.get('signalNameFromAttrib') is not None)

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        if 'renameSignal' in options and options['renameSignal'] is not None:
            rename_tuples = options['renameSignal'].split(',')
            for renameTuple in rename_tuples:
                old, new = renameTuple.split(':')
                db.rename_signal(old, new)

        if 'deleteSignal' in options and options['deleteSignal'] is not None:
            delete_signal_names = options['deleteSignal'].split(',')
            for signal_name in delete_signal_names:
                db.del_signal(signal_name)

        if 'deleteZeroSignals' in options and options['deleteZeroSignals']:
            db.delete_zero_signals()

        if 'deleteSignalAttributes' in options and options['deleteSignalAttributes']:
            unwanted_attributes = options['deleteSignalAttributes'].split(',')
            db.del_signal_attributes(unwanted_attributes)

        if 'deleteFloatingSignals' in options and options['deleteFloatingSignals']:
            for frame in db.frames:
                if frame.name == 'VECTOR__INDEPENDENT_SIG_MSG':
                    for signal in frame:
                        db.del_signal(signal)
                    db.del_frame(frame)

        if options.get('signalNameFromAttrib') is not None:
            for signal in [b for a in db for b in a.signals]:
                signal.name = signal.attributes.get(options.get('signalNameFromAttrib'), signal.name)
