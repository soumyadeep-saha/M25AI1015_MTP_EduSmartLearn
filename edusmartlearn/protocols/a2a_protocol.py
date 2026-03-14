"""
protocols/a2a_protocol.py
=========================
Agent-to-Agent (A2A) Protocol Implementation.

This module defines the structured message format for inter-agent communication
in the EduSmartLearn system. The protocol ensures:
- Type-safe message passing between agents
- Capability negotiation and consent management
- Audit trail for all agent interactions
- Error handling with explicit error codes

Message Flow Example:
    User Request -> Tutor Agent -> Orchestrator -> [Teacher, Retrieval] -> Orchestrator -> Tutor -> User

Key Components:
1. MessageType: Defines all valid message types (task_request, task_response, etc.)
2. AgentCapability: Capabilities agents can advertise (explain_concept, code_execution, etc.)
3. A2AMessage: The core message structure with validation
4. A2ARouter: Routes messages between agents based on capabilities
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """
    Enumeration of all valid A2A message types.
    
    Each type represents a specific interaction pattern:
    - Task messages: For delegating and completing work
    - Control messages: For capability discovery
    - Consent messages: For HITL (Human-in-the-Loop) workflows
    - Quality messages: For review and revision cycles
    """
    # === Task-related messages ===
    TASK_REQUEST = "task_request"           # Request agent to perform a task
    TASK_RESPONSE = "task_response"         # Response containing task results
    TASK_DELEGATION = "task_delegation"     # Delegate task to another agent
    
    # === Control messages ===
    CAPABILITY_QUERY = "capability_query"   # Query what an agent can do
    CAPABILITY_RESPONSE = "capability_response"  # Agent's capability list
    
    # === Consent and safety messages ===
    CONSENT_REQUEST = "consent_request"     # Request user consent for action
    CONSENT_RESPONSE = "consent_response"   # User's consent decision
    
    # === Quality control messages ===
    REVIEW_REQUEST = "review_request"       # Request output review from evaluator
    REVIEW_RESPONSE = "review_response"     # Review feedback
    REVISION_REQUEST = "revision_request"   # Request revision based on feedback
    
    # === Error handling ===
    ERROR = "error"                         # Error notification
    
    # === System messages ===
    HEARTBEAT = "heartbeat"                 # Health check ping
    SHUTDOWN = "shutdown"                   # Graceful shutdown signal


class ErrorCode(str, Enum):
    """
    Standardized error codes for A2A communication.
    
    These codes enable consistent error handling across all agents
    and support automated retry/fallback logic.
    """
    SUCCESS = "SUCCESS"                           # Operation completed successfully
    INVALID_REQUEST = "INVALID_REQUEST"           # Malformed or invalid request
    UNAUTHORIZED = "UNAUTHORIZED"                 # Agent lacks permission
    CAPABILITY_NOT_FOUND = "CAPABILITY_NOT_FOUND" # No agent has required capability
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"  # MCP tool call failed
    TIMEOUT = "TIMEOUT"                           # Operation timed out
    CONSENT_DENIED = "CONSENT_DENIED"             # User denied consent
    SAFETY_VIOLATION = "SAFETY_VIOLATION"         # Safety policy violated
    RATE_LIMITED = "RATE_LIMITED"                 # Too many requests
    INTERNAL_ERROR = "INTERNAL_ERROR"             # Unexpected internal error


class AgentCapability(str, Enum):
    """
    Capabilities that agents can advertise and request.
    
    Used for:
    1. Capability negotiation during task routing
    2. Selecting appropriate agent for a task
    3. Validating agent permissions
    
    Categories:
    - Content generation: Teaching and explanation
    - Domain expertise: Subject-specific knowledge
    - Tool usage: External tool access
    - Quality/Safety: Evaluation and guardrails
    - Personalization: Learner modeling
    """
    # === Content Generation ===
    EXPLAIN_CONCEPT = "explain_concept"       # Generate explanations
    GENERATE_EXAMPLE = "generate_example"     # Create examples
    ANSWER_QUESTION = "answer_question"       # Answer student questions
    
    # === Domain Expertise ===
    AI_CONTENT = "ai_content"                 # Artificial Intelligence topics
    ML_CONTENT = "ml_content"                 # Machine Learning topics
    DL_CONTENT = "dl_content"                 # Deep Learning topics
    PROGRAMMING = "programming"               # Programming/coding help
    
    # === Tool Usage ===
    CODE_EXECUTION = "code_execution"         # Run code in sandbox
    DOCUMENT_RETRIEVAL = "document_retrieval" # RAG document search
    QUIZ_GENERATION = "quiz_generation"       # Create assessments
    
    # === Quality and Safety ===
    CONTENT_EVALUATION = "content_evaluation" # Review content quality
    SAFETY_CHECK = "safety_check"             # Check for policy violations
    
    # === Personalization ===
    LEARNER_MODELING = "learner_modeling"     # Track learner progress


class ConsentRequirement(BaseModel):
    """
    Specifies consent requirements for sensitive operations.
    
    Implements Human-in-the-Loop (HITL) for critical actions like:
    - Code execution
    - Storing personal data
    - Accessing external resources
    
    The consent workflow:
    1. Agent sends CONSENT_REQUEST with this object
    2. System presents request to user
    3. User approves/denies
    4. CONSENT_RESPONSE sent back with decision
    """
    # Whether consent is required for this operation
    required: bool = False
    
    # Type of operation (e.g., "code_execution", "data_storage")
    operation_type: Optional[str] = None
    
    # Human-readable description shown to user
    description: Optional[str] = None
    
    # Whether consent has been granted (filled after user decision)
    granted: Optional[bool] = None
    
    # Timestamp when consent was given/denied
    consent_timestamp: Optional[datetime] = None


class A2AMessage(BaseModel):
    """
    Core A2A message structure - the fundamental unit of inter-agent communication.
    
    Every message between agents uses this schema, enabling:
    - Validation: All fields are type-checked
    - Auditing: Messages can be logged and replayed
    - Routing: Messages can be routed based on capabilities
    - Correlation: Request-response pairs can be tracked
    
    Example - Task Request:
        message = A2AMessage(
            message_type=MessageType.TASK_REQUEST,
            sender="orchestrator",
            receiver="teacher_agent",
            capabilities_requested=[AgentCapability.EXPLAIN_CONCEPT],
            payload={"topic": "neural networks", "level": "beginner"}
        )
    
    Example - Task Response:
        response = original_message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender="teacher_agent",
            payload={"explanation": "Neural networks are..."}
        )
    """
    
    # === Message Identification ===
    # Unique ID for tracking this specific message
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    
    # Reference to parent message (for request-response correlation)
    correlation_id: Optional[str] = None
    
    # === Routing Information ===
    # Type determines how message should be processed
    message_type: MessageType
    
    # Sender agent identifier (e.g., "orchestrator", "teacher_agent")
    sender: str
    
    # Receiver agent identifier (can be "broadcast" for multi-agent)
    receiver: str
    
    # === Capability Negotiation ===
    # Capabilities being requested from receiver
    capabilities_requested: List[AgentCapability] = Field(default_factory=list)
    
    # Capabilities offered by sender (for capability discovery)
    capabilities_offered: List[AgentCapability] = Field(default_factory=list)
    
    # === Consent Management ===
    # Consent requirements for sensitive operations
    consent: ConsentRequirement = Field(default_factory=ConsentRequirement)
    
    # === Payload ===
    # Main message data - structure depends on message_type
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # === Error Information ===
    # Populated when message_type is ERROR
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None
    
    # === Metadata for Observability ===
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None      # Links to user session
    trace_id: Optional[str] = None        # For distributed tracing
    
    # Priority for message queue (1=highest, 10=lowest)
    priority: int = Field(default=5, ge=1, le=10)
    
    def create_response(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        sender: str,
        error_code: Optional[ErrorCode] = None,
        error_message: Optional[str] = None
    ) -> "A2AMessage":
        """
        Create a response message correlated to this message.
        
        Automatically sets:
        - correlation_id to link response to request
        - receiver to original sender
        - session_id and trace_id for continuity
        
        Args:
            message_type: Type of response (usually TASK_RESPONSE or ERROR)
            payload: Response data
            sender: Agent sending the response
            error_code: Optional error code if operation failed
            error_message: Optional error description
            
        Returns:
            New A2AMessage configured as response
        """
        return A2AMessage(
            correlation_id=self.message_id,
            message_type=message_type,
            sender=sender,
            receiver=self.sender,  # Send back to original sender
            payload=payload,
            error_code=error_code,
            error_message=error_message,
            session_id=self.session_id,
            trace_id=self.trace_id
        )


class A2ARouter:
    """
    Routes A2A messages between agents based on capabilities and policies.
    
    The router maintains:
    1. Agent registry: Maps agent IDs to their capabilities
    2. Message queue: For async message processing
    3. Message history: For audit trail and debugging
    
    Routing Logic:
    1. If receiver is specified -> route directly
    2. If capabilities requested -> find agent with matching capability
    3. If no match -> return None (caller handles fallback)
    """
    
    def __init__(self):
        # Registry: agent_id -> list of capabilities
        self._agent_registry: Dict[str, List[AgentCapability]] = {}
        
        # Message queue for async processing (FIFO)
        self._message_queue: List[A2AMessage] = []
        
        # Message history for audit trail
        self._message_history: List[A2AMessage] = []
        
        # Maximum history size to prevent memory issues
        self._max_history_size: int = 10000
    
    def register_agent(self, agent_id: str, capabilities: List[AgentCapability]) -> None:
        """
        Register an agent with its capabilities.
        
        Called when an agent starts up to advertise what it can do.
        
        Args:
            agent_id: Unique identifier for the agent
            capabilities: List of capabilities the agent provides
        """
        self._agent_registry[agent_id] = capabilities
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        Remove an agent from the registry.
        
        Called when an agent shuts down.
        """
        self._agent_registry.pop(agent_id, None)
    
    def get_registered_agents(self) -> Dict[str, List[AgentCapability]]:
        """Get all registered agents and their capabilities."""
        return self._agent_registry.copy()
    
    def find_agents_by_capability(self, capability: AgentCapability) -> List[str]:
        """
        Find all agents that provide a specific capability.
        
        Args:
            capability: The capability to search for
            
        Returns:
            List of agent IDs that provide the capability
        """
        return [
            agent_id 
            for agent_id, caps in self._agent_registry.items() 
            if capability in caps
        ]
    
    def route_message(self, message: A2AMessage) -> Optional[str]:
        """
        Determine the best agent to route a message to.
        
        Routing priority:
        1. Direct routing if receiver is specified and valid
        2. Capability-based routing if capabilities_requested is set
        3. None if no suitable agent found
        
        Args:
            message: The A2A message to route
            
        Returns:
            Agent ID to route to, or None if no match
        """
        # Direct routing if receiver specified
        if message.receiver and message.receiver != "broadcast":
            if message.receiver in self._agent_registry:
                return message.receiver
            return None
        
        # Capability-based routing
        if message.capabilities_requested:
            for capability in message.capabilities_requested:
                agents = self.find_agents_by_capability(capability)
                if agents:
                    # Return first matching agent
                    # Could implement load balancing here
                    return agents[0]
        
        return None
    
    def log_message(self, message: A2AMessage) -> None:
        """
        Add message to history for audit trail.
        
        Maintains bounded history to prevent memory exhaustion.
        """
        self._message_history.append(message)
        
        # Trim history if too large
        if len(self._message_history) > self._max_history_size:
            self._message_history = self._message_history[-self._max_history_size:]
    
    def get_message_history(
        self, 
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[A2AMessage]:
        """
        Retrieve message history, optionally filtered by session.
        
        Args:
            session_id: Filter by session ID if provided
            limit: Maximum number of messages to return
            
        Returns:
            List of A2A messages from history (most recent last)
        """
        history = self._message_history
        if session_id:
            history = [m for m in history if m.session_id == session_id]
        return history[-limit:]
    
    def clear_history(self) -> None:
        """Clear message history (for testing or reset)."""
        self._message_history.clear()


# Global router instance - import this in other modules
a2a_router = A2ARouter()
