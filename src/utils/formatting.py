import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

from src.config import Config


def save_lesson_and_log(
    run_id: str,
    topic: str,
    lesson_content: str,
    rejection_log: List[Dict[str, Any]],
    all_passed: bool,
    total_attempts: int,
    output_dir: Path = None,
) -> Tuple[Path, Path]:
    """Save the final generated lesson to Markdown and rejection history to JSON."""
    out_dir = output_dir or Config.OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_topic = "".join(c if c.isalnum() else "_" for c in topic)[:25].strip("_")

    lesson_filename = f"lesson_{sanitized_topic}_{timestamp_str}.md"
    log_filename = f"rejection_log_{sanitized_topic}_{timestamp_str}.json"

    lesson_path = out_dir / lesson_filename
    log_path = out_dir / log_filename

    # Build Markdown header for lesson
    header = (
        f"---\n"
        f"title: \"Beginner Lesson: {topic}\"\n"
        f"run_id: \"{run_id}\"\n"
        f"date: \"{datetime.datetime.now().isoformat()}\"\n"
        f"status: \"{'PASSED_ALL_RUBRICS' if all_passed else 'BEST_ATTEMPT_MAX_RETRIES'}\"\n"
        f"total_attempts: {total_attempts}\n"
        f"target_audience: \"12th-grade Indian graduate (non-English medium, zero AI knowledge)\"\n"
        f"---\n\n"
    )

    lesson_path.write_text(header + lesson_content, encoding="utf-8")

    # Build structured rejection log payload
    log_payload = {
        "run_id": run_id,
        "topic": topic,
        "timestamp": datetime.datetime.now().isoformat(),
        "final_status": "PASSED" if all_passed else "FAILED_MAX_RETRIES",
        "total_attempts": total_attempts,
        "total_rejections": len(rejection_log),
        "rejection_history": rejection_log,
    }

    log_path.write_text(json.dumps(log_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return lesson_path, log_path
