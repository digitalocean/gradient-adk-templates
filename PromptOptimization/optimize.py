"""
DSPy MIPROv2 prompt optimization for the customer support agent.

This module contains the pure optimization logic: DSPy signature, module,
metric, and the run/save functions. It has no interactive I/O — the
interactive CLI lives in interactive.py.

Usage (standalone):
    python optimize.py [light|medium|heavy] [version_name]

Programmatic:
    from optimize import run_optimization, save_result
    result = run_optimization("light")
    save_result(result, "v2_optimized")
"""

import csv
import json
import os
import sys
import tempfile
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
from prompts import BASELINE_SYSTEM_INSTRUCTION

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"

# DO Serverless inference endpoint
DO_INFERENCE_ENDPOINT = "https://inference.do-ai.run/v1/"
DO_INFERENCE_KEY = os.environ.get("DIGITALOCEAN_INFERENCE_KEY", "")

# Model the agent actually uses at inference (the task model).
# This is intentionally a smaller, cheaper model — DSPy optimization
# compensates for its weaker baseline by learning better instructions
# and few-shot examples.
TASK_MODEL = "llama3-8b-instruct"
# MIPROv2's proposer model (generates candidate instructions). A stronger
# model here produces better instruction candidates without affecting
# the agent's per-request inference cost.
OPTIMIZER_MODEL = "openai-gpt-4.1"

# Fixed role preamble prepended to every optimized instruction to guard
# against hallucinated/scenario-specific instructions from DSPy's proposer.
ROLE_PREAMBLE = (
    "You are a customer support agent for a cloud platform. "
    "Given a customer email, classify it into one of the categories "
    "and write a professional, empathetic response with actionable next steps."
)


# =============================================================================
# DSPy SETUP
# =============================================================================

class ClassifyAndRespond(dspy.Signature):
    """Classify a customer support email and write a helpful response.

    You are a customer support agent for a cloud platform. Given a customer email,
    classify it into one of the categories and write a professional, empathetic response
    with actionable next steps. Be empathetic and professional, acknowledge the
    customer's concern, and provide actionable next steps."""

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
    """Configure DSPy to use DO Serverless inference.

    Sets the task model (Llama 3 8B) as the default LM. Returns both
    the task LM and the proposer LM (GPT-4.1) for use in MIPROv2.
    Caching is disabled so every optimization run makes fresh LLM calls.
    """
    if not DO_INFERENCE_KEY:
        raise RuntimeError("DIGITALOCEAN_INFERENCE_KEY not set. Check your .env file.")

    task_lm = dspy.LM(
        f"openai/{TASK_MODEL}",
        api_base=DO_INFERENCE_ENDPOINT,
        api_key=DO_INFERENCE_KEY,
        cache=False,
    )
    proposer_lm = dspy.LM(
        f"openai/{OPTIMIZER_MODEL}",
        api_base=DO_INFERENCE_ENDPOINT,
        api_key=DO_INFERENCE_KEY,
        cache=False,
    )
    dspy.configure(lm=task_lm)
    return task_lm, proposer_lm


# =============================================================================
# OPTIMIZATION
# =============================================================================

def run_optimization(intensity: str = "light") -> dict:
    """Run DSPy MIPROv2 optimization and return the result.

    Args:
        intensity: One of "light", "medium", "heavy".

    Returns:
        Dict with keys: optimized_instruction, few_shot_text, demos_count,
        train_accuracy, intensity, dspy_data.
    """
    task_lm, proposer_lm = configure_dspy()

    trainset = load_dspy_examples(DATA_DIR / "train.csv")
    print(f"Training examples: {len(trainset)}")
    print(f"Task model: {TASK_MODEL}")
    print(f"Proposer model: {OPTIMIZER_MODEL}")

    print(f"\nRunning MIPROv2 with auto='{intensity}'...")
    print("This will make multiple LLM calls via DO Serverless.")
    print("Progress updates will appear below.\n")

    student = SupportModule()
    optimizer = dspy.MIPROv2(
        metric=support_metric,
        auto=intensity,
        prompt_model=proposer_lm,
        verbose=False,
    )

    print("[1/3] Bootstrapping few-shot examples...")
    optimized = optimizer.compile(
        student,
        trainset=trainset,
    )
    print("[3/3] Optimization search complete.")

    # Serialize via DSPy's own save (the reliable source of truth) then read back
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    optimized.save(tmp_path)
    with open(tmp_path) as f:
        dspy_data = json.load(f)
    os.unlink(tmp_path)

    # Extract optimized instruction
    predictor_key = next(
        (k for k in dspy_data if k not in ("metadata",)), None
    )
    predictor_data = dspy_data.get(predictor_key, {}) if predictor_key else {}

    sig_data = predictor_data.get("signature", {})
    raw_optimized_instruction = sig_data.get("instructions", "").strip()

    if raw_optimized_instruction:
        optimized_instruction = f"{ROLE_PREAMBLE}\n\n{raw_optimized_instruction}"
    else:
        optimized_instruction = BASELINE_SYSTEM_INSTRUCTION

    # Extract few-shot demos (no truncation — keep full examples)
    demos = predictor_data.get("demos", [])
    few_shot_text = ""
    if demos:
        few_shot_lines = ["Examples:"]
        for demo in demos[:5]:
            email = demo.get("email_text", "")
            cat = demo.get("category", "")
            resp = demo.get("response", "")
            if email and cat:
                few_shot_lines.append(f"\nEmail: {email}")
                few_shot_lines.append(f"Category: {cat}")
                if resp:
                    few_shot_lines.append(f"Response: {resp}")
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

    return {
        "optimized_instruction": optimized_instruction,
        "few_shot_text": few_shot_text,
        "demos_count": len(demos),
        "train_accuracy": train_accuracy,
        "intensity": intensity,
        "dspy_data": dspy_data,
    }


def save_result(result: dict, version_name: str) -> None:
    """Save an optimization result as a prompt version.

    Args:
        result: Dict returned by run_optimization().
        version_name: Name for the new prompt version.
    """
    scores = {
        "accuracy": result["train_accuracy"],
        "optimization_intensity": result["intensity"],
    }
    prompt_manager.save_version(
        name=version_name,
        system_instruction=result["optimized_instruction"],
        few_shot_examples=result["few_shot_text"],
        optimizer=f"dspy_miprov2_{result['intensity']}",
        scores=scores,
    )

    # Also save the raw DSPy program for reproducibility
    dspy_save_path = Path(__file__).parent / "prompt_versions" / f"{version_name}_dspy.json"
    try:
        with open(dspy_save_path, "w") as f:
            json.dump(result["dspy_data"], f, indent=2)
    except Exception:
        pass


def default_version_name(intensity: str) -> str:
    """Generate a default version name with timestamp."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"v_dspy_{intensity}_{timestamp}"


# =============================================================================
# STANDALONE CLI
# =============================================================================

if __name__ == "__main__":
    args = sys.argv[1:]
    intensity = args[0] if args else "light"
    if intensity not in ("light", "medium", "heavy"):
        print("Usage: python optimize.py [light|medium|heavy] [version_name]")
        sys.exit(1)

    version_name = args[1] if len(args) > 1 else default_version_name(intensity)

    print(f"Running optimization (intensity={intensity})...")
    result = run_optimization(intensity)
    save_result(result, version_name)

    print(f"\nOptimization complete!")
    print(f"  Version:    {version_name}")
    print(f"  Accuracy:   {result['train_accuracy']:.0%}")
    print(f"  Demos:      {result['demos_count']}")
    print(f"  Instruction: {result['optimized_instruction'][:80]}...")
