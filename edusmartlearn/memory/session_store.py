"""
memory/session_store.py
=======================
Session Store - Manages active tutoring sessions.

Handles:
- Session creation and lifecycle
- Conversation history within sessions
- Session context and state
- Session timeout and cleanup
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import uuid4
from pathlib import Path
import json
from pydantic import BaseModel, Field
import structlog

from config.settings import settings

logger = structlog.get_logger()


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    turn_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """Represents an active tutoring session."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Conversation history
    history: List[ConversationTurn] = Field(default_factory=list)
    
    # Session context (accumulated knowledge about current session)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Topics discussed in this session
    topics: List[str] = Field(default_factory=list)
    
    # Session status
    status: str = "active"  # active, paused, ended
    
    def is_expired(self) -> bool:
        """Check if session has expired due to inactivity."""
        timeout = timedelta(minutes=settings.session.session_timeout_minutes)
        return datetime.utcnow() - self.last_activity > timeout
    
    def add_turn(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add a conversation turn."""
        turn = ConversationTurn(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.history.append(turn)
        self.last_activity = datetime.utcnow()
        
        # Trim history if too long
        max_turns = settings.session.max_history_turns
        if len(self.history) > max_turns:
            self.history = self.history[-max_turns:]
    
    def get_recent_history(self, n: int = 10) -> List[ConversationTurn]:
        """Get the n most recent conversation turns."""
        return self.history[-n:]
    
    def get_context_string(self) -> str:
        """Get session context as a formatted string."""
        parts = []
        if self.topics:
            parts.append(f"Topics discussed: {', '.join(self.topics)}")
        if self.context:
            for key, value in self.context.items():
                parts.append(f"{key}: {value}")
        return "\n".join(parts)


class SessionStore:
    """
    Manages active tutoring sessions with persistence.
    
    Features:
    - Create and retrieve sessions
    - Track conversation history
    - Handle session expiration
    - Provide session context for agents
    - **Persist conversations to disk**
    """
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, str] = {}  # user_id -> active session_id
        
        # Conversation persistence directory
        self._conversations_dir = settings.data_dir / "conversations"
        self._conversations_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(self, user_id: str) -> Session:
        """Create a new session for a user."""
        # End any existing session for this user
        if user_id in self._user_sessions:
            old_session_id = self._user_sessions[user_id]
            self.end_session(old_session_id)
        
        session = Session(user_id=user_id)
        self._sessions[session.session_id] = session
        self._user_sessions[user_id] = session.session_id
        
        logger.info("session_created", session_id=session.session_id, user_id=user_id)
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        
        if session and session.is_expired():
            self.end_session(session_id)
            return None
        
        return session
    
    def get_user_session(self, user_id: str) -> Optional[Session]:
        """Get the active session for a user."""
        session_id = self._user_sessions.get(user_id)
        if session_id:
            return self.get_session(session_id)
        return None
    
    def get_or_create_session(self, user_id: str) -> Session:
        """Get existing session or create new one."""
        session = self.get_user_session(user_id)
        if not session:
            session = self.create_session(user_id)
        return session
    
    def end_session(self, session_id: str) -> None:
        """End a session and save conversation to disk."""
        session = self._sessions.get(session_id)
        if session:
            session.status = "ended"
            
            # Save conversation to disk before ending
            self._save_conversation(session)
            
            # Remove from user mapping
            if session.user_id in self._user_sessions:
                if self._user_sessions[session.user_id] == session_id:
                    del self._user_sessions[session.user_id]
            
            logger.info("session_ended", session_id=session_id)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Add a message to session history and auto-save."""
        session = self.get_session(session_id)
        if session:
            session.add_turn(role, content, metadata)
            # Auto-save after each message for persistence
            self._save_conversation(session)
    
    def update_context(self, session_id: str, **kwargs) -> None:
        """Update session context."""
        session = self.get_session(session_id)
        if session:
            session.context.update(kwargs)
            session.last_activity = datetime.utcnow()
    
    def add_topic(self, session_id: str, topic: str) -> None:
        """Add a topic to the session."""
        session = self.get_session(session_id)
        if session and topic not in session.topics:
            session.topics.append(topic)
    
    def cleanup_expired(self) -> int:
        """Clean up expired sessions. Returns count of cleaned sessions."""
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired:
            self.end_session(session_id)
        
        return len(expired)
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        return len([s for s in self._sessions.values() if s.status == "active"])
    
    def _save_conversation(self, session: Session) -> None:
        """Save conversation history to disk."""
        if not session.history:
            return
        
        # Create filename with user_id and date
        date_str = session.created_at.strftime("%Y-%m-%d")
        filename = f"{session.user_id}_{date_str}_{session.session_id[:8]}.json"
        filepath = self._conversations_dir / filename
        
        # Prepare conversation data
        conversation_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "status": session.status,
            "topics": session.topics,
            "messages": [
                {
                    "turn_id": turn.turn_id,
                    "role": turn.role,
                    "content": turn.content,
                    "timestamp": turn.timestamp.isoformat(),
                    "metadata": turn.metadata
                }
                for turn in session.history
            ]
        }
        
        # Write to file
        with open(filepath, "w") as f:
            json.dump(conversation_data, f, indent=2)
        
        logger.info("conversation_saved", file=str(filepath), messages=len(session.history))
    
    def load_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Load all saved conversations for a user."""
        conversations = []
        
        for filepath in self._conversations_dir.glob(f"{user_id}_*.json"):
            try:
                with open(filepath, "r") as f:
                    conversations.append(json.load(f))
            except Exception as e:
                logger.warning("conversation_load_failed", file=str(filepath), error=str(e))
        
        # Sort by created_at descending
        conversations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return conversations
    
    def get_conversation_history(self, user_id: str, limit: int = 5) -> str:
        """Get formatted conversation history for a user."""
        conversations = self.load_user_conversations(user_id)[:limit]
        
        if not conversations:
            return "No previous conversations found."
        
        lines = [f"Previous conversations for {user_id}:"]
        for conv in conversations:
            date = conv.get("created_at", "Unknown")[:10]
            msg_count = len(conv.get("messages", []))
            topics = ", ".join(conv.get("topics", [])) or "General"
            lines.append(f"  - {date}: {msg_count} messages, Topics: {topics}")
        
        return "\n".join(lines)


# Global session store instance
session_store = SessionStore()
