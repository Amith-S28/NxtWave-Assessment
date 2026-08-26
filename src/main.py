import argparse
import sys
import uuid
from typing import Optional

from src.config import Config
from src.llm import get_llm_client
from src.memory.store import MemoryStore
from src.graph import create_pipeline_graph
from src.utils.logger import print_banner, console
from rich.table import Table
from rich.panel import Panel


def inspect_memory_cli():
    """CLI utility to inspect persistent SQLite memory."""
    store = MemoryStore()
    stats = store.inspect_memory()

    print_banner("🧠 NxtWave System Memory Inspection", "Persistent Self-Evolution Database")

    console.print(f"[bold]Total Runs Recorded:[/bold] {stats['total_runs']}")
    console.print(f"[bold]Total Failures Logged:[/bold] {stats['total_failures_recorded']}")
    console.print(f"[bold]Total Evolved Rules Synthesized:[/bold] {stats['total_evolved_rules']}\n")

    if stats["checkpoint_failure_breakdown"]:
        tbl = Table(title="Historical Checkpoint Failure Breakdown", header_style="bold red")
        tbl.add_column("Checkpoint Name", style="bold")
        tbl.add_column("Failure Count", justify="center", style="yellow")
        for item in stats["checkpoint_failure_breakdown"]:
            tbl.add_row(item["checkpoint_name"], str(item["count"]))
        console.print(tbl)

    if stats["recent_evolved_instructions"]:
        tbl2 = Table(title="Active Evolved Prompt Guidelines", header_style="bold green")
        tbl2.add_column("#", width=4)
        tbl2.add_column("Topic", style="cyan", width=25)
        tbl2.add_column("Evolved Guideline Rule", style="white")
        for idx, item in enumerate(stats["recent_evolved_instructions"], 1):
            tbl2.add_row(str(idx), item["topic"], item["instruction"])
        console.print(tbl2)


def clear_memory_cli():
    """CLI utility to clear persistent SQLite memory."""
    store = MemoryStore()
    store.clear_memory()
    console.print(Panel("[bold yellow]🧹 System memory database cleared successfully.[/bold yellow]"))


def run_pipeline(
    topic: str = "RAG (Retrieval-Augmented Generation)",
    max_retries: int = 2,
    inject_error: bool = False,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    mock: bool = False,
):
    """Run the complete Self-Evaluating Lesson Content Generator pipeline."""
    print_banner(
        "🚀 NxtWave Self-Evaluating Content Generator",
        f"Topic: {topic} | Max Retries: {max_retries} | Error Injection: {inject_error}",
    )

    # Initialize client & memory
    llm_client = get_llm_client(provider=provider, model=model, api_key=api_key, mock=mock)
    memory_store = MemoryStore()

    # Compile LangGraph state machine
    graph = create_pipeline_graph(llm=llm_client, memory_store=memory_store)

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    initial_state = {
        "run_id": run_id,
        "topic": topic,
        "learner_profile": Config.DEFAULT_LEARNER_PROFILE,
        "current_lesson": "",
        "attempt_number": 0,
        "max_attempts": 1 + max_retries,
        "rubric_results": [],
        "all_passed": False,
        "rejection_log": [],
        "retry_feedback": None,
        "memory_context": "",
        "evolved_instructions": [],
        "inject_error": inject_error,
        "status": "INITIALIZED",
        "output_lesson_path": None,
        "output_log_path": None,
    }

    # Execute graph
    final_state = graph.invoke(initial_state)

    # Output final executive summary
    console.print("\n" + "=" * 60)
    if final_state.get("all_passed"):
        console.print(
            Panel(
                f"[bold green]✨ SUCCESS: Lesson generated and verified against all 7 hard rubric checkpoints![/bold green]\n\n"
                f"[bold]Total Attempts Used:[/bold] {final_state.get('attempt_number', 1)}\n"
                f"[bold]Deliverable Lesson:[/bold] {final_state.get('output_lesson_path')}\n"
                f"[bold]Rejection & Evaluation Log:[/bold] {final_state.get('output_log_path')}",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold yellow]⚠️ PIPELINE TERMINATED: Max retries ({max_retries}) reached without 100% rubric pass.[/bold yellow]\n\n"
                f"[bold]Total Attempts Used:[/bold] {final_state.get('attempt_number', 1)}\n"
                f"[bold]Best Candidate Lesson:[/bold] {final_state.get('output_lesson_path')}\n"
                f"[bold]Rejection & Evaluation Log:[/bold] {final_state.get('output_log_path')}",
                border_style="yellow",
            )
        )
    console.print("=" * 60 + "\n")

    return final_state


def main():
    parser = argparse.ArgumentParser(
        description="Self-Evaluating Lesson Content Generator — Agentic Generate-Evaluate-Regenerate Loop"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="RAG (Retrieval-Augmented Generation)",
        help="The educational topic to generate a lesson on (default: 'RAG (Retrieval-Augmented Generation)')",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum regeneration retries upon rubric failure (default: 2)",
    )
    parser.add_argument(
        "--inject-error",
        action="store_true",
        help="Deliberately inject a factual misconception in attempt #1 to demonstrate evaluator discrimination",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gemini", "openai", "mock"],
        default=None,
        help="LLM Provider to use (gemini or openai)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Specific model name (e.g. gemini-2.5-flash or gpt-4o)",
    )
    parser.add_argument(
        "--inspect-memory",
        action="store_true",
        help="Inspect SQLite system memory stats, failure logs, and evolved guidelines",
    )
    parser.add_argument(
        "--clear-memory",
        action="store_true",
        help="Clear persistent system memory database",
    )

    args = parser.parse_args()

    if args.inspect_memory:
        inspect_memory_cli()
        return

    if args.clear_memory:
        clear_memory_cli()
        return

    try:
        run_pipeline(
            topic=args.topic,
            max_retries=args.max_retries,
            inject_error=args.inject_error,
            provider=args.provider,
            model=args.model,
        )
    except Exception as e:
        console.print(f"\n[bold red]FATAL EXECUTION ERROR:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
