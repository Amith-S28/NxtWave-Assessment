import os
import tempfile
from pathlib import Path
from src.memory.store import MemoryStore
from src.nodes.memory_manager import load_memory_node, persist_memory_node
from src.llm import MockLLMClient
from src.state import PipelineState


def test_memory_store_lifecycle():
    """Verify full SQLite memory lifecycle: save run, save evolved rules, retrieve, inspect, and clear."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        store = MemoryStore(db_path=db_path)

        # Initial check
        assert store.get_evolved_instructions("RAG") == []
        stats = store.inspect_memory()
        assert stats["total_runs"] == 0

        # Save run with failures
        rejection_log = [
            {
                "attempt_number": 1,
                "failed_checkpoints": ["Clear, No Unexplained Jargon"],
                "results": [
                    {
                        "checkpoint_name": "Clear, No Unexplained Jargon",
                        "passed": False,
                        "reasoning": "Used 'vector embeddings' without explaining.",
                        "suggestion": "Define vector embedding as numerical representation of meaning.",
                    }
                ],
            }
        ]

        store.save_run(
            run_id="run-101",
            topic="RAG",
            total_attempts=2,
            final_passed=True,
            rejection_log=rejection_log,
        )

        # Save evolved instructions
        instructions = [
            "Always define 'vector embedding' as 'a digital fingerprint of meaning' on first use.",
            "Use the open-book exam analogy for RAG."
        ]
        store.save_evolved_instructions("run-101", "RAG", instructions)

        # Retrieve instructions
        retrieved = store.get_evolved_instructions("RAG")
        assert len(retrieved) == 2
        assert any("digital fingerprint" in inst for inst in retrieved)

        # Check inspection stats
        stats = store.inspect_memory()
        assert stats["total_runs"] == 1
        assert stats["total_failures_recorded"] == 1
        assert stats["total_evolved_rules"] == 2
        assert stats["checkpoint_failure_breakdown"][0]["checkpoint_name"] == "Clear, No Unexplained Jargon"

        # Deduplication test: inserting same instruction again should not duplicate
        store.save_evolved_instructions("run-102", "RAG", ["Use the open-book exam analogy for RAG."])
        retrieved2 = store.get_evolved_instructions("RAG")
        assert len(retrieved2) == 2

        # Clear memory
        store.clear_memory()
        assert store.get_evolved_instructions("RAG") == []
        stats_after = store.inspect_memory()
        assert stats_after["total_runs"] == 0


def test_cross_run_self_evolution_flow():
    """Verify that failures in Run 1 persist synthesized rules that are loaded in Run 2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_evolution.db"
        store = MemoryStore(db_path=db_path)

        # Mock LLM for memory distillation that returns a JSON list of evolved rules
        mock_llm = MockLLMClient(
            default_response='["When explaining RAG, always explain vector search using a library catalog analogy."]'
        )

        # Run 1: Had a rejection on attempt 1
        run1_state: PipelineState = {
            "run_id": "run-1",
            "topic": "Introduction to RAG",
            "learner_profile": "12th grade",
            "current_lesson": "Passable lesson draft",
            "attempt_number": 2,
            "max_attempts": 3,
            "rubric_results": [],
            "all_passed": True,
            "rejection_log": [
                {
                    "attempt_number": 1,
                    "failed_checkpoints": ["Teaches by Concrete Example & Analogy"],
                    "results": [
                        {
                            "checkpoint_name": "Teaches by Concrete Example & Analogy",
                            "passed": False,
                            "reasoning": "Missing clear everyday analogy for vector search.",
                            "suggestion": "Add library catalog analogy.",
                        }
                    ],
                }
            ],
            "retry_feedback": None,
            "memory_context": "",
            "evolved_instructions": [],
            "inject_error": False,
            "status": "EVALUATING",
            "output_lesson_path": None,
            "output_log_path": None,
        }

        # Persist Run 1
        persist_res = persist_memory_node(run1_state, memory_store=store, llm=mock_llm)
        assert persist_res["status"] == "COMPLETED_PASSED"

        # Check that evolved rule was stored in SQLite
        saved_rules = store.get_evolved_instructions("Introduction to RAG")
        assert len(saved_rules) == 1
        assert "library catalog" in saved_rules[0]

        # Run 2: Fresh run loads memory
        run2_state: PipelineState = {
            "run_id": "run-2",
            "topic": "Introduction to RAG",
            "learner_profile": "12th grade",
            "current_lesson": "",
            "attempt_number": 0,
            "max_attempts": 3,
            "rubric_results": [],
            "all_passed": False,
            "rejection_log": [],
            "retry_feedback": None,
            "memory_context": "",
            "evolved_instructions": [],
            "inject_error": False,
            "status": "INITIALIZING",
            "output_lesson_path": None,
            "output_log_path": None,
        }

        loaded_res = load_memory_node(run2_state, memory_store=store)
        assert len(loaded_res["evolved_instructions"]) == 1
        assert "library catalog" in loaded_res["evolved_instructions"][0]
