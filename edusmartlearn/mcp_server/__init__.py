# MCP Server module for EduSmartLearn
# Provides tool access via Model Context Protocol

from mcp_server.tools import doc_search, code_run, quiz_bank, logging_tool

__all__ = ["doc_search", "code_run", "quiz_bank", "logging_tool"]
