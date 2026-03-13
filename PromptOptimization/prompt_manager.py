"""
Prompt version manager.

Tracks prompt versions as JSON files in prompt_versions/.
Each version stores the system instruction, few-shot examples, metadata,
and evaluation scores. One version is marked as "active" and used by the agent.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

VERSIONS_DIR = Path(__file__).parent / "prompt_versions"
ACTIVE_FILE = VERSIONS_DIR / "_active.json"


def _ensure_dir():
    VERSIONS_DIR.mkdir(exist_ok=True)


def save_version(
    name: str,
    system_instruction: str,
    few_shot_examples: str = "",
    optimizer: str = "manual",
    scores: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> Path:
    """Save a new prompt version."""
    _ensure_dir()
    version = {
        "name": name,
        "system_instruction": system_instruction,
        "few_shot_examples": few_shot_examples,
        "optimizer": optimizer,
        "scores": scores or {},
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    path = VERSIONS_DIR / f"{name}.json"
    path.write_text(json.dumps(version, indent=2))
    return path


def load_version(name: str) -> dict:
    """Load a prompt version by name."""
    path = VERSIONS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Prompt version '{name}' not found at {path}")
    return json.loads(path.read_text())


def list_versions() -> list[dict]:
    """List all saved prompt versions, sorted by creation time."""
    _ensure_dir()
    versions = []
    for f in VERSIONS_DIR.glob("*.json"):
        if f.name == "_active.json" or f.name.endswith("_dspy.json"):
            continue
        try:
            data = json.loads(f.read_text())
            if "name" not in data:
                continue
            versions.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(versions, key=lambda v: v.get("created_at", ""))


def get_active_name() -> Optional[str]:
    """Get the name of the currently active prompt version."""
    if ACTIVE_FILE.exists():
        data = json.loads(ACTIVE_FILE.read_text())
        return data.get("active")
    return None


def set_active(name: str):
    """Set the active prompt version."""
    path = VERSIONS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Prompt version '{name}' not found")
    _ensure_dir()
    ACTIVE_FILE.write_text(json.dumps({"active": name}))


def get_active_version() -> Optional[dict]:
    """Load the currently active prompt version."""
    name = get_active_name()
    if name is None:
        return None
    try:
        return load_version(name)
    except FileNotFoundError:
        return None


def update_scores(name: str, scores: dict):
    """Update the scores for an existing version."""
    version = load_version(name)
    version["scores"].update(scores)
    path = VERSIONS_DIR / f"{name}.json"
    path.write_text(json.dumps(version, indent=2))


def format_version_summary(version: dict) -> str:
    """Format a version as a one-line summary."""
    name = version["name"]
    optimizer = version.get("optimizer", "?")
    scores = version.get("scores", {})
    created = version.get("created_at", "?")[:19]

    score_parts = []
    if "accuracy" in scores:
        score_parts.append(f"acc={scores['accuracy']:.0%}")
    if "response_quality" in scores:
        score_parts.append(f"quality={scores['response_quality']:.1f}/5")
    score_str = ", ".join(score_parts) if score_parts else "not evaluated"

    active = get_active_name()
    marker = " [ACTIVE]" if name == active else ""

    return f"  {name}{marker} | {optimizer} | {score_str} | {created}"


def format_version_detail(version: dict) -> str:
    """Format a version with full details for comparison."""
    lines = [
        f"Version: {version['name']}",
        f"Optimizer: {version.get('optimizer', '?')}",
        f"Created: {version.get('created_at', '?')[:19]}",
        f"Scores: {json.dumps(version.get('scores', {}), indent=2)}",
        "",
        "System Instruction:",
        version["system_instruction"],
    ]
    if version.get("few_shot_examples"):
        lines += ["", "Few-Shot Examples:", version["few_shot_examples"]]
    return "\n".join(lines)


def create_baseline():
    """Create the baseline prompt version if it doesn't exist."""
    from prompts import BASELINE_SYSTEM_INSTRUCTION

    _ensure_dir()
    baseline_path = VERSIONS_DIR / "v1_baseline.json"
    if baseline_path.exists():
        return

    save_version(
        name="v1_baseline",
        system_instruction=BASELINE_SYSTEM_INSTRUCTION,
        optimizer="manual",
    )
    set_active("v1_baseline")
