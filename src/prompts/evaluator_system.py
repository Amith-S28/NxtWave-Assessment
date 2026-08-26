"""
Evaluator system prompt.

This wraps each rubric checkpoint's evaluation prompt with instructions
for structured output. The evaluator is told to reason FIRST, then
give its verdict — Chain-of-Thought improves judgment accuracy.
"""

EVALUATOR_WRAPPER_PROMPT = """\
You are a strict quality evaluator for educational content. You evaluate ONE specific quality dimension at a time.

## Important Rules
1. Be STRICT. When in doubt, FAIL. It is better to catch a real issue than to let a bad lesson pass.
2. Provide your reasoning FIRST, citing specific passages from the lesson.
3. THEN give your binary pass/fail verdict.
4. If you fail the checkpoint, provide a SPECIFIC, ACTIONABLE suggestion for how to fix it.
5. Your response must be valid JSON matching the schema below.

## Response Schema
{{
    "checkpoint_name": "{checkpoint_name}",
    "passed": true or false,
    "reasoning": "Your step-by-step reasoning, citing specific passages...",
    "suggestion": "If failed: specific fix suggestion. If passed: empty string."
}}

## Evaluation Criteria
{evaluation_prompt}
"""


def build_evaluator_prompt(checkpoint_name: str, evaluation_prompt: str, lesson_content: str) -> str:
    """
    Build the full evaluator prompt for a single checkpoint.

    Injects the lesson content into the checkpoint's evaluation prompt,
    then wraps it in the structured-output wrapper.
    """
    # First, inject the lesson into the checkpoint-specific prompt
    filled_evaluation = evaluation_prompt.format(lesson_content=lesson_content)

    # Then wrap it in the structured output instructions
    return EVALUATOR_WRAPPER_PROMPT.format(
        checkpoint_name=checkpoint_name,
        evaluation_prompt=filled_evaluation,
    )
