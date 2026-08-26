import pytest
from src.rubric.checkpoints import RUBRIC_CHECKPOINTS, get_checkpoint_by_name
from src.rubric.schemas import CheckpointEvaluation, RubricResult, RejectionLogEntry
from src.llm import MockLLMClient
from src.prompts.evaluator_prompts import build_checkpoint_evaluation_prompt
from src.prompts.generator_prompts import build_generator_prompt


def test_rubric_checkpoints_loaded():
    """Verify that all 7 required rubric checkpoints are registered."""
    assert len(RUBRIC_CHECKPOINTS) == 7
    expected_checkpoints = [
        "Factual Accuracy & Grounding",
        "Completeness — Core Concepts",
        "Beginner-Friendly Language",
        "Teaches by Concrete Example & Analogy",
        "Clear, No Unexplained Jargon",
        "Coherent Teaching Flow",
        "Appropriate Length & Structural Density",
    ]
    actual_names = [cp.name for cp in RUBRIC_CHECKPOINTS]
    for expected in expected_checkpoints:
        assert expected in actual_names


def test_get_checkpoint_by_name():
    """Verify checkpoint lookup by name."""
    cp = get_checkpoint_by_name("Factual Accuracy & Grounding")
    assert cp.dimension == "Accuracy"
    assert "retrieval" in cp.pass_criteria.lower()

    with pytest.raises(ValueError):
        get_checkpoint_by_name("NonExistentCheckpoint")


def test_evaluation_prompt_builder():
    """Verify evaluation prompt contains checkpoint pass criteria and candidate text."""
    cp = get_checkpoint_by_name("Clear, No Unexplained Jargon")
    lesson = "Here is a lesson about RAG."
    prompt = build_checkpoint_evaluation_prompt(cp, lesson)

    assert "RUBRIC CHECKPOINT: Clear, No Unexplained Jargon" in prompt
    assert "PASS CRITERIA:" in prompt
    assert "FAIL SIGNALS" in prompt
    assert lesson in prompt


def test_mock_evaluator_structured_output():
    """Verify mock LLM returns valid CheckpointEvaluation schema."""
    mock_llm = MockLLMClient(default_verdict=True)
    cp = get_checkpoint_by_name("Factual Accuracy & Grounding")
    prompt = build_checkpoint_evaluation_prompt(cp, "Sample text")

    result = mock_llm.generate_structured(
        prompt=prompt,
        response_schema=CheckpointEvaluation,
    )

    assert isinstance(result, CheckpointEvaluation)
    assert result.passed is True
    assert len(result.reasoning) > 0


def test_generator_prompt_layering():
    """Verify prompt builder layers base instructions, evolved memory, retry feedback, and error injection."""
    # Test Base prompt
    p1 = build_generator_prompt("Introduction to RAG")
    assert "Introduction to RAG" in p1
    assert "12th-grade" in p1

    # Test Memory Evolved Instructions Layer
    evolved = ["Always define vector database on first use.", "Use open-book exam analogy."]
    p2 = build_generator_prompt("Introduction to RAG", evolved_instructions=evolved)
    assert "LESSONS LEARNED & EVOLVED GUIDELINES" in p2
    assert "Always define vector database on first use." in p2

    # Test Retry Feedback Layer
    feedback = "Attempt 1 failed because you dropped unexplained jargon."
    p3 = build_generator_prompt("Introduction to RAG", retry_feedback=feedback)
    assert "CRITICAL: YOUR PREVIOUS DRAFT FAILED EVALUATION" in p3
    assert "unexplained jargon" in p3

    # Test Error Injection Layer
    p4 = build_generator_prompt("Introduction to RAG", inject_error=True)
    assert "[DEMONSTRATION OVERRIDE]" in p4
    assert "permanently retraining" in p4


def test_rejection_log_entry_schema():
    """Verify RejectionLogEntry Pydantic schema validation."""
    entry = RejectionLogEntry(
        attempt_number=1,
        failed_checkpoints=["Factual Accuracy & Grounding"],
        results=[
            RubricResult(
                checkpoint_name="Factual Accuracy & Grounding",
                passed=False,
                reasoning="Claimed RAG trains weights.",
                suggestion="Clarify that RAG queries external docs at inference time.",
            )
        ],
        feedback_provided="Please fix factual claims.",
        lesson_snapshot="Draft 1 content",
    )

    assert entry.attempt_number == 1
    assert len(entry.failed_checkpoints) == 1
    assert entry.results[0].passed is False
