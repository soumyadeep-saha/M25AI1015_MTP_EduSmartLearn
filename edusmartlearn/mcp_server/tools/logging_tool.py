"""
mcp_server/tools/logging_tool.py
================================
Structured Logging Tool for Observability and Audit Trail.

Provides structured logging for:
- A2A message exchanges
- Tool invocations and results
- Policy decisions
- Error tracking

Tool Scope: WRITE access to logs
Agents with access: All agents (for audit compliance)
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntry(BaseModel):
    """Structured log entry."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel
    event_type: str  # e.g., "a2a_message", "tool_call", "policy_decision"
    agent_id: str
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "message": self.message,
            "data": self.data
        }


class LoggingTool:
    """
    Structured logging tool for audit trail and observability.
    
    Features:
    - Structured JSON logs for easy parsing
    - Session-based log filtering
    - Log rotation and retention
    - Query interface for log analysis
    
    Usage:
        tool = LoggingTool(logs_dir=Path("./logs"))
        await tool.log(
            level=LogLevel.INFO,
            event_type="a2a_message",
            agent_id="orchestrator",
            message="Task delegated to teacher agent",
            data={"task_type": "explain_concept"}
        )
    """
    
    TOOL_NAME = "logging"
    TOOL_DESCRIPTION = "Write structured logs for audit trail"
    TOOL_SCHEMA = {
        "type": "object",
        "properties": {
            "level": {"type": "string", "enum": ["debug", "info", "warning", "error"]},
            "event_type": {"type": "string", "description": "Type of event"},
            "message": {"type": "string", "description": "Log message"},
            "data": {"type": "object", "description": "Additional data"}
        },
        "required": ["level", "event_type", "message"]
    }
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self._log_buffer: List[LogEntry] = []
        self._buffer_size = 100  # Flush after this many entries
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize logging directory."""
        if self._initialized:
            return
        
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        logger.info("logging_tool_initialized", logs_dir=str(self.logs_dir))
    
    def _get_log_file(self) -> Path:
        """Get current log file path (daily rotation)."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self.logs_dir / f"edusmartlearn_{date_str}.jsonl"
    
    async def log(
        self,
        level: LogLevel,
        event_type: str,
        agent_id: str,
        message: str,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Write a structured log entry.
        
        Args:
            level: Log severity level
            event_type: Type of event (a2a_message, tool_call, etc.)
            agent_id: ID of the agent generating the log
            message: Human-readable log message
            session_id: Optional session identifier
            trace_id: Optional trace identifier for distributed tracing
            data: Additional structured data
        """
        if not self._initialized:
            await self.initialize()
        
        entry = LogEntry(
            level=level,
            event_type=event_type,
            agent_id=agent_id,
            session_id=session_id,
            trace_id=trace_id,
            message=message,
            data=data or {}
        )
        
        self._log_buffer.append(entry)
        
        # Flush if buffer is full
        if len(self._log_buffer) >= self._buffer_size:
            await self.flush()
        
        # Also log to structlog for console output
        log_method = getattr(logger, level.value)
        log_method(message, event_type=event_type, agent_id=agent_id, **entry.data)
    
    async def flush(self) -> None:
        """Flush log buffer to file."""
        if not self._log_buffer:
            return
        
        log_file = self._get_log_file()
        
        with open(log_file, "a") as f:
            for entry in self._log_buffer:
                f.write(json.dumps(entry.to_dict()) + "\n")
        
        self._log_buffer.clear()
    
    async def query_logs(
        self,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """
        Query logs with filters.
        
        Args:
            session_id: Filter by session
            event_type: Filter by event type
            level: Filter by log level
            start_time: Filter by time (entries after this time)
            limit: Maximum entries to return
        """
        await self.flush()  # Ensure all logs are written
        
        results = []
        log_file = self._get_log_file()
        
        if not log_file.exists():
            return results
        
        with open(log_file, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    entry = LogEntry(
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        level=LogLevel(data["level"]),
                        event_type=data["event_type"],
                        agent_id=data["agent_id"],
                        session_id=data.get("session_id"),
                        trace_id=data.get("trace_id"),
                        message=data["message"],
                        data=data.get("data", {})
                    )
                    
                    # Apply filters
                    if session_id and entry.session_id != session_id:
                        continue
                    if event_type and entry.event_type != event_type:
                        continue
                    if level and entry.level != level:
                        continue
                    if start_time and entry.timestamp < start_time:
                        continue
                    
                    results.append(entry)
                    
                    if len(results) >= limit:
                        break
                        
                except Exception:
                    continue
        
        return results
    
    async def log_a2a_message(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        message_id: str,
        session_id: Optional[str] = None,
        payload_summary: Optional[str] = None
    ) -> None:
        """Convenience method for logging A2A messages."""
        await self.log(
            level=LogLevel.INFO,
            event_type="a2a_message",
            agent_id=sender,
            session_id=session_id,
            message=f"A2A {message_type}: {sender} -> {receiver}",
            data={
                "message_id": message_id,
                "sender": sender,
                "receiver": receiver,
                "message_type": message_type,
                "payload_summary": payload_summary
            }
        )
    
    async def log_tool_call(
        self,
        agent_id: str,
        tool_name: str,
        success: bool,
        execution_time_ms: float,
        session_id: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Convenience method for logging tool calls."""
        level = LogLevel.INFO if success else LogLevel.ERROR
        await self.log(
            level=level,
            event_type="tool_call",
            agent_id=agent_id,
            session_id=session_id,
            message=f"Tool call: {tool_name} ({'success' if success else 'failed'})",
            data={
                "tool_name": tool_name,
                "success": success,
                "execution_time_ms": execution_time_ms,
                "error": error
            }
        )
