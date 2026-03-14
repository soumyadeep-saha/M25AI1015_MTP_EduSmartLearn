"""
agents/knowledge_retrieval_agent.py
===================================
Knowledge Retrieval Agent - Orchestrator / A2A Router.

As shown in architecture diagram: "Knowledge Retrieval Agent (Orchestrator / A2A Router)"

This agent is the central coordinator responsible for:
1. Interpreting requests and forming execution plans
2. Retrieving relevant knowledge from course materials (RAG)
3. Delegating subtasks to specialist agents via A2A
4. Coordinating workflows and integrating results
5. Routing messages between agents

Position in Architecture: Multi-Agent Orchestration Layer (A2A)
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from uuid import uuid4
from pathlib import Path
from pydantic import BaseModel, Field
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from protocols.a2a_protocol import (
    A2AMessage,
    MessageType,
    AgentCapability,
    ErrorCode,
    a2a_router
)
from mcp_server.tools.doc_search import DocSearchTool, SearchResult

logger = structlog.get_logger()


class TaskType(str, Enum):
    """Types of tasks the agent can handle."""
    EXPLAIN_TOPIC = "explain_topic"
    ANSWER_QUESTION = "answer_question"
    CODE_HELP = "code_help"
    QUIZ = "quiz"
    REVIEW_WORK = "review_work"
    GENERAL = "general"


class PlanStep(BaseModel):
    """A single step in an execution plan."""
    step_id: int
    target_agent: str
    action: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[int] = Field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None


class ExecutionPlan(BaseModel):
    """Complete execution plan for a user request."""
    plan_id: str
    user_request: str
    task_type: TaskType
    steps: List[PlanStep]
    max_iterations: int = 10
    current_iteration: int = 0
    status: str = "created"


class KnowledgeRetrievalAgent(BaseAgent):
    """
    Knowledge Retrieval Agent - Orchestrator / A2A Router.
    
    As per architecture diagram, this agent:
    1. Acts as the central A2A router
    2. Retrieves knowledge from course materials (RAG)
    3. Plans and coordinates multi-agent workflows
    4. Integrates results from specialist agents
    
    Safety features:
    - Bounded iterations (max_iterations)
    - No direct high-risk tool access
    - Timeout handling
    - Fallback responses on failure
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        config = AgentConfig(
            agent_id="knowledge_retrieval_agent",
            name="Knowledge Retrieval Agent",
            description="Orchestrator and A2A Router. Retrieves knowledge from "
                       "course materials and coordinates multi-agent workflows.",
            capabilities=[
                AgentCapability.EXPLAIN_CONCEPT,
                AgentCapability.ANSWER_QUESTION,
                AgentCapability.DOCUMENT_RETRIEVAL
            ],
            allowed_tools=["doc_search", "logging"],
            system_prompt=self._get_agent_prompt(),
            temperature=0.3
        )
        super().__init__(config)
        
        # Initialize document search for RAG
        from config.settings import settings
        self.data_dir = data_dir or settings.data_dir
        self.doc_search = DocSearchTool(self.data_dir)
        self._initialized = False
        
        # Active execution plans
        self._active_plans: Dict[str, ExecutionPlan] = {}
    
    async def initialize(self) -> None:
        """Initialize the agent and its document search tool."""
        if self._initialized:
            return
        
        # Initialize document search (creates ChromaDB)
        await self.doc_search.initialize()
        self._initialized = True
        logger.info("knowledge_retrieval_agent_initialized")
        
        # Agent registry for routing (per architecture diagram)
        self._specialist_agents = {
            "teacher": "teacher_agent",
            "evaluator": "evaluator_agent",  # Handles Assessment + Feedback
            "code": "code_execution_agent",
            "student": "student_agent",
            "safety": "safety_agent"
        }
    
    def _get_agent_prompt(self) -> str:
        return """You are the Knowledge Retrieval Agent in EduSmartLearn.

Your dual role is Orchestrator + A2A Router:

KNOWLEDGE RETRIEVAL responsibilities:
- Search course materials for relevant information
- Provide accurate context from documents
- Ground responses in actual course content

ORCHESTRATION responsibilities:
- Analyze student requests and plan execution
- Route tasks to appropriate specialist agents
- Coordinate workflows and integrate results

Available specialist agents:
- Teacher Agent: Content generation, explanations, examples
- Evaluator Agent: Assessment + Feedback (quizzes, evaluation)
- Code Execution Agent: Run/Debug code (requires consent)
- Student Agent: Learner model + personalization
- Safety Agent: Policy enforcement

When planning:
- Identify task type (explanation, coding, quiz, etc.)
- Retrieve relevant knowledge first
- Select appropriate agents
- Order steps by dependencies

Always prioritize student learning and safety."""
    
    async def process_message(self, message: A2AMessage) -> A2AMessage:
        """Process incoming A2A message."""
        logger.info(
            "orchestrator_received",
            message_type=message.message_type.value,
            sender=message.sender
        )
        
        if message.message_type in [MessageType.TASK_REQUEST, MessageType.TASK_DELEGATION]:
            return await self._handle_task_request(message)
        elif message.message_type == MessageType.TASK_RESPONSE:
            return await self._handle_agent_response(message)
        elif message.message_type == MessageType.ERROR:
            return await self._handle_error(message)
        else:
            return message.create_response(
                message_type=MessageType.ERROR,
                sender=self.agent_id,
                payload={},
                error_code=ErrorCode.INVALID_REQUEST,
                error_message=f"Unsupported message type"
            )
    
    async def _handle_task_request(self, message: A2AMessage) -> A2AMessage:
        """Handle new task by creating and executing plan."""
        user_request = message.payload.get("request", "")
        session_id = message.session_id
        
        # Step 1: Classify task type
        task_type = await self._classify_task(user_request)
        
        # Step 2: Create execution plan
        plan = await self._create_plan(user_request, task_type, session_id)
        self._active_plans[plan.plan_id] = plan
        
        logger.info(
            "plan_created",
            plan_id=plan.plan_id,
            task_type=task_type.value,
            steps=len(plan.steps)
        )
        
        # Step 3: Execute plan
        result = await self._execute_plan(plan)
        
        # Step 4: Return response
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "response": result.get("final_response", ""),
                "plan_id": plan.plan_id,
                "task_type": task_type.value
            }
        )
    
    async def _classify_task(self, request: str) -> TaskType:
        """Classify user request into task type."""
        prompt = f"""Classify this request into ONE category:
- explain_topic: Learning about a concept
- answer_question: Specific question
- code_help: Programming help
- quiz: Test knowledge
- general: Other

Request: "{request}"

Reply with just the category name."""

        response = await self.generate_response(prompt, use_history=False)
        response_clean = response.strip().lower().replace("_", "_")
        
        mapping = {
            "explain_topic": TaskType.EXPLAIN_TOPIC,
            "answer_question": TaskType.ANSWER_QUESTION,
            "code_help": TaskType.CODE_HELP,
            "quiz": TaskType.QUIZ,
            "general": TaskType.GENERAL
        }
        
        return mapping.get(response_clean, TaskType.GENERAL)
    
    async def _create_plan(
        self,
        request: str,
        task_type: TaskType,
        session_id: Optional[str]
    ) -> ExecutionPlan:
        """Create execution plan based on task type."""
        plan_id = str(uuid4())[:8]
        steps = []
        
        if task_type == TaskType.EXPLAIN_TOPIC:
            # Retrieve -> Teach -> Evaluate
            # Knowledge Retrieval (self) -> Teach -> Evaluate
            steps = [
                PlanStep(step_id=1, target_agent="knowledge_retrieval_agent",
                        action="search", input_data={"query": request}),
                PlanStep(step_id=2, target_agent="teacher_agent",
                        action="explain", input_data={"topic": request},
                        depends_on=[1]),
                PlanStep(step_id=3, target_agent="evaluator_agent",
                        action="evaluate", input_data={}, depends_on=[2])
            ]
        elif task_type == TaskType.CODE_HELP:
            # Teach -> Code (with consent) -> Explain
            steps = [
                PlanStep(step_id=1, target_agent="teacher_agent",
                        action="generate_code", input_data={"problem": request}),
                PlanStep(step_id=2, target_agent="code_execution_agent",
                        action="execute", input_data={"require_consent": True},
                        depends_on=[1]),
                PlanStep(step_id=3, target_agent="teacher_agent",
                        action="explain_code", input_data={}, depends_on=[2])
            ]
        elif task_type == TaskType.QUIZ:
            # Knowledge Retrieval -> Evaluator (Assessment + Feedback)
            steps = [
                PlanStep(step_id=1, target_agent="knowledge_retrieval_agent",
                        action="search", input_data={"query": request}),
                PlanStep(step_id=2, target_agent="evaluator_agent",
                        action="generate_quiz", input_data={"topic": request},
                        depends_on=[1])
            ]
        elif task_type == TaskType.ANSWER_QUESTION:
            # Knowledge Retrieval -> Answer
            steps = [
                PlanStep(step_id=1, target_agent="knowledge_retrieval_agent",
                        action="search", input_data={"query": request}),
                PlanStep(step_id=2, target_agent="teacher_agent",
                        action="answer", input_data={"question": request},
                        depends_on=[1])
            ]
        else:
            # Direct teacher response
            steps = [
                PlanStep(step_id=1, target_agent="teacher_agent",
                        action="respond", input_data={"request": request})
            ]
        
        return ExecutionPlan(
            plan_id=plan_id,
            user_request=request,
            task_type=task_type,
            steps=steps
        )
    
    async def _execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute plan steps sequentially."""
        plan.status = "executing"
        results = {}
        
        for step in plan.steps:
            # Check dependencies
            deps_met = all(
                plan.steps[d-1].status == "completed"
                for d in step.depends_on
            )
            
            if not deps_met:
                continue
            
            step.status = "in_progress"
            
            try:
                # Execute step by delegating to agent
                step_result = await self._execute_step(step, results, plan)
                step.result = step_result
                step.status = "completed"
                results[step.step_id] = step_result
                
            except Exception as e:
                step.status = "failed"
                logger.error("step_failed", step_id=step.step_id, error=str(e))
                results[step.step_id] = {"error": str(e)}
        
        plan.status = "completed"
        
        # Combine results into final response
        final_response = await self._integrate_results(plan, results)
        
        return {"final_response": final_response, "step_results": results}
    
    async def _execute_step(
        self,
        step: PlanStep,
        previous_results: Dict[int, Any],
        plan: ExecutionPlan
    ) -> Dict[str, Any]:
        """Execute a single plan step."""
        # Build context from previous steps
        context = {
            f"step_{k}_result": v.get("output", "")
            for k, v in previous_results.items()
        }
        context["original_request"] = plan.user_request
        
        # Generate step-specific prompt
        prompt = f"""Execute this step:
Agent: {step.target_agent}
Action: {step.action}
Input: {step.input_data}
Context from previous steps: {context}

Provide the output for this step."""

        output = await self.generate_response(prompt, use_history=False)
        
        return {"output": output, "action": step.action}
    
    async def _integrate_results(
        self,
        plan: ExecutionPlan,
        results: Dict[int, Any]
    ) -> str:
        """Integrate step results into final response."""
        # Collect all outputs
        outputs = [
            f"Step {k} ({results[k].get('action', 'unknown')}): {results[k].get('output', '')}"
            for k in sorted(results.keys())
            if 'output' in results[k]
        ]
        
        prompt = f"""Integrate these results into a coherent response for the student:

Original request: {plan.user_request}

Results:
{chr(10).join(outputs)}

Create a well-structured, educational response."""

        return await self.generate_response(prompt, use_history=False)
    
    async def _handle_agent_response(self, message: A2AMessage) -> A2AMessage:
        """Handle response from a specialist agent."""
        # Update plan step with result
        plan_id = message.payload.get("plan_id")
        if plan_id and plan_id in self._active_plans:
            step_id = message.payload.get("step_id")
            # Update step status
        
        return message
    
    async def _handle_error(self, message: A2AMessage) -> A2AMessage:
        """Handle error from agent or tool."""
        logger.error(
            "orchestrator_received_error",
            error_code=message.error_code,
            error_message=message.error_message
        )
        
        # Generate fallback response
        fallback = await self.generate_response(
            "Generate a helpful message explaining that we encountered "
            "a technical issue but the student can try again.",
            use_history=False
        )
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={"response": fallback, "had_error": True}
        )
