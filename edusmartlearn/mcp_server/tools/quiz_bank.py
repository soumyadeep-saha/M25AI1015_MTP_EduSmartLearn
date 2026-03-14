"""
mcp_server/tools/quiz_bank.py
=============================
Quiz Bank Tool for Assessment Management.

Provides storage and retrieval of quiz questions for formative assessments.
Supports multiple question types: MCQ, short answer, true/false.

Tool Scope: READ/WRITE access to quiz storage
Agents with access: Quiz Agent, Evaluator Agent
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


class QuizQuestion(BaseModel):
    """Represents a single quiz question."""
    question_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    question_type: str  # "mcq", "short_answer", "true_false"
    topic: str
    difficulty: str  # "easy", "medium", "hard"
    question_text: str
    options: Optional[List[str]] = None  # For MCQ
    correct_answer: str
    explanation: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Quiz(BaseModel):
    """Represents a complete quiz."""
    quiz_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    title: str
    topic: str
    questions: List[QuizQuestion]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    time_limit_minutes: Optional[int] = None


class QuizResult(BaseModel):
    """Result of quiz evaluation."""
    quiz_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    feedback: List[Dict[str, Any]]


class QuizBankTool:
    """
    Quiz bank for storing and retrieving assessment questions.
    
    Features:
    - Store questions by topic and difficulty
    - Generate quizzes from question pool
    - Evaluate student answers
    - Track question usage statistics
    
    Usage:
        tool = QuizBankTool(data_dir=Path("./data"))
        await tool.initialize()
        quiz = await tool.generate_quiz(topic="neural_networks", num_questions=5)
    """
    
    TOOL_NAME = "quiz_bank"
    TOOL_DESCRIPTION = "Store and retrieve quiz questions for assessments"
    TOOL_SCHEMA = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["get_questions", "add_question", "generate_quiz", "evaluate"],
                "description": "Action to perform"
            },
            "topic": {"type": "string", "description": "Topic filter"},
            "difficulty": {"type": "string", "description": "Difficulty level"},
            "num_questions": {"type": "integer", "description": "Number of questions"}
        },
        "required": ["action"]
    }
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.quiz_file = data_dir / "quiz_bank.json"
        self._questions: List[QuizQuestion] = []
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize quiz bank and load existing questions."""
        if self._initialized:
            return
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if self.quiz_file.exists():
            try:
                data = json.loads(self.quiz_file.read_text())
                self._questions = [QuizQuestion(**q) for q in data.get("questions", [])]
            except Exception as e:
                logger.warning("quiz_bank_load_failed", error=str(e))
                self._questions = []
        else:
            # Add sample questions
            await self._add_sample_questions()
        
        self._initialized = True
        logger.info("quiz_bank_initialized", question_count=len(self._questions))
    
    async def _add_sample_questions(self) -> None:
        """Add sample questions for demonstration."""
        samples = [
            QuizQuestion(
                question_type="mcq",
                topic="machine_learning",
                difficulty="easy",
                question_text="What is the primary goal of supervised learning?",
                options=[
                    "A) Find hidden patterns in data",
                    "B) Learn from labeled examples to make predictions",
                    "C) Maximize a reward signal",
                    "D) Reduce data dimensionality"
                ],
                correct_answer="B",
                explanation="Supervised learning uses labeled training data to learn a mapping from inputs to outputs."
            ),
            QuizQuestion(
                question_type="mcq",
                topic="neural_networks",
                difficulty="medium",
                question_text="What is the purpose of the activation function in a neural network?",
                options=[
                    "A) To initialize weights",
                    "B) To introduce non-linearity",
                    "C) To normalize inputs",
                    "D) To reduce overfitting"
                ],
                correct_answer="B",
                explanation="Activation functions introduce non-linearity, allowing networks to learn complex patterns."
            ),
            QuizQuestion(
                question_type="true_false",
                topic="deep_learning",
                difficulty="easy",
                question_text="Backpropagation is used to compute gradients in neural networks.",
                correct_answer="True",
                explanation="Backpropagation efficiently computes gradients using the chain rule."
            ),
        ]
        self._questions.extend(samples)
        await self._save()
    
    async def _save(self) -> None:
        """Save questions to file."""
        data = {"questions": [q.model_dump(mode='json') for q in self._questions]}
        self.quiz_file.write_text(json.dumps(data, indent=2, default=str))
    
    async def add_question(self, question: QuizQuestion) -> str:
        """Add a new question to the bank."""
        if not self._initialized:
            await self.initialize()
        
        self._questions.append(question)
        await self._save()
        
        logger.info("question_added", question_id=question.question_id, topic=question.topic)
        return question.question_id
    
    async def get_questions(
        self,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 10
    ) -> List[QuizQuestion]:
        """Get questions filtered by topic and difficulty."""
        if not self._initialized:
            await self.initialize()
        
        filtered = self._questions
        
        if topic:
            filtered = [q for q in filtered if topic.lower() in q.topic.lower()]
        if difficulty:
            filtered = [q for q in filtered if q.difficulty == difficulty]
        
        return filtered[:limit]
    
    async def generate_quiz(
        self,
        topic: str,
        num_questions: int = 5,
        difficulty: Optional[str] = None,
        title: Optional[str] = None
    ) -> Quiz:
        """Generate a quiz from the question bank."""
        import random
        
        questions = await self.get_questions(topic=topic, difficulty=difficulty, limit=50)
        
        if len(questions) < num_questions:
            logger.warning("insufficient_questions", available=len(questions), requested=num_questions)
            num_questions = len(questions)
        
        selected = random.sample(questions, min(num_questions, len(questions)))
        
        quiz = Quiz(
            title=title or f"Quiz: {topic}",
            topic=topic,
            questions=selected,
            time_limit_minutes=num_questions * 2  # 2 minutes per question
        )
        
        logger.info("quiz_generated", quiz_id=quiz.quiz_id, questions=len(selected))
        return quiz
    
    async def evaluate_answers(
        self,
        quiz_id: str,
        answers: Dict[str, str]  # question_id -> answer
    ) -> QuizResult:
        """Evaluate student answers for a quiz."""
        if not self._initialized:
            await self.initialize()
        
        feedback = []
        correct = 0
        total = len(answers)
        
        for question_id, student_answer in answers.items():
            # Find the question
            question = next((q for q in self._questions if q.question_id == question_id), None)
            
            if question:
                is_correct = student_answer.strip().upper() == question.correct_answer.strip().upper()
                if is_correct:
                    correct += 1
                
                feedback.append({
                    "question_id": question_id,
                    "correct": is_correct,
                    "student_answer": student_answer,
                    "correct_answer": question.correct_answer,
                    "explanation": question.explanation
                })
        
        score = (correct / total * 100) if total > 0 else 0
        
        logger.info("quiz_evaluated", quiz_id=quiz_id, score=score)
        
        return QuizResult(
            quiz_id=quiz_id,
            total_questions=total,
            correct_answers=correct,
            score_percentage=score,
            feedback=feedback
        )
