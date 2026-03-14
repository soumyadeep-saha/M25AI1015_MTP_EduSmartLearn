"""
observability/metrics.py
========================
Metrics Collector - Evaluation metrics for agent quality.

Tracks metrics aligned with agent-quality pillars:
- Effectiveness: Task completion, accuracy
- Efficiency: Response time, token usage
- Robustness: Error rates, recovery
- Safety/Alignment: Policy compliance
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path
import structlog

from config.settings import settings

logger = structlog.get_logger()


class MetricsCollector:
    """
    Collects and aggregates metrics for evaluation.
    
    Metrics categories:
    1. Effectiveness: How well tasks are completed
    2. Efficiency: Resource usage and response times
    3. Robustness: Error handling and recovery
    4. Safety: Policy compliance and security
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.data_dir
        self.metrics_dir = self.data_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory metrics (aggregated periodically)
        self._metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Counters
        self._counters: Dict[str, int] = defaultdict(int)
    
    # === Effectiveness Metrics ===
    
    def record_task_completion(
        self,
        task_type: str,
        success: bool,
        session_id: Optional[str] = None
    ) -> None:
        """Record task completion status."""
        self._metrics["task_completion"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "task_type": task_type,
            "success": success,
            "session_id": session_id
        })
        
        self._counters[f"tasks_{task_type}_total"] += 1
        if success:
            self._counters[f"tasks_{task_type}_success"] += 1
    
    def record_quiz_score(
        self,
        topic: str,
        score: float,
        user_id: str
    ) -> None:
        """Record quiz performance."""
        self._metrics["quiz_scores"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "topic": topic,
            "score": score,
            "user_id": user_id
        })
    
    # === Efficiency Metrics ===
    
    def record_response_time(
        self,
        agent_id: str,
        response_time_ms: float,
        action: str
    ) -> None:
        """Record agent response time."""
        self._metrics["response_times"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "response_time_ms": response_time_ms,
            "action": action
        })
    
    def record_tool_latency(
        self,
        tool_name: str,
        latency_ms: float
    ) -> None:
        """Record tool execution latency."""
        self._metrics["tool_latency"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "tool_name": tool_name,
            "latency_ms": latency_ms
        })
    
    # === Robustness Metrics ===
    
    def record_error(
        self,
        agent_id: str,
        error_type: str,
        recovered: bool
    ) -> None:
        """Record error occurrence."""
        self._metrics["errors"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "error_type": error_type,
            "recovered": recovered
        })
        
        self._counters["errors_total"] += 1
        if recovered:
            self._counters["errors_recovered"] += 1
    
    # === Safety Metrics ===
    
    def record_safety_check(
        self,
        check_type: str,
        passed: bool,
        session_id: Optional[str] = None
    ) -> None:
        """Record safety check result."""
        self._metrics["safety_checks"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "check_type": check_type,
            "passed": passed,
            "session_id": session_id
        })
        
        self._counters["safety_checks_total"] += 1
        if not passed:
            self._counters["safety_violations"] += 1
    
    def record_consent_request(
        self,
        operation: str,
        granted: bool
    ) -> None:
        """Record consent request outcome."""
        self._metrics["consent_requests"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "granted": granted
        })
    
    # === Aggregation and Reporting ===
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        return {
            "effectiveness": self._get_effectiveness_summary(),
            "efficiency": self._get_efficiency_summary(),
            "robustness": self._get_robustness_summary(),
            "safety": self._get_safety_summary(),
            "counters": dict(self._counters)
        }
    
    def _get_effectiveness_summary(self) -> Dict[str, Any]:
        """Summarize effectiveness metrics."""
        completions = self._metrics.get("task_completion", [])
        if not completions:
            return {"task_success_rate": 0.0}
        
        success_count = sum(1 for c in completions if c["success"])
        return {
            "task_success_rate": success_count / len(completions),
            "total_tasks": len(completions)
        }
    
    def _get_efficiency_summary(self) -> Dict[str, Any]:
        """Summarize efficiency metrics."""
        times = self._metrics.get("response_times", [])
        if not times:
            return {"avg_response_time_ms": 0.0}
        
        avg_time = sum(t["response_time_ms"] for t in times) / len(times)
        return {
            "avg_response_time_ms": avg_time,
            "total_responses": len(times)
        }
    
    def _get_robustness_summary(self) -> Dict[str, Any]:
        """Summarize robustness metrics."""
        errors = self._metrics.get("errors", [])
        if not errors:
            return {"error_rate": 0.0, "recovery_rate": 1.0}
        
        recovered = sum(1 for e in errors if e["recovered"])
        return {
            "total_errors": len(errors),
            "recovery_rate": recovered / len(errors) if errors else 1.0
        }
    
    def _get_safety_summary(self) -> Dict[str, Any]:
        """Summarize safety metrics."""
        checks = self._metrics.get("safety_checks", [])
        if not checks:
            return {"safety_compliance_rate": 1.0}
        
        passed = sum(1 for c in checks if c["passed"])
        return {
            "safety_compliance_rate": passed / len(checks),
            "total_checks": len(checks),
            "violations": len(checks) - passed
        }
    
    def save_metrics(self) -> None:
        """Save metrics to file."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H")
        metrics_file = self.metrics_dir / f"metrics_{timestamp}.json"
        
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": self.get_summary(),
            "raw_metrics": {k: v for k, v in self._metrics.items()}
        }
        
        metrics_file.write_text(json.dumps(data, indent=2))
        logger.info("metrics_saved", file=str(metrics_file))
    
    def reset(self) -> None:
        """Reset all metrics (after saving)."""
        self._metrics.clear()
        self._counters.clear()


# Global metrics collector instance
metrics_collector = MetricsCollector()
