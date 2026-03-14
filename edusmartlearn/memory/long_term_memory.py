"""
memory/long_term_memory.py
==========================
Long-Term Memory - Persistent learner data storage.

Handles:
- Learner profile persistence
- Learning history
- Preferences and settings
- Privacy-compliant data management
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import structlog

from config.settings import settings

logger = structlog.get_logger()


class LongTermMemory:
    """
    Manages persistent learner data with privacy controls.
    
    Features:
    - Store and retrieve learner data
    - Privacy-compliant data handling
    - Data retention policies
    - User data export/deletion
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.data_dir
        self.memory_dir = self.data_dir / "long_term_memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_file(self, user_id: str) -> Path:
        """Get the file path for a user's data."""
        return self.memory_dir / f"{user_id}_memory.json"
    
    def store(
        self,
        user_id: str,
        key: str,
        value: Any,
        consent_verified: bool = False
    ) -> bool:
        """
        Store data for a user.
        
        Args:
            user_id: User identifier
            key: Data key
            value: Data to store
            consent_verified: Whether user consented to storage
            
        Returns:
            True if stored successfully
        """
        if settings.safety.require_consent_for_data_storage and not consent_verified:
            logger.warning("storage_blocked_no_consent", user_id=user_id, key=key)
            return False
        
        user_data = self.retrieve_all(user_id)
        user_data[key] = {
            "value": value,
            "stored_at": datetime.utcnow().isoformat(),
            "consent_verified": consent_verified
        }
        
        self._save_user_data(user_id, user_data)
        logger.info("data_stored", user_id=user_id, key=key)
        return True
    
    def retrieve(self, user_id: str, key: str, default: Any = None) -> Any:
        """Retrieve specific data for a user."""
        user_data = self.retrieve_all(user_id)
        entry = user_data.get(key, {})
        return entry.get("value", default)
    
    def retrieve_all(self, user_id: str) -> Dict[str, Any]:
        """Retrieve all data for a user."""
        user_file = self._get_user_file(user_id)
        
        if not user_file.exists():
            return {}
        
        try:
            return json.loads(user_file.read_text())
        except Exception as e:
            logger.error("memory_read_failed", user_id=user_id, error=str(e))
            return {}
    
    def _save_user_data(self, user_id: str, data: Dict[str, Any]) -> None:
        """Save user data to file."""
        user_file = self._get_user_file(user_id)
        user_file.write_text(json.dumps(data, indent=2, default=str))
    
    def delete(self, user_id: str, key: str) -> bool:
        """Delete specific data for a user."""
        user_data = self.retrieve_all(user_id)
        
        if key in user_data:
            del user_data[key]
            self._save_user_data(user_id, user_data)
            logger.info("data_deleted", user_id=user_id, key=key)
            return True
        
        return False
    
    def delete_all_user_data(self, user_id: str) -> bool:
        """Delete all data for a user (GDPR compliance)."""
        user_file = self._get_user_file(user_id)
        
        if user_file.exists():
            user_file.unlink()
            logger.info("all_user_data_deleted", user_id=user_id)
            return True
        
        return False
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data (GDPR compliance)."""
        return self.retrieve_all(user_id)
    
    def cleanup_old_data(self) -> int:
        """Remove data older than retention period."""
        retention_days = settings.session.memory_retention_days
        cutoff = datetime.utcnow().timestamp() - (retention_days * 24 * 60 * 60)
        
        cleaned = 0
        for user_file in self.memory_dir.glob("*_memory.json"):
            try:
                data = json.loads(user_file.read_text())
                updated = False
                
                for key in list(data.keys()):
                    stored_at = data[key].get("stored_at", "")
                    if stored_at:
                        stored_time = datetime.fromisoformat(stored_at).timestamp()
                        if stored_time < cutoff:
                            del data[key]
                            updated = True
                            cleaned += 1
                
                if updated:
                    user_file.write_text(json.dumps(data, indent=2))
                    
            except Exception as e:
                logger.warning("cleanup_failed", file=str(user_file), error=str(e))
        
        logger.info("memory_cleanup_completed", items_removed=cleaned)
        return cleaned


# Global long-term memory instance
long_term_memory = LongTermMemory()
