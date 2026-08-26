import json
import logging
from typing import Dict, Any, Optional, List

from src.state import PipelineState
from src.memory.store import MemoryStore
from src.llm import LLMClient, get_llm_client
from src.prompts.memory_prompts import (
    MEMORY_DISTILLATION_SYSTEM_PROMPT,
    build_memory_distillation_prompt,
)
from src.utils.logger import (
    print_step,
    print_memory_loaded,
    print_memory_evolved,
    console,
)
from src.utils.formatting import save_lesson_and_log

logger = logging.getLogger(__name__)


def load_memory_node(
    state: PipelineState,
    memory_store: Optional[MemoryStore] = None,
) -> Dict[str, Any]:
    """LangGraph node: Loads past failure records and evolved rules from SQLite before generation."""
    store = memory_store or MemoryStore()
    topic = state.get("topic", "Introduction to RAG")

    print_step("Loading System Memory & Evolved Rules", f"Topic: {topic}")

    evolved_instructions = store.get_evolved_instructions(topic=topic, limit=6)
    print_memory_loaded(evolved_instructions)

    memory_summary = "\n".join(evolved_instructions) if evolved_instructions else "No previous memory."

    return {
        "evolved_instructions": evolved_instructions,
        "memory_context": memory_summary,
    }


def persist_memory_node(
    state: PipelineState,
    memory_store: Optional[MemoryStore] = None,
    llm: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """LangGraph node: Persists run logs, synthesizes newly evolved guidelines, and writes final deliverables."""
    store = memory_store or MemoryStore()
    client = llm or get_llm_client()

    run_id = state.get("run_id", "run-default")
    topic = state.get("topic", "Introduction to RAG")
    total_attempts = state.get("attempt_number", 1)
    all_passed = state.get("all_passed", False)
    rejection_log = state.get("rejection_log", [])
    current_lesson = state.get("current_lesson", "")

    print_step("Persisting Run Results & Synthesizing Self-Evolution", f"Run ID: {run_id}")

    # 1. Save run and failure records to SQLite
    store.save_run(
        run_id=run_id,
        topic=topic,
        total_attempts=total_attempts,
        final_passed=all_passed,
        rejection_log=rejection_log,
    )

    # 2. Self-evolution: If failures occurred, synthesize and persist evolved rules
    newly_evolved_rules: List[str] = []
    if rejection_log:
        console.print("[dim]Analyzing failure patterns to synthesize permanent instruction patches...[/dim]")
        try:
            distill_prompt = build_memory_distillation_prompt(topic, rejection_log)
            raw_output = client.generate_text(
                prompt=distill_prompt,
                system_instruction=MEMORY_DISTILLATION_SYSTEM_PROMPT,
                temperature=0.2,
            )

            clean_output = raw_output.strip()
            if clean_output.startswith("```json"):
                clean_output = clean_output[7:]
            if clean_output.startswith("```"):
                clean_output = clean_output[3:]
            if clean_output.endswith("```"):
                clean_output = clean_output[:-3]
            clean_output = clean_output.strip()

            parsed = json.loads(clean_output)
            if isinstance(parsed, list):
                newly_evolved_rules = [str(r) for r in parsed if str(r).strip()]
            elif isinstance(parsed, dict) and "instructions" in parsed:
                newly_evolved_rules = [str(r) for r in parsed["instructions"]]

            if newly_evolved_rules:
                store.save_evolved_instructions(run_id, topic, newly_evolved_rules)
                print_memory_evolved(newly_evolved_rules)

        except Exception as e:
            logger.warning(f"Failed to synthesize evolved instructions: {e}")

    # 3. Save final Markdown lesson and JSON rejection log files
    lesson_path, log_path = save_lesson_and_log(
        run_id=run_id,
        topic=topic,
        lesson_content=current_lesson,
        rejection_log=rejection_log,
        all_passed=all_passed,
        total_attempts=total_attempts,
    )

    console.print(f"[bold green]📄 Passing/Final Lesson saved to:[/bold green] [cyan]{lesson_path}[/cyan]")
    console.print(f"[bold yellow]📋 Detailed Rejection Log saved to:[/bold yellow] [cyan]{log_path}[/cyan]")

    return {
        "output_lesson_path": str(lesson_path),
        "output_log_path": str(log_path),
        "status": "COMPLETED_PASSED" if all_passed else "COMPLETED_MAX_RETRIES",
    }
