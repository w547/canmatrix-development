# -*- coding: utf-8 -*-
import typing

import canmatrix
from .base import ConvertHandler


class ProtocolHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "协议转换"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return (options.get('convertToExtended') is not None and options['convertToExtended']) or \
               (options.get('convertToJ1939') is not None and options['convertToJ1939'])

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        if options.get('convertToExtended') is not None and options['convertToExtended']:
            for frame in db.frames:
                frame.is_j1939 = False
            db.add_attribute("ProtocolType", "ExtendedCAN")

        if options.get('convertToJ1939') is not None and options['convertToJ1939']:
            for frame in db.frames:
                frame.is_j1939 = True
            db.add_attribute("ProtocolType", "J1939")
