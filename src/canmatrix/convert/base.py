# -*- coding: utf-8 -*-
import logging
import typing
from abc import ABC, abstractmethod

import canmatrix

logger = logging.getLogger(__name__)


class ConvertHandler(ABC):
    @property
    @abstractmethod
    def name(self):
        # type: () -> str
        pass

    def should_run(self, options):
        # type: (typing.Dict[str, typing.Any]) -> bool
        return False

    @abstractmethod
    def handle(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        pass


class HandlerRegistry:
    def __init__(self):
        self._handlers = []  # type: typing.List[ConvertHandler]

    def register(self, handler):
        # type: (ConvertHandler) -> None
        self._handlers.append(handler)

    def execute_all(self, db, options):
        # type: (canmatrix.CanMatrix, typing.Dict[str, typing.Any]) -> None
        for handler in self._handlers:
            if handler.should_run(options):
                logger.debug("Running handler: %s", handler.name)
                handler.handle(db, options)
