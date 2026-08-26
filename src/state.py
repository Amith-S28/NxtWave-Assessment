"""LangGraph state definition.

This is the "order ticket" that flows through every node in the pipeline.
Every node reads from and writes to this single typed structure, making
the data flow explicit and inspectable in traces.
"""

from typing import TypedDict, List, Dict, Any, Optional
from src.rubric.schemas import RubricResult, RejectionLogEntry, CheckpointEvaluation


class PipelineState(TypedDict, total=False):
    """Shared state flowing through all graph nodes."""

    # --- Run Identification & Input ---
    run_id: str
    topic: str
    learner_profile: str

    # --- Generation ---
    current_lesson: str
    attempt_number: int
    max_attempts: int

    # --- Evaluation ---
    rubric_results: List[Dict[str, Any]]
    all_passed: bool

    # --- Rejection Log & Retry Feedback ---
    rejection_log: List[Dict[str, Any]]
    retry_feedback: Optional[str]

    # --- Memory / Self-Evolution ---
    memory_context: str
    evolved_instructions: List[str]

    # --- Demonstration & Outputs ---
    inject_error: bool
    status: str
    output_lesson_path: Optional[str]
    output_log_path: Optional[str]
