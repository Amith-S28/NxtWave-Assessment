import sys
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure UTF-8 output encoding for Windows compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(force_terminal=True, legacy_windows=False)


def print_banner(title: str, subtitle: str = ""):
    """Print an attractive system banner."""
    content = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, border_style="cyan", expand=False))


def print_step(step_name: str, message: str = ""):
    """Print step transition indicator."""
    msg = f"[bold yellow]>> {step_name}[/bold yellow]"
    if message:
        msg += f" - [white]{message}[/white]"
    console.print(msg)


def print_evaluation_table(attempt: int, results: List[Dict[str, Any]], all_passed: bool):
    """Print a clean rubric evaluation summary table."""
    table = Table(
        title=f"Rubric Evaluation Results -- Attempt #{attempt}",
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Checkpoint", style="bold", width=32)
    table.add_column("Verdict", justify="center", width=10)
    table.add_column("Reasoning & Feedback", style="white")

    for idx, res in enumerate(results, 1):
        passed = res.get("passed", False)
        verdict = "[bold green]PASS[/bold green]" if passed else "[bold red]FAIL[/bold red]"
        reasoning = res.get("reasoning", "")
        suggestion = res.get("suggestion", "")
        detail = f"{reasoning}"
        if not passed and suggestion:
            detail += f"\n[bold yellow]Fix Suggestion:[/bold yellow] {suggestion}"

        table.add_row(str(idx), res.get("checkpoint_name", ""), verdict, detail)

    console.print(table)

    if all_passed:
        console.print(Panel("[bold green]ALL RUBRIC CHECKS PASSED -- Lesson cleared for shipping![/bold green]", border_style="green"))
    else:
        failed_count = sum(1 for r in results if not r.get("passed", False))
        console.print(Panel(f"[bold red]{failed_count} CHECKPOINT(S) FAILED -- Triggering targeted regeneration loop.[/bold red]", border_style="red"))


def print_memory_loaded(instructions: List[str]):
    """Display memory patches retrieved before generation."""
    if not instructions:
        console.print("[dim]No past memory patches found for this topic (starting fresh).[/dim]")
        return

    table = Table(title="System Memory: Evolved Guidelines from Past Runs", header_style="bold blue")
    table.add_column("#", width=4)
    table.add_column("Guideline Injected into Generator Prompt", style="cyan")

    for i, inst in enumerate(instructions, 1):
        table.add_row(str(i), inst)

    console.print(table)


def print_memory_evolved(new_instructions: List[str]):
    """Display newly synthesized evolved rules."""
    if not new_instructions:
        return
    table = Table(title="Self-Evolution: New Rules Persisted to Memory", header_style="bold green")
    table.add_column("#", width=4)
    table.add_column("Newly Synthesized Rule", style="green")

    for i, inst in enumerate(new_instructions, 1):
        table.add_row(str(i), inst)

    console.print(table)
