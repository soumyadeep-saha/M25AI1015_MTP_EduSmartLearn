"""
agents/tutor_agent.py
=====================
Tutor Agent - Session Manager and User Interface Handler.

The Tutor Agent is the primary interface between users and the system.
It manages:
- Conversation flow and session state
- User request interpretation
- Response presentation
- Triggering the orchestrator for complex tasks

Position in Architecture: Interaction & State Layer
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from protocols.a2a_protocol import (
    A2AMessage,
    MessageType,
    AgentCapability,
    ErrorCode
)

logger = structlog.get_logger()


class TutorAgent(BaseAgent):
    """
    Tutor Agent - The student's primary point of contact.
    
    Responsibilities:
    1. Maintain conversation flow with the student
    2. Manage session state (context, history)
    3. Interpret user requests and determine if orchestration needed
    4. Present responses in student-friendly format
    5. Handle session lifecycle (start, continue, end)
    
    The Tutor decides whether to:
    - Answer directly (simple queries)
    - Delegate to Orchestrator (complex multi-step tasks)
    """
    
    def __init__(self):
        config = AgentConfig(
            agent_id="tutor_agent",
            name="Tutor Agent",
            description="Primary interface for students. Manages conversation flow, "
                       "session state, and coordinates with other agents for complex tasks.",
            capabilities=[
                AgentCapability.ANSWER_QUESTION,
                AgentCapability.EXPLAIN_CONCEPT
            ],
            allowed_tools=["logging"],  # Minimal tool access
            system_prompt=self._get_tutor_prompt(),
            temperature=0.7  # Balanced for friendly yet accurate responses
        )
        super().__init__(config)
        
        # Session management
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def _get_tutor_prompt(self) -> str:
        return """You are a friendly and knowledgeable tutor in the EduSmartLearn system.

Your role is to:
1. Welcome students and understand their learning needs
2. Answer questions clearly and encouragingly
3. Determine when to handle requests directly vs. delegate to specialists
4. Present information in an accessible, student-friendly way
5. Track conversation context for continuity

Communication style:
- Be warm, encouraging, and patient
- Use clear, jargon-free language when possible
- Provide examples to illustrate concepts
- Ask clarifying questions when needed
- Celebrate student progress and effort

When you receive a request:
- Simple questions: Answer directly
- Complex topics: Indicate you'll get specialized help
- Code requests: Note that code execution requires consent
- Quizzes: Offer to generate practice questions

Always maintain a supportive learning environment."""
    
    def create_session(self, user_id: str) -> str:
        """
        Create a new tutoring session.
        
        Args:
            user_id: Identifier for the student
            
        Returns:
            Session ID for tracking
        """
        session_id = str(uuid4())[:8]
        
        self._sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "message_count": 0,
            "topics_discussed": [],
            "context": {}
        }
        
        logger.info("session_created", session_id=session_id, user_id=user_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs) -> None:
        """Update session with new data."""
        if session_id in self._sessions:
            self._sessions[session_id].update(kwargs)
            self._sessions[session_id]["last_activity"] = datetime.utcnow()
    
    async def process_message(self, message: A2AMessage) -> A2AMessage:
        """
        Process incoming A2A message.
        
        Routes based on message type:
        - TASK_REQUEST: Handle user query
        - TASK_RESPONSE: Format and return orchestrator results
        """
        logger.info(
            "tutor_processing_message",
            message_type=message.message_type.value,
            session_id=message.session_id
        )
        
        if message.message_type == MessageType.TASK_REQUEST:
            return await self._handle_user_request(message)
        elif message.message_type == MessageType.TASK_RESPONSE:
            return await self._format_response(message)
        else:
            return message.create_response(
                message_type=MessageType.ERROR,
                sender=self.agent_id,
                payload={},
                error_code=ErrorCode.INVALID_REQUEST,
                error_message=f"Unsupported message type: {message.message_type}"
            )
    
    async def _handle_user_request(self, message: A2AMessage) -> A2AMessage:
        """
        Handle a user's learning request.
        
        Determines whether to:
        1. Answer directly (simple queries)
        2. Delegate to orchestrator (complex tasks)
        """
        user_query = message.payload.get("query", "")
        session_id = message.session_id
        
        # Update session
        if session_id:
            self.update_session(session_id, message_count=
                self._sessions.get(session_id, {}).get("message_count", 0) + 1
            )
        
        # Classify request complexity
        needs_orchestration = await self._needs_orchestration(user_query)
        
        if needs_orchestration:
            # Delegate to orchestrator
            return A2AMessage(
                message_type=MessageType.TASK_DELEGATION,
                sender=self.agent_id,
                receiver="orchestrator",
                session_id=session_id,
                payload={
                    "request": user_query,
                    "context": self._sessions.get(session_id, {}).get("context", {})
                },
                correlation_id=message.message_id
            )
        else:
            # Handle directly with LLM
            response = await self.generate_response(
                f"Student question: {user_query}\n\nProvide a helpful, encouraging response."
            )
            
            return message.create_response(
                message_type=MessageType.TASK_RESPONSE,
                sender=self.agent_id,
                payload={
                    "response": response,
                    "handled_by": "tutor_direct"
                }
            )
    
    async def _needs_orchestration(self, query: str) -> bool:
        """
        Determine if query needs multi-agent orchestration.
        
        Complex tasks requiring orchestration:
        - Code execution requests
        - Quiz generation
        - Deep topic explanations
        - Document retrieval needs
        """
        # Keywords indicating complex tasks
        complex_indicators = [
            "run", "execute", "code", "program",
            "quiz", "test", "assessment",
            "explain in detail", "teach me",
            "search", "find", "look up",
            "step by step", "tutorial"
        ]
        
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in complex_indicators)
    
    async def _format_response(self, message: A2AMessage) -> A2AMessage:
        """Format orchestrator response for student presentation."""
        raw_response = message.payload.get("response", "")
        
        # Add friendly wrapper if needed
        formatted = await self.generate_response(
            f"Format this response for a student in a friendly, encouraging way:\n\n{raw_response}",
            use_history=False
        )
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={"response": formatted}
        )
    
    async def greet_student(self, session_id: str, student_name: str = "there") -> str:
        """Generate a personalized greeting for the student."""
        greeting = await self.generate_response(
            f"Generate a warm, brief greeting for a student named {student_name} "
            "who is starting a tutoring session. Mention you can help with "
            "explanations, coding practice, and quizzes.",
            use_history=False
        )
        return greeting
