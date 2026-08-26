from src.rubric.checkpoints import CheckpointDefinition


EVALUATOR_SYSTEM_PROMPT = """You are a Strict, Uncompromising Content Quality & Pedagogy Judge at an AI Education Institute.
Your job is to evaluate educational lessons against hard pass/fail rubric checkpoints.

EVALUATION RULES:
1. Binary Gate: There is NO partial credit. The candidate lesson either meets 100% of the pass criteria for this checkpoint, or it FAILS (passed = false).
2. Evidence-Based Reasoning: You must quote or cite specific lines or sections from the lesson to justify your evaluation in the `reasoning` field.
3. Actionable Feedback: If the lesson fails, provide a concrete, step-by-step fix in the `suggestion` field that tells the author exactly what to add, delete, or rewrite. If it passes, leave `suggestion` as an empty string.
4. Target Persona Focus: Keep the learner profile in mind (12th-grade Indian graduate, non-English-medium background, zero prior AI knowledge).
"""


def build_checkpoint_evaluation_prompt(checkpoint: CheckpointDefinition, lesson_text: str) -> str:
    """Build a focused prompt to evaluate a single rubric checkpoint."""
    return f"""Please evaluate the candidate lesson below against the rubric checkpoint: '{checkpoint.name}'.

============================================================
RUBRIC CHECKPOINT: {checkpoint.name}
DIMENSION: {checkpoint.dimension}
OVERVIEW: {checkpoint.description}

PASS CRITERIA:
{checkpoint.pass_criteria}

FAIL SIGNALS (If any of these are present, you MUST mark passed = false):
{checkpoint.fail_signals}

SPECIFIC EVALUATION INSTRUCTIONS:
{checkpoint.evaluation_prompt_instructions}
============================================================

CANDIDATE LESSON TEXT TO EVALUATE:
------------------------------------------------------------
{lesson_text}
------------------------------------------------------------

Provide your evaluation adhering to the following JSON schema:
- checkpoint_name: "{checkpoint.name}"
- passed: true or false
- reasoning: Step-by-step chain of thought analyzing the lesson against the pass criteria and fail signals.
- suggestion: Clear and actionable instructions to fix the issue if failed (or empty string if passed).
"""
