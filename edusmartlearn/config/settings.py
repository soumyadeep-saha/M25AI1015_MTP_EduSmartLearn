"""
config/settings.py
==================
Global configuration settings for EduSmartLearn multi-agent teaching system.

This module manages:
- API keys and credentials (loaded from environment)
- Model configurations for Gemini LLM
- MCP server settings
- Safety and guardrail parameters
- Session management settings

Usage:
    from config.settings import settings
    api_key = settings.gemini.api_key
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GeminiConfig(BaseModel):
    """
    Configuration for Google Gemini LLM backend.
    
    Gemini is used as the language model for all agents in the system.
    The gemini-1.5-flash model provides a good balance of speed and quality.
    """
    
    # API key loaded from environment variable for security
    # NEVER hardcode API keys in source code
    api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    
    # Model selection: gemini-2.0-flash is fast and cost-effective
    # Alternative: gemini-1.5-pro for more complex reasoning
    model_name: str = "gemini-2.0-flash"
    
    # Temperature controls randomness in generation
    # 0.0 = deterministic, 1.0 = very creative
    # 0.7 balances creativity with consistency for teaching
    temperature: float = 0.7
    
    # Maximum tokens in model response
    max_output_tokens: int = 2048
    
    # Top-p (nucleus sampling) for response diversity
    top_p: float = 0.95
    
    # Top-k limits vocabulary choices
    top_k: int = 40


class MCPConfig(BaseModel):
    """
    Configuration for Model Context Protocol (MCP) server.
    
    MCP provides standardized tool access for agents including:
    - Document search (RAG)
    - Code execution (sandboxed)
    - Quiz bank operations
    - Structured logging
    """
    
    # Server host and port
    host: str = Field(default_factory=lambda: os.getenv("MCP_HOST", "localhost"))
    port: int = Field(default_factory=lambda: int(os.getenv("MCP_PORT", "8080")))
    
    # Timeout for tool calls in seconds
    tool_timeout: int = 30
    
    # Maximum retries for failed tool calls
    max_retries: int = 3
    
    # Retry backoff multiplier
    retry_backoff: float = 1.5


class SafetyConfig(BaseModel):
    """
    Safety and guardrail configuration.
    
    Implements defense-in-depth security:
    - Consent requirements for sensitive operations
    - Sandboxing limits for code execution
    - Rate limiting to prevent abuse
    - Content filtering for harmful content
    """
    
    # === Consent Requirements (HITL - Human In The Loop) ===
    # These operations require explicit user approval before execution
    require_consent_for_code_execution: bool = True
    require_consent_for_data_storage: bool = True
    
    # === Code Execution Sandbox Limits ===
    # Prevents resource exhaustion and malicious code
    code_execution_timeout: int = 10  # Maximum execution time in seconds
    code_max_memory_mb: int = 128     # Maximum memory usage
    code_allow_network: bool = False   # Network access disabled by default
    code_allow_file_io: bool = False   # File I/O disabled by default
    
    # === Rate Limiting ===
    # Prevents abuse and ensures fair resource usage
    max_requests_per_minute: int = 60
    max_tool_calls_per_session: int = 100
    
    # === Content Filtering ===
    block_harmful_content: bool = True
    sanitize_user_input: bool = True
    
    # === Prompt Injection Defense ===
    # Separates user content from system instructions
    enable_input_sanitization: bool = True
    max_input_length: int = 10000  # Characters


class SessionConfig(BaseModel):
    """
    Session and memory configuration.
    
    Manages:
    - Session lifecycle and timeouts
    - Conversation history limits
    - Long-term memory for personalization
    """
    
    # Session timeout in minutes (inactive sessions expire)
    session_timeout_minutes: int = 60
    
    # Maximum conversation turns to keep in context
    # Prevents context window overflow
    max_history_turns: int = 20
    
    # Long-term memory settings for learner personalization
    enable_long_term_memory: bool = True
    memory_retention_days: int = 90  # How long to keep learner data


class Settings(BaseModel):
    """
    Main settings container aggregating all configurations.
    
    This is the primary configuration object used throughout the system.
    Import and use: from config.settings import settings
    """
    
    # === Project Paths ===
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    
    # === Sub-configurations ===
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    
    # === Debug Mode ===
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "course_materials").mkdir(exist_ok=True)
        (self.data_dir / "learner_profiles").mkdir(exist_ok=True)


# Global settings instance - import this in other modules
settings = Settings()
