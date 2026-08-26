import logging
from typing import Dict, Any, Optional

from src.state import PipelineState
from src.llm import LLMClient, get_llm_client
from src.prompts.generator_prompts import (
    GENERATOR_SYSTEM_PROMPT,
    build_generator_prompt,
)
from src.utils.logger import print_step, console

logger = logging.getLogger(__name__)


def generator_node(
    state: PipelineState,
    llm: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """LangGraph node: Generates or regenerates the lesson content."""
    client = llm or get_llm_client()
    attempt = state.get("attempt_number", 0) + 1
    topic = state.get("topic", "Introduction to RAG")
    learner_profile = state.get("learner_profile")
    evolved_instructions = state.get("evolved_instructions", [])
    retry_feedback = state.get("retry_feedback")
    inject_error = state.get("inject_error", False) and (attempt == 1)

    is_retry = attempt > 1
    step_title = f"Generating Lesson (Attempt #{attempt})" if not is_retry else f"Regenerating Lesson with Targeted Feedback (Attempt #{attempt})"
    print_step(step_title, f"Topic: {topic}")

    if is_retry and retry_feedback:
        console.print("[yellow]Applying evaluator feedback to fix previous draft weaknesses...[/yellow]")

    if inject_error:
        console.print("[bold red]🚨 [DEMO MODE] Deliberately injecting factual error to test evaluator discrimination...[/bold red]")

    prompt = build_generator_prompt(
        topic=topic,
        learner_profile=learner_profile,
        evolved_instructions=evolved_instructions,
        retry_feedback=retry_feedback if is_retry else None,
        inject_error=inject_error,
    )

    lesson_content = client.generate_text(
        prompt=prompt,
        system_instruction=GENERATOR_SYSTEM_PROMPT,
        temperature=0.4,
    )

    word_count = len(lesson_content.split())
    console.print(f"[dim]Generated draft ({word_count} words). Proceeding to rubric evaluation...[/dim]")

    return {
        "current_lesson": lesson_content,
        "attempt_number": attempt,
        "inject_error": False,  # Reset after first attempt
    }
