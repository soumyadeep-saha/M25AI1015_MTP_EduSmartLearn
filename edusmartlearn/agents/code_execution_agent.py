"""
agents/code_execution_agent.py
==============================
Code Execution Agent - Sandboxed Code Runner.

The Code Execution Agent handles programming practice by:
- Generating code solutions
- Running code in a secure sandbox
- Debugging and explaining errors
- Verifying outputs

Position in Architecture: Multi-Agent Orchestration Layer
Tool Access: code_run (EXECUTE - requires CONSENT)

SECURITY: All code execution requires explicit user consent.
"""

from typing import Dict, Any, Optional
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from protocols.a2a_protocol import (
    A2AMessage,
    MessageType,
    AgentCapability,
    ErrorCode,
    ConsentRequirement
)
from mcp_server.tools.code_run import CodeRunTool, ExecutionResult

logger = structlog.get_logger()


class CodeExecutionAgent(BaseAgent):
    """
    Code Execution Agent - Runs code in a secure sandbox.
    
    Responsibilities:
    1. Execute student code safely
    2. Capture and explain output/errors
    3. Debug code issues
    4. Verify code correctness
    
    SECURITY FEATURES:
    - Requires explicit user consent before execution
    - Runs in sandboxed environment
    - Limited execution time and memory
    - No file/network access
    """
    
    def __init__(self):
        config = AgentConfig(
            agent_id="code_execution_agent",
            name="Code Execution Agent",
            description="Executes code in a secure sandbox with user consent. "
                       "Provides debugging and output verification.",
            capabilities=[
                AgentCapability.CODE_EXECUTION,
                AgentCapability.PROGRAMMING
            ],
            allowed_tools=["code_run", "logging"],
            system_prompt=self._get_code_prompt(),
            temperature=0.3  # Lower for precise code handling
        )
        super().__init__(config)
        
        # Initialize code execution tool
        from config.settings import settings
        self.code_tool = CodeRunTool(
            timeout=settings.safety.code_execution_timeout,
            max_memory_mb=settings.safety.code_max_memory_mb
        )
    
    def _get_code_prompt(self) -> str:
        return """You are the Code Execution Agent in EduSmartLearn.

Your role is to:
1. Execute student code safely in a sandbox
2. Explain execution results clearly
3. Debug errors and suggest fixes
4. Verify code correctness

Security guidelines:
- ALWAYS require user consent before execution
- Run only in the sandboxed environment
- Explain any security restrictions to students
- Never execute code that could be harmful

When explaining results:
- Show output clearly
- Explain any errors in student-friendly terms
- Suggest specific fixes for bugs
- Highlight good coding practices

Help students learn through hands-on coding practice."""
    
    async def process_message(self, message: A2AMessage) -> A2AMessage:
        """Process code execution requests."""
        logger.info(
            "code_agent_processing",
            message_type=message.message_type.value,
            action=message.payload.get("action")
        )
        
        if message.message_type == MessageType.CONSENT_RESPONSE:
            return await self._handle_consent_response(message)
        
        if message.message_type != MessageType.TASK_REQUEST:
            return message.create_response(
                message_type=MessageType.ERROR,
                sender=self.agent_id,
                payload={},
                error_code=ErrorCode.INVALID_REQUEST,
                error_message="Code agent handles TASK_REQUEST or CONSENT_RESPONSE"
            )
        
        action = message.payload.get("action", "execute")
        
        if action == "execute":
            return await self._execute_code(message)
        elif action == "debug":
            return await self._debug_code(message)
        elif action == "verify":
            return await self._verify_code(message)
        else:
            return await self._execute_code(message)
    
    async def _execute_code(self, message: A2AMessage) -> A2AMessage:
        """Execute code with consent check."""
        code = message.payload.get("code", "")
        require_consent = message.payload.get("require_consent", True)
        consent_granted = message.consent.granted
        
        # Check if consent is required and not yet granted
        if require_consent and not consent_granted:
            # Request consent from user
            return A2AMessage(
                message_type=MessageType.CONSENT_REQUEST,
                sender=self.agent_id,
                receiver="tutor_agent",  # Goes back to tutor for user
                correlation_id=message.message_id,
                session_id=message.session_id,
                consent=ConsentRequirement(
                    required=True,
                    operation_type="code_execution",
                    description=f"Execute the following code:\n```\n{code[:500]}{'...' if len(code) > 500 else ''}\n```",
                    granted=None
                ),
                payload={
                    "code": code,
                    "original_message_id": message.message_id
                }
            )
        
        # Execute with consent
        result = await self.code_tool.execute(
            code=code,
            consent_verified=True
        )
        
        # Format result for student
        formatted = await self._format_execution_result(code, result)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": formatted,
                "action": "execute",
                "success": result.success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error_type": result.error_type,
                "error_message": result.error_message,
                "execution_time_ms": result.execution_time_ms
            }
        )
    
    async def _format_execution_result(
        self,
        code: str,
        result: ExecutionResult
    ) -> str:
        """Format execution result for student understanding."""
        if result.success:
            output = f"""**Code Execution Successful** ✓

**Output:**
```
{result.stdout if result.stdout else '(no output)'}
```

**Execution time:** {result.execution_time_ms:.2f}ms
"""
            if result.return_value:
                output += f"\n**Return value:** {result.return_value}"
        else:
            # Generate helpful error explanation
            error_explanation = await self.generate_response(
                f"""Explain this error to a student learning to code:

Code:
```python
{code}
```

Error type: {result.error_type}
Error message: {result.error_message}
Error line: {result.error_line}

Provide:
1. What the error means in simple terms
2. Why it occurred
3. How to fix it""",
                use_history=False
            )
            
            output = f"""**Code Execution Failed** ✗

**Error:** {result.error_type}
**Message:** {result.error_message}
{f'**Line:** {result.error_line}' if result.error_line else ''}

**Explanation:**
{error_explanation}
"""
        
        return output
    
    async def _debug_code(self, message: A2AMessage) -> A2AMessage:
        """Debug code and suggest fixes."""
        code = message.payload.get("code", "")
        error = message.payload.get("error", "")
        
        prompt = f"""Debug this code and provide fixes:

Code:
```python
{code}
```

Error: {error}

Provide:
1. Identify the bug(s)
2. Explain why they cause the error
3. Show the corrected code
4. Explain the fix"""

        debug_response = await self.generate_response(prompt, use_history=False)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": debug_response,
                "action": "debug"
            }
        )
    
    async def _verify_code(self, message: A2AMessage) -> A2AMessage:
        """Verify code against expected output."""
        code = message.payload.get("code", "")
        expected_output = message.payload.get("expected_output", "")
        
        # Execute the code
        result = await self.code_tool.execute(code=code, consent_verified=True)
        
        # Compare outputs
        actual = result.stdout.strip() if result.success else ""
        expected = expected_output.strip()
        matches = actual == expected
        
        verification = f"""**Code Verification**

**Expected output:**
```
{expected}
```

**Actual output:**
```
{actual if result.success else f'Error: {result.error_message}'}
```

**Result:** {'✓ PASS' if matches else '✗ FAIL'}
"""
        
        if not matches and result.success:
            # Explain difference
            diff_explanation = await self.generate_response(
                f"Explain why this code output differs from expected:\n"
                f"Expected: {expected}\nActual: {actual}",
                use_history=False
            )
            verification += f"\n**Analysis:**\n{diff_explanation}"
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": verification,
                "action": "verify",
                "passed": matches,
                "expected": expected,
                "actual": actual
            }
        )
    
    async def _handle_consent_response(self, message: A2AMessage) -> A2AMessage:
        """Handle user's consent decision."""
        if message.consent.granted:
            # Proceed with execution
            code = message.payload.get("code", "")
            result = await self.code_tool.execute(code=code, consent_verified=True)
            formatted = await self._format_execution_result(code, result)
            
            return message.create_response(
                message_type=MessageType.TASK_RESPONSE,
                sender=self.agent_id,
                payload={"output": formatted, "action": "execute", "success": result.success}
            )
        else:
            return message.create_response(
                message_type=MessageType.TASK_RESPONSE,
                sender=self.agent_id,
                payload={
                    "output": "Code execution was not approved. I can still help explain the code without running it.",
                    "action": "execute",
                    "success": False
                },
                error_code=ErrorCode.CONSENT_DENIED,
                error_message="User did not consent to code execution"
            )
