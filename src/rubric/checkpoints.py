from dataclasses import dataclass
from typing import List


@dataclass
class CheckpointDefinition:
    """Definition and evaluation criteria for a single rubric checkpoint."""
    id: str
    name: str
    dimension: str
    description: str
    pass_criteria: str
    fail_signals: str
    evaluation_prompt_instructions: str


RUBRIC_CHECKPOINTS: List[CheckpointDefinition] = [
    CheckpointDefinition(
        id="chk_accuracy",
        name="Factual Accuracy & Grounding",
        dimension="Accuracy",
        description="Every technical claim, definition, and mechanism about the topic is factually correct and verifiable.",
        pass_criteria=(
            "1. Accurately describes RAG as a retrieval + generation pipeline that looks up relevant knowledge at inference time.\n"
            "2. Does NOT claim that RAG retrains, fine-tunes, or modifies the underlying model weights.\n"
            "3. Correctly distinguishes between the LLM's static training memory and dynamic external retrieval.\n"
            "4. No hallucinated components or false technical claims."
        ),
        fail_signals=(
            "States that RAG 'trains the model on your documents', confuses RAG with fine-tuning, "
            "claims RAG permanently alters LLM parameters, or invents non-existent architectural stages."
        ),
        evaluation_prompt_instructions=(
            "Carefully examine every factual statement about RAG. Check if any statement confuses retrieval "
            "with model training or fine-tuning. Verify whether all explanations of how data flows are technically accurate."
        )
    ),
    CheckpointDefinition(
        id="chk_completeness",
        name="Completeness — Core Concepts",
        dimension="Completeness",
        description="The lesson covers all three fundamental pillars: What it is, Why it matters, and How it works.",
        pass_criteria=(
            "1. WHAT: Clearly defines what RAG stands for (Retrieval-Augmented Generation) and what it does.\n"
            "2. WHY: Explains the specific problems RAG solves (LLM knowledge cutoff, hallucinations, private/custom data access).\n"
            "3. HOW: Clearly breaks down the 3-step pipeline: (1) Retrieve relevant info, (2) Augment the prompt, (3) Generate the final answer."
        ),
        fail_signals=(
            "Skips explaining why RAG is needed (e.g. mentions nothing about outdated data or hallucinations), "
            "or skips the 'Augment' step, or only gives a 1-sentence definition without explaining the workflow."
        ),
        evaluation_prompt_instructions=(
            "Verify that the lesson has dedicated sections or clear explanations covering: (1) What is RAG, "
            "(2) Why do we need it (the core pain points it solves), and (3) How it works (step-by-step pipeline)."
        )
    ),
    CheckpointDefinition(
        id="chk_language",
        name="Beginner-Friendly Language",
        dimension="Accessibility",
        description="Written specifically for a 12th-grade Indian graduate from a non-English-medium background with limited English vocabulary.",
        pass_criteria=(
            "1. Uses simple, direct, conversational English with short sentences.\n"
            "2. Avoids dense academic phrasing, high-difficulty GRE vocabulary, and overly complex sentence structures.\n"
            "3. Uses encouraging, clear, and relatable phrasing that builds confidence."
        ),
        fail_signals=(
            "Uses dense academic vocabulary (e.g. 'ubiquitous', 'paradigmatic', 'salient', 'stochastic', 'heterogeneous', 'epistemological'), "
            "has overly long convoluted compound sentences (>30 words), or reads like an engineering research paper."
        ),
        evaluation_prompt_instructions=(
            "Read through the prose as a 12th-grade student from an Indian vernacular/non-English medium background. "
            "Are there obscure English words? Are sentences short and easy to follow? If the vocabulary is intimidating, FAIL."
        )
    ),
    CheckpointDefinition(
        id="chk_examples",
        name="Teaches by Concrete Example & Analogy",
        dimension="Pedagogy",
        description="Includes at least one intuitive real-world analogy and a concrete step-by-step example walkthrough.",
        pass_criteria=(
            "1. Provides an intuitive real-world analogy (e.g. Open-book exam vs Closed-book exam, doctor consulting medical records, librarian finding books, or chef looking up a recipe).\n"
            "2. Provides a concrete step-by-step scenario walkthrough (e.g. asking a chatbot about a specific recent event, college admission fee, or company policy) showing the user query, retrieved document, augmented prompt, and final answer."
        ),
        fail_signals=(
            "Entirely theoretical and abstract without any relatable everyday analogy, or missing a concrete worked example showing the data flow."
        ),
        evaluation_prompt_instructions=(
            "Look for: (1) A vivid everyday analogy that a beginner can instantly picture, and (2) A concrete, end-to-end example walkthrough showing a question being answered with RAG."
        )
    ),
    CheckpointDefinition(
        id="chk_jargon",
        name="Clear, No Unexplained Jargon",
        dimension="Clarity",
        description="Zero unexplained technical terms. Every acronym or AI term used is defined intuitively on first appearance.",
        pass_criteria=(
            "1. Every technical term (such as LLM, Hallucination, Retrieval, Prompt, Vector/Embedding, Database, Context Window) is clearly explained in simple plain English before or right when it is used.\n"
            "2. No technical buzzwords are dropped without immediate context."
        ),
        fail_signals=(
            "Mentions terms like 'embeddings', 'vector database', 'semantic similarity', 'cosine distance', 'token limit', or 'hallucination' without explaining what they mean in simple terms."
        ),
        evaluation_prompt_instructions=(
            "Check every technical AI term in the text. Did the author introduce and define it in plain language on first mention? "
            "If any technical jargon appears without a simple explanation, this check MUST FAIL."
        )
    ),
    CheckpointDefinition(
        id="chk_flow",
        name="Coherent Teaching Flow",
        dimension="Structure",
        description="The instructional flow is logical, scaffolding concepts step-by-step from problem to solution to summary.",
        pass_criteria=(
            "1. Follows a clear progression: Hook (relatable problem) -> Core Concept -> Mechanism (How it works) -> Concrete Example -> Practical Summary.\n"
            "2. Never assumes knowledge from a section that has not been introduced yet.\n"
            "3. Transitions between sections are smooth and natural."
        ),
        fail_signals=(
            "Disjointed structure, sudden jumps between topics, explains advanced retrieval mechanics before explaining what problem RAG solves, or lacks a coherent conclusion/summary."
        ),
        evaluation_prompt_instructions=(
            "Trace the progression of ideas from start to finish. Does each section naturally build upon the previous one? "
            "Is the hierarchy easy to follow for someone starting from absolute zero?"
        )
    ),
    CheckpointDefinition(
        id="chk_length_density",
        name="Appropriate Length & Structural Density",
        dimension="Format",
        description="Lesson length is well-calibrated (700-1800 words) with scannable formatting, subheadings, bullet points, and short paragraphs.",
        pass_criteria=(
            "1. Word count is in the range of 700 to 1800 words.\n"
            "2. Paragraphs are concise (under ~120 words each) and visually distinct.\n"
            "3. Uses clear markdown headings, bullet points, callouts, or summary boxes to prevent wall-of-text fatigue."
        ),
        fail_signals=(
            "Under 600 words (too shallow to teach the topic), over 2200 words (too dense/exhausting for a beginner), "
            "or consists of giant unbroken walls of text with no visual structure."
        ),
        evaluation_prompt_instructions=(
            "Evaluate the length and readability structure. Check if the text is broken into digestible bite-sized paragraphs "
            "with clear headers and bullet points. Estimate whether the content provides sufficient depth without being overly bloated."
        )
    )
]


def get_checkpoint_by_name(name: str) -> CheckpointDefinition:
    """Retrieve a checkpoint definition by its exact name."""
    for cp in RUBRIC_CHECKPOINTS:
        if cp.name.lower() == name.lower() or cp.id.lower() == name.lower():
            return cp
    raise ValueError(f"Unknown checkpoint: {name}")
