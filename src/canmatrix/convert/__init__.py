# -*- coding: utf-8 -*-
from ._core import (
    apply_mojibake_fix_to_db,
    convert,
    convert_pdu_container_to_multiplexed,
    fix_mojibake_gbk,
)
from .base import ConvertHandler, HandlerRegistry
from .ecu_handler import EcuHandler
from .frame_handler import FrameHandler
from .signal_handler import SignalHandler
from .merge_handler import MergeHandler
from .validation_handler import ValidationHandler
from .attribute_handler import AttributeHandler
from .dlc_handler import DlcHandler
from .protocol_handler import ProtocolHandler
from .pdu_handler import PduHandler
from .signal_value_handler import SignalValueHandler


def create_default_handler_registry():
    registry = HandlerRegistry()
    registry.register(MergeHandler())
    registry.register(EcuHandler())
    registry.register(FrameHandler())
    registry.register(SignalHandler())
    registry.register(DlcHandler())
    registry.register(SignalValueHandler())
    registry.register(PduHandler())
    registry.register(ProtocolHandler())
    registry.register(AttributeHandler())
    registry.register(ValidationHandler())
    return registry
