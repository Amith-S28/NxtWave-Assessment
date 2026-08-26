import logging
from typing import Dict, Any, Optional, List

from src.state import PipelineState
from src.llm import LLMClient, get_llm_client
from src.rubric.checkpoints import RUBRIC_CHECKPOINTS
from src.rubric.schemas import CheckpointEvaluation
from src.prompts.evaluator_prompts import (
    EVALUATOR_SYSTEM_PROMPT,
    build_checkpoint_evaluation_prompt,
)
from src.utils.logger import print_step, print_evaluation_table, console

logger = logging.getLogger(__name__)


def evaluator_node(
    state: PipelineState,
    llm: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """LangGraph node: Evaluates candidate lesson against all 7 hard pass/fail rubric checkpoints."""
    client = llm or get_llm_client()
    attempt = state.get("attempt_number", 1)
    lesson_text = state.get("current_lesson", "")

    print_step(f"Evaluating Draft #{attempt} Against 7 Rubric Checkpoints", "Rigor: Strict Binary Gates")

    rubric_results: List[Dict[str, Any]] = []
    failed_checkpoints: List[str] = []
    feedback_lines: List[str] = []

    for idx, cp in enumerate(RUBRIC_CHECKPOINTS, 1):
        eval_prompt = build_checkpoint_evaluation_prompt(cp, lesson_text)
        
        try:
            eval_output = client.generate_structured(
                prompt=eval_prompt,
                response_schema=CheckpointEvaluation,
                system_instruction=EVALUATOR_SYSTEM_PROMPT,
                temperature=0.0,
            )
            result_dict = {
                "checkpoint_name": cp.name,
                "dimension": cp.dimension,
                "passed": bool(eval_output.passed),
                "reasoning": eval_output.reasoning,
                "suggestion": eval_output.suggestion or "",
            }
        except Exception as e:
            logger.warning(f"Structured eval fallback for {cp.name}: {e}")
            result_dict = {
                "checkpoint_name": cp.name,
                "dimension": cp.dimension,
                "passed": False,
                "reasoning": f"Evaluation error: {str(e)}",
                "suggestion": "Re-verify this dimension carefully.",
            }

        rubric_results.append(result_dict)

        if not result_dict["passed"]:
            failed_checkpoints.append(cp.name)
            feedback_lines.append(
                f"- [{cp.name}] FAILED: {result_dict['reasoning']}\n"
                f"  ACTIONABLE FIX: {result_dict['suggestion']}"
            )

        # Gentle pacing between evaluator calls to respect free-tier RPM burst quotas
        if idx < len(RUBRIC_CHECKPOINTS):
            import time
            time.sleep(1.0)

    all_passed = len(failed_checkpoints) == 0

    # Print clean formatted table to console
    print_evaluation_table(attempt, rubric_results, all_passed)

    # Accumulate into rejection log if failed
    existing_rejection_log = list(state.get("rejection_log", []))
    retry_feedback = None

    if not all_passed:
        retry_feedback = (
            f"=== FAILURES DETECTED IN ATTEMPT #{attempt} ({len(failed_checkpoints)} OF 7 CHECKS FAILED) ===\n"
            + "\n".join(feedback_lines)
            + "\n\nPlease rewrite the lesson to resolve ALL of the above issues while keeping what was good."
        )

        rejection_entry = {
            "attempt_number": attempt,
            "failed_checkpoints": failed_checkpoints,
            "results": rubric_results,
            "feedback_provided": retry_feedback,
            "lesson_snapshot": lesson_text,
        }
        existing_rejection_log.append(rejection_entry)

    return {
        "rubric_results": rubric_results,
        "all_passed": all_passed,
        "retry_feedback": retry_feedback,
        "rejection_log": existing_rejection_log,
    }
