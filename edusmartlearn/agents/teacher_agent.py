"""
agents/teacher_agent.py
=======================
Teacher Agent - Content Generation Specialist.

The Teacher Agent is responsible for generating educational content:
- Explanations of concepts
- Examples and analogies
- Step-by-step tutorials
- Code solutions with explanations

Position in Architecture: Multi-Agent Orchestration Layer
Sub-agents: AI Content, ML Content, DL Content, Programming Language agents
"""

from typing import Dict, Any, Optional, List
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from protocols.a2a_protocol import (
    A2AMessage,
    MessageType,
    AgentCapability,
    ErrorCode
)

logger = structlog.get_logger()


class TeacherAgent(BaseAgent):
    """
    Teacher Agent - Generates educational content.
    
    Responsibilities:
    1. Generate clear explanations of concepts
    2. Create examples and analogies
    3. Provide step-by-step guidance
    4. Generate and explain code solutions
    5. Adapt content to learner's level
    
    Uses retrieved context from Retrieval Agent for accuracy.
    """
    
    def __init__(self):
        config = AgentConfig(
            agent_id="teacher_agent",
            name="Teacher Agent",
            description="Generates educational content including explanations, "
                       "examples, tutorials, and code solutions.",
            capabilities=[
                AgentCapability.EXPLAIN_CONCEPT,
                AgentCapability.GENERATE_EXAMPLE,
                AgentCapability.ANSWER_QUESTION,
                AgentCapability.AI_CONTENT,
                AgentCapability.ML_CONTENT,
                AgentCapability.DL_CONTENT,
                AgentCapability.PROGRAMMING
            ],
            allowed_tools=["doc_search", "logging"],
            system_prompt=self._get_teacher_prompt(),
            temperature=0.7
        )
        super().__init__(config)
    
    def _get_teacher_prompt(self) -> str:
        return """You are an expert Teacher Agent in the EduSmartLearn system.

Your expertise spans:
- Artificial Intelligence (AI)
- Machine Learning (ML)
- Deep Learning (DL)
- Programming (Python, algorithms, data structures)

Teaching principles:
1. Start with fundamentals before advanced concepts
2. Use analogies to connect new ideas to familiar ones
3. Provide concrete examples for abstract concepts
4. Break complex topics into digestible steps
5. Include visual descriptions when helpful
6. Anticipate common misconceptions

When explaining code:
- Explain the purpose before the implementation
- Comment key lines
- Discuss time/space complexity when relevant
- Suggest improvements or alternatives

Adapt your explanations based on:
- The learner's apparent level (beginner/intermediate/advanced)
- The specific question or topic
- Any context provided from course materials

Always be accurate, clear, and encouraging."""
    
    async def process_message(self, message: A2AMessage) -> A2AMessage:
        """Process teaching requests."""
        logger.info(
            "teacher_processing",
            message_type=message.message_type.value,
            action=message.payload.get("action")
        )
        
        if message.message_type != MessageType.TASK_REQUEST:
            return message.create_response(
                message_type=MessageType.ERROR,
                sender=self.agent_id,
                payload={},
                error_code=ErrorCode.INVALID_REQUEST,
                error_message="Teacher agent only handles TASK_REQUEST"
            )
        
        action = message.payload.get("action", "explain")
        
        if action == "explain":
            return await self._explain_topic(message)
        elif action == "generate_code":
            return await self._generate_code(message)
        elif action == "explain_code":
            return await self._explain_code(message)
        elif action == "answer":
            return await self._answer_question(message)
        elif action == "generate_example":
            return await self._generate_example(message)
        else:
            return await self._general_response(message)
    
    async def _explain_topic(self, message: A2AMessage) -> A2AMessage:
        """Generate explanation for a topic."""
        topic = message.payload.get("topic", "")
        context = message.payload.get("context", {})
        level = message.payload.get("level", "intermediate")
        
        prompt = f"""Explain the following topic for a {level} level student:

Topic: {topic}

{"Context from course materials: " + str(context) if context else ""}

Structure your explanation with:
1. Brief introduction (what and why it matters)
2. Core concepts explained clearly
3. A practical example
4. Key takeaways

Keep it educational and engaging."""

        explanation = await self.generate_response(prompt)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": explanation,
                "action": "explain",
                "topic": topic
            }
        )
    
    async def _generate_code(self, message: A2AMessage) -> A2AMessage:
        """Generate code solution for a problem."""
        problem = message.payload.get("problem", "")
        language = message.payload.get("language", "python")
        
        prompt = f"""Generate a {language} solution for this problem:

Problem: {problem}

Provide:
1. The complete, working code
2. Comments explaining key parts
3. Example usage
4. Brief explanation of the approach

Make the code clean, readable, and educational."""

        code_solution = await self.generate_response(prompt)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": code_solution,
                "action": "generate_code",
                "language": language
            }
        )
    
    async def _explain_code(self, message: A2AMessage) -> A2AMessage:
        """Explain existing code."""
        code = message.payload.get("code", "")
        execution_result = message.payload.get("execution_result", "")
        
        prompt = f"""Explain this code to a student:

```
{code}
```

{"Execution result: " + execution_result if execution_result else ""}

Provide:
1. What the code does (high-level purpose)
2. Line-by-line explanation of key parts
3. Any important concepts demonstrated
4. Potential improvements or variations"""

        explanation = await self.generate_response(prompt)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": explanation,
                "action": "explain_code"
            }
        )
    
    async def _answer_question(self, message: A2AMessage) -> A2AMessage:
        """Answer a specific question."""
        question = message.payload.get("question", "")
        context = message.payload.get("context", {})
        
        prompt = f"""Answer this student's question:

Question: {question}

{"Relevant context: " + str(context) if context else ""}

Provide a clear, accurate answer that:
1. Directly addresses the question
2. Explains the reasoning
3. Gives an example if helpful
4. Suggests related topics to explore"""

        answer = await self.generate_response(prompt)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": answer,
                "action": "answer",
                "question": question
            }
        )
    
    async def _generate_example(self, message: A2AMessage) -> A2AMessage:
        """Generate examples for a concept."""
        concept = message.payload.get("concept", "")
        num_examples = message.payload.get("num_examples", 2)
        
        prompt = f"""Generate {num_examples} clear examples for this concept:

Concept: {concept}

For each example:
1. Describe the scenario
2. Show how the concept applies
3. Explain why it's a good example

Make examples practical and memorable."""

        examples = await self.generate_response(prompt)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": examples,
                "action": "generate_example",
                "concept": concept
            }
        )
    
    async def _general_response(self, message: A2AMessage) -> A2AMessage:
        """Handle general teaching requests."""
        request = message.payload.get("request", "")
        
        response = await self.generate_response(
            f"As a teacher, respond to: {request}"
        )
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={"output": response, "action": "general"}
        )
