# -*- coding: utf-8 -*-
import logging
import typing

import canmatrix
from .base import ConvertHandler

logger = logging.getLogger(__name__)


class FrameHandler(ConvertHandler):
    @property
    def name(self):
        # type: () -> str
        return "Frame操作"

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return ('renameFrame' in options and options['renameFrame'] is not None) or \
               ('deleteFrame' in options and options['deleteFrame'] is not None) or \
               ('addFrameReceiver' in options and options['addFrameReceiver'] is not None) or \
               ('frameIdIncrement' in options and options['frameIdIncrement'] is not None) or \
               ('changeFrameId' in options and options['changeFrameId'] is not None) or \
               ('setFrameFd' in options and options['setFrameFd'] is not None) or \
               ('unsetFrameFd' in options and options['unsetFrameFd'] is not None) or \
               ('compressFrame' in options and options['compressFrame'] is not None) or \
               (options.get('frameNameFromAttrib') is not None)

    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        if 'renameFrame' in options and options['renameFrame'] is not None:
            rename_tuples = options['renameFrame'].split(',')
            for renameTuple in rename_tuples:
                old, new = renameTuple.split(':')
                db.rename_frame(old, new)

        if 'deleteFrame' in options and options['deleteFrame'] is not None:
            delete_frame_names = options['deleteFrame'].split(',')
            for frame_name in delete_frame_names:
                db.del_frame(frame_name)

        if 'addFrameReceiver' in options and options['addFrameReceiver'] is not None:
            touples = options['addFrameReceiver'].split(',')
            for touple in touples:
                (frameName, ecu) = touple.split(':')
                frames = db.glob_frames(frameName)
                for frame in frames:
                    for signal in frame.signals:
                        signal.add_receiver(ecu)
                    frame.update_receiver()

        if 'frameIdIncrement' in options and options['frameIdIncrement'] is not None:
            id_increment = int(options['frameIdIncrement'])
            for frame in db.frames:
                frame.arbitration_id.id += id_increment

        if 'changeFrameId' in options and options['changeFrameId'] is not None:
            change_tuples = options['changeFrameId'].split(',')
            for renameTuple in change_tuples:
                old, new = renameTuple.split(':')
                frame = db.frame_by_id(canmatrix.ArbitrationId(int(old)))
                if frame is not None:
                    frame.arbitration_id.id = int(new)
                else:
                    logger.error("frame with id {} not found", old)

        if 'setFrameFd' in options and options['setFrameFd'] is not None:
            fd_frame_list = options['setFrameFd'].split(',')
            for frame_name in fd_frame_list:
                frame_ptr = db.frame_by_name(frame_name)
                if frame_ptr is not None:
                    frame_ptr.is_fd = True

        if 'unsetFrameFd' in options and options['unsetFrameFd'] is not None:
            fd_frame_list = options['unsetFrameFd'].split(',')
            for frame_name in fd_frame_list:
                frame_ptr = db.frame_by_name(frame_name)
                if frame_ptr is not None:
                    frame_ptr.is_fd = False
                    frame_ptr.del_attribute("VFrameFormat")

        if 'compressFrame' in options and options['compressFrame'] is not None:
            frames_cmdline = options['compressFrame'].split(',')
            for frame_name in frames_cmdline:
                frames = db.glob_frames(frame_name)
                for frame in frames:
                    frame.compress()

        if options.get('frameNameFromAttrib') is not None:
            for frame in db:
                frame.name = frame.attributes.get(options.get('frameNameFromAttrib'), frame.name)
