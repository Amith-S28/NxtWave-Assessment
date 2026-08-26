import pytest
from src.graph import route_after_evaluation
from src.state import PipelineState


def test_route_after_evaluation_pass():
    """When all rubric checkpoints pass, route should be 'pass'."""
    state: PipelineState = {
        "run_id": "test-1",
        "topic": "RAG",
        "learner_profile": "12th grade",
        "current_lesson": "Passable lesson",
        "attempt_number": 1,
        "max_attempts": 3,
        "rubric_results": [],
        "all_passed": True,
        "rejection_log": [],
        "retry_feedback": None,
        "memory_context": "",
        "evolved_instructions": [],
        "inject_error": False,
        "status": "EVALUATING",
        "output_lesson_path": None,
        "output_log_path": None,
    }
    decision = route_after_evaluation(state)
    assert decision == "pass"


def test_route_after_evaluation_retry():
    """When checks fail and attempts < max_attempts, route should be 'retry'."""
    state: PipelineState = {
        "run_id": "test-2",
        "topic": "RAG",
        "learner_profile": "12th grade",
        "current_lesson": "Failed lesson",
        "attempt_number": 1,
        "max_attempts": 3,
        "rubric_results": [],
        "all_passed": False,
        "rejection_log": [],
        "retry_feedback": "Fix jargon",
        "memory_context": "",
        "evolved_instructions": [],
        "inject_error": False,
        "status": "EVALUATING",
        "output_lesson_path": None,
        "output_log_path": None,
    }
    decision = route_after_evaluation(state)
    assert decision == "retry"


def test_route_after_evaluation_max_retries_exceeded():
    """When checks fail and attempt reaches max_attempts, route should terminate."""
    state: PipelineState = {
        "run_id": "test-3",
        "topic": "RAG",
        "learner_profile": "12th grade",
        "current_lesson": "Failed lesson",
        "attempt_number": 3,
        "max_attempts": 3,
        "rubric_results": [],
        "all_passed": False,
        "rejection_log": [],
        "retry_feedback": "Fix jargon",
        "memory_context": "",
        "evolved_instructions": [],
        "inject_error": False,
        "status": "EVALUATING",
        "output_lesson_path": None,
        "output_log_path": None,
    }
    decision = route_after_evaluation(state)
    assert decision == "max_retries_exceeded"
