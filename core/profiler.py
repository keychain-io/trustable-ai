"""
Workflow Profiling Framework

Provides timing, token estimation, and cost analysis for multi-agent workflows.
Helps identify bottlenecks and optimize agent execution.

Usage:
    from workflow_profiler import WorkflowProfiler

    profiler = WorkflowProfiler("sprint-planning")

    # Time an agent call
    call_data = profiler.start_agent_call("business-analyst", task_description, model="sonnet")
    # ... execute agent ...
    profiler.complete_agent_call(call_data, success=True, output_length=len(output))

    # Generate report
    profiler.save_report()
    print(profiler.generate_report())
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AgentCallMetrics:
    """Metrics for a single agent call."""
    agent_name: str
    task_description: str
    model: str
    started_at: str
    completed_at: str
    duration_seconds: float
    tokens_input_estimate: int
    tokens_output_estimate: int
    tokens_total_estimate: int
    cost_estimate_usd: float
    success: bool
    error: Optional[str] = None


class WorkflowProfiler:
    """
    Profile multi-agent workflow execution.

    Tracks timing, token usage estimates, and costs for each agent call.
    Generates reports to identify bottlenecks and optimize workflows.
    """

    # Model pricing (USD per 1M tokens) as of 2025
    MODEL_PRICING = {
        "opus": {"input": 15.00, "output": 75.00},
        "sonnet": {"input": 3.00, "output": 15.00},
        "haiku": {"input": 0.25, "output": 1.25}
    }

    def __init__(self, workflow_name: str):
        """
        Initialize workflow profiler.

        Args:
            workflow_name: Name of workflow being profiled
        """
        self.workflow_name = workflow_name
        self.started_at = datetime.now()
        self.agent_calls: List[AgentCallMetrics] = []
        self.total_duration = 0.0
        self.metadata: Dict[str, Any] = {}

    def start_agent_call(
        self,
        agent_name: str,
        task_description: str,
        model: str = "sonnet"
    ) -> Dict[str, Any]:
        """
        Start timing an agent call.

        Args:
            agent_name: Name of the agent
            task_description: Description of the task
            model: Model being used (opus, sonnet, haiku)

        Returns:
            Dict with call data for passing to complete_agent_call
        """
        return {
            "agent_name": agent_name,
            "task_description": task_description,
            "model": model.lower(),
            "started_at": datetime.now().isoformat(),
            "start_time": time.time()
        }

    def complete_agent_call(
        self,
        call_data: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None,
        output_length: Optional[int] = None
    ) -> None:
        """
        Record completed agent call.

        Args:
            call_data: Data from start_agent_call
            success: Whether the call succeeded
            error: Optional error message
            output_length: Optional output length in characters
        """
        duration = time.time() - call_data["start_time"]

        # Estimate tokens
        input_tokens = self._estimate_tokens(call_data["task_description"], is_code=False)
        output_tokens = self._estimate_tokens_from_length(output_length) if output_length else input_tokens // 2
        total_tokens = input_tokens + output_tokens

        # Estimate cost
        cost = self._estimate_cost(
            call_data["model"],
            input_tokens,
            output_tokens
        )

        metrics = AgentCallMetrics(
            agent_name=call_data["agent_name"],
            task_description=call_data["task_description"][:200] + "..." if len(call_data["task_description"]) > 200 else call_data["task_description"],
            model=call_data["model"],
            started_at=call_data["started_at"],
            completed_at=datetime.now().isoformat(),
            duration_seconds=duration,
            tokens_input_estimate=input_tokens,
            tokens_output_estimate=output_tokens,
            tokens_total_estimate=total_tokens,
            cost_estimate_usd=cost,
            success=success,
            error=error
        )

        self.agent_calls.append(metrics)
        self.total_duration += duration

        # Print immediate feedback
        status = "✅" if success else "❌"
        print(f"{status} {call_data['agent_name']} completed in {duration:.2f}s (~{total_tokens} tokens, ~${cost:.4f})")

    def _estimate_tokens(self, text: str, is_code: bool = False) -> int:
        """
        Estimate token count from text.

        Claude models use ~3.5 chars per token for English text,
        ~4.5 chars per token for code.

        Args:
            text: Text to estimate
            is_code: Whether text is primarily code

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Detect if text looks like code
        if not is_code:
            code_indicators = ['{', '}', 'def ', 'class ', 'import ', 'function ', '    ']
            code_count = sum(1 for indicator in code_indicators if indicator in text)
            is_code = code_count >= 3

        chars_per_token = 4.5 if is_code else 3.5
        return int(len(text) / chars_per_token)

    def _estimate_tokens_from_length(self, length: int) -> int:
        """Estimate tokens from character length."""
        return int(length / 4.0)  # Average estimate

    def _estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate API cost for agent call.

        Args:
            model: Model name (opus, sonnet, haiku)
            input_tokens: Input token count
            output_tokens: Output token count

        Returns:
            Estimated cost in USD
        """
        model_lower = model.lower()
        if model_lower not in self.MODEL_PRICING:
            model_lower = "sonnet"  # Default to sonnet

        pricing = self.MODEL_PRICING[model_lower]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def set_metadata(self, key: str, value: Any) -> None:
        """Store arbitrary metadata."""
        self.metadata[key] = value

    def generate_report(self) -> str:
        """
        Generate human-readable profiling report.

        Returns:
            Markdown formatted report
        """
        report = []
        report.append(f"# Workflow Profile: {self.workflow_name}")
        report.append("")
        report.append(f"**Started:** {self.started_at.isoformat()}")
        report.append(f"**Total Duration:** {self.total_duration:.2f}s")
        report.append(f"**Total Agent Calls:** {len(self.agent_calls)}")
        report.append("")

        # Summary statistics
        total_cost = sum(call.cost_estimate_usd for call in self.agent_calls)
        total_tokens = sum(call.tokens_total_estimate for call in self.agent_calls)
        successful_calls = sum(1 for call in self.agent_calls if call.success)

        report.append("## Summary Statistics")
        report.append("")
        report.append(f"- **Total Cost (estimated):** ${total_cost:.4f}")
        report.append(f"- **Total Tokens (estimated):** {total_tokens:,}")
        report.append(f"- **Successful Calls:** {successful_calls}/{len(self.agent_calls)}")
        report.append(f"- **Average Call Duration:** {self.total_duration / len(self.agent_calls):.2f}s")
        report.append("")

        # Agent call details table
        report.append("## Agent Call Details")
        report.append("")
        report.append("| Agent | Model | Duration | Tokens | Cost | Status |")
        report.append("|-------|-------|----------|--------|------|--------|")

        for call in self.agent_calls:
            status = "✅" if call.success else "❌"
            report.append(
                f"| {call.agent_name} | {call.model} | "
                f"{call.duration_seconds:.2f}s | {call.tokens_total_estimate:,} | "
                f"${call.cost_estimate_usd:.4f} | {status} |"
            )

        report.append("")

        # Model breakdown
        model_stats: Dict[str, Dict[str, Any]] = {}
        for call in self.agent_calls:
            if call.model not in model_stats:
                model_stats[call.model] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            model_stats[call.model]["count"] += 1
            model_stats[call.model]["total_duration"] += call.duration_seconds
            model_stats[call.model]["total_tokens"] += call.tokens_total_estimate
            model_stats[call.model]["total_cost"] += call.cost_estimate_usd

        report.append("## Model Usage")
        report.append("")
        report.append("| Model | Calls | Total Duration | Total Tokens | Total Cost | Avg Duration |")
        report.append("|-------|-------|----------------|--------------|------------|--------------|")

        for model, stats in sorted(model_stats.items()):
            avg_duration = stats["total_duration"] / stats["count"]
            report.append(
                f"| {model} | {stats['count']} | {stats['total_duration']:.2f}s | "
                f"{stats['total_tokens']:,} | ${stats['total_cost']:.4f} | {avg_duration:.2f}s |"
            )

        report.append("")

        # Bottleneck detection
        if self.agent_calls:
            slowest = max(self.agent_calls, key=lambda x: x.duration_seconds)
            most_expensive = max(self.agent_calls, key=lambda x: x.cost_estimate_usd)

            report.append("## Bottlenecks")
            report.append("")
            report.append(f"**Slowest Call:** {slowest.agent_name} ({slowest.duration_seconds:.2f}s)")
            report.append(f"- Task: {slowest.task_description}")
            report.append("")
            report.append(f"**Most Expensive Call:** {most_expensive.agent_name} (${most_expensive.cost_estimate_usd:.4f})")
            report.append(f"- Model: {most_expensive.model}")
            report.append(f"- Tokens: {most_expensive.tokens_total_estimate:,}")
            report.append("")

        # Errors
        errors = [call for call in self.agent_calls if not call.success]
        if errors:
            report.append("## Errors")
            report.append("")
            for error_call in errors:
                report.append(f"- **{error_call.agent_name}:** {error_call.error}")
            report.append("")

        # Metadata
        if self.metadata:
            report.append("## Metadata")
            report.append("")
            for key, value in self.metadata.items():
                report.append(f"- **{key}:** {value}")
            report.append("")

        return "\n".join(report)

    def save_report(self, output_dir: Optional[Path] = None) -> Path:
        """
        Save profile report to file.

        Args:
            output_dir: Directory to save report (default: .claude/profiling/)

        Returns:
            Path to saved report file
        """
        if output_dir is None:
            output_dir = Path(".claude/profiling")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{self.workflow_name}-{timestamp}.md"
        filepath = output_dir / filename

        # Save markdown report
        filepath.write_text(self.generate_report(), encoding='utf-8')
        print(f"📊 Profile report saved: {filepath}")

        # Save raw JSON
        json_file = filepath.with_suffix(".json")
        json_data = {
            "workflow_name": self.workflow_name,
            "started_at": self.started_at.isoformat(),
            "total_duration": self.total_duration,
            "metadata": self.metadata,
            "agent_calls": [asdict(call) for call in self.agent_calls]
        }
        json_file.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
        print(f"📊 Profile data saved: {json_file}")

        return filepath

    def print_summary(self) -> None:
        """Print a quick summary to console."""
        print("\n" + "=" * 80)
        print(f"Workflow Profile: {self.workflow_name}")
        print("=" * 80)
        print(f"Duration: {self.total_duration:.2f}s")
        print(f"Agent Calls: {len(self.agent_calls)}")

        total_cost = sum(call.cost_estimate_usd for call in self.agent_calls)
        total_tokens = sum(call.tokens_total_estimate for call in self.agent_calls)

        print(f"Total Tokens (est): {total_tokens:,}")
        print(f"Total Cost (est): ${total_cost:.4f}")
        print("=" * 80 + "\n")


def compare_workflow_runs(
    baseline_file: Path,
    current_file: Path
) -> str:
    """
    Compare two workflow runs to detect performance regression.

    Args:
        baseline_file: Path to baseline JSON profile
        current_file: Path to current JSON profile

    Returns:
        Markdown comparison report
    """
    baseline = json.loads(baseline_file.read_text())
    current = json.loads(current_file.read_text())

    report = []
    report.append(f"# Workflow Performance Comparison")
    report.append("")
    report.append(f"**Baseline:** {baseline['started_at']}")
    report.append(f"**Current:** {current['started_at']}")
    report.append("")

    # Duration comparison
    baseline_duration = baseline['total_duration']
    current_duration = current['total_duration']
    duration_change = ((current_duration - baseline_duration) / baseline_duration) * 100

    report.append("## Overall Performance")
    report.append("")
    report.append(f"- Baseline Duration: {baseline_duration:.2f}s")
    report.append(f"- Current Duration: {current_duration:.2f}s")
    report.append(f"- Change: {duration_change:+.1f}%")
    report.append("")

    if abs(duration_change) > 20:
        emoji = "🔴" if duration_change > 0 else "🟢"
        report.append(f"{emoji} **Significant change detected!**")
        report.append("")

    # Token comparison
    baseline_tokens = sum(call['tokens_total_estimate'] for call in baseline['agent_calls'])
    current_tokens = sum(call['tokens_total_estimate'] for call in current['agent_calls'])
    tokens_change = ((current_tokens - baseline_tokens) / baseline_tokens) * 100 if baseline_tokens > 0 else 0

    report.append("## Token Usage")
    report.append("")
    report.append(f"- Baseline Tokens: {baseline_tokens:,}")
    report.append(f"- Current Tokens: {current_tokens:,}")
    report.append(f"- Change: {tokens_change:+.1f}%")
    report.append("")

    # Cost comparison
    baseline_cost = sum(call['cost_estimate_usd'] for call in baseline['agent_calls'])
    current_cost = sum(call['cost_estimate_usd'] for call in current['agent_calls'])
    cost_change = ((current_cost - baseline_cost) / baseline_cost) * 100 if baseline_cost > 0 else 0

    report.append("## Cost")
    report.append("")
    report.append(f"- Baseline Cost: ${baseline_cost:.4f}")
    report.append(f"- Current Cost: ${current_cost:.4f}")
    report.append(f"- Change: {cost_change:+.1f}%")
    report.append("")

    return "\n".join(report)


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "compare" and len(sys.argv) > 3:
            baseline = Path(sys.argv[2])
            current = Path(sys.argv[3])
            print(compare_workflow_runs(baseline, current))

        elif command == "list":
            profile_dir = Path(".claude/profiling")
            if profile_dir.exists():
                profiles = sorted(profile_dir.glob("*.json"))
                print(f"Found {len(profiles)} profile runs:")
                for profile in profiles:
                    data = json.loads(profile.read_text())
                    print(f"  • {profile.name} - {data['started_at']} - {data['total_duration']:.2f}s")
    else:
        print("Usage:")
        print("  python profiler.py list")
        print("  python profiler.py compare <baseline.json> <current.json>")
