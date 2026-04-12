"""
main.py
=======
EduSmartLearn - Safe Multi-Agent Teaching System

Main entry point for the application. This module:
1. Initializes all agents and tools
2. Sets up the multi-agent system
3. Provides CLI and API interfaces for interaction

Usage:
    # CLI mode
    python main.py
    
    # Or import and use programmatically
    from main import EduSmartLearn
    system = EduSmartLearn()
    await system.initialize()
    response = await system.chat("Explain neural networks")
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()

# Import configuration
from config.settings import settings

# Import agents (per architecture diagram)
from agents.tutor_agent import TutorAgent
from agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from agents.teacher_agent import TeacherAgent
from agents.code_execution_agent import CodeExecutionAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.safety_agent import SafetyAgent
from agents.student_agent import StudentAgent

# Import protocols
from protocols.a2a_protocol import A2AMessage, MessageType, a2a_router

# Import memory and observability
from memory.session_store import session_store
from observability.audit_logger import audit_logger
from observability.metrics import metrics_collector


class EduSmartLearn:
    """
    Main class for the EduSmartLearn multi-agent teaching system.
    
    This class orchestrates all agents and provides the primary interface
    for interacting with the teaching system.
    
    Architecture layers (per diagram):
    1. Interaction & State Layer: Tutor Agent (Session manager + Dialog)
    2. Multi-Agent Orchestration Layer (A2A):
       - Knowledge Retrieval Agent (Orchestrator / A2A Router)
       - Teacher Agent (Content Generation)
       - Evaluator Agent (Assessment + Feedback)
       - Code Execution Agent (Run / Debug)
       - Student Agent (Learner Model + Personalization)
    3. Safety Layer: Safety/Guardrail Agent + Policy Engine
    4. Execution & Integration Layer: MCP Server & Tools, LLM Backends
    
    Example:
        system = EduSmartLearn()
        await system.initialize()
        
        # Start a session
        session = system.start_session("user123")
        
        # Chat with the system
        response = await system.chat("Explain backpropagation", session.session_id)
        print(response)
    """
    
    def __init__(self):
        """Initialize the EduSmartLearn system."""
        self._initialized = False
        
        # Agent instances (per architecture diagram)
        self.tutor: Optional[TutorAgent] = None
        self.knowledge_retrieval: Optional[KnowledgeRetrievalAgent] = None
        self.teacher: Optional[TeacherAgent] = None
        self.code_execution: Optional[CodeExecutionAgent] = None
        self.evaluator: Optional[EvaluatorAgent] = None
        self.safety: Optional[SafetyAgent] = None
        self.student: Optional[StudentAgent] = None
    
    async def initialize(self) -> None:
        """
        Initialize all agents and tools.
        
        This must be called before using the system.
        """
        if self._initialized:
            return
        
        logger.info("initializing_edusmartlearn")
        
        # Ensure directories exist
        settings.ensure_directories()
        
        # Check for API key
        if not settings.gemini.api_key:
            logger.warning(
                "gemini_api_key_not_set",
                message="Set GEMINI_API_KEY environment variable"
            )
        
        # Initialize agents (per architecture diagram)
        logger.info("initializing_agents")
        
        self.tutor = TutorAgent()
        self.knowledge_retrieval = KnowledgeRetrievalAgent()
        self.teacher = TeacherAgent()
        self.code_execution = CodeExecutionAgent()
        self.evaluator = EvaluatorAgent()
        self.safety = SafetyAgent()
        self.student = StudentAgent()
        
        # Initialize knowledge retrieval agent's doc_search (creates ChromaDB)
        await self.knowledge_retrieval.initialize()
        
        # Initialize evaluator's quiz bank (Assessment + Feedback)
        await self.evaluator.initialize()
        
        self._initialized = True
        logger.info("edusmartlearn_initialized", agents_count=7)
    
    def start_session(self, user_id: str) -> Any:
        """
        Start a new tutoring session.
        
        Args:
            user_id: Identifier for the user
            
        Returns:
            Session object
        """
        session = session_store.create_session(user_id)
        
        # Update tutor's session tracking
        self.tutor.create_session(user_id)
        
        logger.info("session_started", session_id=session.session_id, user_id=user_id)
        return session
    
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: str = "default_user"
    ) -> str:
        """
        Send a message and get a response.
        
        This is the main interaction method. It:
        1. Validates the message through safety checks
        2. Routes to tutor agent
        3. Orchestrates multi-agent workflow if needed
        4. Returns the final response
        
        Args:
            message: User's message/question
            session_id: Optional session ID (creates new if not provided)
            user_id: User identifier
            
        Returns:
            Response from the teaching system
        """
        if not self._initialized:
            await self.initialize()
        
        # Get or create session
        if session_id:
            session = session_store.get_session(session_id)
            if not session:
                session = session_store.create_session(user_id)
        else:
            session = session_store.get_or_create_session(user_id)
        
        session_id = session.session_id
        
        # Record user message
        session_store.add_message(session_id, "user", message)
        
        # Start timing for response metrics
        import time
        start_time = time.time()
        
        # Safety check
        safety_message = A2AMessage(
            message_type=MessageType.TASK_REQUEST,
            sender="system",
            receiver="safety_agent",
            session_id=session_id,
            payload={"action": "check", "content": message}
        )
        
        safety_response = await self.safety.process_message(safety_message)
        
        # Record safety check metrics
        safety_passed = safety_response.error_code is None
        metrics_collector.record_safety_check(
            check_type="content_filter",
            passed=safety_passed,
            session_id=session_id
        )
        
        if not safety_passed:
            metrics_collector.record_task_completion(
                task_type="chat",
                success=False,
                session_id=session_id
            )
            return f"I'm sorry, but I can't process that request. {safety_response.payload.get('output', '')}"
        
        # Create task request for tutor
        task_message = A2AMessage(
            message_type=MessageType.TASK_REQUEST,
            sender="user",
            receiver="tutor_agent",
            session_id=session_id,
            payload={"query": message}
        )
        
        # Log the message
        audit_logger.log_a2a_message(
            sender="user",
            receiver="tutor_agent",
            message_type="task_request",
            message_id=task_message.message_id,
            session_id=session_id
        )
        
        # Process through tutor
        tutor_response = await self.tutor.process_message(task_message)
        
        # Check if orchestration is needed
        if tutor_response.message_type == MessageType.TASK_DELEGATION:
            # Route to Knowledge Retrieval Agent (Orchestrator / A2A Router)
            kr_response = await self.knowledge_retrieval.process_message(tutor_response)
            response_text = kr_response.payload.get("response", "")
        else:
            response_text = tutor_response.payload.get("response", "")
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Record assistant response
        session_store.add_message(session_id, "assistant", response_text)
        
        # Record metrics
        metrics_collector.record_task_completion(
            task_type="chat",
            success=True,
            session_id=session_id
        )
        metrics_collector.record_response_time(
            agent_id="system",
            response_time_ms=response_time_ms,
            action="chat"
        )
        # Track tool calls: safety_check + tutor LLM call + optional doc_search
        metrics_collector.record_tool_latency(tool_name="safety_check", latency_ms=0)
        metrics_collector.record_tool_latency(tool_name="llm_generate", latency_ms=response_time_ms)
        if tutor_response.message_type == MessageType.TASK_DELEGATION:
            metrics_collector.record_tool_latency(tool_name="doc_search", latency_ms=0)
        
        return response_text
    
    async def generate_quiz(
        self,
        topic: str,
        num_questions: int = 5,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a quiz on a topic.
        
        Args:
            topic: Topic for the quiz
            num_questions: Number of questions
            session_id: Optional session ID
            
        Returns:
            Quiz data including questions
        """
        if not self._initialized:
            await self.initialize()
        
        import time
        start_time = time.time()
        
        # Quiz generation is handled by Evaluator Agent (Assessment + Feedback)
        quiz_message = A2AMessage(
            message_type=MessageType.TASK_REQUEST,
            sender="system",
            receiver="evaluator_agent",
            session_id=session_id,
            payload={
                "action": "generate_quiz",
                "topic": topic,
                "num_questions": num_questions
            }
        )
        
        response = await self.evaluator.process_message(quiz_message)
        
        # Record metrics
        response_time_ms = (time.time() - start_time) * 1000
        success = response.error_code is None
        metrics_collector.record_task_completion(
            task_type="quiz",
            success=success,
            session_id=session_id
        )
        metrics_collector.record_response_time(
            agent_id="evaluator_agent",
            response_time_ms=response_time_ms,
            action="generate_quiz"
        )
        # Track tool calls: quiz_bank + llm_generate
        metrics_collector.record_tool_latency(tool_name="quiz_bank", latency_ms=response_time_ms)
        metrics_collector.record_tool_latency(tool_name="llm_generate", latency_ms=0)
        
        return response.payload
    
    async def execute_code(
        self,
        code: str,
        consent_granted: bool = False,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute code in the sandbox.
        
        Args:
            code: Python code to execute
            consent_granted: Whether user has consented
            session_id: Optional session ID
            
        Returns:
            Execution result
        """
        if not self._initialized:
            await self.initialize()
        
        import time
        start_time = time.time()
        
        from protocols.a2a_protocol import ConsentRequirement
        
        # Record safety check for code execution consent
        metrics_collector.record_safety_check(
            check_type="code_execution_consent",
            passed=consent_granted,
            session_id=session_id
        )
        
        code_message = A2AMessage(
            message_type=MessageType.TASK_REQUEST,
            sender="system",
            receiver="code_execution_agent",
            session_id=session_id,
            consent=ConsentRequirement(
                required=True,
                operation_type="code_execution",
                granted=consent_granted
            ),
            payload={
                "action": "execute",
                "code": code,
                "require_consent": True
            }
        )
        
        response = await self.code_execution.process_message(code_message)
        
        # Record metrics
        response_time_ms = (time.time() - start_time) * 1000
        success = response.error_code is None and response.payload.get("success", False)
        metrics_collector.record_task_completion(
            task_type="code_execution",
            success=success,
            session_id=session_id
        )
        metrics_collector.record_response_time(
            agent_id="code_execution_agent",
            response_time_ms=response_time_ms,
            action="execute_code"
        )
        # Track tool calls: safety_check + code_run
        metrics_collector.record_tool_latency(tool_name="safety_check", latency_ms=0)
        metrics_collector.record_tool_latency(tool_name="code_run", latency_ms=response_time_ms)
        
        return response.payload
    
    async def get_learner_profile(self, user_id: str) -> Dict[str, Any]:
        """Get learner profile for a user."""
        if not self._initialized:
            await self.initialize()
        
        profile_message = A2AMessage(
            message_type=MessageType.TASK_REQUEST,
            sender="system",
            receiver="student_agent",
            payload={"action": "get_profile", "user_id": user_id}
        )
        
        response = await self.student.process_message(profile_message)
        return response.payload
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get system metrics summary."""
        return metrics_collector.get_summary()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the system."""
        logger.info("shutting_down_edusmartlearn")
        
        # Flush logs and metrics
        audit_logger.flush()
        metrics_collector.save_metrics()
        
        # Cleanup sessions
        session_store.cleanup_expired()
        
        logger.info("edusmartlearn_shutdown_complete")


async def interactive_cli():
    """Run interactive CLI for testing."""
    print("\n" + "="*60)
    print("  EduSmartLearn - Safe Multi-Agent Teaching System")
    print("  MTech Project: Agent-to-Agent Protocol & MCP Tools")
    print("="*60 + "\n")
    
    # Initialize system
    system = EduSmartLearn()
    
    print("Initializing system...")
    await system.initialize()
    print("System ready!\n")
    
    # Ask for user ID
    user_id = input("Enter your User ID (or press Enter for 'cli_user'): ").strip()
    if not user_id:
        user_id = "cli_user"
    
    # Start session
    session = system.start_session(user_id)
    
    # Initialize learner profile (increments session count, auto-saves)
    system.student.initialize_session(user_id)
    
    print(f"\nWelcome, {user_id}!")
    print(f"Session started: {session.session_id}\n")
    
    print("Commands:")
    print("  /quiz <topic>  - Generate a quiz")
    print("      Example: /quiz neural networks")
    print("      Example: /quiz python programming")
    print("      Example: /quiz deep learning")
    print("      Example: /quiz supervised learning")
    print("  /code          - Enter code execution mode, Next Line: Give actual code to execute, Next Line: END")
    print("  /profile       - View your learner profile")
    print("  /history       - View past conversations")
    print("  /metrics       - View system metrics")
    print("  /quit          - Exit")
    print("-"*60 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "/quit":
                print("\nGoodbye! Keep learning!")
                break
            
            elif user_input.lower().startswith("/quiz"):
                topic = user_input[5:].strip() or "machine learning"
                print(f"\nGenerating quiz on '{topic}'...")
                result = await system.generate_quiz(topic, 3, session.session_id)
                print(f"\n{result.get('output', 'Quiz generated')}\n")
            
            elif user_input.lower() == "/code":
                print("\nEnter Python code (type 'END' on a new line to execute):")
                code_lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    code_lines.append(line)
                
                code = "\n".join(code_lines)
                print("\nExecuting code (with consent)...")
                result = await system.execute_code(code, consent_granted=True, session_id=session.session_id)
                print(f"\n{result.get('output', 'Execution complete')}\n")
            
            elif user_input.lower() == "/profile":
                result = await system.get_learner_profile(user_id)
                print(f"\n{result.get('output', 'Profile loaded')}\n")
            
            elif user_input.lower() == "/history":
                conversations = session_store.load_user_conversations(user_id)
                if not conversations:
                    print("\nNo previous conversations found.\n")
                else:
                    print(f"\n📜 Found {len(conversations)} saved conversation(s):\n")
                    for i, conv in enumerate(conversations[:5], 1):
                        date = conv.get("created_at", "Unknown")[:19].replace("T", " ")
                        msg_count = len(conv.get("messages", []))
                        print(f"  {i}. {date} - {msg_count} messages")
                        # Show last few messages preview
                        messages = conv.get("messages", [])[-3:]
                        for msg in messages:
                            role = "You" if msg["role"] == "user" else "Tutor"
                            content = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
                            print(f"     {role}: {content}")
                        print()
                    print()
            
            elif user_input.lower() == "/metrics":
                metrics = system.get_metrics_summary()
                print(f"\nSystem Metrics:")
                print(f"  Effectiveness: {metrics['effectiveness']}")
                print(f"  Efficiency: {metrics['efficiency']}")
                print(f"  Safety: {metrics['safety']}\n")
            
            else:
                # Regular chat
                response = await system.chat(user_input, session.session_id, user_id)
                print(f"\nTutor: {response}\n")
                
        except KeyboardInterrupt:
            print("\n\nInterrupted. Shutting down...")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
    
    await system.shutdown()


def main():
    """Main entry point."""
    asyncio.run(interactive_cli())


if __name__ == "__main__":
    main()
