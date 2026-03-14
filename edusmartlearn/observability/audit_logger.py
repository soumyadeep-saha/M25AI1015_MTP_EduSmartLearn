"""
observability/audit_logger.py
=============================
Audit Logger - Structured logging for compliance and debugging.

Records:
- All A2A message exchanges
- Tool invocations and results
- Policy decisions
- Security events
- Error tracking
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from enum import Enum
import structlog

from config.settings import settings

logger = structlog.get_logger()


class AuditEventType(str, Enum):
    """Types of audit events."""
    A2A_MESSAGE = "a2a_message"
    TOOL_CALL = "tool_call"
    POLICY_DECISION = "policy_decision"
    SECURITY_EVENT = "security_event"
    SESSION_EVENT = "session_event"
    ERROR = "error"
    USER_ACTION = "user_action"


class AuditEntry:
    """Represents a single audit log entry."""
    
    def __init__(
        self,
        event_type: AuditEventType,
        agent_id: str,
        action: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        outcome: str = "success"
    ):
        self.timestamp = datetime.utcnow()
        self.event_type = event_type
        self.agent_id = agent_id
        self.action = action
        self.session_id = session_id
        self.user_id = user_id
        self.details = details or {}
        self.outcome = outcome
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "action": self.action,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "details": self.details,
            "outcome": self.outcome
        }


class AuditLogger:
    """
    Structured audit logging for compliance and debugging.
    
    Features:
    - Structured JSON logs
    - Daily log rotation
    - Query interface for analysis
    - Compliance-ready format
    """
    
    def __init__(self, logs_dir: Optional[Path] = None):
        self.logs_dir = logs_dir or settings.logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._buffer: List[AuditEntry] = []
        self._buffer_size = 50
    
    def _get_log_file(self) -> Path:
        """Get current log file (daily rotation)."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.logs_dir / f"audit_{date_str}.jsonl"
    
    def log(self, entry: AuditEntry) -> None:
        """Log an audit entry."""
        self._buffer.append(entry)
        
        # Also log to structlog for console output
        logger.info(
            entry.action,
            event_type=entry.event_type.value,
            agent_id=entry.agent_id,
            outcome=entry.outcome
        )
        
        if len(self._buffer) >= self._buffer_size:
            self.flush()
    
    def log_a2a_message(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        message_id: str,
        session_id: Optional[str] = None
    ) -> None:
        """Log an A2A message exchange."""
        self.log(AuditEntry(
            event_type=AuditEventType.A2A_MESSAGE,
            agent_id=sender,
            action=f"a2a_{message_type}",
            session_id=session_id,
            details={
                "message_id": message_id,
                "sender": sender,
                "receiver": receiver,
                "message_type": message_type
            }
        ))
    
    def log_tool_call(
        self,
        agent_id: str,
        tool_name: str,
        success: bool,
        execution_time_ms: float,
        session_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Log a tool invocation."""
        self.log(AuditEntry(
            event_type=AuditEventType.TOOL_CALL,
            agent_id=agent_id,
            action=f"tool_{tool_name}",
            session_id=session_id,
            outcome="success" if success else "failure",
            details={
                "tool_name": tool_name,
                "execution_time_ms": execution_time_ms,
                "error": error
            }
        ))
    
    def log_policy_decision(
        self,
        agent_id: str,
        policy: str,
        decision: str,
        reason: str,
        session_id: Optional[str] = None
    ) -> None:
        """Log a policy decision."""
        self.log(AuditEntry(
            event_type=AuditEventType.POLICY_DECISION,
            agent_id=agent_id,
            action=f"policy_{policy}",
            session_id=session_id,
            outcome=decision,
            details={"policy": policy, "reason": reason}
        ))
    
    def log_security_event(
        self,
        agent_id: str,
        event: str,
        severity: str,
        details: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> None:
        """Log a security-relevant event."""
        self.log(AuditEntry(
            event_type=AuditEventType.SECURITY_EVENT,
            agent_id=agent_id,
            action=f"security_{event}",
            session_id=session_id,
            outcome=severity,
            details=details
        ))
    
    def flush(self) -> None:
        """Flush buffer to file."""
        if not self._buffer:
            return
        
        log_file = self._get_log_file()
        
        with open(log_file, "a") as f:
            for entry in self._buffer:
                f.write(json.dumps(entry.to_dict()) + "\n")
        
        self._buffer.clear()
    
    def query(
        self,
        event_type: Optional[AuditEventType] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters."""
        self.flush()
        
        results = []
        log_file = self._get_log_file()
        
        if not log_file.exists():
            return results
        
        with open(log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    # Apply filters
                    if event_type and entry["event_type"] != event_type.value:
                        continue
                    if session_id and entry.get("session_id") != session_id:
                        continue
                    if agent_id and entry["agent_id"] != agent_id:
                        continue
                    if start_time:
                        entry_time = datetime.fromisoformat(entry["timestamp"])
                        if entry_time < start_time:
                            continue
                    
                    results.append(entry)
                    
                    if len(results) >= limit:
                        break
                        
                except Exception:
                    continue
        
        return results


# Global audit logger instance
audit_logger = AuditLogger()
