"""
Shared prompt templates used across the pipeline.
"""

MEMORY_DISTILLATION_PROMPT = """\
You are analyzing the results of a content generation pipeline run. Your job is to distill the failures into a single, actionable instruction that will prevent the same mistakes in future runs.

## Run Results
- Topic: {topic}
- Attempt count: {attempt_count}
- Final outcome: {"PASSED" if {final_passed} else "FAILED"}

## Failures Encountered
{failures_summary}

## Your Task
Write ONE concise instruction (1-3 sentences) that a content writer should follow in the future to avoid these specific failure patterns. Be specific and actionable — not vague advice like "write better."

Example good output: "When writing about RAG, always define 'embedding' as 'a numerical fingerprint that captures meaning' on first use, and avoid using 'vector database' without immediately explaining it as 'a special filing system for these fingerprints.'"

Write ONLY the instruction, nothing else.
"""

ERROR_INJECTION_PROMPT = """\
You are a content saboteur for testing purposes. Take the lesson below and introduce exactly ONE factual error about RAG.

## Rules
- Replace one correct statement with a plausible but WRONG claim.
- The error should be about what RAG IS or HOW IT WORKS (not a typo or grammar issue).
- Good error examples: "RAG trains the model on new data" or "RAG permanently stores information in the model's memory"
- Keep the rest of the lesson intact.
- At the end, add a hidden comment: <!-- INJECTED ERROR: [describe the error] -->

## Lesson
{lesson_content}

Output the modified lesson only.
"""
