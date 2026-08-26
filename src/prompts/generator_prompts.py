from typing import List, Optional


GENERATOR_SYSTEM_PROMPT = """You are a Master Curriculum Designer and AI Educator specializing in making cutting-edge AI concepts accessible to foundational learners.

TARGET LEARNER PROFILE:
- 12th-grade graduate from India.
- Non-English-medium schooling background with basic, limited English vocabulary.
- Zero prior computer science, AI, or programming knowledge.
- Aspires to understand AI to build a modern technology career.

INSTRUCTIONAL DESIGN PRINCIPLES:
1. Simplicity over Complexity: Use clean, direct English with short sentences (under 20 words where possible). Avoid academic jargon and obscure GRE-level vocabulary.
2. Relatable Analogies: Anchor every abstract idea in an everyday experience (e.g., open-book vs. closed-book exams, checking a diary, looking up a railway schedule).
3. Zero Orphan Jargon: Whenever an AI term (like LLM, Hallucination, Retrieval, Prompt, Embedding, Vector Database) is mentioned, you MUST immediately explain it in plain everyday English right there.
4. Factual Precision: Be 100% technically accurate. RAG connects an AI to external documents at question time; it does NOT retrain or update the AI model weights.
5. Scannable Structure: Use clear markdown headers, bold keywords, bullet points, callout boxes, and short digestible paragraphs (max 100-120 words per paragraph).

PEDAGOGICAL FLOW TO FOLLOW:
- 🌟 Title & Learning Goals: Clear and encouraging.
- 1. The Big Problem (The Hook): Why do normal AI chatbots fail when asked about private notes or today's news?
- 2. What is RAG?: Plain-English explanation of Retrieval-Augmented Generation.
- 3. The Core Analogy: The "Open-Book Exam" comparison.
- 4. Why Do We Need RAG?: The 3 big challenges solved (Outdated information, Hallucinations/guessing, Private data).
- 5. How RAG Works (The 3 Steps):
     • Step 1: Retrieve (Search relevant notes)
     • Step 2: Augment (Add found notes into the prompt)
     • Step 3: Generate (Produce accurate answer)
- 6. Real-World Walkthrough: Trace a concrete example from start to finish with clear inputs and outputs.
- 7. Quick Recap & Beginner's Mini-Glossary.
"""


def build_generator_prompt(
    topic: str,
    learner_profile: Optional[str] = None,
    evolved_instructions: Optional[List[str]] = None,
    retry_feedback: Optional[str] = None,
    inject_error: bool = False,
) -> str:
    """Build the multi-layered generator prompt."""
    profile = learner_profile or (
        "12th-grade graduate from India with limited English vocabulary, "
        "non-English-medium background, zero prior AI knowledge."
    )

    prompt_parts = [
        f"Generate a comprehensive, standalone beginner-friendly lesson on the topic: '{topic}'.",
        f"\nTARGET AUDIENCE: {profile}",
    ]

    # Layer 2: Evolved Instructions from past runs (Self-Evolution memory)
    if evolved_instructions and len(evolved_instructions) > 0:
        prompt_parts.append("\n" + "=" * 50)
        prompt_parts.append("📚 LESSONS LEARNED & EVOLVED GUIDELINES FROM PAST RUNS:")
        prompt_parts.append("In past runs, specific weaknesses were flagged by the rubric evaluator. You MUST apply these guidelines:")
        for idx, rule in enumerate(evolved_instructions, 1):
            prompt_parts.append(f"{idx}. {rule}")
        prompt_parts.append("=" * 50)

    # Layer 3: Retry Feedback from the immediately preceding evaluation failure
    if retry_feedback:
        prompt_parts.append("\n" + "⚠️ " * 15)
        prompt_parts.append("CRITICAL: YOUR PREVIOUS DRAFT FAILED EVALUATION AGAINST OUR QUALITY RUBRIC.")
        prompt_parts.append("Review the exact failures and suggestions below, and REWRITE the lesson to strictly resolve every issue:")
        prompt_parts.append(retry_feedback)
        prompt_parts.append("⚠️ " * 15)

    if inject_error:
        # Deliberate error injection mode for assessment demonstration
        prompt_parts.append(
            "\n[DEMONSTRATION OVERRIDE]: Intentionally insert a factual misconception into the lesson: "
            "claim that 'RAG works by permanently retraining and updating the AI model's internal weights on new company files.' "
            "This will test the evaluator's ability to catch factual inaccuracies."
        )

    prompt_parts.append(
        "\nWrite out the COMPLETE, full lesson content in clean Markdown. "
        "Do NOT truncate, do NOT use placeholders, and ensure full depth and clarity."
    )

    return "\n".join(prompt_parts)
