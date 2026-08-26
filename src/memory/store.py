import sqlite3
import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Generator

from src.config import Config


class MemoryStore:
    """SQLite-backed persistent memory store for tracking runs, failures, and evolved instructions."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager that provides a connection and guarantees closing it."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        """Initialize database schema if not already present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Run history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS run_history (
                    run_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    total_attempts INTEGER NOT NULL,
                    final_passed BOOLEAN NOT NULL
                )
            """)

            # Failure records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failure_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    checkpoint_name TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    suggestion TEXT,
                    was_fixed_on_retry BOOLEAN DEFAULT 0,
                    FOREIGN KEY (run_id) REFERENCES run_history(run_id)
                )
            """)

            # Evolved instructions table (Self-evolution across runs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evolved_instructions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    instruction TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES run_history(run_id)
                )
            """)

            conn.commit()

    def save_run(
        self,
        run_id: str,
        topic: str,
        total_attempts: int,
        final_passed: bool,
        rejection_log: List[Dict[str, Any]],
    ):
        """Save run details and failure records to memory."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO run_history (run_id, timestamp, topic, total_attempts, final_passed)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, now, topic, total_attempts, 1 if final_passed else 0),
            )

            for entry in rejection_log:
                attempt_num = entry.get("attempt_number", 1)
                for res in entry.get("results", []):
                    if not res.get("passed", True):
                        cursor.execute(
                            """
                            INSERT INTO failure_records 
                            (run_id, attempt_number, checkpoint_name, reasoning, suggestion, was_fixed_on_retry)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                run_id,
                                attempt_num,
                                res.get("checkpoint_name", "Unknown"),
                                res.get("reasoning", ""),
                                res.get("suggestion", ""),
                                1 if final_passed else 0,
                            ),
                        )

            conn.commit()

    def save_evolved_instructions(
        self,
        run_id: str,
        topic: str,
        instructions: List[str],
    ):
        """Save newly evolved instruction rules into the persistent memory."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for inst in instructions:
                inst_clean = inst.strip()
                if not inst_clean:
                    continue

                # Check if exact instruction already exists for this topic
                cursor.execute(
                    "SELECT COUNT(*) FROM evolved_instructions WHERE topic = ? AND instruction = ?",
                    (topic, inst_clean),
                )
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        """
                        INSERT INTO evolved_instructions (run_id, topic, instruction, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (run_id, topic, inst_clean, now),
                    )
            conn.commit()

    def get_evolved_instructions(self, topic: str, limit: int = 8) -> List[str]:
        """Retrieve most recent evolved instructions relevant to the given topic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT instruction FROM evolved_instructions
                WHERE topic = ? OR topic = 'GLOBAL' OR ? LIKE '%' || topic || '%'
                ORDER BY id DESC LIMIT ?
                """,
                (topic, topic, limit),
            )
            rows = cursor.fetchall()
            return [row["instruction"] for row in rows]

    def get_past_failure_summary(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get summary of past failure checkpoints for the topic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT f.checkpoint_name, f.reasoning, f.suggestion, r.timestamp
                FROM failure_records f
                JOIN run_history r ON f.run_id = r.run_id
                WHERE r.topic = ?
                ORDER BY f.id DESC LIMIT ?
                """,
                (topic, limit),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Retrieve all recorded runs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM run_history ORDER BY timestamp DESC"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def inspect_memory(self) -> Dict[str, Any]:
        """Get comprehensive memory inspection statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM run_history")
            total_runs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM failure_records")
            total_failures = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM evolved_instructions")
            total_evolved = cursor.fetchone()[0]

            cursor.execute("SELECT checkpoint_name, COUNT(*) as count FROM failure_records GROUP BY checkpoint_name ORDER BY count DESC")
            checkpoint_stats = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT * FROM evolved_instructions ORDER BY id DESC LIMIT 10")
            recent_instructions = [dict(row) for row in cursor.fetchall()]

            return {
                "total_runs": total_runs,
                "total_failures_recorded": total_failures,
                "total_evolved_rules": total_evolved,
                "checkpoint_failure_breakdown": checkpoint_stats,
                "recent_evolved_instructions": recent_instructions,
            }

    def clear_memory(self):
        """Clear all tables in memory store."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM failure_records")
            cursor.execute("DELETE FROM evolved_instructions")
            cursor.execute("DELETE FROM run_history")
            conn.commit()
