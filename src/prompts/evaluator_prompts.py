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


def build_all_checkpoints_evaluation_prompt(lesson_text: str, attempt_number: int = 1) -> str:
    """Build a comprehensive batched prompt to evaluate all 7 rubric checkpoints in a single LLM call."""
    from src.rubric.checkpoints import RUBRIC_CHECKPOINTS

    checkpoints_block = []
    for idx, cp in enumerate(RUBRIC_CHECKPOINTS, 1):
        checkpoints_block.append(
            f"--- CHECKPOINT {idx}: {cp.name} ({cp.dimension}) ---\n"
            f"Description: {cp.description}\n\n"
            f"Pass Criteria:\n{cp.pass_criteria}\n\n"
            f"Fail Signals:\n{cp.fail_signals}\n\n"
            f"Instructions:\n{cp.evaluation_prompt_instructions}\n"
        )
    checkpoints_text = "\n".join(checkpoints_block)

    return f"""Please evaluate the candidate lesson below against ALL 7 of the following hard pass/fail rubric checkpoints.

============================================================
THE 7 RUBRIC CHECKPOINTS TO EVALUATE:
============================================================
{checkpoints_text}

============================================================
CANDIDATE LESSON TEXT TO EVALUATE (Attempt #{attempt_number}):
============================================================
{lesson_text}
============================================================

Evaluate EVERY single checkpoint independently and return an EvaluationResult with:
- attempt_number: {attempt_number}
- checkpoints: List of 7 CheckpointEvaluation objects (one for each checkpoint in exact order), each with:
  - checkpoint_name: Exact name of the checkpoint
  - passed: true or false (binary gate, zero partial credit)
  - reasoning: Specific evidence and chain-of-thought analysis
  - suggestion: Concrete actionable fix if failed, or empty string if passed
- all_passed: true ONLY if all 7 checkpoints passed (false if even 1 failed)
- summary: A concise 1-line verdict of the evaluation
"""
