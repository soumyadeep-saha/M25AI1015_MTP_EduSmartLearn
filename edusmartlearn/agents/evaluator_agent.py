"""
agents/evaluator_agent.py
=========================
Evaluator Agent - Assessment + Feedback Specialist.

The Evaluator Agent handles:
- Quiz/Assessment generation and evaluation
- Content quality review
- Student feedback generation
- Factual correctness checking

Position in Architecture: Multi-Agent Orchestration Layer (A2A)
As shown in architecture diagram: "Evaluator Agent (Assessment + Feedback)"
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from protocols.a2a_protocol import (
    A2AMessage,
    MessageType,
    AgentCapability,
    ErrorCode
)
from mcp_server.tools.quiz_bank import QuizBankTool, Quiz, QuizQuestion

logger = structlog.get_logger()


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent - Assessment + Feedback.
    
    Responsibilities:
    1. Generate quizzes and assessments
    2. Evaluate student answers and provide feedback
    3. Review content quality and accuracy
    4. Fact-check explanations
    5. Provide constructive learning feedback
    
    This agent combines assessment generation with quality evaluation.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        config = AgentConfig(
            agent_id="evaluator_agent",
            name="Evaluator Agent",
            description="Handles assessment generation, answer evaluation, "
                       "and content quality review with constructive feedback.",
            capabilities=[
                AgentCapability.CONTENT_EVALUATION,
                AgentCapability.QUIZ_GENERATION
            ],
            allowed_tools=["quiz_bank", "doc_search", "logging"],
            system_prompt=self._get_evaluator_prompt(),
            temperature=0.4
        )
        super().__init__(config)
        
        # Initialize quiz bank for assessments
        from config.settings import settings
        self.data_dir = data_dir or settings.data_dir
        self.quiz_bank = QuizBankTool(self.data_dir)
        self._initialized = False
    
    def _get_evaluator_prompt(self) -> str:
        return """You are the Evaluator Agent in EduSmartLearn.

Your dual role is Assessment + Feedback:

ASSESSMENT responsibilities:
- Generate quiz questions that test understanding
- Create varied question types (MCQ, short answer, true/false)
- Evaluate student answers fairly and accurately
- Provide constructive feedback on quiz performance

FEEDBACK/EVALUATION responsibilities:
- Review content for factual accuracy
- Check clarity and pedagogical quality
- Identify areas for improvement
- Provide actionable suggestions

Evaluation criteria:
1. **Factual Accuracy**: Is the information correct?
2. **Clarity**: Is the explanation clear and understandable?
3. **Completeness**: Are key points covered?
4. **Pedagogy**: Is it appropriate for learning?

Always be encouraging while maintaining accuracy standards."""
    
    async def initialize(self) -> None:
        """Initialize the quiz bank tool."""
        if not self._initialized:
            await self.quiz_bank.initialize()
            self._initialized = True
    
    async def process_message(self, message: A2AMessage) -> A2AMessage:
        """Process evaluation and assessment requests."""
        logger.info(
            "evaluator_processing",
            message_type=message.message_type.value,
            action=message.payload.get("action")
        )
        
        if message.message_type != MessageType.TASK_REQUEST:
            return message.create_response(
                message_type=MessageType.ERROR,
                sender=self.agent_id,
                payload={},
                error_code=ErrorCode.INVALID_REQUEST,
                error_message="Evaluator only handles TASK_REQUEST"
            )
        
        action = message.payload.get("action", "evaluate")
        
        # Assessment actions
        if action == "generate_quiz":
            return await self._generate_quiz(message)
        elif action == "evaluate_answers":
            return await self._evaluate_answers(message)
        # Feedback/evaluation actions
        elif action == "evaluate":
            return await self._evaluate_content(message)
        elif action == "fact_check":
            return await self._fact_check(message)
        elif action == "review_code":
            return await self._review_code(message)
        else:
            return await self._evaluate_content(message)
    
    # ==================== ASSESSMENT METHODS ====================
    
    async def _generate_quiz(self, message: A2AMessage) -> A2AMessage:
        """Generate a quiz on a topic."""
        await self.initialize()
        
        topic = message.payload.get("topic", "")
        num_questions = message.payload.get("num_questions", 5)
        difficulty = message.payload.get("difficulty")
        
        # Try to get questions from bank first
        quiz = await self.quiz_bank.generate_quiz(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty
        )
        
        # If not enough questions, generate new ones with LLM
        if len(quiz.questions) < num_questions:
            new_questions = await self._generate_questions_llm(
                topic=topic,
                count=num_questions - len(quiz.questions),
                difficulty=difficulty or "medium"
            )
            quiz.questions.extend(new_questions)
        
        # Format quiz for presentation
        formatted = self._format_quiz(quiz)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": formatted,
                "action": "generate_quiz",
                "quiz_id": quiz.quiz_id,
                "num_questions": len(quiz.questions),
                "questions": [q.model_dump() for q in quiz.questions]
            }
        )
    
    async def _generate_questions_llm(
        self,
        topic: str,
        count: int,
        difficulty: str
    ) -> List[QuizQuestion]:
        """Generate questions using LLM."""
        prompt = f"""Generate {count} quiz questions about "{topic}" at {difficulty} difficulty.

For each question, provide in this exact format:
QUESTION: [question text]
TYPE: [mcq/true_false/short_answer]
OPTIONS: [A) ... B) ... C) ... D) ...] (for MCQ only)
ANSWER: [correct answer letter or text]
EXPLANATION: [why this is correct]

Make questions that test understanding, not just memorization."""

        response = await self.generate_response(prompt, use_history=False)
        
        # Parse response into QuizQuestion objects
        questions = self._parse_questions(response, topic, difficulty)
        
        # Save to quiz bank
        for q in questions:
            await self.quiz_bank.add_question(q)
        
        return questions
    
    def _parse_questions(
        self,
        response: str,
        topic: str,
        difficulty: str
    ) -> List[QuizQuestion]:
        """Parse LLM response into QuizQuestion objects."""
        questions = []
        parts = response.split("QUESTION:")
        
        for part in parts[1:]:
            try:
                lines = part.strip().split("\n")
                question_text = lines[0].strip()
                
                q_type = "mcq"
                options = None
                answer = ""
                explanation = ""
                
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith("TYPE:"):
                        q_type = line.replace("TYPE:", "").strip().lower()
                    elif line.startswith("OPTIONS:"):
                        opts_text = line.replace("OPTIONS:", "").strip()
                        options = [o.strip() for o in opts_text.split(",") if o.strip()]
                    elif line.startswith("ANSWER:"):
                        answer = line.replace("ANSWER:", "").strip()
                    elif line.startswith("EXPLANATION:"):
                        explanation = line.replace("EXPLANATION:", "").strip()
                
                if question_text and answer:
                    questions.append(QuizQuestion(
                        question_type=q_type,
                        topic=topic,
                        difficulty=difficulty,
                        question_text=question_text,
                        options=options if q_type == "mcq" else None,
                        correct_answer=answer,
                        explanation=explanation
                    ))
            except Exception as e:
                logger.warning("question_parse_failed", error=str(e))
                continue
        
        return questions
    
    def _format_quiz(self, quiz: Quiz) -> str:
        """Format quiz for student presentation."""
        lines = [f"# {quiz.title}", f"Topic: {quiz.topic}", ""]
        
        for i, q in enumerate(quiz.questions, 1):
            lines.append(f"**Question {i}** ({q.difficulty})")
            lines.append(q.question_text)
            
            if q.options:
                for opt in q.options:
                    lines.append(f"  {opt}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    async def _evaluate_answers(self, message: A2AMessage) -> A2AMessage:
        """Evaluate student's quiz answers."""
        await self.initialize()
        
        quiz_id = message.payload.get("quiz_id", "")
        answers = message.payload.get("answers", {})
        
        # Evaluate using quiz bank
        result = await self.quiz_bank.evaluate_answers(quiz_id, answers)
        
        # Generate constructive feedback
        feedback = await self._generate_feedback(result)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": feedback,
                "action": "evaluate_answers",
                "score": result.score_percentage,
                "correct": result.correct_answers,
                "total": result.total_questions,
                "detailed_feedback": result.feedback
            }
        )
    
    async def _generate_feedback(self, result) -> str:
        """Generate constructive feedback for quiz results."""
        prompt = f"""Generate encouraging feedback for a student who scored {result.score_percentage:.1f}% 
({result.correct_answers}/{result.total_questions} correct).

Detailed results:
{result.feedback}

Provide:
1. Positive acknowledgment of effort
2. Summary of performance
3. Specific feedback on incorrect answers
4. Suggestions for improvement"""

        return await self.generate_response(prompt, use_history=False)
    
    # ==================== CONTENT EVALUATION METHODS ====================
    
    async def _evaluate_content(self, message: A2AMessage) -> A2AMessage:
        """Evaluate content quality and accuracy."""
        content = message.payload.get("content", "")
        content_type = message.payload.get("content_type", "explanation")
        topic = message.payload.get("topic", "")
        
        prompt = f"""Evaluate this {content_type} about "{topic}":

Content:
{content}

Evaluate on these criteria (score 1-5 each):
1. Factual Accuracy
2. Clarity
3. Completeness
4. Pedagogical Quality
5. Appropriateness

For each criterion:
- Give a score (1-5)
- Provide specific feedback
- Suggest improvements if needed

End with:
- Overall quality score (1-5)
- Recommendation: APPROVE / REVISE / REJECT
- Summary of key issues (if any)"""

        evaluation = await self.generate_response(prompt, use_history=False)
        
        # Parse evaluation for structured data
        scores = self._parse_evaluation(evaluation)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": evaluation,
                "action": "evaluate",
                "scores": scores,
                "recommendation": scores.get("recommendation", "REVISE")
            }
        )
    
    def _parse_evaluation(self, evaluation: str) -> Dict[str, Any]:
        """Parse evaluation response for structured scores."""
        scores = {
            "accuracy": 3,
            "clarity": 3,
            "completeness": 3,
            "pedagogy": 3,
            "appropriateness": 3,
            "overall": 3,
            "recommendation": "REVISE"
        }
        
        eval_lower = evaluation.lower()
        
        # Simple parsing for recommendation
        if "approve" in eval_lower:
            scores["recommendation"] = "APPROVE"
        elif "reject" in eval_lower:
            scores["recommendation"] = "REJECT"
        
        return scores
    
    async def _fact_check(self, message: A2AMessage) -> A2AMessage:
        """Fact-check specific claims."""
        claims = message.payload.get("claims", [])
        context = message.payload.get("context", "")
        
        prompt = f"""Fact-check these claims:

Claims:
{chr(10).join(f'- {c}' for c in claims)}

{"Context: " + context if context else ""}

For each claim:
1. Is it accurate? (TRUE / FALSE / UNCERTAIN)
2. Confidence level (HIGH / MEDIUM / LOW)
3. Explanation or correction if needed
4. Source suggestion if available"""

        fact_check = await self.generate_response(prompt, use_history=False)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": fact_check,
                "action": "fact_check"
            }
        )
    
    async def _review_code(self, message: A2AMessage) -> A2AMessage:
        """Review code for quality and correctness."""
        code = message.payload.get("code", "")
        purpose = message.payload.get("purpose", "")
        
        prompt = f"""Review this code:

```
{code}
```

Purpose: {purpose}

Evaluate:
1. **Correctness**: Does it work as intended?
2. **Style**: Is it clean and readable?
3. **Efficiency**: Are there performance issues?
4. **Best Practices**: Does it follow good practices?
5. **Educational Value**: Is it good for learning?

Provide:
- Issues found (if any)
- Specific suggestions
- Overall assessment"""

        review = await self.generate_response(prompt, use_history=False)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": review,
                "action": "review_code"
            }
        )
