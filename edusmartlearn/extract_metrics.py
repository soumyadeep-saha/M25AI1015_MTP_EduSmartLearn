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
    """Display metrics matching the MTech report evaluation table."""
    if not data:
        return
    
    summary = data.get("summary", {})
    raw = data.get("raw_metrics", {})
    
    print("=" * 80)
    print("  EduSmartLearn - Evaluation Metrics Report")
    print("=" * 80)
    print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
    print(f"  Files Loaded: {data.get('files_loaded', 1)}")
    print("=" * 80)
    
    # ── EFFECTIVENESS ──
    effectiveness = summary.get("effectiveness", {})
    task_success = effectiveness.get("task_success_rate", 0) * 100
    total_tasks = effectiveness.get("total_tasks", 0)
    
    print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│  EFFECTIVENESS                                                              │")
    print("├──────────────────────────┬──────────────────────────────────┬────────────────┤")
    print("│ Metric                   │ Definition                       │ Result         │")
    print("├──────────────────────────┼──────────────────────────────────┼────────────────┤")
    print(f"│ Task Success Rate (%)    │ Fraction of tasks completed with │ {task_success:>13.1f}% │")
    print(f"│                          │ correct and useful response      │ ({total_tasks} tasks) │" if total_tasks < 100 else f"│                          │ correct and useful response      │ ({total_tasks} tasks)│")
    print("├──────────────────────────┼──────────────────────────────────┼────────────────┤")
    print("│ Explanation Quality (1-5)│ Human-based rating of clarity    │   (Manual)     │")
    print("│                          │ Rate each response 1-5 yourself  │                │")
    print("└──────────────────────────┴──────────────────────────────────┴────────────────┘")
    
    # ── EFFICIENCY ──
    efficiency = summary.get("efficiency", {})
    avg_latency_ms = efficiency.get("avg_response_time_ms", 0)
    avg_latency_s = avg_latency_ms / 1000.0
    total_responses = efficiency.get("total_responses", 0)
    
    # Calculate Avg Tool Calls / Task from raw metrics
    tool_calls = raw.get("tool_latency", [])
    completions = raw.get("task_completion", [])
    avg_tool_calls = len(tool_calls) / len(completions) if completions else 0
    
    # Calculate per-task latency breakdown
    response_times = raw.get("response_times", [])
    chat_times = [r["response_time_ms"] for r in response_times if r.get("action") == "chat"]
    quiz_times = [r["response_time_ms"] for r in response_times if r.get("action") == "generate_quiz"]
    code_times = [r["response_time_ms"] for r in response_times if r.get("action") == "execute_code"]
    
    print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│  EFFICIENCY                                                                 │")
    print("├──────────────────────────┬──────────────────────────────────┬────────────────┤")
    print("│ Metric                   │ Definition                       │ Result         │")
    print("├──────────────────────────┼──────────────────────────────────┼────────────────┤")
    print(f"│ Avg Tool Calls / Task    │ Average MCP tool invocations     │ {avg_tool_calls:>13.1f}  │")
    print(f"│                          │ per task                         │ ({len(tool_calls)} calls) │" if len(tool_calls) < 100 else f"│                          │ per task                         │({len(tool_calls)} calls)│")
    print("├──────────────────────────┼──────────────────────────────────┼────────────────┤")
    print(f"│ Latency / Task (s)       │ End-to-end time from user query  │ {avg_latency_s:>12.2f}s │")
    print(f"│                          │ to final response                │ ({total_responses} resp)  │")
    if chat_times:
        avg_chat = sum(chat_times) / len(chat_times) / 1000
        print(f"│   - Chat avg             │                                  │ {avg_chat:>12.2f}s │")
    if quiz_times:
        avg_quiz = sum(quiz_times) / len(quiz_times) / 1000
        print(f"│   - Quiz avg             │                                  │ {avg_quiz:>12.2f}s │")
    if code_times:
        avg_code = sum(code_times) / len(code_times) / 1000
        print(f"│   - Code avg             │                                  │ {avg_code:>12.2f}s │")
    print("└──────────────────────────┴──────────────────────────────────┴────────────────┘")
    
    # ── ROBUSTNESS ──
    robustness = summary.get("robustness", {})
    recovery_rate = robustness.get("recovery_rate", 1) * 100
    total_errors = robustness.get("total_errors", 0)
    
    print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│  ROBUSTNESS                                                                 │")
    print("├──────────────────────────┬──────────────────────────────────┬────────────────┤")
    print("│ Metric                   │ Definition                       │ Result         │")
    print("├──────────────────────────┼──────────────────────────────────┼────────────────┤")
    print(f"│ Recovery Rate (%)        │ Fraction of tool failures        │ {recovery_rate:>13.1f}% │")
    print(f"│                          │ handled through retry/fallback   │ ({total_errors} errors) │")
    print(f"│                          │ without incorrect output         │                │")
    print("└──────────────────────────┴──────────────────────────────────┴────────────────┘")
    
    # ── SAFETY & ALIGNMENT ──
    safety = summary.get("safety", {})
    total_checks = safety.get("total_checks", 0)
    violations = safety.get("violations", 0)
    blocked = total_checks - (total_checks - violations) if total_checks > 0 else 0
    
    # Calculate blocked unsafe call rate from safety_checks raw data
    safety_checks = raw.get("safety_checks", [])
    total_safety = len(safety_checks)
    blocked_count = sum(1 for c in safety_checks if not c.get("passed"))
    blocked_rate = (blocked_count / total_safety * 100) if total_safety > 0 else 100.0
    
    print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│  SAFETY & ALIGNMENT                                                         │")
    print("├──────────────────────────┬──────────────────────────────────┬────────────────┤")
    print("│ Metric                   │ Definition                       │ Result         │")
    print("├──────────────────────────┼──────────────────────────────────┼────────────────┤")
    print(f"│ Blocked Unsafe Call Rate │ Disallowed tool calls blocked    │ {blocked_rate:>13.1f}% │")
    print(f"│                          │ by policy / total tool calls     │ ({blocked_count}/{total_safety} checks)│")
    print("├──────────────────────────┼──────────────────────────────────┼────────────────┤")
    print(f"│ Policy Violation Count   │ Times system produced disallowed │ {violations:>14} │")
    print(f"│                          │ output or executed unsafe action │                │")
    print("└──────────────────────────┴──────────────────────────────────┴────────────────┘")
    
    # ── TASK BREAKDOWN ──
    counters = summary.get("counters", {})
    if counters:
        print("\n┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│  TASK BREAKDOWN                                                             │")
        print("├──────────────────────────────────────────┬────────────────────────────────────┤")
        for key, value in sorted(counters.items()):
            print(f"│  {key:<39} │ {value:>34} │")
        print("└──────────────────────────────────────────┴────────────────────────────────────┘")
    
    print("\n" + "=" * 80)
    print("  Report Complete")
    print("=" * 80)


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
