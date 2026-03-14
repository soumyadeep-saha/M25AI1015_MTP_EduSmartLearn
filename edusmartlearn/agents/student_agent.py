"""
agents/student_agent.py
=======================
Student Agent - Learner Model + Personalization.

As shown in architecture diagram: "Student Agent (Learner Model + Personalization)"

The Student Agent tracks and manages learner information:
- Knowledge state and mastery levels
- Learning preferences
- Misconceptions and weak areas
- Progress over time

Position in Architecture: Multi-Agent Orchestration Layer (A2A)
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import structlog

from agents.base_agent import BaseAgent, AgentConfig
from memory.long_term_memory import LongTermMemory
from protocols.a2a_protocol import (
    A2AMessage,
    MessageType,
    AgentCapability,
    ErrorCode,
    ConsentRequirement
)

logger = structlog.get_logger()


class LearnerProfile:
    """Represents a learner's profile and progress."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        
        # Knowledge state by topic
        self.mastery_levels: Dict[str, float] = {}  # topic -> 0.0-1.0
        
        # Learning preferences
        self.preferences = {
            "explanation_style": "balanced",  # concise, balanced, detailed
            "example_preference": "practical",  # theoretical, practical, both
            "difficulty_preference": "adaptive"  # easy, medium, hard, adaptive
        }
        
        # Tracked misconceptions
        self.misconceptions: List[Dict[str, Any]] = []
        
        # Quiz history
        self.quiz_history: List[Dict[str, Any]] = []
        
        # Topics studied
        self.topics_studied: List[str] = []
        
        # Session count
        self.session_count: int = 0
        
        # Long-term memory (conversation summaries, key learnings)
        self.long_term_memory: Dict[str, Any] = {
            "key_learnings": [],
            "conversation_summaries": [],
            "frequently_asked_topics": {},
            "learning_milestones": []
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "mastery_levels": self.mastery_levels,
            "preferences": self.preferences,
            "misconceptions": self.misconceptions,
            "quiz_history": self.quiz_history,
            "topics_studied": self.topics_studied,
            "session_count": self.session_count,
            "long_term_memory": self.long_term_memory
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearnerProfile":
        profile = cls(data["user_id"])
        profile.created_at = datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat()))
        profile.last_updated = datetime.fromisoformat(data.get("last_updated", datetime.utcnow().isoformat()))
        profile.mastery_levels = data.get("mastery_levels", {})
        profile.preferences = data.get("preferences", profile.preferences)
        profile.misconceptions = data.get("misconceptions", [])
        profile.quiz_history = data.get("quiz_history", [])
        profile.topics_studied = data.get("topics_studied", [])
        profile.session_count = data.get("session_count", 0)
        profile.long_term_memory = data.get("long_term_memory", {
            "key_learnings": [],
            "conversation_summaries": [],
            "frequently_asked_topics": {},
            "learning_milestones": []
        })
        return profile


class StudentAgent(BaseAgent):
    """
    Student Agent - Learner Model + Personalization (per architecture diagram).
    
    Responsibilities:
    1. Track learner knowledge state (mastery levels)
    2. Identify misconceptions and weak areas
    3. Store learning preferences
    4. Recommend next activities
    5. Adapt difficulty based on performance
    
    Privacy: Only stores minimal, approved data with user consent.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        config = AgentConfig(
            agent_id="student_agent",
            name="Student Agent",
            description="Learner Model + Personalization. Tracks learner profiles "
                       "for personalized learning experiences.",
            capabilities=[
                AgentCapability.LEARNER_MODELING
            ],
            allowed_tools=["logging"],
            system_prompt=self._get_student_model_prompt(),
            temperature=0.3
        )
        super().__init__(config)
        
        from config.settings import settings
        self.data_dir = data_dir or settings.data_dir
        self.profiles_dir = self.data_dir / "learner_profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of profiles
        self._profiles: Dict[str, LearnerProfile] = {}
        
        # Long-term memory store
        self._long_term_memory = LongTermMemory(self.data_dir)
    
    def _get_student_model_prompt(self) -> str:
        return """You are the Student Model Agent in EduSmartLearn.

Your role is to understand and support each learner:

1. **Track Progress**: Monitor mastery levels across topics
2. **Identify Gaps**: Detect misconceptions and weak areas
3. **Personalize**: Adapt recommendations to learning style
4. **Recommend**: Suggest appropriate next activities

Privacy principles:
- Store only necessary learning data
- Require consent for data storage
- Allow learners to view/delete their data
- Use data only to improve learning

When analyzing learner performance:
- Look for patterns in quiz results
- Identify recurring mistakes
- Note topics that need review
- Celebrate progress and growth

Help each learner succeed at their own pace."""
    
    async def process_message(self, message: A2AMessage) -> A2AMessage:
        """Process student model requests."""
        logger.info(
            "student_model_processing",
            message_type=message.message_type.value,
            action=message.payload.get("action")
        )
        
        if message.message_type != MessageType.TASK_REQUEST:
            return message.create_response(
                message_type=MessageType.ERROR,
                sender=self.agent_id,
                payload={},
                error_code=ErrorCode.INVALID_REQUEST,
                error_message="Student model only handles TASK_REQUEST"
            )
        
        action = message.payload.get("action", "get_profile")
        
        if action == "get_profile":
            return await self._get_profile(message)
        elif action == "update_mastery":
            return await self._update_mastery(message)
        elif action == "record_quiz":
            return await self._record_quiz_result(message)
        elif action == "get_recommendations":
            return await self._get_recommendations(message)
        elif action == "update_preferences":
            return await self._update_preferences(message)
        else:
            return await self._get_profile(message)
    
    def _load_profile(self, user_id: str, increment_session: bool = False) -> LearnerProfile:
        """Load or create learner profile with auto-save."""
        if user_id in self._profiles:
            profile = self._profiles[user_id]
            if increment_session:
                profile.session_count += 1
                self._save_profile(profile)
            return profile
        
        profile_file = self.profiles_dir / f"{user_id}.json"
        
        if profile_file.exists():
            try:
                data = json.loads(profile_file.read_text())
                profile = LearnerProfile.from_dict(data)
                logger.info("profile_loaded", user_id=user_id, sessions=profile.session_count)
            except Exception as e:
                logger.warning("profile_load_failed", user_id=user_id, error=str(e))
                profile = LearnerProfile(user_id)
        else:
            profile = LearnerProfile(user_id)
            logger.info("profile_created", user_id=user_id)
        
        # Increment session count for new session
        if increment_session:
            profile.session_count += 1
        
        self._profiles[user_id] = profile
        
        # Auto-save on load to persist session count
        self._save_profile(profile)
        
        return profile
    
    def _save_profile(self, profile: LearnerProfile) -> None:
        """Save learner profile to disk (includes long-term memory)."""
        profile.last_updated = datetime.utcnow()
        profile_file = self.profiles_dir / f"{profile.user_id}.json"
        profile_file.write_text(json.dumps(profile.to_dict(), indent=2))
        
        # Also sync to long-term memory store
        self._long_term_memory.store(
            user_id=profile.user_id,
            key="learner_profile",
            value=profile.to_dict(),
            consent_verified=True
        )
        
        logger.info("profile_saved", user_id=profile.user_id, file=str(profile_file))
    
    async def _get_profile(self, message: A2AMessage) -> A2AMessage:
        """Get learner profile."""
        user_id = message.payload.get("user_id", "")
        
        if not user_id:
            return message.create_response(
                message_type=MessageType.ERROR,
                sender=self.agent_id,
                payload={},
                error_code=ErrorCode.INVALID_REQUEST,
                error_message="user_id is required"
            )
        
        profile = self._load_profile(user_id)
        
        # Generate summary
        summary = await self._generate_profile_summary(profile)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": summary,
                "action": "get_profile",
                "profile": profile.to_dict()
            }
        )
    
    async def _generate_profile_summary(self, profile: LearnerProfile) -> str:
        """Generate human-readable profile summary."""
        if not profile.mastery_levels and not profile.quiz_history:
            return f"New learner profile for {profile.user_id}. No learning history yet."
        
        # Calculate overall progress
        if profile.mastery_levels:
            avg_mastery = sum(profile.mastery_levels.values()) / len(profile.mastery_levels)
            strong_topics = [t for t, m in profile.mastery_levels.items() if m >= 0.7]
            weak_topics = [t for t, m in profile.mastery_levels.items() if m < 0.4]
        else:
            avg_mastery = 0
            strong_topics = []
            weak_topics = []
        
        summary = f"""**Learner Profile: {profile.user_id}**

**Sessions:** {profile.session_count}
**Topics Studied:** {len(profile.topics_studied)}
**Average Mastery:** {avg_mastery*100:.1f}%

**Strong Areas:** {', '.join(strong_topics) if strong_topics else 'Building foundation'}
**Areas to Improve:** {', '.join(weak_topics) if weak_topics else 'Keep practicing!'}

**Preferences:**
- Explanation style: {profile.preferences.get('explanation_style', 'balanced')}
- Difficulty: {profile.preferences.get('difficulty_preference', 'adaptive')}
"""
        return summary
    
    async def _update_mastery(self, message: A2AMessage) -> A2AMessage:
        """Update mastery level for a topic."""
        user_id = message.payload.get("user_id", "")
        topic = message.payload.get("topic", "")
        score = message.payload.get("score", 0.0)  # 0.0 to 1.0
        
        profile = self._load_profile(user_id)
        
        # Update mastery with exponential moving average
        current = profile.mastery_levels.get(topic, 0.5)
        alpha = 0.3  # Learning rate
        new_mastery = alpha * score + (1 - alpha) * current
        
        profile.mastery_levels[topic] = new_mastery
        
        if topic not in profile.topics_studied:
            profile.topics_studied.append(topic)
        
        self._save_profile(profile)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": f"Updated mastery for {topic}: {new_mastery*100:.1f}%",
                "action": "update_mastery",
                "topic": topic,
                "new_mastery": new_mastery
            }
        )
    
    async def _record_quiz_result(self, message: A2AMessage) -> A2AMessage:
        """Record quiz result and update mastery."""
        user_id = message.payload.get("user_id", "")
        quiz_id = message.payload.get("quiz_id", "")
        topic = message.payload.get("topic", "")
        score = message.payload.get("score", 0.0)
        details = message.payload.get("details", {})
        
        profile = self._load_profile(user_id)
        
        # Record quiz
        profile.quiz_history.append({
            "quiz_id": quiz_id,
            "topic": topic,
            "score": score,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        })
        
        # Update mastery based on quiz score
        current = profile.mastery_levels.get(topic, 0.5)
        new_mastery = 0.4 * (score / 100) + 0.6 * current
        profile.mastery_levels[topic] = new_mastery
        
        self._save_profile(profile)
        
        # Generate feedback
        feedback = await self._generate_quiz_feedback(profile, topic, score)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": feedback,
                "action": "record_quiz",
                "new_mastery": new_mastery
            }
        )
    
    async def _generate_quiz_feedback(
        self,
        profile: LearnerProfile,
        topic: str,
        score: float
    ) -> str:
        """Generate personalized feedback on quiz performance."""
        mastery = profile.mastery_levels.get(topic, 0.5)
        
        prompt = f"""Generate brief, encouraging feedback for a student who scored {score:.1f}% 
on a quiz about {topic}. Their current mastery level is {mastery*100:.1f}%.

Keep it positive and suggest next steps."""

        return await self.generate_response(prompt, use_history=False)
    
    async def _get_recommendations(self, message: A2AMessage) -> A2AMessage:
        """Get personalized learning recommendations."""
        user_id = message.payload.get("user_id", "")
        
        profile = self._load_profile(user_id)
        
        # Generate recommendations based on profile
        recommendations = await self._generate_recommendations(profile)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": recommendations,
                "action": "get_recommendations"
            }
        )
    
    async def _generate_recommendations(self, profile: LearnerProfile) -> str:
        """Generate personalized learning recommendations."""
        # Find weak topics
        weak_topics = [
            t for t, m in profile.mastery_levels.items() if m < 0.5
        ]
        
        # Find topics to advance
        ready_topics = [
            t for t, m in profile.mastery_levels.items() if 0.5 <= m < 0.8
        ]
        
        prompt = f"""Generate 3 personalized learning recommendations for a student with:

Weak areas needing review: {weak_topics if weak_topics else 'None identified yet'}
Topics ready to advance: {ready_topics if ready_topics else 'Building foundation'}
Preferred style: {profile.preferences.get('explanation_style', 'balanced')}
Sessions completed: {profile.session_count}

Provide specific, actionable recommendations."""

        return await self.generate_response(prompt, use_history=False)
    
    async def _update_preferences(self, message: A2AMessage) -> A2AMessage:
        """Update learner preferences."""
        user_id = message.payload.get("user_id", "")
        preferences = message.payload.get("preferences", {})
        
        profile = self._load_profile(user_id)
        profile.preferences.update(preferences)
        self._save_profile(profile)
        
        return message.create_response(
            message_type=MessageType.TASK_RESPONSE,
            sender=self.agent_id,
            payload={
                "output": "Preferences updated successfully",
                "action": "update_preferences",
                "preferences": profile.preferences
            }
        )
    
    def add_key_learning(self, user_id: str, topic: str, learning: str) -> None:
        """Add a key learning to long-term memory."""
        profile = self._load_profile(user_id)
        profile.long_term_memory["key_learnings"].append({
            "topic": topic,
            "learning": learning,
            "timestamp": datetime.utcnow().isoformat()
        })
        self._save_profile(profile)
    
    def add_conversation_summary(self, user_id: str, session_id: str, summary: str) -> None:
        """Add a conversation summary to long-term memory."""
        profile = self._load_profile(user_id)
        profile.long_term_memory["conversation_summaries"].append({
            "session_id": session_id,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })
        # Keep only last 20 summaries
        profile.long_term_memory["conversation_summaries"] = \
            profile.long_term_memory["conversation_summaries"][-20:]
        self._save_profile(profile)
    
    def track_topic(self, user_id: str, topic: str) -> None:
        """Track frequently asked topics."""
        profile = self._load_profile(user_id)
        topics = profile.long_term_memory["frequently_asked_topics"]
        topics[topic] = topics.get(topic, 0) + 1
        self._save_profile(profile)
    
    def add_milestone(self, user_id: str, milestone: str) -> None:
        """Add a learning milestone."""
        profile = self._load_profile(user_id)
        profile.long_term_memory["learning_milestones"].append({
            "milestone": milestone,
            "timestamp": datetime.utcnow().isoformat()
        })
        self._save_profile(profile)
    
    def initialize_session(self, user_id: str) -> LearnerProfile:
        """Initialize a new session for a user (increments session count)."""
        return self._load_profile(user_id, increment_session=True)
