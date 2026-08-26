"""Pydantic schemas for rubric evaluation output."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CheckpointEvaluation(BaseModel):
    """Evaluation result for a single rubric checkpoint."""
    checkpoint_name: str = Field(description="The exact name of the rubric checkpoint being evaluated.")
    passed: bool = Field(description="True if the lesson satisfies all pass criteria; False otherwise.")
    reasoning: str = Field(description="Detailed, objective explanation of why the lesson passed or failed this checkpoint.")
    suggestion: str = Field(default="", description="Specific, actionable correction for the generator if failed; empty string if passed.")


# Alias for compatibility with alternate naming
RubricCheckpointResult = CheckpointEvaluation


class RubricResult(BaseModel):
    """Standard rubric checkpoint result used across state and logging."""
    checkpoint_name: str
    passed: bool
    reasoning: str
    suggestion: str = ""


class RejectionLogEntry(BaseModel):
    """Log record of an attempt that failed one or more rubric checks."""
    attempt_number: int
    failed_checkpoints: List[str]
    results: List[RubricResult]
    feedback_provided: str
    lesson_snapshot: str


class EvaluationResult(BaseModel):
    """Aggregated result of all rubric checkpoints for one evaluation pass."""
    attempt_number: int = Field(description="Which attempt this evaluation is for (1-indexed).")
    checkpoints: List[CheckpointEvaluation] = Field(description="Results for each rubric checkpoint.")
    all_passed: bool = Field(description="True only if every single checkpoint passed.")
    summary: str = Field(default="", description="One-line summary of the overall evaluation outcome.")

    @classmethod
    def from_checkpoint_results(
        cls, attempt_number: int, results: List[CheckpointEvaluation]
    ) -> "EvaluationResult":
        all_passed = all(r.passed for r in results)
        failed = [r.checkpoint_name for r in results if not r.passed]
        if all_passed:
            summary = "All checkpoints passed."
        else:
            summary = f"Failed {len(failed)}/{len(results)} checkpoints: {', '.join(failed)}"
        return cls(
            attempt_number=attempt_number,
            checkpoints=results,
            all_passed=all_passed,
            summary=summary,
        )
