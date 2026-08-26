from typing import Optional, Dict, Any, Callable
from langgraph.graph import StateGraph, END

from src.state import PipelineState
from src.llm import LLMClient, get_llm_client
from src.memory.store import MemoryStore
from src.nodes.generator import generator_node
from src.nodes.evaluator import evaluator_node
from src.nodes.memory_manager import load_memory_node, persist_memory_node


def route_after_evaluation(state: PipelineState) -> str:
    """Conditional router determining whether to terminate or retry generation."""
    if state.get("all_passed", False):
        return "pass"

    attempt = state.get("attempt_number", 1)
    max_attempts = state.get("max_attempts", 3)

    if attempt < max_attempts:
        return "retry"
    else:
        return "max_retries_exceeded"


def create_pipeline_graph(
    llm: Optional[LLMClient] = None,
    memory_store: Optional[MemoryStore] = None,
):
    """Construct and compile the stateful LangGraph self-evaluating generation graph."""
    client = llm or get_llm_client()
    store = memory_store or MemoryStore()

    # Wrap nodes with injected dependencies
    def wrapped_load_memory(state: PipelineState) -> Dict[str, Any]:
        return load_memory_node(state, memory_store=store)

    def wrapped_generator(state: PipelineState) -> Dict[str, Any]:
        return generator_node(state, llm=client)

    def wrapped_evaluator(state: PipelineState) -> Dict[str, Any]:
        return evaluator_node(state, llm=client)

    def wrapped_persist_memory(state: PipelineState) -> Dict[str, Any]:
        return persist_memory_node(state, memory_store=store, llm=client)

    # Initialize StateGraph
    builder = StateGraph(PipelineState)

    # Add Nodes
    builder.add_node("load_memory", wrapped_load_memory)
    builder.add_node("generate", wrapped_generator)
    builder.add_node("evaluate", wrapped_evaluator)
    builder.add_node("persist_memory", wrapped_persist_memory)

    # Define Linear Edges
    builder.set_entry_point("load_memory")
    builder.add_edge("load_memory", "generate")
    builder.add_edge("generate", "evaluate")

    # Define Conditional Branching from Evaluator
    builder.add_conditional_edges(
        "evaluate",
        route_after_evaluation,
        {
            "pass": "persist_memory",
            "retry": "generate",
            "max_retries_exceeded": "persist_memory",
        },
    )

    builder.add_edge("persist_memory", END)

    return builder.compile()
