# -*- coding: utf-8 -*-
import typing

import canmatrix
from .base import ConvertHandler


class EcuHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "ECU操作"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return ('renameEcu' in options and options['renameEcu'] is not None) or \
               ('deleteEcu' in options and options['deleteEcu'] is not None) or \
               ('deleteObsoleteEcus' in options and options['deleteObsoleteEcus'])

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        if 'renameEcu' in options and options['renameEcu'] is not None:
            rename_tuples = options['renameEcu'].split(',')
            for renameTuple in rename_tuples:
                old, new = renameTuple.split(':')
                db.rename_ecu(old, new)
        if 'deleteEcu' in options and options['deleteEcu'] is not None:
            delete_ecu_list = options['deleteEcu'].split(',')
            for ecu in delete_ecu_list:
                db.del_ecu(ecu)
        if 'deleteObsoleteEcus' in options and options['deleteObsoleteEcus']:
            db.delete_obsolete_ecus()
