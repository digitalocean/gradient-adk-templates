"""
Prompt Optimization Workflow - Interactive CLI

This is the main guided workflow for optimizing your agent's prompt.
It orchestrates DSPy optimization, local evaluation, Gradient evaluation,
version management, and deployment.

Usage:
    python optimize.py

The workflow provides a menu-driven interface:
    [1] Run optimization (DSPy MIPROv2)
    [2] Evaluate prompt locally (DSPy metrics)
    [3] Evaluate with Gradient (local agent)
    [4] Compare prompt versions
    [5] Set active prompt version
    [6] Rollback to previous version
    [7] Deploy agent to Gradient
    [8] Evaluate deployed agent (Gradient)
    [9] Exit
"""

import csv
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import logging

import dspy

from dotenv import load_dotenv

# Suppress noisy DSPy/LiteLLM output during optimization
logging.getLogger("dspy").setLevel(logging.WARNING)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

import prompt_manager
from prompts import BASELINE_SYSTEM_INSTRUCTION, CATEGORY_DEFINITIONS

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"

# DO Serverless inference endpoint
DO_INFERENCE_ENDPOINT = "https://inference.do-ai.run/v1/"
DO_INFERENCE_KEY = os.environ.get("DIGITALOCEAN_INFERENCE_KEY", "")

# Model to use for optimization (the proposer model in MIPROv2)
OPTIMIZER_MODEL = "openai-gpt-4.1"
# Model the agent actually uses (the task model)
TASK_MODEL = "openai-gpt-4.1"


# =============================================================================
# DSPy SETUP
# =============================================================================

class ClassifyAndRespond(dspy.Signature):
    """Classify a customer support email and write a helpful response.

    You are a customer support agent for a cloud platform. Given a customer email,
    classify it into one of the categories and write a professional, empathetic response
    with actionable next steps."""

    email_text: str = dspy.InputField(desc="The customer's support email")
    category: str = dspy.OutputField(
        desc="One of: billing, technical, account, general"
    )
    response: str = dspy.OutputField(
        desc="A helpful, empathetic support response with actionable next steps"
    )


class SupportModule(dspy.Module):
    def __init__(self):
        self.classify_respond = dspy.ChainOfThought(ClassifyAndRespond)

    def forward(self, email_text: str):
        return self.classify_respond(email_text=email_text)


def support_metric(example, prediction, trace=None):
    """Combined metric: category accuracy (60%) + response quality heuristic (40%)."""
    # Category accuracy
    cat_correct = prediction.category.strip().lower() == example.category.strip().lower()

    # Response quality heuristic (fast, no LLM judge needed during optimization)
    response = prediction.response.strip().lower()
    quality_score = 0.0

    # Check for non-trivial response
    if len(response) > 50:
        quality_score += 0.3
    # Check for empathetic language
    empathy_words = ["understand", "sorry", "apologize", "appreciate", "help", "concern"]
    if any(word in response for word in empathy_words):
        quality_score += 0.3
    # Check for actionable steps
    action_words = ["step", "please", "follow", "click", "navigate", "contact", "try", "check", "verify"]
    if any(word in response for word in action_words):
        quality_score += 0.4

    return 0.6 * float(cat_correct) + 0.4 * quality_score


def load_dspy_examples(csv_path: Path) -> list:
    """Load CSV data as DSPy Examples."""
    examples = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            examples.append(
                dspy.Example(
                    email_text=row["email_text"],
                    category=row["category"],
                ).with_inputs("email_text")
            )
    return examples


def configure_dspy():
    """Configure DSPy to use DO Serverless inference."""
    if not DO_INFERENCE_KEY:
        print("Error: DIGITALOCEAN_INFERENCE_KEY not set. Check your .env file.")
        sys.exit(1)

    lm = dspy.LM(
        f"openai/{TASK_MODEL}",
        api_base=DO_INFERENCE_ENDPOINT,
        api_key=DO_INFERENCE_KEY,
    )
    dspy.configure(lm=lm)
    return lm


# =============================================================================
# WORKFLOW ACTIONS
# =============================================================================

def action_optimize():
    """Run DSPy MIPROv2 optimization."""
    print("\n" + "=" * 60)
    print("DSPy PROMPT OPTIMIZATION (MIPROv2)")
    print("=" * 60)

    # Configure DSPy with DO Serverless
    configure_dspy()

    # Load training data
    trainset = load_dspy_examples(DATA_DIR / "train.csv")
    print(f"Training examples: {len(trainset)}")

    # Choose optimization intensity
    print("\nOptimization intensity:")
    print("  [1] Light  - ~10 trials, fastest (~2-5 min)")
    print("  [2] Medium - ~25 trials, balanced (~5-15 min)")
    print("  [3] Heavy  - ~50 trials, most thorough (~15-30 min)")
    choice = input("\nSelect intensity [1]: ").strip() or "1"
    auto_map = {"1": "light", "2": "medium", "3": "heavy"}
    auto = auto_map.get(choice, "light")

    print(f"\nRunning MIPROv2 with auto='{auto}'...")
    print("This will make multiple LLM calls via DO Serverless.")
    print("Progress updates will appear below.\n")

    # Create and optimize the module
    student = SupportModule()
    optimizer = dspy.MIPROv2(
        metric=support_metric,
        auto=auto,
        verbose=False,
    )

    try:
        print("[1/3] Bootstrapping few-shot examples...")
        optimized = optimizer.compile(
            student,
            trainset=trainset,
        )
        print("[3/3] Optimization search complete.")
    except Exception as e:
        print(f"\nOptimization failed: {e}")
        print("Check your DIGITALOCEAN_INFERENCE_KEY and network connection.")
        return

    # Save the DSPy program first, then read it back to extract the optimized
    # instruction and demos. DSPy's own serialization is the reliable source
    # of truth — manual getattr extraction misses optimized values.
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    optimized.save(tmp_path)
    with open(tmp_path) as f:
        dspy_data = json.load(f)
    os.unlink(tmp_path)

    # Extract optimized instruction from the DSPy save
    predictor_key = next(
        (k for k in dspy_data if k not in ("metadata",)), None
    )
    predictor_data = dspy_data.get(predictor_key, {}) if predictor_key else {}

    sig_data = predictor_data.get("signature", {})
    optimized_instruction = sig_data.get("instructions", "").strip()
    if not optimized_instruction:
        optimized_instruction = BASELINE_SYSTEM_INSTRUCTION

    # Extract few-shot demos from the DSPy save
    demos = predictor_data.get("demos", [])
    few_shot_text = ""
    if demos:
        few_shot_lines = ["Examples:"]
        for demo in demos[:5]:
            email = demo.get("email_text", "")
            cat = demo.get("category", "")
            resp = demo.get("response", "")
            if email and cat:
                few_shot_lines.append(f"\nEmail: {email[:200]}")
                few_shot_lines.append(f"Category: {cat}")
                if resp:
                    few_shot_lines.append(f"Response: {resp[:300]}")
        few_shot_text = "\n".join(few_shot_lines)

    # Quick validation on training set
    print("\nRunning quick validation...")
    correct = 0
    total = min(len(trainset), 20)
    for ex in trainset[:total]:
        try:
            pred = optimized(email_text=ex.email_text)
            if pred.category.strip().lower() == ex.category.strip().lower():
                correct += 1
        except Exception:
            pass
    train_accuracy = correct / total if total > 0 else 0

    # Let the user name the version
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    default_name = f"v_dspy_{auto}_{timestamp}"
    version_name = input(f"\nVersion name [{default_name}]: ").strip() or default_name

    scores = {"accuracy": train_accuracy, "optimization_intensity": auto}
    prompt_manager.save_version(
        name=version_name,
        system_instruction=optimized_instruction,
        few_shot_examples=few_shot_text,
        optimizer=f"dspy_miprov2_{auto}",
        scores=scores,
    )

    # Also save the raw DSPy program for reproducibility
    dspy_save_path = Path(__file__).parent / "prompt_versions" / f"{version_name}_dspy.json"
    try:
        optimized.save(str(dspy_save_path))
    except Exception:
        pass

    print(f"\n{'='*60}")
    print("Optimization complete!")
    print(f"  Version:    {version_name}")
    print(f"  Accuracy:   {train_accuracy:.0%}")
    print(f"  Demos:      {len(demos)}")
    print(f"  Instruction: {optimized_instruction[:80]}...")
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


def action_evaluate_gradient_local():
    """Run Gradient evaluation against the locally running agent."""
    print("\n" + "=" * 60)
    print("GRADIENT EVALUATION (LOCAL AGENT)")
    print("=" * 60)
    print()
    print("This will:")
    print("  1. Start the agent locally with `gradient agent run`")
    print("  2. Run `gradient agent evaluate` against it")
    print("  3. Show results with Gradient's built-in metrics")
    print()

    active = prompt_manager.get_active_name()
    if active:
        print(f"Active prompt version: {active}")
    else:
        print("Warning: No active prompt version set. Using baseline.")
        prompt_manager.create_baseline()

    eval_dataset = DATA_DIR / "eval_dataset.csv"
    if not eval_dataset.exists():
        print(f"Error: Evaluation dataset not found at {eval_dataset}")
        return

    # Configure evaluation parameters
    print("\nGradient evaluation settings:")
    test_case_name = input("  Test case name [prompt-opt-eval]: ").strip() or "prompt-opt-eval"

    print("\n  Available metric categories:")
    print("    correctness         - Factual accuracy, instruction following")
    print("    user_outcomes       - Goal progress and completion")
    print("    safety_and_security - PII, toxicity, prompt injection")
    categories = input("  Categories [correctness]: ").strip() or "correctness"

    star_metric = input("  Star metric [Correctness (general hallucinations)]: ").strip() or "Correctness (general hallucinations)"
    threshold = input("  Success threshold [70.0]: ").strip() or "70.0"

    proceed = input("\nStart local agent and run evaluation? [y/N]: ").strip().lower()
    if proceed != "y":
        return

    # Start the local agent in the background
    print("\nStarting local agent with `gradient agent run`...")
    agent_proc = subprocess.Popen(
        ["gradient", "agent", "run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path(__file__).parent),
    )

    try:
        # Wait for the agent to be ready
        print("Waiting for agent to start (up to 30s)...")
        agent_ready = False
        for _ in range(30):
            time.sleep(1)
            try:
                import urllib.request
                req = urllib.request.Request("http://localhost:8080/run", method="POST",
                                            data=b'{"prompt": "test"}',
                                            headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=3)
                agent_ready = True
                break
            except Exception:
                continue

        if not agent_ready:
            print("Warning: Agent may not be fully ready. Proceeding anyway...")

        # Run gradient evaluation
        print(f"\nRunning: gradient agent evaluate")
        eval_cmd = [
            "gradient", "agent", "evaluate",
            "--test-case-name", test_case_name,
            "--dataset-file", str(eval_dataset),
            "--categories", categories,
            "--star-metric-name", star_metric,
            "--success-threshold", threshold,
        ]

        print(f"Command: {' '.join(eval_cmd)}\n")
        eval_result = subprocess.run(
            eval_cmd,
            cwd=str(Path(__file__).parent),
            capture_output=False,
        )

        if eval_result.returncode == 0:
            print("\nGradient evaluation completed successfully.")
        else:
            print(f"\nGradient evaluation exited with code {eval_result.returncode}")
            print("Tip: Make sure `gradient-adk` is installed and you're logged in.")

    finally:
        # Stop the local agent
        print("\nStopping local agent...")
        agent_proc.terminate()
        try:
            agent_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            agent_proc.kill()


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

    # Show prompt diffs
    try:
        va = prompt_manager.load_version(name_a)
        vb = prompt_manager.load_version(name_b)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    print(f"\n{'='*60}")
    print(f"PROMPT DIFF: {name_a} -> {name_b}")
    print(f"{'='*60}")
    print(f"\n--- {name_a} instruction ---")
    print(va["system_instruction"])
    print(f"\n--- {name_b} instruction ---")
    print(vb["system_instruction"])

    if va.get("few_shot_examples") or vb.get("few_shot_examples"):
        print(f"\n--- {name_a} examples ---")
        print(va.get("few_shot_examples", "(none)"))
        print(f"\n--- {name_b} examples ---")
        print(vb.get("few_shot_examples", "(none)"))

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
        print("Tip: Run option [8] to evaluate the deployed agent with Gradient metrics.")
    else:
        print(f"\nDeployment exited with code {result.returncode}")


def action_evaluate_gradient_deployed():
    """Run Gradient evaluation on the deployed agent."""
    print("\n" + "=" * 60)
    print("GRADIENT EVALUATION (DEPLOYED AGENT)")
    print("=" * 60)

    eval_dataset = DATA_DIR / "eval_dataset.csv"
    if not eval_dataset.exists():
        print(f"Error: Evaluation dataset not found at {eval_dataset}")
        return

    test_case_name = input("  Test case name [prompt-opt-deployed]: ").strip() or "prompt-opt-deployed"
    categories = input("  Categories [correctness,user_outcomes]: ").strip() or "correctness,user_outcomes"
    star_metric = input("  Star metric [Correctness (general hallucinations)]: ").strip() or "Correctness (general hallucinations)"
    threshold = input("  Success threshold [75.0]: ").strip() or "75.0"

    eval_cmd = [
        "gradient", "agent", "evaluate",
        "--test-case-name", test_case_name,
        "--dataset-file", str(eval_dataset),
        "--categories", categories,
        "--star-metric-name", star_metric,
        "--success-threshold", threshold,
    ]

    print(f"\nRunning: {' '.join(eval_cmd)}\n")
    subprocess.run(eval_cmd, cwd=str(Path(__file__).parent))


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
        score_parts.append(f"quality={scores['response_quality']:.1f}/10")
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
  [3] Evaluate with Gradient (local agent)

  --- Manage Versions ---
  [4] Compare prompt versions
  [5] Set active prompt version
  [6] Rollback to previous version

  --- Deploy ---
  [7] Deploy agent to Gradient
  [8] Evaluate deployed agent (Gradient)

  [9] Exit
""")


def main():
    # Ensure baseline exists
    prompt_manager.create_baseline()

    actions = {
        "1": action_optimize,
        "2": action_evaluate_local,
        "3": action_evaluate_gradient_local,
        "4": action_compare,
        "5": action_set_active,
        "6": action_rollback,
        "7": action_deploy,
        "8": action_evaluate_gradient_deployed,
    }

    while True:
        print_menu()
        choice = input("  Select an action: ").strip()

        if choice == "9":
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
            print("Invalid choice. Please select 1-9.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
