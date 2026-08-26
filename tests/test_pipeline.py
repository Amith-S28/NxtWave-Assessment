import tempfile
from pathlib import Path
from src.llm import MockLLMClient
from src.memory.store import MemoryStore
from src.graph import create_pipeline_graph
from src.config import Config


def test_pipeline_pass_first_attempt():
    """Verify that a passing evaluation on attempt #1 routes to memory persistence and outputs files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        out_dir = Path(tmpdir) / "output"
        store = MemoryStore(db_path=db_path)

        mock_llm = MockLLMClient(
            default_response="# Introduction to RAG\n\nFull beginner lesson content here...",
            default_verdict=True,
        )

        graph = create_pipeline_graph(llm=mock_llm, memory_store=store)

        initial_state = {
            "run_id": "test-run-1",
            "topic": "Introduction to RAG",
            "learner_profile": Config.DEFAULT_LEARNER_PROFILE,
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
            "status": "INITIALIZED",
            "output_lesson_path": None,
            "output_log_path": None,
        }

        final_state = graph.invoke(initial_state)

        assert final_state["all_passed"] is True
        assert final_state["attempt_number"] == 1
        assert len(final_state["rubric_results"]) == 7
        assert final_state["status"] == "COMPLETED_PASSED"
        assert final_state["output_lesson_path"] is not None
        assert Path(final_state["output_lesson_path"]).exists()


def test_pipeline_retry_then_terminate():
    """Verify that a failing evaluation increments attempt counter up to max_attempts and terminates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        store = MemoryStore(db_path=db_path)

        # Mock that always fails
        mock_llm = MockLLMClient(
            default_response="# Flawed RAG Lesson Draft",
            default_verdict=False,
        )

        graph = create_pipeline_graph(llm=mock_llm, memory_store=store)

        initial_state = {
            "run_id": "test-run-2",
            "topic": "Introduction to RAG",
            "learner_profile": Config.DEFAULT_LEARNER_PROFILE,
            "current_lesson": "",
            "attempt_number": 0,
            "max_attempts": 2,  # 2 attempts total
            "rubric_results": [],
            "all_passed": False,
            "rejection_log": [],
            "retry_feedback": None,
            "memory_context": "",
            "evolved_instructions": [],
            "inject_error": False,
            "status": "INITIALIZED",
            "output_lesson_path": None,
            "output_log_path": None,
        }

        final_state = graph.invoke(initial_state)

        assert final_state["all_passed"] is False
        assert final_state["attempt_number"] == 2
        assert len(final_state["rejection_log"]) == 2
        assert final_state["status"] == "COMPLETED_MAX_RETRIES"
        assert Path(final_state["output_log_path"]).exists()
