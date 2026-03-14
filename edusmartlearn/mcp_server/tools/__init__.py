# MCP Tools for EduSmartLearn
# Each tool provides specific functionality with least-privilege access

from mcp_server.tools.doc_search import DocSearchTool
from mcp_server.tools.code_run import CodeRunTool
from mcp_server.tools.quiz_bank import QuizBankTool
from mcp_server.tools.logging_tool import LoggingTool

__all__ = ["DocSearchTool", "CodeRunTool", "QuizBankTool", "LoggingTool"]
