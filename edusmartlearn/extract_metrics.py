"""
extract_metrics.py
==================
Script to extract and display evaluation metrics after a test session.

Usage:
    python extract_metrics.py

Run this AFTER completing your test session with main.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

# Import the metrics collector
from observability.metrics import metrics_collector
from config.settings import settings


def load_all_metrics():
    """Load and aggregate ALL metrics files."""
    metrics_dir = settings.data_dir / "metrics"
    
    if not metrics_dir.exists():
        print("No metrics directory found. Run main.py first.")
        return None
    
    # Find all metrics files
    metrics_files = sorted(metrics_dir.glob("metrics_*.json"))
    
    if not metrics_files:
        print("No metrics files found. Run main.py and interact with the system first.")
        return None
    
    print(f"Loading {len(metrics_files)} metrics file(s)...\n")
    
    # Aggregate raw metrics from all files
    aggregated = {
        "task_completion": [],
        "response_times": [],
        "tool_latency": [],
        "errors": [],
        "safety_checks": [],
        "consent_requests": [],
        "quiz_scores": []
    }
    
    all_counters = {}
    
    for metrics_file in metrics_files:
        print(f"  - {metrics_file.name}")
        with open(metrics_file) as f:
            data = json.load(f)
        
        # Aggregate raw metrics
        raw = data.get("raw_metrics", {})
        for key in aggregated:
            if key in raw:
                aggregated[key].extend(raw[key])
        
        # Aggregate counters
        counters = data.get("summary", {}).get("counters", {})
        for key, value in counters.items():
            all_counters[key] = all_counters.get(key, 0) + value
    
    # Calculate aggregated summary
    summary = calculate_aggregated_summary(aggregated, all_counters)
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_loaded": len(metrics_files),
        "summary": summary,
        "raw_metrics": aggregated
    }


def calculate_aggregated_summary(raw_metrics, counters):
    """Calculate summary from aggregated raw metrics."""
    summary = {"counters": counters}
    
    # Effectiveness
    completions = raw_metrics.get("task_completion", [])
    if completions:
        success_count = sum(1 for c in completions if c.get("success"))
        summary["effectiveness"] = {
            "task_success_rate": success_count / len(completions),
            "total_tasks": len(completions)
        }
    else:
        summary["effectiveness"] = {"task_success_rate": 0.0, "total_tasks": 0}
    
    # Efficiency
    times = raw_metrics.get("response_times", [])
    if times:
        avg_time = sum(t.get("response_time_ms", 0) for t in times) / len(times)
        summary["efficiency"] = {
            "avg_response_time_ms": avg_time,
            "total_responses": len(times)
        }
    else:
        summary["efficiency"] = {"avg_response_time_ms": 0.0, "total_responses": 0}
    
    # Robustness
    errors = raw_metrics.get("errors", [])
    if errors:
        recovered = sum(1 for e in errors if e.get("recovered"))
        summary["robustness"] = {
            "total_errors": len(errors),
            "recovery_rate": recovered / len(errors)
        }
    else:
        summary["robustness"] = {"total_errors": 0, "recovery_rate": 1.0}
    
    # Safety
    checks = raw_metrics.get("safety_checks", [])
    if checks:
        passed = sum(1 for c in checks if c.get("passed"))
        summary["safety"] = {
            "safety_compliance_rate": passed / len(checks),
            "total_checks": len(checks),
            "violations": len(checks) - passed
        }
    else:
        summary["safety"] = {"safety_compliance_rate": 1.0, "total_checks": 0, "violations": 0}
    
    return summary


def display_metrics(data):
    """Display metrics in a formatted table."""
    if not data:
        return
    
    summary = data.get("summary", {})
    
    print("=" * 60)
    print("  EduSmartLearn - Evaluation Metrics Report")
    print("=" * 60)
    print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
    print(f"  Files Loaded: {data.get('files_loaded', 1)}")
    print("=" * 60)
    
    # Effectiveness
    effectiveness = summary.get("effectiveness", {})
    task_success = effectiveness.get("task_success_rate", 0) * 100
    total_tasks = effectiveness.get("total_tasks", 0)
    
    print("\n EFFECTIVENESS")
    print("-" * 40)
    print(f"  Task Success Rate:     {task_success:.1f}%")
    print(f"  Total Tasks:           {total_tasks}")
    
    # Efficiency
    efficiency = summary.get("efficiency", {})
    avg_latency = efficiency.get("avg_response_time_ms", 0)
    total_responses = efficiency.get("total_responses", 0)
    
    print("\n EFFICIENCY")
    print("-" * 40)
    print(f"  Avg Response Time:     {avg_latency:.0f} ms")
    print(f"  Total Responses:       {total_responses}")
    
    # Robustness
    robustness = summary.get("robustness", {})
    recovery_rate = robustness.get("recovery_rate", 1) * 100
    total_errors = robustness.get("total_errors", 0)
    
    print("\n ROBUSTNESS")
    print("-" * 40)
    print(f"  Recovery Rate:         {recovery_rate:.1f}%")
    print(f"  Total Errors:          {total_errors}")
    
    # Safety
    safety = summary.get("safety", {})
    compliance_rate = safety.get("safety_compliance_rate", 1) * 100
    violations = safety.get("violations", 0)
    total_checks = safety.get("total_checks", 0)
    
    print("\n SAFETY & ALIGNMENT")
    print("-" * 40)
    print(f"  Safety Compliance:     {compliance_rate:.1f}%")
    print(f"  Policy Violations:     {violations}")
    print(f"  Total Safety Checks:   {total_checks}")
    
    # Counters
    counters = summary.get("counters", {})
    if counters:
        print("\n COUNTERS")
        print("-" * 40)
        for key, value in counters.items():
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("  Report Complete")
    print("=" * 60)


def main():
    """Main function to extract and display metrics."""
    print("\n Extracting EduSmartLearn Metrics...\n")
    
    # Load and aggregate ALL metrics files
    data = load_all_metrics()
    
    if data:
        display_metrics(data)
    else:
        print("\n Tip: Run 'python main.py', complete your test queries,")
        print("   then run this script to see the metrics.")


if __name__ == "__main__":
    main()
