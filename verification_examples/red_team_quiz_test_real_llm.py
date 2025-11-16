#!/usr/bin/env python3
"""
Red team testing with REAL LLM verification for verification_system.py.

This script tests the verification system using actual OpenAI API calls
to verify quiz question correctness. Requires OPENAI_API_KEY environment variable.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add parent directory to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import verification_system  # noqa: E402


def create_real_llm_function() -> callable:
    """
    Create a real LLM function that calls OpenAI API.
    
    Returns:
        Callable that takes a prompt and returns LLM response
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Please set it to use real LLM verification."
        )
    
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai package not installed. Install with: pip install openai"
        )
    
    client = OpenAI(api_key=api_key)
    
    def llm_function(prompt: str) -> str:
        """Call OpenAI API with the given prompt."""
        try:
            logger.info("Calling OpenAI API...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective for verification
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a quality assurance expert reviewing "
                            "AI-generated educational content. Always respond "
                            "with valid JSON only."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent verification
                max_tokens=1000,
            )
            
            result = response.choices[0].message.content
            logger.info(f"Received response: {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            # Return default low-confidence response on error
            return json.dumps({
                "confidence": 0.5,
                "issues": [f"LLM verification failed: {str(e)}"],
                "warnings": [],
                "suggestions": []
            })
    
    return llm_function


# Red team questions - deliberately flawed for testing
RED_TEAM_QUESTIONS = [
    {
        "name": "Wrong Capital",
        "question": "What is the capital of South Korea?",
        "options": ["Seoul", "Busan", "Tokyo", "Paris"],
        "correct_index": 3,  # WRONG! Paris is marked as correct
        "expected_issue": "Should detect Paris is not capital of South Korea"
    },
    {
        "name": "Math Error",
        "question": "What is 2 + 2 equal to?",
        "options": ["5", "4", "22", "2"],
        "correct_index": 0,  # WRONG! 5 is marked as correct
        "expected_issue": "Should detect basic arithmetic error"
    },
    {
        "name": "Obvious Factual Error",
        "question": "Which programming language was created by Guido van Rossum?",
        "options": ["Java", "C++", "Python", "JavaScript"],
        "correct_index": 0,  # WRONG! Java is marked as correct
        "expected_issue": "Should know Python was created by Guido van Rossum"
    },
    {
        "name": "Historical Fact Error",
        "question": "In which year did World War II end?",
        "options": ["1943", "1944", "1945", "1946"],
        "correct_index": 0,  # WRONG! 1943 is marked as correct
        "expected_issue": "Should know WWII ended in 1945"
    },
    {
        "name": "Multiple Valid Answers",
        "question": "Which of these is a prime number?",
        "options": ["2", "4", "6", "8"],
        "correct_index": 0, 
        "expected_issue": "Should warn that all options are prime numbers"
    },
    {
        "name": "Ambiguous Question",
        "question": "What is the best programming language?",
        "options": ["Python", "Java", "C++", "JavaScript"],
        "correct_index": 0,
        "expected_issue": "Should warn about subjective/opinion-based question"
    },
]


def main() -> int:
    """Run red team tests with real LLM verification."""
    
    print("=" * 80)
    print("RED TEAM QUIZ VERIFICATION TEST - REAL LLM")
    print("=" * 80)
    print()
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY environment variable not set!")
        print()
        print("To run this test:")
        print("  1. Get your OpenAI API key from platform.openai.com")
        print("  2. Set environment variable:")
        print("     export OPENAI_API_KEY='your-key-here'")
        print("  3. Run this script again")
        return 1
    
    print(f"✓ OpenAI API key found: {api_key[:8]}...{api_key[-4:]}")
    print()
    
    # Create real LLM function
    try:
        llm_func = create_real_llm_function()
        verification_system.set_llm_function(llm_func)
        print("✓ Real LLM function configured")
        print()
    except Exception as e:
        print(f"❌ ERROR setting up LLM function: {e}")
        return 1
    
    # Extract just the questions for batch verification
    questions = [
        {k: v for k, v in q.items() if k not in ['name', 'expected_issue']}
        for q in RED_TEAM_QUESTIONS
    ]
    
    # Step 1: Structural verification (no LLM needed)
    print("=" * 80)
    print("STEP 1: STRUCTURAL VERIFICATION (verify_quiz_batch)")
    print("=" * 80)
    print("This checks format, structure, and basic quality without LLM.")
    print()
    
    results, overall_conf = verification_system.verify_quiz_batch(questions)
    print(f"Overall structural confidence: {overall_conf:.1%}")
    print()
    
    for idx, (test_case, result) in enumerate(zip(RED_TEAM_QUESTIONS, results), start=1):
        icon = "⚠️" if result.needs_review else "✓"
        print(f"[{idx}] {icon} {test_case['name']}")
        print(f"    Question: {test_case['question']}")
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
    
    # Step 2: Factual verification with REAL LLM
    print()
    print("=" * 80)
    print("STEP 2: FACTUAL VERIFICATION WITH REAL LLM (verify_quiz_answer_correctness)")
    print("=" * 80)
    print("This uses OpenAI API to verify if marked answers are actually correct.")
    print()
    
    answer_results = []
    
    for idx, (test_case, question) in enumerate(zip(RED_TEAM_QUESTIONS, questions), start=1):
        print(f"\n[{idx}] Verifying: {test_case['name']}")
        print(f"    Expected issue: {test_case['expected_issue']}")
        print(f"    Calling OpenAI API...")
        
        answer_result = verification_system.verify_quiz_answer_correctness(question)
        answer_results.append(answer_result)
        
        icon = "⚠️" if answer_result.needs_review else "✓"
        print(f"    {icon} Confidence: {answer_result.confidence:.1%}")
        
        if answer_result.issues:
            print("    ❌ Issues detected:")
            for issue in answer_result.issues:
                print(f"       • {issue}")
        
        if answer_result.warnings:
            print("    ⚠️  Warnings:")
            for warning in answer_result.warnings:
                print(f"       • {warning}")
        
        if not answer_result.issues and not answer_result.warnings:
            print("    ✓ No issues detected")
    
    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    flagged_count = sum(1 for r in answer_results if r.needs_review)
    avg_confidence = sum(r.confidence for r in answer_results) / len(answer_results)
    
    print(f"Total questions tested: {len(RED_TEAM_QUESTIONS)}")
    print(f"Questions flagged for review: {flagged_count} / {len(RED_TEAM_QUESTIONS)}")
    print(f"Average LLM confidence: {avg_confidence:.1%}")
    print()
    
    if flagged_count >= len(RED_TEAM_QUESTIONS) * 0.7:  # 70% threshold
        print("✅ VERIFICATION SYSTEM WORKING WELL!")
        print(f"   Detected issues in {flagged_count} out of {len(RED_TEAM_QUESTIONS)} flawed questions.")
    else:
        print("⚠️  VERIFICATION SYSTEM MISSED SOME ISSUES")
        print(f"   Only flagged {flagged_count} out of {len(RED_TEAM_QUESTIONS)} flawed questions.")
    
    print()
    print("=" * 80)
    
    # Create verification report
    report_path = verification_system.create_review_report(
        answer_results,
        output_path="red_team_verification_report_real_llm.txt"
    )
    print(f"\n📄 Full verification report saved to: {report_path}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

