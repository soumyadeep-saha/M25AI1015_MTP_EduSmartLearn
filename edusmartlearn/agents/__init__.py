# Agents module for EduSmartLearn
# Contains all specialized agents for the multi-agent teaching system
#
# Architecture (per diagram):
# - Tutor Agent: Session manager + Dialog
# - Knowledge Retrieval Agent: Orchestrator / A2A Router
# - Teacher Agent: Content Generation
# - Evaluator Agent: Assessment + Feedback
# - Code Execution Agent: Run / Debug
# - Student Agent: Learner Model + Personalization
# - Safety Agent: Guardrails + Policy Engine

from agents.base_agent import BaseAgent, AgentConfig
from agents.tutor_agent import TutorAgent
from agents.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from agents.teacher_agent import TeacherAgent
from agents.code_execution_agent import CodeExecutionAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.safety_agent import SafetyAgent
from agents.student_agent import StudentAgent

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "TutorAgent",
    "KnowledgeRetrievalAgent",
    "TeacherAgent",
    "CodeExecutionAgent",
    "EvaluatorAgent",
    "SafetyAgent",
    "StudentAgent"
]
