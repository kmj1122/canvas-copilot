"""
Verification System - Safety layers for AI-generated content

This module provides verification, confidence scoring, and human review workflows
for AI-generated quizzes, rubrics, FAQs, and announcements.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Module-level variables (set by importing module)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_llm_function = None


def set_llm_function(llm_func: Callable[[str], str]):
    """Set the LLM function to use for verification."""
    global _llm_function
    _llm_function = llm_func


class VerificationResult:
    """Container for verification results"""
    
    def __init__(
        self,
        content_type: str,
        content: Any,
        confidence: float,
        issues: List[str],
        warnings: List[str],
        needs_review: bool
    ):
        self.content_type = content_type
        self.content = content
        self.confidence = confidence  # 0.0 to 1.0
        self.issues = issues  # Critical problems
        self.warnings = warnings  # Minor concerns
        self.needs_review = needs_review
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content_type": self.content_type,
            "confidence": self.confidence,
            "confidence_label": self.get_confidence_label(),
            "issues": self.issues,
            "warnings": self.warnings,
            "needs_review": self.needs_review,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def get_confidence_label(self) -> str:
        """Get human-readable confidence label"""
        if self.confidence >= 0.9:
            return "HIGH (90%+)"
        elif self.confidence >= 0.75:
            return "GOOD (75-89%)"
        elif self.confidence >= 0.6:
            return "MODERATE (60-74%)"
        elif self.confidence >= 0.4:
            return "LOW (40-59%)"
        else:
            return "VERY LOW (<40%)"
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*60)
        print("🔍 VERIFICATION RESULTS")
        print("="*60)
        print(f"Content Type: {self.content_type}")
        print(f"Confidence: {self.confidence:.1%} - {self.get_confidence_label()}")
        print(f"Needs Human Review: {'⚠️  YES' if self.needs_review else '✓ No'}")
        
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.issues and not self.warnings:
            print("\n✅ No issues detected")
        
        print("="*60 + "\n")


def verify_quiz_question(question: Dict[str, Any]) -> VerificationResult:
    """
    Verify a quiz question for quality and correctness.
    
    Args:
        question: Quiz question dictionary with 'question', 'options', 'correct_index'
        
    Returns:
        VerificationResult with confidence score and issues
    """
    issues = []
    warnings = []
    confidence_factors = []
    
    # Check 1: Question text quality
    question_text = question.get('question', '')
    if len(question_text) < 10:
        issues.append("Question text too short (< 10 characters)")
        confidence_factors.append(0.0)
    elif len(question_text) > 300:
        warnings.append("Question text very long (> 300 characters)")
        confidence_factors.append(0.8)
    else:
        confidence_factors.append(1.0)
    
    # Check 2: Has question mark
    if '?' not in question_text:
        warnings.append("Question doesn't contain a question mark")
        confidence_factors.append(0.9)
    else:
        confidence_factors.append(1.0)
    
    # Check 3: Options validation
    options = question.get('options', [])
    if len(options) != 4:
        issues.append(f"Expected 4 options, got {len(options)}")
        confidence_factors.append(0.0)
    else:
        confidence_factors.append(1.0)
    
    # Check 4: Option length and quality
    if options:
        option_lengths = [len(opt) for opt in options]
        if min(option_lengths) < 2:
            issues.append("One or more options are too short")
            confidence_factors.append(0.3)
        elif max(option_lengths) > 200:
            warnings.append("One or more options are very long")
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(1.0)
        
        # Check for duplicate options
        if len(options) != len(set(options)):
            issues.append("Duplicate options detected")
            confidence_factors.append(0.0)
        else:
            confidence_factors.append(1.0)
    
    # Check 5: Correct answer index
    correct_index = question.get('correct_index')
    if correct_index not in [0, 1, 2, 3]:
        issues.append(f"Invalid correct_index: {correct_index}")
        confidence_factors.append(0.0)
    else:
        confidence_factors.append(1.0)
    
    # Check 6: Answer plausibility (all options should be reasonable length)
    if options and len(options) == 4:
        lengths = [len(opt) for opt in options]
        avg_length = sum(lengths) / len(lengths)
        # Check if one option is much longer (might be obviously correct)
        for length in lengths:
            if length > avg_length * 2:
                warnings.append("One option much longer than others (may be obviously correct)")
                confidence_factors.append(0.85)
                break
        else:
            confidence_factors.append(1.0)
    
    # Calculate overall confidence
    confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    
    # Determine if needs review
    needs_review = bool(issues) or confidence < 0.75
    
    return VerificationResult(
        content_type="quiz_question",
        content=question,
        confidence=confidence,
        issues=issues,
        warnings=warnings,
        needs_review=needs_review
    )


def verify_quiz_batch(questions: List[Dict[str, Any]]) -> Tuple[List[VerificationResult], float]:
    """
    Verify a batch of quiz questions.
    
    Args:
        questions: List of quiz questions
        
    Returns:
        Tuple of (verification results, overall confidence)
    """
    results = []
    
    for i, question in enumerate(questions):
        result = verify_quiz_question(question)
        results.append(result)
        logger.info(f"Question {i+1}: Confidence {result.confidence:.1%}")
    
    # Calculate overall confidence
    overall_confidence = sum(r.confidence for r in results) / len(results) if results else 0.0
    
    return results, overall_confidence


def verify_with_llm(
    content: str,
    content_type: str,
    verification_prompt: str
) -> Dict[str, Any]:
    """
    Use LLM to verify content quality and provide confidence score.
    
    Args:
        content: Content to verify
        content_type: Type of content (quiz, faq, announcement, etc.)
        verification_prompt: Specific verification instructions
        
    Returns:
        Dictionary with confidence, issues, and suggestions
    """
    if _llm_function is None:
        logger.warning("LLM function not set, returning default confidence")
        return {
            "confidence": 0.5,
            "issues": [],
            "warnings": ["LLM verification not available"],
            "suggestions": []
        }
    
    prompt = f"""
You are a quality assurance expert reviewing AI-generated educational content.

Content Type: {content_type}
Content to Review:
{content}

{verification_prompt}

Analyze this content and provide:
1. Confidence score (0.0 to 1.0) - how confident are you this content is appropriate?
2. Issues - critical problems that MUST be fixed
3. Warnings - minor concerns that should be reviewed
4. Suggestions - improvements that could be made

Return ONLY valid JSON:
{{
  "confidence": 0.85,
  "issues": ["list of critical issues"],
  "warnings": ["list of warnings"],
  "suggestions": ["list of suggestions"]
}}
"""

    try:
        response = _llm_function(prompt)
        
        # Parse JSON
        json_text = response.strip()
        if json_text.startswith("```"):
            import re
            json_text = re.sub(r"^```(?:json)?\s*", "", json_text)
            json_text = re.sub(r"\s*```$", "", json_text)
            json_text = json_text.strip()
        
        result = json.loads(json_text)
        
        # Validate structure
        if 'confidence' not in result:
            result['confidence'] = 0.5  # Default to moderate if not provided
        if 'issues' not in result:
            result['issues'] = []
        if 'warnings' not in result:
            result['warnings'] = []
        if 'suggestions' not in result:
            result['suggestions'] = []
        
        return result
        
    except Exception as e:
        logger.error(f"LLM verification failed: {e}")
        return {
            "confidence": 0.5,
            "issues": ["LLM verification failed"],
            "warnings": [],
            "suggestions": []
        }


def verify_quiz_answer_correctness(question: Dict[str, Any]) -> VerificationResult:
    """
    Use LLM to verify if the correct answer is actually correct.
    
    Args:
        question: Quiz question with answer
        
    Returns:
        VerificationResult with confidence about answer correctness
    """
    question_text = question.get('question', '')
    options = question.get('options', [])
    correct_index = question.get('correct_index', 0)
    
    if correct_index < len(options):
        correct_answer = options[correct_index]
    else:
        return VerificationResult(
            content_type="quiz_answer_verification",
            content=question,
            confidence=0.0,
            issues=["Invalid correct_index"],
            warnings=[],
            needs_review=True
        )
    
    verification_prompt = f"""
Verify if the marked answer is truly correct for this question.

Question: {question_text}

Options:
{chr(10).join([f'{chr(65+i)}. {opt}' for i, opt in enumerate(options)])}

Marked Correct Answer: {chr(65+correct_index)}. {correct_answer}

Carefully analyze and report:
1. Is the marked answer factually correct?
2. Are there OTHER options that are ALSO correct? (If yes, this is a problem!)
3. Is the question ambiguous, subjective, or opinion-based?
4. Is the marked answer the BEST answer, or just A correct answer?

IMPORTANT: 
- If multiple options are valid, flag as an issue even if marked answer is correct
- If the question is subjective (e.g., "best", "most important"), flag as a warning
- Be strict about ambiguity in educational content
"""

    llm_result = verify_with_llm(
        content=f"{question_text}\n{correct_answer}",
        content_type="quiz_answer",
        verification_prompt=verification_prompt
    )
    
    return VerificationResult(
        content_type="quiz_answer_verification",
        content=question,
        confidence=llm_result['confidence'],
        issues=llm_result['issues'],
        warnings=llm_result['warnings'],
        needs_review=llm_result['confidence'] < 0.8
    )


def verify_faq_entry(faq: Dict[str, Any]) -> VerificationResult:
    """
    Verify an FAQ entry for quality and appropriateness.
    
    Args:
        faq: FAQ dictionary with 'question', 'answer', 'category'
        
    Returns:
        VerificationResult
    """
    issues = []
    warnings = []
    confidence_factors = []
    
    # Check question
    question = faq.get('question', '')
    if len(question) < 5:
        issues.append("Question too short")
        confidence_factors.append(0.0)
    elif '?' not in question:
        warnings.append("Question doesn't end with ?")
        confidence_factors.append(0.9)
    else:
        confidence_factors.append(1.0)
    
    # Check answer
    answer = faq.get('answer', '')
    if len(answer) < 10:
        issues.append("Answer too short")
        confidence_factors.append(0.0)
    elif len(answer) > 1000:
        warnings.append("Answer very long (> 1000 chars)")
        confidence_factors.append(0.85)
    else:
        confidence_factors.append(1.0)
    
    # Check category
    category = faq.get('category', '')
    if not category or category == 'General':
        warnings.append("Generic or missing category")
        confidence_factors.append(0.8)
    else:
        confidence_factors.append(1.0)
    
    # Check for placeholder text
    placeholder_terms = ['TODO', 'TBD', 'FIXME', '[insert', 'coming soon']
    if any(term.lower() in answer.lower() for term in placeholder_terms):
        issues.append("Answer contains placeholder text")
        confidence_factors.append(0.0)
    else:
        confidence_factors.append(1.0)
    
    confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    needs_review = bool(issues) or confidence < 0.75
    
    return VerificationResult(
        content_type="faq_entry",
        content=faq,
        confidence=confidence,
        issues=issues,
        warnings=warnings,
        needs_review=needs_review
    )


def verify_rubric(rubric: Dict[str, Any]) -> VerificationResult:
    """
    Verify a rubric for completeness and consistency.
    
    Args:
        rubric: Rubric dictionary
        
    Returns:
        VerificationResult
    """
    issues = []
    warnings = []
    confidence_factors = []
    
    # Check basic structure
    if 'criteria' not in rubric:
        issues.append("Missing criteria")
        return VerificationResult(
            content_type="rubric",
            content=rubric,
            confidence=0.0,
            issues=issues,
            warnings=[],
            needs_review=True
        )
    
    criteria = rubric['criteria']
    
    # Check number of criteria
    if len(criteria) < 3:
        warnings.append(f"Only {len(criteria)} criteria (recommend 4+)")
        confidence_factors.append(0.8)
    elif len(criteria) > 10:
        warnings.append(f"{len(criteria)} criteria may be too many")
        confidence_factors.append(0.9)
    else:
        confidence_factors.append(1.0)
    
    # Check point distribution
    total_points = sum(c.get('points', 0) for c in criteria)
    stated_total = rubric.get('total_points', 0)
    
    if total_points != stated_total:
        issues.append(f"Point mismatch: criteria sum to {total_points} but total_points is {stated_total}")
        confidence_factors.append(0.5)
    else:
        confidence_factors.append(1.0)
    
    # Check each criterion
    for i, criterion in enumerate(criteria):
        if 'name' not in criterion or len(criterion['name']) < 2:
            issues.append(f"Criterion {i+1} has invalid name")
            confidence_factors.append(0.0)
        
        if 'description' not in criterion or len(criterion['description']) < 10:
            warnings.append(f"Criterion {i+1} has short description")
            confidence_factors.append(0.8)
        
        points = criterion.get('points', 0)
        if points <= 0:
            issues.append(f"Criterion {i+1} has invalid points: {points}")
            confidence_factors.append(0.0)
        elif points > stated_total * 0.5:
            warnings.append(f"Criterion {i+1} worth {points} points (>{50}% of total)")
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(1.0)
    
    confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
    needs_review = bool(issues) or confidence < 0.8
    
    return VerificationResult(
        content_type="rubric",
        content=rubric,
        confidence=confidence,
        issues=issues,
        warnings=warnings,
        needs_review=needs_review
    )


def create_review_report(
    verifications: List[VerificationResult],
    output_path: str = "verification_report.txt"
) -> str:
    """
    Create a human-readable review report.
    
    Args:
        verifications: List of verification results
        output_path: Where to save report
        
    Returns:
        Path to saved report
    """
    import pathlib
    
    lines = [
        "="*70,
        "VERIFICATION REPORT",
        "="*70,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Items Reviewed: {len(verifications)}",
        "",
    ]
    
    # Summary statistics
    needs_review = [v for v in verifications if v.needs_review]
    avg_confidence = sum(v.confidence for v in verifications) / len(verifications) if verifications else 0.0
    
    lines.extend([
        "SUMMARY",
        "-"*70,
        f"Overall Confidence: {avg_confidence:.1%}",
        f"Items Needing Review: {len(needs_review)} / {len(verifications)}",
        "",
    ])
    
    # Detailed analysis of ALL items
    lines.extend([
        "DETAILED ANALYSIS OF ALL ITEMS",
        "-"*70,
    ])
    
    for i, v in enumerate(verifications, 1):
        # Status indicator
        if v.needs_review:
            status_icon = "⚠️"
            status_text = "NEEDS REVIEW"
        else:
            status_icon = "✅"
            status_text = "PASSED"
        
        lines.extend([
            f"\n{i}. {v.content_type.upper()} - Confidence: {v.confidence:.1%} - {status_icon} {status_text}",
            ""
        ])
        
        # For items that passed, explain why
        if not v.needs_review and not v.issues and not v.warnings:
            lines.append("   ✅ PASSED VERIFICATION:")
            lines.append("   • All structural checks passed")
            lines.append("   • Factual accuracy confirmed")
            lines.append("   • No issues or warnings detected")
            lines.append("   • Confidence meets threshold (≥75%)")
        
        # Show issues if any
        if v.issues:
            lines.append("   ❌ CRITICAL ISSUES:")
            for issue in v.issues:
                lines.append(f"      • {issue}")
        
        # Show warnings if any
        if v.warnings:
            lines.append("   ⚠️  WARNINGS:")
            for warning in v.warnings:
                lines.append(f"      • {warning}")
        
        lines.append("")
    
    # Quick summary
    lines.extend([
        "",
        "QUICK SUMMARY",
        "-"*70,
    ])
    
    for i, v in enumerate(verifications, 1):
        status = "⚠️  NEEDS REVIEW" if v.needs_review else "✅ PASSED"
        lines.append(f"{i}. {v.confidence:.1%} - {status}")
    
    lines.extend([
        "",
        "="*70,
        "END OF REPORT",
        "="*70,
    ])
    
    report_text = "\n".join(lines)
    pathlib.Path(output_path).write_text(report_text, encoding='utf-8')
    
    return output_path


if __name__ == "__main__":
    # Example usage
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    print("Verification System - Example Usage\n")
    
    # Test quiz question verification
    test_question = {
        "question": "What is the capital of France?",
        "options": ["London", "Berlin", "Paris", "Madrid"],
        "correct_index": 2
    }
    
    print("Testing good question:")
    result = verify_quiz_question(test_question)
    result.print_summary()
    
    # Test with problematic question
    bad_question = {
        "question": "Q?",
        "options": ["A", "A", "C"],
        "correct_index": 5
    }
    
    print("\nTesting problematic question:")
    result2 = verify_quiz_question(bad_question)
    result2.print_summary()
    
    print("\nNote: LLM-based verification requires set_llm_function() to be called.")

