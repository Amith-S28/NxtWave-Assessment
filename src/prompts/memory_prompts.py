from typing import List, Dict, Any


MEMORY_DISTILLATION_SYSTEM_PROMPT = """You are a Self-Evolution Memory Synthesizer for an AI Lesson Content System.
Your job is to analyze the evaluation failures and retry improvements from a generation run, and distill 1 to 2 sharp, permanent instructional rules.

GUIDELINES FOR EVOLVED INSTRUCTIONS:
1. Highly Specific: Instead of "write clearly", state "Always explain 'vector database' as 'a digital filing cabinet that finds documents by meaning' on first use."
2. Proactive: State what to DO or AVOID from the very start of generation.
3. Concise: Keep each distilled rule to 1-2 clear sentences.
"""


def build_memory_distillation_prompt(topic: str, rejection_log: List[Dict[str, Any]]) -> str:
    """Build prompt to synthesize learned instructions from rejection logs."""
    log_summary_lines = []
    for entry in rejection_log:
        att = entry.get("attempt_number", 1)
        failed_cps = entry.get("failed_checkpoints", [])
        log_summary_lines.append(f"Attempt #{att} failed on checkpoints: {', '.join(failed_cps)}")
        for r in entry.get("results", []):
            if not r.get("passed", True):
                name = r.get("checkpoint_name")
                reason = r.get("reasoning", "")
                sugg = r.get("suggestion", "")
                log_summary_lines.append(f"  - [{name}] Reason: {reason} | Suggestion: {sugg}")

    log_text = "\n".join(log_summary_lines)

    return f"""Topic: {topic}

Below is the rejection log and evaluator feedback from recent generation attempts:
------------------------------------------------------------
{log_text}
------------------------------------------------------------

Based on these specific failures and corrections, synthesize 1 to 3 permanent, actionable rules (evolved instructions) that the content generator must follow in future runs for '{topic}' to avoid these exact mistakes.

Format your output as a JSON array of strings:
["Instruction rule 1", "Instruction rule 2"]
"""
