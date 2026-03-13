"""
Local evaluation harness for the customer support agent.

Evaluates a prompt version against the validation set using two metrics:
1. Classification accuracy (exact match on category)
2. Response quality (LLM-as-judge score 1-10)

Usage:
    python evaluate.py                    # Evaluate the active prompt version
    python evaluate.py v2_optimized       # Evaluate a specific version
    python evaluate.py v1_baseline v2_optimized  # Compare two versions side-by-side
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_gradient import ChatGradient

import prompt_manager
from prompts import CATEGORY_LABELS, JUDGE_MODEL, TASK_MODEL, build_prompt

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"

JUDGE_PROMPT = """You are evaluating a customer support agent's response. Score it using the rubric below.

Customer email: {email}
Correct category: {correct_category}
Predicted category: {predicted_category}
Expected traits: {expected_traits}

Agent response:
{response}

Rubric (pick exactly one):

5 - Excellent: Correctly addresses the customer's issue, empathetic and professional tone, provides specific and actionable next steps, matches expected traits.
4 - Good: Addresses the issue adequately with minor gaps, professional tone, provides next steps that could be more specific.
3 - Acceptable: Partially addresses the issue, tone is adequate but not empathetic, next steps are vague or generic.
2 - Poor: Misses key aspects of the issue, tone is robotic or dismissive, next steps are missing or unhelpful.
1 - Unacceptable: Does not address the customer's issue, unprofessional tone, no actionable guidance, or response is incoherent.

Respond with ONLY a single number from 1 to 5."""


def load_dataset(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def run_agent_on_email(email_text: str, version: dict) -> tuple[str, str]:
    """Run the agent's classify+respond logic on a single email. Returns (category, response)."""
    prompt = build_prompt(
        system_instruction=version["system_instruction"],
        category_labels=CATEGORY_LABELS,
        few_shot_examples=version.get("few_shot_examples", ""),
    )

    llm = ChatGradient(model=TASK_MODEL, temperature=0.0)
    chain = prompt | llm
    result = chain.invoke({"email_text": email_text})
    content = result.content

    category = "general"
    match = re.search(r"Category:\s*(\w+)", content, re.IGNORECASE)
    if match:
        parsed = match.group(1).lower()
        if parsed in {"billing", "technical", "account", "general"}:
            category = parsed

    response_text = re.sub(
        r"^Category:\s*\w+\s*\n?", "", content, count=1, flags=re.IGNORECASE
    ).strip()
    response_text = re.sub(
        r"^Response:\s*", "", response_text, count=1, flags=re.IGNORECASE
    ).strip()

    return category, response_text


def judge_response(
    email: str,
    correct_category: str,
    predicted_category: str,
    expected_traits: str,
    response: str,
) -> float:
    """Use an LLM judge to score response quality on a 1-5 rubric."""
    llm = ChatGradient(model=JUDGE_MODEL, temperature=0.0)
    prompt_text = JUDGE_PROMPT.format(
        email=email,
        correct_category=correct_category,
        predicted_category=predicted_category,
        expected_traits=expected_traits,
        response=response,
    )
    result = llm.invoke([{"role": "user", "content": prompt_text}])
    try:
        score = float(re.search(r"[1-5]", result.content).group())
        return max(1.0, min(5.0, score))
    except (AttributeError, ValueError):
        return 3.0


def evaluate_version(version_name: str, dataset_path: Path = DATA_DIR / "val.csv") -> dict:
    """Evaluate a prompt version and return scores."""
    version = prompt_manager.load_version(version_name)
    dataset = load_dataset(dataset_path)

    print(f"\nEvaluating '{version_name}' on {len(dataset)} examples...")
    print("-" * 60)

    correct = 0
    quality_scores = []
    category_results = {"billing": {"correct": 0, "total": 0},
                        "technical": {"correct": 0, "total": 0},
                        "account": {"correct": 0, "total": 0},
                        "general": {"correct": 0, "total": 0}}

    for i, row in enumerate(dataset):
        email = row["email_text"]
        expected_cat = row["category"]
        expected_traits = row.get("good_response_traits", "")

        predicted_cat, response = run_agent_on_email(email, version)

        cat_correct = predicted_cat == expected_cat
        if cat_correct:
            correct += 1

        quality = judge_response(email, expected_cat, predicted_cat, expected_traits, response)
        quality_scores.append(quality)

        if expected_cat in category_results:
            category_results[expected_cat]["total"] += 1
            if cat_correct:
                category_results[expected_cat]["correct"] += 1

        status = "OK" if cat_correct else "MISS"
        print(f"  [{i+1}/{len(dataset)}] {status} | expected={expected_cat} got={predicted_cat} | quality={quality:.0f}/5")

    accuracy = correct / len(dataset) if dataset else 0
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    print("-" * 60)
    print(f"Classification Accuracy: {accuracy:.1%} ({correct}/{len(dataset)})")
    print(f"Avg Response Quality:    {avg_quality:.1f}/5")
    print()
    print("Per-category breakdown:")
    for cat, stats in category_results.items():
        if stats["total"] > 0:
            cat_acc = stats["correct"] / stats["total"]
            print(f"  {cat:12s}: {cat_acc:.0%} ({stats['correct']}/{stats['total']})")

    scores = {"accuracy": accuracy, "response_quality": avg_quality}
    prompt_manager.update_scores(version_name, scores)

    return scores


def compare_versions(name_a: str, name_b: str, dataset_path: Path = DATA_DIR / "val.csv"):
    """Evaluate and compare two prompt versions side-by-side."""
    print(f"\n{'='*60}")
    print(f"COMPARING: {name_a} vs {name_b}")
    print(f"{'='*60}")

    scores_a = evaluate_version(name_a, dataset_path)
    scores_b = evaluate_version(name_b, dataset_path)

    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"{'Metric':<25} {name_a:<20} {name_b:<20} {'Delta':<10}")
    print("-" * 75)

    acc_delta = scores_b["accuracy"] - scores_a["accuracy"]
    qual_delta = scores_b["response_quality"] - scores_a["response_quality"]

    print(f"{'Accuracy':<25} {scores_a['accuracy']:<20.1%} {scores_b['accuracy']:<20.1%} {acc_delta:+.1%}")
    print(f"{'Response Quality':<25} {scores_a['response_quality']:<20.1f} {scores_b['response_quality']:<20.1f} {qual_delta:+.1f}")


if __name__ == "__main__":
    prompt_manager.create_baseline()

    args = sys.argv[1:]
    if len(args) == 0:
        active = prompt_manager.get_active_name() or "v1_baseline"
        evaluate_version(active)
    elif len(args) == 1:
        evaluate_version(args[0])
    elif len(args) == 2:
        compare_versions(args[0], args[1])
    else:
        print("Usage: python evaluate.py [version_name] [version_name_b]")
