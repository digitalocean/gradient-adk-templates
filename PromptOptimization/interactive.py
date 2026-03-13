"""
Prompt Optimization Workflow - Interactive CLI

Menu-driven interface for the optimize-evaluate-deploy cycle.
Orchestrates the optimization engine (optimize.py), local evaluation
(evaluate.py), prompt version management, and Gradient deployment.

Usage:
    python interactive.py

Menu:
    [1] Run optimization (DSPy MIPROv2)
    [2] Evaluate prompt locally (DSPy metrics)
    [3] Compare prompt versions
    [4] Set active prompt version
    [5] Rollback to previous version
    [6] Deploy agent to Gradient
    [7] Evaluate deployed agent (Gradient)
    [8] Exit
"""

import json
import subprocess
from pathlib import Path

from dotenv import load_dotenv

import prompt_manager
from optimize import default_version_name, run_optimization, save_result
from prompts import CATEGORY_LABELS, RESPONSE_FORMAT

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"


# =============================================================================
# WORKFLOW ACTIONS
# =============================================================================

def action_optimize():
    """Run DSPy MIPROv2 optimization."""
    print("\n" + "=" * 60)
    print("DSPy PROMPT OPTIMIZATION (MIPROv2)")
    print("=" * 60)

    # Choose optimization intensity
    print("\nOptimization intensity:")
    print("  [1] Light  - ~10 trials, fastest (~2-5 min)")
    print("  [2] Medium - ~25 trials, balanced (~5-15 min)")
    print("  [3] Heavy  - ~50 trials, most thorough (~15-30 min)")
    choice = input("\nSelect intensity [1]: ").strip() or "1"
    auto_map = {"1": "light", "2": "medium", "3": "heavy"}
    intensity = auto_map.get(choice, "light")

    try:
        result = run_optimization(intensity)
    except Exception as e:
        print(f"\nOptimization failed: {e}")
        print("Check your DIGITALOCEAN_INFERENCE_KEY and network connection.")
        return

    # Let the user name the version
    default_name = default_version_name(intensity)
    version_name = input(f"\nVersion name [{default_name}]: ").strip() or default_name

    save_result(result, version_name)

    print(f"\n{'='*60}")
    print("Optimization complete!")
    print(f"  Version:    {version_name}")
    print(f"  Accuracy:   {result['train_accuracy']:.0%}")
    print(f"  Demos:      {result['demos_count']}")
    print(f"  Instruction: {result['optimized_instruction'][:80]}...")
    print(f"{'='*60}")

    # Ask if user wants to set as active
    set_it = input("\nSet this as the active prompt version? [y/N]: ").strip().lower()
    if set_it == "y":
        prompt_manager.set_active(version_name)
        print(f"Active prompt set to: {version_name}")

    # Ask if user wants to run a full evaluation
    run_eval = input("Run full local evaluation on validation set? [y/N]: ").strip().lower()
    if run_eval == "y":
        from evaluate import evaluate_version
        evaluate_version(version_name)


def action_evaluate_local():
    """Evaluate the active prompt version locally with DSPy metrics."""
    active = prompt_manager.get_active_name()
    if not active:
        print("No active prompt version. Run optimization first or set one.")
        return

    versions = prompt_manager.list_versions()
    if not versions:
        print("No prompt versions found.")
        return

    print("\nAvailable versions:")
    for v in versions:
        print(prompt_manager.format_version_summary(v))

    version_name = input(f"\nVersion to evaluate [{active}]: ").strip() or active

    from evaluate import evaluate_version
    evaluate_version(version_name)


def action_compare():
    """Compare two prompt versions side-by-side."""
    versions = prompt_manager.list_versions()
    if len(versions) < 2:
        print("Need at least 2 prompt versions to compare. Run optimization first.")
        return

    print("\nAvailable versions:")
    for v in versions:
        print(prompt_manager.format_version_summary(v))

    name_a = input("\nFirst version: ").strip()
    name_b = input("Second version: ").strip()

    if not name_a or not name_b:
        print("Please provide two version names.")
        return

    # Show each version's full assembled prompt, one after the other
    try:
        va = prompt_manager.load_version(name_a)
        vb = prompt_manager.load_version(name_b)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    for version in [va, vb]:
        name = version["name"]
        print(f"\n{'='*60}")
        print(f"  VERSION: {name}")
        print(f"  Optimizer: {version.get('optimizer', 'manual')}")
        scores = version.get("scores", {})
        if scores:
            parts = []
            if "accuracy" in scores:
                parts.append(f"acc={scores['accuracy']:.0%}")
            if "response_quality" in scores:
                parts.append(f"quality={scores['response_quality']:.1f}/5")
            if parts:
                print(f"  Scores: {', '.join(parts)}")
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

        print(f"\n  [Human Template]")
        print(f"  | Customer email:")
        print(f"  | {{email_text}}")

    run_eval = input("\nRun evaluation comparison? [y/N]: ").strip().lower()
    if run_eval == "y":
        from evaluate import compare_versions
        compare_versions(name_a, name_b)


def action_set_active():
    """Set the active prompt version."""
    versions = prompt_manager.list_versions()
    if not versions:
        print("No prompt versions found.")
        return

    print("\nAvailable versions:")
    for v in versions:
        print(prompt_manager.format_version_summary(v))

    name = input("\nVersion to activate: ").strip()
    if not name:
        return

    try:
        prompt_manager.set_active(name)
        print(f"Active prompt set to: {name}")
    except FileNotFoundError as e:
        print(f"Error: {e}")


def action_rollback():
    """Rollback to a previous prompt version."""
    versions = prompt_manager.list_versions()
    if not versions:
        print("No prompt versions to rollback to.")
        return

    active = prompt_manager.get_active_name()
    print(f"\nCurrent active: {active}")
    print("\nAvailable versions:")
    for v in versions:
        print(prompt_manager.format_version_summary(v))

    name = input("\nVersion to rollback to: ").strip()
    if not name:
        return

    try:
        prompt_manager.set_active(name)
        print(f"Rolled back to: {name}")
    except FileNotFoundError as e:
        print(f"Error: {e}")


def action_deploy():
    """Deploy the agent to Gradient with the current active prompt."""
    active = prompt_manager.get_active_name()
    if not active:
        print("No active prompt version set. Set one before deploying.")
        return

    version = prompt_manager.get_active_version()
    print(f"\nDeploying with prompt version: {active}")
    print(f"Optimizer: {version.get('optimizer', '?')}")
    print(f"Scores: {json.dumps(version.get('scores', {}))}")

    confirm = input("\nProceed with `gradient agent deploy`? [y/N]: ").strip().lower()
    if confirm != "y":
        return

    print("\nRunning: gradient agent deploy\n")
    result = subprocess.run(
        ["gradient", "agent", "deploy"],
        cwd=str(Path(__file__).parent),
    )

    if result.returncode == 0:
        print("\nDeployment successful!")
        print("Tip: Run option [7] to evaluate the deployed agent with Gradient metrics.")
    else:
        print(f"\nDeployment exited with code {result.returncode}")


def action_evaluate_gradient_deployed():
    """Run Gradient evaluation on the deployed agent."""
    print("\n" + "=" * 60)
    print("GRADIENT EVALUATION (DEPLOYED AGENT)")
    print("=" * 60)
    print()
    print("This evaluates the deployed agent using Gradient's built-in")
    print("metrics against a held-out dataset that was not used during")
    print("optimization or local evaluation.")

    gradient_eval_dataset = DATA_DIR / "gradient_eval_dataset.csv"
    if not gradient_eval_dataset.exists():
        print(f"\nError: Gradient evaluation dataset not found at {gradient_eval_dataset}")
        return

    active = prompt_manager.get_active_name()
    if active:
        print(f"\nActive prompt version: {active}")

    test_case_name = input("\n  Test case name [prompt-opt-deployed]: ").strip() or "prompt-opt-deployed"

    print("\n  Available metric categories:")
    print("    correctness         - Factual accuracy, instruction following")
    print("    user_outcomes       - Goal progress and completion")
    print("    safety_and_security - PII, toxicity, prompt injection")
    categories = input("  Categories [correctness,user_outcomes]: ").strip() or "correctness,user_outcomes"

    star_metric = input("  Star metric [Correctness (general hallucinations)]: ").strip() or "Correctness (general hallucinations)"
    threshold = input("  Success threshold [75.0]: ").strip() or "75.0"

    proceed = input("\nRun Gradient evaluation on deployed agent? [y/N]: ").strip().lower()
    if proceed != "y":
        return

    eval_cmd = [
        "gradient", "agent", "evaluate",
        "--test-case-name", test_case_name,
        "--dataset-file", str(gradient_eval_dataset),
        "--categories", categories,
        "--star-metric-name", star_metric,
        "--success-threshold", threshold,
    ]

    print(f"\nRunning: {' '.join(eval_cmd)}\n")
    result = subprocess.run(eval_cmd, cwd=str(Path(__file__).parent))

    if result.returncode == 0:
        print("\nGradient evaluation completed successfully.")
    else:
        print(f"\nGradient evaluation exited with code {result.returncode}")
        print("Tip: Make sure `gradient-adk` is installed, you're logged in,")
        print("and the agent has been deployed with option [6].")


# =============================================================================
# MAIN MENU
# =============================================================================

def print_menu():
    active = prompt_manager.get_active_name() or "(none)"
    active_version = prompt_manager.get_active_version()
    scores = active_version.get("scores", {}) if active_version else {}

    score_parts = []
    if "accuracy" in scores:
        score_parts.append(f"acc={scores['accuracy']:.0%}")
    if "response_quality" in scores:
        score_parts.append(f"quality={scores['response_quality']:.1f}/5")
    score_str = f" ({', '.join(score_parts)})" if score_parts else ""

    print(f"""
{'='*60}
  PROMPT OPTIMIZATION WORKFLOW
{'='*60}

  Active prompt: {active}{score_str}

  --- Optimize ---
  [1] Run optimization (DSPy MIPROv2)

  --- Evaluate ---
  [2] Evaluate prompt locally (DSPy metrics)

  --- Manage Versions ---
  [3] Compare prompt versions
  [4] Set active prompt version
  [5] Rollback to previous version

  --- Deploy ---
  [6] Deploy agent to Gradient
  [7] Evaluate deployed agent (Gradient)

  [8] Exit
""")


def main():
    # Ensure baseline exists
    prompt_manager.create_baseline()

    actions = {
        "1": action_optimize,
        "2": action_evaluate_local,
        "3": action_compare,
        "4": action_set_active,
        "5": action_rollback,
        "6": action_deploy,
        "7": action_evaluate_gradient_deployed,
    }

    while True:
        print_menu()
        choice = input("  Select an action: ").strip()

        if choice == "8":
            print("Goodbye!")
            break

        action = actions.get(choice)
        if action:
            try:
                action()
            except KeyboardInterrupt:
                print("\n\nAction cancelled.")
            except Exception as e:
                print(f"\nError: {e}")
        else:
            print("Invalid choice. Please select 1-8.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
