"""
agents/base_agent.py
====================
Base Agent Class for EduSmartLearn Multi-Agent System.

This module provides the foundational agent class that all specialized
agents inherit from. It handles:
- LLM integration with Google Gemini
- A2A protocol message handling
- MCP tool access with permission checking
- Logging and observability

Architecture:
    BaseAgent (abstract)
        ├── TutorAgent (session management)
        ├── OrchestratorAgent (workflow coordination)
        ├── TeacherAgent (content generation)
        ├── RetrievalAgent (RAG)
        ├── QuizAgent (assessments)
        ├── CodeExecutionAgent (sandboxed execution)
        ├── EvaluatorAgent (quality checking)
        ├── SafetyAgent (guardrails)
        └── StudentModelAgent (personalization)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import structlog

from protocols.a2a_protocol import (
    A2AMessage, 
    MessageType, 
    AgentCapability, 
    ErrorCode,
    a2a_router
)
from config.settings import settings

logger = structlog.get_logger()


class AgentConfig(BaseModel):
    """
    Configuration for an agent instance.
    
    Defines the agent's identity, capabilities, and permissions.
    Each agent type creates its own config with appropriate settings.
    """
    # Unique identifier (e.g., "teacher_agent", "orchestrator")
    agent_id: str
    
    # Human-readable name for display
    name: str
    
    # Description of agent's purpose and responsibilities
    description: str
    
    # Capabilities this agent provides (for A2A routing)
    capabilities: List[AgentCapability]
    
    # MCP tools this agent can access (least-privilege)
    allowed_tools: List[str] = Field(default_factory=list)
    
    # System prompt for the LLM (defines agent behavior)
    system_prompt: str = ""
    
    # Model configuration overrides
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents in EduSmartLearn.
    
    Provides:
    1. LLM integration via Google Gemini API
    2. A2A message handling (send/receive)
    3. MCP tool invocation with permission checking
    4. Structured logging for observability
    
    Subclasses must implement:
    - process_message(): Handle incoming A2A messages
    
    Example:
        class TeacherAgent(BaseAgent):
            def __init__(self):
                config = AgentConfig(
                    agent_id="teacher_agent",
                    name="Teacher Agent",
                    capabilities=[AgentCapability.EXPLAIN_CONCEPT],
                    allowed_tools=["doc_search", "logging"]
                )
                super().__init__(config)
            
            async def process_message(self, message: A2AMessage) -> A2AMessage:
                # Generate teaching content
                response = await self.generate_response(message.payload["topic"])
                return message.create_response(...)
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration with ID, capabilities, tools
        """
        self.config = config
        self.agent_id = config.agent_id
        self.name = config.name
        self.capabilities = config.capabilities
        self.allowed_tools = set(config.allowed_tools)
        
        # Initialize Gemini LLM
        self._init_llm()
        
        # Register with A2A router for message routing
        a2a_router.register_agent(self.agent_id, self.capabilities)
        
        # Conversation history for context
        self._conversation_history: List[Dict[str, str]] = []
        
        logger.info(
            "agent_initialized",
            agent_id=self.agent_id,
            capabilities=[c.value for c in self.capabilities],
            tools=list(self.allowed_tools)
        )
    
    def _init_llm(self) -> None:
        """
        Initialize the Google Gemini LLM client.
        
        Uses gemini-2.0-flash by default for fast, cost-effective responses.
        Configuration can be overridden per-agent.
        """
        # Initialize client with API key
        self.client = genai.Client(api_key=settings.gemini.api_key)
        
        # Store model name for later use
        self.model_name = settings.gemini.model_name
        
        # Build generation config with system instruction
        system_prompt = self.config.system_prompt or self._get_default_system_prompt()
        
        self.generation_config = types.GenerateContentConfig(
            temperature=self.config.temperature or settings.gemini.temperature,
            max_output_tokens=self.config.max_output_tokens or settings.gemini.max_output_tokens,
            top_p=settings.gemini.top_p,
            top_k=settings.gemini.top_k,
            system_instruction=system_prompt
        )
        
        # Chat history for multi-turn conversations
        self._chat_history: List[types.Content] = []
    
    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt for this agent.
        
        Subclasses should override this for specialized prompts.
        """
        return f"""You are {self.name}, an AI agent in the EduSmartLearn teaching system.

Your role: {self.config.description}

Guidelines:
1. Provide accurate, educational content appropriate for the learner's level.
2. Be encouraging and supportive while maintaining academic rigor.
3. Use clear explanations with examples when helpful.
4. If uncertain about something, acknowledge it honestly.
5. Follow safety guidelines and avoid harmful content.

Your capabilities: {', '.join(c.value for c in self.capabilities)}
"""
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        use_history: bool = True
    ) -> str:
        """
        Generate a response using the Gemini LLM.
        
        Args:
            prompt: Input prompt for the model
            context: Optional context (e.g., retrieved documents)
            use_history: Whether to use conversation history
            
        Returns:
            Generated text response
        """
        # Build full prompt with context if provided
        full_prompt = prompt
        if context:
            context_str = "\n".join(f"[{k}]: {v}" for k, v in context.items())
            full_prompt = f"Context:\n{context_str}\n\nQuery: {prompt}"
        
        try:
            # Build contents list
            contents = []
            if use_history:
                contents.extend(self._chat_history)
            
            # Add current user message
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=full_prompt)]
            ))
            
            # Generate response
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=self.generation_config
            )
            
            result = response.text
            
            # Update chat history for multi-turn
            if use_history:
                self._chat_history.append(types.Content(
                    role="user",
                    parts=[types.Part(text=full_prompt)]
                ))
                self._chat_history.append(types.Content(
                    role="model",
                    parts=[types.Part(text=result)]
                ))
            
            # Store in history
            self._conversation_history.append({
                "role": "user",
                "content": prompt
            })
            self._conversation_history.append({
                "role": "assistant", 
                "content": result
            })
            
            logger.debug(
                "llm_response_generated",
                agent_id=self.agent_id,
                prompt_length=len(prompt),
                response_length=len(result)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "llm_generation_failed",
                agent_id=self.agent_id,
                error=str(e)
            )
            raise
    
    async def send_message(self, message: A2AMessage) -> None:
        """
        Send an A2A message to another agent.
        
        The message is logged and routed via the A2A router.
        
        Args:
            message: A2A message to send
        """
        # Log for audit trail
        a2a_router.log_message(message)
        
        logger.info(
            "a2a_message_sent",
            sender=message.sender,
            receiver=message.receiver,
            message_type=message.message_type.value,
            message_id=message.message_id
        )
    
    @abstractmethod
    async def process_message(self, message: A2AMessage) -> A2AMessage:
        """
        Process an incoming A2A message.
        
        Must be implemented by all agent subclasses.
        
        Args:
            message: Incoming A2A message
            
        Returns:
            Response A2A message
        """
        pass
    
    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent has permission to use a tool."""
        return tool_name in self.allowed_tools
    
    async def invoke_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke an MCP tool with permission checking.
        
        Args:
            tool_name: Name of tool to invoke
            parameters: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            PermissionError: If agent lacks tool access
        """
        # Least-privilege check
        if not self.can_use_tool(tool_name):
            logger.warning(
                "tool_access_denied",
                agent_id=self.agent_id,
                tool=tool_name
            )
            raise PermissionError(
                f"Agent {self.agent_id} does not have access to tool {tool_name}"
            )
        
        logger.info(
            "tool_invocation",
            agent_id=self.agent_id,
            tool=tool_name
        )
        
        # Return placeholder - actual implementation connects to MCP server
        return {"status": "success", "tool": tool_name}
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get capabilities this agent provides."""
        return self.capabilities
    
    def reset_conversation(self) -> None:
        """Reset conversation history for new session."""
        self._chat_history.clear()
        self._conversation_history.clear()
        logger.info("conversation_reset", agent_id=self.agent_id)
