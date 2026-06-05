# -*- coding: utf-8 -*-
import typing

import canmatrix
import canmatrix.copy
import canmatrix.formats
from .base import ConvertHandler


class MergeHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "数据库合并"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return 'merge' in options and options['merge'] is not None

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        merge_files = options['merge'].split(',')
        for database in merge_files:
            merge_string = database.split(':')
            db_temp_list = canmatrix.formats.loadp(merge_string[0])
            for dbTemp in db_temp_list:
                if merge_string.__len__() == 1:
                    db.merge([db_temp_list[dbTemp]])
                for mergeOpt in merge_string[1:]:
                    if mergeOpt.split('=')[0] == "ecu":
                        canmatrix.copy.copy_ecu_with_frames(
                            mergeOpt.split('=')[1], db_temp_list[dbTemp], db)
                    if mergeOpt.split('=')[0] == "frame":
                        frame_to_copy = db_temp_list[dbTemp].frame_by_name(mergeOpt.split('=')[1])
                        canmatrix.copy.copy_frame(frame_to_copy.arbitration_id, db_temp_list[dbTemp], db)
