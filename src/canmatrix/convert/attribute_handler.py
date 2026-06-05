# -*- coding: utf-8 -*-
import typing

import canmatrix
from .base import ConvertHandler


class AttributeHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "属性操作"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return ('deleteFrameAttributes' in options and options['deleteFrameAttributes']) or \
               ('deleteObsoleteDefines' in options and options['deleteObsoleteDefines'])

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        if 'deleteFrameAttributes' in options and options['deleteFrameAttributes']:
            unwanted_attributes = options['deleteFrameAttributes'].split(',')
            db.del_frame_attributes(unwanted_attributes)

        if 'deleteObsoleteDefines' in options and options['deleteObsoleteDefines']:
            db.delete_obsolete_defines()
