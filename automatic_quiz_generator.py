"""
Automatic Quiz Generator from Transcripts

Reads transcript files (VTT format) from the Transcripts folder,
generates multiple-choice quiz questions using an LLM,
and creates a Canvas quiz with those questions.
"""

import os
import re
import json
import pathlib
import argparse
import logging
from typing import Dict, Any, List, Optional

import requests

# Import shared utilities from organize_project
import organize_project
import verification_system

# Module-level variables (can be overridden by app.py)
CANVAS_BASE_URL = organize_project.CANVAS_BASE_URL
CANVAS_TOKEN = organize_project.CANVAS_TOKEN
OPENAI_API_KEY = organize_project.OPENAI_API_KEY

# Set up verification system with LLM function
verification_system.set_llm_function(organize_project.call_llm)


def canvas_get(path: str, params: Dict[str, Any] = None) -> Any:
    """Helper to call Canvas GET endpoints."""
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
    resp = requests.get(f"{CANVAS_BASE_URL}{path}", headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def canvas_post(path: str, data: Dict[str, Any]) -> Any:
    """Helper to call Canvas POST endpoints."""
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
    resp = requests.post(f"{CANVAS_BASE_URL}{path}", headers=headers, data=data)
    resp.raise_for_status()
    return resp.json()


def canvas_put(path: str, data: Dict[str, Any]) -> Any:
    """Helper to call Canvas PUT endpoints."""
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
    resp = requests.put(f"{CANVAS_BASE_URL}{path}", headers=headers, data=data)
    resp.raise_for_status()
    return resp.json()


def call_llm(prompt: str) -> str:
    """Call LLM with the module's API key."""
    return organize_project.call_llm(prompt)

logger = logging.getLogger(__name__)


def extract_text_from_vtt(vtt_path: str) -> str:
    """
    Extract text content from a WebVTT (VTT) transcript file.
    
    Args:
        vtt_path: Path to the VTT file
        
    Returns:
        Extracted text content as a string
    """
    try:
        content = pathlib.Path(vtt_path).read_text(encoding="utf-8", errors="ignore")
        # Remove WEBVTT header and timestamp lines
        lines = content.split("\n")
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines, WEBVTT header, and timestamp lines
            if not line:
                continue
            if line == "WEBVTT":
                continue
            # Skip timestamp lines (format: 00:00:00.000 --> 00:00:00.000)
            if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}", line):
                continue
            # Skip standalone numbers (cue sequence numbers)
            if line.isdigit():
                continue
            # This should be actual transcript text
            text_lines.append(line)
        
        text = " ".join(text_lines)
        logger.info(
            f"Extracted {len(text)} characters from VTT: "
            f"{pathlib.Path(vtt_path).name}"
        )
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {vtt_path}: {e}", exc_info=True)
        return ""


def collect_transcript_text(transcripts_folder: str) -> str:
    """
    Collect text from all transcript files in the specified folder.
    
    Args:
        transcripts_folder: Path to folder containing transcript files
        
    Returns:
        Concatenated text from all transcripts
    """
    logger.info(f"Collecting transcripts from: {transcripts_folder}")
    transcripts_dir = pathlib.Path(transcripts_folder)
    
    if not transcripts_dir.exists():
        logger.warning(f"Transcripts folder does not exist: {transcripts_folder}")
        return ""
    
    all_text_chunks: List[str] = []
    
    # Find all VTT files
    vtt_files = sorted(transcripts_dir.glob("*.vtt"))
    logger.info(f"Found {len(vtt_files)} VTT files")
    
    for vtt_file in vtt_files:
        logger.info(f"Processing transcript: {vtt_file.name}")
        text = extract_text_from_vtt(str(vtt_file))
        if text:
            all_text_chunks.append(f"=== TRANSCRIPT: {vtt_file.name} ===\n{text}\n")
    
    if not all_text_chunks:
        logger.warning("No transcript text extracted")
        return ""
    
    combined_text = "\n\n".join(all_text_chunks)
    logger.info(
        f"Collected {len(all_text_chunks)} transcripts with "
        f"{len(combined_text)} total characters"
    )
    return combined_text


def generate_quiz_questions(
    transcript_text: str, num_questions: int = 10
) -> List[Dict[str, Any]]:
    """
    Use LLM to generate multiple-choice quiz questions from transcript text.
    
    Args:
        transcript_text: The combined text from all transcripts
        num_questions: Number of questions to generate
        
    Returns:
        List of question dictionaries with keys: question, options, correct_index
    """
    # Truncate text if too long (keep first 15000 chars to avoid token limits)
    text_sample = transcript_text[:15000]
    if len(transcript_text) > 15000:
        logger.warning(
            f"Transcript text truncated from {len(transcript_text)} to "
            f"{len(text_sample)} characters"
        )
    
    prompt = f"""
You are generating multiple-choice quiz questions based on course lecture transcripts.

Generate exactly {num_questions} multiple-choice questions about the content in these transcripts.
Each question should:
- Be clear and test understanding of key concepts discussed
- Have exactly 4 answer options (A, B, C, D)
- Have exactly ONE correct answer
- Be based on actual content from the transcripts

Return a JSON array of questions. Each question should have this structure:
{{
  "question": "The question text here",
  "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
  "correct_index": 0
}}

Where correct_index is 0, 1, 2, or 3 indicating which option (A, B, C, or D) is correct.

Return ONLY valid JSON, no other text before or after.

Transcripts:
{text_sample}
"""

    logger.info(f"Calling LLM to generate {num_questions} quiz questions")
    raw_response = call_llm(prompt)
    
    # Try to extract JSON from response (might have markdown code blocks)
    json_text = raw_response.strip()
    if json_text.startswith("```"):
        # Remove markdown code blocks
        json_text = re.sub(r"^```(?:json)?\s*", "", json_text)
        json_text = re.sub(r"\s*```$", "", json_text)
        json_text = json_text.strip()
    
    try:
        questions = json.loads(json_text)
        if not isinstance(questions, list):
            logger.error("LLM returned non-list response")
            return []
        
        # Validate question structure
        valid_questions = []
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                logger.warning(f"Question {i} is not a dict, skipping")
                continue
            if "question" not in q or "options" not in q or "correct_index" not in q:
                logger.warning(f"Question {i} missing required fields, skipping")
                continue
            if not isinstance(q["options"], list) or len(q["options"]) != 4:
                logger.warning(f"Question {i} does not have exactly 4 options, skipping")
                continue
            if q["correct_index"] not in [0, 1, 2, 3]:
                logger.warning(f"Question {i} has invalid correct_index, skipping")
                continue
            valid_questions.append(q)
        
        logger.info(f"Generated {len(valid_questions)} valid questions")
        return valid_questions
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Raw response: {raw_response[:500]}")
        return []


def create_canvas_quiz(
    course_id: int,
    quiz_title: str,
    quiz_description: str = "",
    points_possible: int = 10,
    unlock_at: Optional[str] = None,
    due_at: Optional[str] = None,
    lock_at: Optional[str] = None,
    hide_correct_answers: bool = True,
) -> Dict[str, Any]:
    """
    Create a new quiz in Canvas.
    
    Args:
        course_id: Canvas course ID
        quiz_title: Title for the quiz
        quiz_description: Optional description for the quiz
        points_possible: Total points for the quiz
        unlock_at: ISO datetime string when quiz becomes available (optional)
        due_at: ISO datetime string when quiz is due (optional)
        lock_at: ISO datetime string when quiz locks (optional)
        hide_correct_answers: If True, don't show correct answers to students
        
    Returns:
        Canvas quiz object
    """
    data = {
        "quiz[title]": quiz_title,
        "quiz[description]": quiz_description,
        "quiz[quiz_type]": "assignment",
        "quiz[published]": "false",  # Start unpublished, publish after adding questions
        "quiz[points_possible]": points_possible,
        "quiz[show_correct_answers]": "false" if hide_correct_answers else "true",
        "quiz[allowed_attempts]": -1,  # -1 means unlimited attempts
    }
    
    # Add dates if provided
    if unlock_at:
        data["quiz[unlock_at]"] = unlock_at
        logger.info(f"Quiz will be available from: {unlock_at}")
    
    if due_at:
        data["quiz[due_at]"] = due_at
        logger.info(f"Quiz due date: {due_at}")
    
    if lock_at:
        data["quiz[lock_at]"] = lock_at
        logger.info(f"Quiz will lock at: {lock_at}")
    
    logger.info(f"Creating Canvas quiz: {quiz_title} ({points_possible} pts)")
    logger.debug(f"Quiz creation data: {data}")
    
    quiz = canvas_post(f"/api/v1/courses/{course_id}/quizzes", data=data)
    
    logger.info(f"Created quiz with ID: {quiz.get('id')}")
    logger.info(f"Quiz URL: {CANVAS_BASE_URL}/courses/{course_id}/quizzes/{quiz.get('id')}")
    
    # Log what Canvas returned for dates
    if quiz.get('unlock_at'):
        logger.info(f"Canvas confirmed unlock_at: {quiz.get('unlock_at')}")
    if quiz.get('due_at'):
        logger.info(f"Canvas confirmed due_at: {quiz.get('due_at')}")
    if quiz.get('lock_at'):
        logger.info(f"Canvas confirmed lock_at: {quiz.get('lock_at')}")
    
    return quiz


def add_question_to_quiz(
    course_id: int, quiz_id: int, question_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add a multiple-choice question to a Canvas quiz.
    
    Args:
        course_id: Canvas course ID
        quiz_id: Canvas quiz ID
        question_data: Dict with keys: question, options, correct_index
        
    Returns:
        Canvas question object
    """
    question_text = question_data["question"]
    options = question_data["options"]
    correct_index = question_data["correct_index"]
    
    # Build question payload with answers
    # Canvas API expects: question[answers][i][answer_text] and question[answers][i][answer_weight]
    # Get points from question_data or default to 1
    points = question_data.get("points", 1)
    
    question_payload = {
        "question[question_name]": question_text[:80],  # Canvas limits name length
        "question[question_text]": question_text,
        "question[question_type]": "multiple_choice_question",
        "question[points_possible]": points,
    }
    
    # Add answer options - one answer with weight=100 (correct), others with weight=0
    for i, option_text in enumerate(options):
        question_payload[f"question[answers][{i}][answer_text]"] = option_text
        question_payload[f"question[answers][{i}][answer_weight]"] = (
            100 if i == correct_index else 0
        )
    
    logger.debug(f"Adding question to quiz {quiz_id}: {question_text[:50]}...")
    logger.debug(f"Question payload keys: {list(question_payload.keys())}")
    
    question = canvas_post(
        f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions", data=question_payload
    )
    return question


def publish_quiz(course_id: int, quiz_id: int) -> Dict[str, Any]:
    """
    Publish a Canvas quiz.
    
    Args:
        course_id: Canvas course ID
        quiz_id: Canvas quiz ID
        
    Returns:
        Updated quiz object
    """
    data = {"quiz[published]": "true"}
    logger.info(f"Publishing quiz {quiz_id}")
    quiz = canvas_put(f"/api/v1/courses/{course_id}/quizzes/{quiz_id}", data=data)
    return quiz


def generate_quiz_from_transcripts(
    course_id: int,
    transcripts_folder: str = "Transcripts",
    quiz_title: str = "Auto-Generated Quiz from Transcripts",
    num_questions: int = 10,
    points_per_question: int = 1,
    publish: bool = False,
    dry_run: bool = False,
    unlock_at: Optional[str] = None,
    due_at: Optional[str] = None,
    lock_at: Optional[str] = None,
    hide_correct_answers: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Main function: Generate quiz from transcripts and create in Canvas.
    
    Args:
        course_id: Canvas course ID
        transcripts_folder: Path to folder containing transcript files
        quiz_title: Title for the generated quiz
        num_questions: Number of questions to generate
        points_per_question: Points for each question (default: 1)
        publish: Whether to publish the quiz immediately
        dry_run: If True, don't create quiz in Canvas, just show questions
        unlock_at: ISO datetime when quiz becomes available (e.g., "2024-11-18T00:00:00Z")
        due_at: ISO datetime when quiz is due (e.g., "2024-11-20T23:59:00Z")
        lock_at: ISO datetime when quiz locks (e.g., "2024-11-20T23:59:00Z")
        hide_correct_answers: If True, don't show correct answers to students (default: True)
        
    Returns:
        Dictionary with quiz info and generated questions, or None if dry_run
    """
    logger.info("Starting automatic quiz generation from transcripts")
    
    # Step 1: Collect transcript text
    transcript_text = collect_transcript_text(transcripts_folder)
    if not transcript_text:
        logger.error("No transcript text collected. Cannot generate quiz.")
        return None
    
    # Step 2: Generate questions using LLM
    questions = generate_quiz_questions(transcript_text, num_questions)
    if not questions:
        logger.error("No questions generated. Cannot create quiz.")
        return None
    
    # Step 2.5: VERIFY QUESTIONS (Safety Layer)
    print(f"\n🔍 Verifying {len(questions)} generated questions...")
    verification_results, overall_confidence = verification_system.verify_quiz_batch(questions)
    
    print(f"\n📊 Verification Summary:")
    print(f"   Overall Confidence: {overall_confidence:.1%}")
    
    needs_review = [r for r in verification_results if r.needs_review]
    if needs_review:
        print(f"   ⚠️  {len(needs_review)} questions need human review")
    else:
        print(f"   ✓ All questions passed verification")
    
    # Display generated questions with confidence scores
    print(f"\n=== Generated {len(questions)} Quiz Questions ===\n")
    for i, (q, v_result) in enumerate(zip(questions, verification_results), 1):
        confidence_icon = "✓" if v_result.confidence >= 0.75 else "⚠️"
        print(f"Question {i} [{confidence_icon} {v_result.confidence:.0%}]: {q['question']}")
        for j, option in enumerate(q["options"]):
            marker = "✓" if j == q["correct_index"] else " "
            print(f"  {marker} {chr(65+j)}. {option}")
        
        if v_result.issues:
            print(f"  ❌ ISSUES: {', '.join(v_result.issues)}")
        if v_result.warnings:
            print(f"  ⚠️  WARNINGS: {', '.join(v_result.warnings)}")
        print()
    
    # Warn if overall confidence is low
    if overall_confidence < 0.75:
        print("\n" + "="*60)
        print("⚠️  WARNING: Low Confidence Quiz")
        print("="*60)
        print(f"Overall confidence is {overall_confidence:.1%} (below 75% threshold)")
        print("RECOMMENDATION: Review questions before publishing")
        print("="*60 + "\n")
    
    if dry_run:
        print("\n[DRY_RUN=True] Not creating quiz in Canvas.")
        return {"questions": questions, "quiz": None}
    
    # Step 3: Create Canvas quiz
    if not CANVAS_TOKEN:
        logger.error("CANVAS_TOKEN not set. Cannot create Canvas quiz.")
        return {"questions": questions, "quiz": None}
    
    # Calculate total points
    total_points = len(questions) * points_per_question
    
    quiz_description = (
        f"This quiz was automatically generated from course lecture transcripts. "
        f"It contains {len(questions)} multiple-choice questions worth "
        f"{points_per_question} point(s) each for a total of {total_points} points."
    )
    
    # Log quiz settings for debugging
    print(f"\n=== Quiz Settings ===")
    print(f"Title: {quiz_title}")
    print(f"Total Points: {total_points} ({num_questions} questions × {points_per_question} pts)")
    print(f"Available From: {unlock_at or 'Not set'}")
    print(f"Due Date: {due_at or 'Not set'}")
    print(f"Lock Date: {lock_at or 'Not set'}")
    print(f"Hide Correct Answers: {hide_correct_answers}")
    print(f"Publish: {publish}")
    print()
    
    quiz = create_canvas_quiz(
        course_id,
        quiz_title,
        quiz_description,
        points_possible=total_points,
        unlock_at=unlock_at,
        due_at=due_at,
        lock_at=lock_at,
        hide_correct_answers=hide_correct_answers,
    )
    quiz_id = quiz["id"]
    
    # Step 4: Add questions to quiz
    logger.info(f"Adding {len(questions)} questions to quiz {quiz_id}")
    added_questions = []
    
    # Only add high-confidence questions, or all if user acknowledges risk
    questions_to_add = questions
    if overall_confidence < 0.75:
        print("\n⚠️  Some questions have low confidence.")
        print("You may want to review them before adding to Canvas.")
        # In production, could prompt user here
    
    for i, question_data in enumerate(questions_to_add, 1):
        try:
            # Add points info to question data
            question_data["points"] = points_per_question
            canvas_question = add_question_to_quiz(course_id, quiz_id, question_data)
            added_questions.append(canvas_question)
            logger.info(f"Added question {i}/{len(questions)}")
        except Exception as e:
            logger.error(f"Failed to add question {i}: {e}", exc_info=True)
    
    # Save verification report
    if verification_results:
        report_path = verification_system.create_review_report(
            verification_results,
            output_path=f"quiz_verification_{quiz_id}.txt"
        )
        print(f"\n📄 Verification report saved: {report_path}")
    
    # Step 5: Publish quiz if requested
    if publish and added_questions:
        try:
            publish_quiz(course_id, quiz_id)
            print(f"\n✓ Quiz '{quiz_title}' created and published in Canvas!")
        except Exception as e:
            logger.error(f"Failed to publish quiz: {e}", exc_info=True)
            print(f"\n✓ Quiz '{quiz_title}' created but not published (error occurred)")
    else:
        print(f"\n✓ Quiz '{quiz_title}' created in Canvas (unpublished)")
    
    return {
        "quiz": quiz,
        "questions": questions,
        "added_questions": added_questions,
        "verification_results": verification_results,
        "overall_confidence": overall_confidence,
    }


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    parser = argparse.ArgumentParser(
        description="Generate Canvas quiz from transcript files"
    )
    parser.add_argument(
        "--course-id",
        type=int,
        default=175906,
        help="Canvas course ID (default: 175906)",
    )
    parser.add_argument(
        "--transcripts-folder",
        type=str,
        default="Transcripts",
        help="Path to folder containing transcript VTT files (default: Transcripts)",
    )
    parser.add_argument(
        "--quiz-title",
        type=str,
        default="Quiz",
        help="Title for the generated quiz",
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        default=10,
        help="Number of questions to generate (default: 10)",
    )
    parser.add_argument(
        "--points-per-question",
        type=int,
        default=1,
        help="Points for each question (default: 1)",
    )
    parser.add_argument(
        "--unlock-at",
        type=str,
        help="When quiz becomes available (ISO format: YYYY-MM-DDTHH:MM:SSZ)",
    )
    parser.add_argument(
        "--due-at",
        type=str,
        help="When quiz is due (ISO format: YYYY-MM-DDTHH:MM:SSZ)",
    )
    parser.add_argument(
        "--lock-at",
        type=str,
        help="When quiz locks (ISO format: YYYY-MM-DDTHH:MM:SSZ)",
    )
    parser.add_argument(
        "--show-correct-answers",
        action="store_true",
        help="Show correct answers to students (default: hide answers)",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish the quiz immediately after creation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate questions but don't create quiz in Canvas",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    if not CANVAS_TOKEN and not args.dry_run:
        raise SystemExit("Set CANVAS_TOKEN env var (or use --dry-run to preview)")
    
    result = generate_quiz_from_transcripts(
        course_id=args.course_id,
        transcripts_folder=args.transcripts_folder,
        quiz_title=args.quiz_title,
        num_questions=args.num_questions,
        points_per_question=args.points_per_question,
        publish=args.publish,
        dry_run=args.dry_run,
        unlock_at=args.unlock_at,
        due_at=args.due_at,
        lock_at=args.lock_at,
        hide_correct_answers=not args.show_correct_answers,
    )
    
    if result:
        logger.info("Quiz generation completed successfully")
    else:
        logger.error("Quiz generation failed")
        exit(1)

