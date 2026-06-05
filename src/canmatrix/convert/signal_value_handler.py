# -*- coding: utf-8 -*-
import typing

import canmatrix
from .base import ConvertHandler


class SignalValueHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "Signal值计算"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return (options.get('calcSignalMaximumsWhereZero') is not None and options['calcSignalMaximumsWhereZero']) or \
               (options.get('recalcSignalMaximums') is not None and options['recalcSignalMaximums']) or \
               (options.get('recalcSignalMinimums') is not None and options['recalcSignalMinimums'])

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        if options.get('calcSignalMaximumsWhereZero') is not None and options['calcSignalMaximumsWhereZero']:
            for signal in [b for a in db for b in a.signals]:
                if signal.max == 0 or signal.max is None:
                    signal.calc_max_for_none = True
                    signal.set_max(None)

        if options.get('recalcSignalMaximums') is not None and options['recalcSignalMaximums']:
            for signal in [b for a in db for b in a.signals]:
                signal.calc_max_for_none = True
                signal.set_max(None)

        if options.get('recalcSignalMinimums') is not None and options['recalcSignalMinimums']:
            for signal in [b for a in db for b in a.signals]:
                signal.calc_min_for_none = True
                signal.set_min(None)
