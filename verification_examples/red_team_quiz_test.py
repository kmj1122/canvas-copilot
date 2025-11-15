#!/usr/bin/env python3
"""
Ad-hoc red teaming script for verification_system.py.

Creates intentionally flawed quiz questions and runs them through the
verification layer so we can confirm issues are detected. Also plugs in a
simple fake LLM so verify_quiz_answer_correctness() can flag obviously wrong
answers without hitting the network.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import verification_system  # noqa: E402


def fake_llm(prompt: str) -> str:
    """Return handcrafted JSON so answer verification can run offline."""
    lowered = prompt.lower()
    if "capital of korea" in lowered:
        return json.dumps({
            "confidence": 0.2,
            "issues": [
                "Marked answer is Paris but Seoul is the capital of South Korea."
            ],
            "warnings": [],
            "suggestions": [
                "Set the correct option index to the choice that says 'Seoul'."
            ],
        })
    if "2 + 2" in lowered or "2+2" in lowered:
        return json.dumps({
            "confidence": 0.3,
            "issues": [
                "Math error: marked answer should evaluate to 4."
            ],
            "warnings": [],
            "suggestions": [
                "Double-check arithmetic before publishing."
            ],
        })
    return json.dumps({
        "confidence": 0.9,
        "issues": [],
        "warnings": [],
        "suggestions": []
    })


RED_TEAM_QUESTIONS = [
    {
        "question": "Where is the capital of Korea located?",
        "options": ["Seoul", "Busan", "Incheon", "Paris"],
        "correct_index": 3,
    },
    {
        "question": "This is barely a question",
        "options": ["Yes", "No"],
        "correct_index": 0,
    },
    {
        "question": "Choose the right placeholder response?",
        "options": ["TODO", "TBD", "FixMe", "All of the above"],
        "correct_index": 3,
    },
    {
        "question": "What is 2 + 2 equal to??",
        "options": ["5", "4", "22", "2"],
        "correct_index": 0,
    },
    {
        "question": "Duplicate answers make quizzes weak?",
        "options": ["Redundancy", "Redundancy", "Variety", "Diversity"],
        "correct_index": 1,
    },
    {
        "question": "Broken index example?",
        "options": ["A", "B", "C", "D"],
        "correct_index": 7,
    },
]


def main() -> int:
    verification_system.set_llm_function(fake_llm)

    print("=" * 70)
    print("Running structural verification via verify_quiz_batch()")
    print("=" * 70)
    results, overall_conf = verification_system.verify_quiz_batch(RED_TEAM_QUESTIONS)
    print(f"Overall structural confidence: {overall_conf:.1%}\n")

    for idx, (question, result) in enumerate(zip(RED_TEAM_QUESTIONS, results), start=1):
        icon = "⚠️" if result.needs_review else "✓"
        print(f"[{idx}] {icon} {question['question']}")
        print(f"    Confidence: {result.confidence:.1%}")
        if result.issues:
            print("    Issues:")
            for issue in result.issues:
                print(f"      • {issue}")
        if result.warnings:
            print("    Warnings:")
            for warning in result.warnings:
                print(f"      • {warning}")
        print()

    print("=" * 70)
    print("Running factual verification via verify_quiz_answer_correctness()")
    print("=" * 70)
    for idx, question in enumerate(RED_TEAM_QUESTIONS, start=1):
        answer_result = verification_system.verify_quiz_answer_correctness(question)
        icon = "⚠️" if answer_result.needs_review else "✓"
        print(f"[{idx}] {icon} {question['question']}")
        print(f"    Confidence: {answer_result.confidence:.1%}")
        if answer_result.issues:
            print("    Issues:")
            for issue in answer_result.issues:
                print(f"      • {issue}")
        if answer_result.warnings:
            print("    Warnings:")
            for warning in answer_result.warnings:
                print(f"      • {warning}")
        print()

    print("Done. Use these outputs to confirm the verification pipeline flags "
          "the expected problems.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
