"""Memory record schemas.

These define the structure of data persisted in SQLite
for cross-run self-evolution.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List


@dataclass
class FailureRecord:
    """A single checkpoint failure from a pipeline run."""
    checkpoint_name: str
    reasoning: str
    suggestion: str
    was_fixed_on_retry: bool = False
    fix_strategy: str = ""
    id: Optional[int] = None
    run_id: Optional[str] = None


@dataclass
class RunRecord:
    """Complete record of a pipeline run, stored for self-evolution."""
    run_id: str
    timestamp: str
    topic: str
    total_attempts: int
    final_passed: bool
    failures: List[FailureRecord] = field(default_factory=list)
    evolved_instruction: str = ""

    @classmethod
    def create(cls, run_id: str, topic: str) -> "RunRecord":
        return cls(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            topic=topic,
            total_attempts=0,
            final_passed=False,
        )


# Alias for compatibility
RunHistoryRecord = RunRecord


@dataclass
class EvolvedInstructionRecord:
    """A synthesized guideline stored in memory for prompt patching."""
    topic: str
    instruction: str
    created_at: str
    id: Optional[int] = None
    run_id: Optional[str] = None
