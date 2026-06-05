# -*- coding: utf-8 -*-
import logging
import typing

import canmatrix
from .base import ConvertHandler

logger = logging.getLogger(__name__)


class ValidationHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "校验与警告"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return (options.get('checkSignalReceiver') is not None and options['checkSignalReceiver']) or \
               (options.get('checkFloatingSignals') is not None and options['checkFloatingSignals']) or \
               (options.get('checkFloatingFrames') is not None and options['checkFloatingFrames']) or \
               (options.get('warnSignalMinMaxSame') is not None and options['warnSignalMinMaxSame']) or \
               (options.get('checkSignalUnit') is not None and options['checkSignalUnit'])

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        if options.get('checkSignalReceiver') is not None and options['checkSignalReceiver']:
            for frame in db.frames:
                for signal in frame:
                    if len(signal.receivers) == 0:
                        logger.warning("Please add Receiver for the signal %s ", (frame.name + "::" + signal.name))

        if options.get('checkFloatingSignals') is not None and options['checkFloatingSignals']:
            for frame in db.frames:
                if frame.name == 'VECTOR__INDEPENDENT_SIG_MSG':
                    for signal in frame:
                        logger.warning("Please map the signal %s to a valid frame or delete by deleteFloatingSignals", signal.name)

        if options.get('checkFloatingFrames') is not None and options['checkFloatingFrames']:
            for frame in db.frames:
                if len(frame.transmitters) == 0:
                    logger.warning("No Transmitter Node Found for Frame %s", frame.name)

        if options.get('warnSignalMinMaxSame') is not None and options['warnSignalMinMaxSame']:
            for frame in db.frames:
                for signal in frame.signals:
                    if (signal.phys2raw(signal.max) - signal.phys2raw(signal.min)) == 0:
                        logger.warning("Invalid Min , Max value of %s", (frame.name + "::" + signal.name))

        if options.get('checkSignalUnit') is not None and options['checkSignalUnit']:
            for frame in db.frames:
                for signal in frame:
                    if signal.unit == "" and len(signal.values) == 0:
                        logger.warning("Please add value table for the signal %s or add appropriate Unit", (frame.name + "::" + signal.name))
