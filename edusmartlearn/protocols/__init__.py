# Protocols module for EduSmartLearn
# Contains A2A (Agent-to-Agent) protocol definitions

from protocols.a2a_protocol import (
    A2AMessage,
    MessageType,
    ErrorCode,
    AgentCapability,
    ConsentRequirement,
    A2ARouter,
    a2a_router
)

__all__ = [
    "A2AMessage",
    "MessageType", 
    "ErrorCode",
    "AgentCapability",
    "ConsentRequirement",
    "A2ARouter",
    "a2a_router"
]
