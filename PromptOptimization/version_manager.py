#!/usr/bin/env python3
"""
Prompt version management CLI.

Quick command-line access to list, inspect, activate, compare, and rollback
prompt versions without launching the full interactive workflow.

Usage:
    python version_manager.py list
    python version_manager.py show <version_name>
    python version_manager.py activate <version_name>
    python version_manager.py rollback <version_name>
    python version_manager.py compare <version_a> <version_b>
"""

import sys

from dotenv import load_dotenv

import prompt_manager
from prompts import CATEGORY_LABELS, RESPONSE_FORMAT

load_dotenv()


def cmd_list():
    """List all prompt versions with scores."""
    prompt_manager.create_baseline()
    versions = prompt_manager.list_versions()
    if not versions:
        print("No prompt versions found.")
        return

    active = prompt_manager.get_active_name()
    print(f"\nActive version: {active or '(none)'}")
    print(f"Total versions: {len(versions)}\n")

    for v in versions:
        print(prompt_manager.format_version_summary(v))

    print()


def cmd_show(name: str):
    """Show full details of a prompt version."""
    try:
        version = prompt_manager.load_version(name)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    active = prompt_manager.get_active_name()
    marker = " [ACTIVE]" if name == active else ""

    print(f"\n{'='*60}")
    print(f"  Version: {name}{marker}")
    print(f"  Optimizer: {version.get('optimizer', '?')}")
    print(f"  Created: {version.get('created_at', '?')[:19]}")

    scores = version.get("scores", {})
    if scores:
        parts = []
        if "accuracy" in scores:
            parts.append(f"acc={scores['accuracy']:.0%}")
        if "response_quality" in scores:
            parts.append(f"quality={scores['response_quality']:.1f}/5")
        if "optimization_intensity" in scores:
            parts.append(f"intensity={scores['optimization_intensity']}")
        print(f"  Scores: {', '.join(parts)}")
    else:
        print("  Scores: not evaluated")
    print(f"{'='*60}")

    print(f"\n  [System Instruction]")
    for line in version["system_instruction"].splitlines():
        print(f"  | {line}")

    print(f"\n  [Category Labels]  (fixed)")
    for line in CATEGORY_LABELS.splitlines():
        print(f"  | {line}")

    print(f"\n  [Response Format]  (fixed)")
    for line in RESPONSE_FORMAT.splitlines():
        print(f"  | {line}")

    examples = version.get("few_shot_examples", "")
    if examples:
        print(f"\n  [Few-Shot Examples]")
        for line in examples.splitlines():
            print(f"  | {line}")
    else:
        print(f"\n  [Few-Shot Examples]")
        print(f"  | (none)")

    print()


def cmd_activate(name: str):
    """Set a version as the active prompt."""
    try:
        prompt_manager.set_active(name)
        print(f"Active prompt set to: {name}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_rollback(name: str):
    """Rollback to a previous version."""
    current = prompt_manager.get_active_name()
    if current == name:
        print(f"'{name}' is already the active version.")
        return

    try:
        prompt_manager.set_active(name)
        print(f"Rolled back from '{current}' to '{name}'")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_compare(name_a: str, name_b: str):
    """Compare two versions side-by-side, optionally running evaluation."""
    try:
        va = prompt_manager.load_version(name_a)
        vb = prompt_manager.load_version(name_b)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    for version in [va, vb]:
        name = version["name"]
        active = prompt_manager.get_active_name()
        marker = " [ACTIVE]" if name == active else ""

        print(f"\n{'='*60}")
        print(f"  VERSION: {name}{marker}")
        print(f"  Optimizer: {version.get('optimizer', '?')}")
        scores = version.get("scores", {})
        if scores:
            parts = []
            if "accuracy" in scores:
                parts.append(f"acc={scores['accuracy']:.0%}")
            if "response_quality" in scores:
                parts.append(f"quality={scores['response_quality']:.1f}/5")
            if parts:
                print(f"  Scores: {', '.join(parts)}")
        else:
            print("  Scores: not evaluated")
        print(f"{'='*60}")

        print(f"\n  [System Instruction]")
        for line in version["system_instruction"].splitlines():
            print(f"  | {line}")

        examples = version.get("few_shot_examples", "")
        if examples:
            print(f"\n  [Few-Shot Examples]")
            for line in examples.splitlines():
                print(f"  | {line}")
        else:
            print(f"\n  [Few-Shot Examples]")
            print(f"  | (none)")

    # Offer to run evaluation comparison
    run_eval = input("\nRun evaluation comparison? [y/N]: ").strip().lower()
    if run_eval == "y":
        from evaluate import compare_versions
        compare_versions(name_a, name_b)


USAGE = """\
Usage: python version_manager.py <command> [args]

Commands:
  list                          List all prompt versions with scores
  show <version>                Show full details of a version
  activate <version>            Set a version as the active prompt
  rollback <version>            Rollback to a previous version
  compare <version_a> <version_b>  Compare two versions side-by-side
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        cmd_list()
    elif command == "show" and len(sys.argv) == 3:
        cmd_show(sys.argv[2])
    elif command == "activate" and len(sys.argv) == 3:
        cmd_activate(sys.argv[2])
    elif command == "rollback" and len(sys.argv) == 3:
        cmd_rollback(sys.argv[2])
    elif command == "compare" and len(sys.argv) == 4:
        cmd_compare(sys.argv[2], sys.argv[3])
    else:
        print(USAGE)
        sys.exit(1)


if __name__ == "__main__":
    main()
