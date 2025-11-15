"""
FAQ Generator - Parse common student questions and generate FAQ document

This module analyzes student emails, forum posts, and other communications
to identify common questions and generate comprehensive FAQ documents.
"""

import os
import re
import json
import pathlib
import argparse
import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

import requests

# Import shared utilities
import organize_project
import verification_system

# Module-level variables
CANVAS_BASE_URL = organize_project.CANVAS_BASE_URL
CANVAS_TOKEN = organize_project.CANVAS_TOKEN
OPENAI_API_KEY = organize_project.OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Set LLM function for verification
verification_system.set_llm_function(organize_project.call_llm)


def extract_course_context_from_syllabus(syllabus_folder: str = "sllaybus") -> str:
    """
    Read syllabus files and extract course context for FAQ generation.
    
    Args:
        syllabus_folder: Path to folder containing syllabus files
        
    Returns:
        Extracted course context as string
    """
    logger.info(f"Reading syllabus files from: {syllabus_folder}")
    
    folder = pathlib.Path(syllabus_folder)
    if not folder.exists():
        logger.warning(f"Syllabus folder not found: {syllabus_folder}")
        return ""
    
    all_text = []
    
    # Read all syllabus files
    for file_path in sorted(folder.glob("*")):
        if file_path.is_file():
            logger.info(f"Reading syllabus: {file_path.name}")
            try:
                # Use the existing text extraction function from organize_project
                text = organize_project.extract_text_from_file(str(file_path))
                if text:
                    all_text.append(f"=== {file_path.name} ===\n{text}\n")
                    logger.debug(f"Extracted {len(text)} characters from {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to read syllabus file {file_path}: {e}")
    
    combined_text = "\n\n".join(all_text)
    logger.info(f"Extracted {len(combined_text)} total characters from syllabus files")
    
    if not combined_text:
        logger.warning("No text extracted from syllabus files")
        return ""
    
    # Use LLM to summarize key course information
    prompt = f"""
Read the following course syllabus and extract key information that would be helpful 
for generating FAQ answers. Focus on:

1. Course name and number
2. Course description and objectives
3. Key policies (attendance, late work, academic integrity)
4. Assignment types and grading breakdown
5. Important dates
6. Contact information and office hours
7. Required materials

Provide a concise summary (200-300 words) of the most important course information.

Syllabus:
{combined_text[:8000]}
"""
    
    try:
        logger.info("Extracting course context using LLM")
        context = organize_project.call_llm(prompt)
        logger.info(f"Extracted course context ({len(context)} characters)")
        return context
    except Exception as e:
        logger.error(f"Failed to extract course context: {e}")
        # Return raw text (truncated) as fallback
        return combined_text[:2000]


def extract_questions_from_text(text: str) -> List[str]:
    """
    Extract potential questions from text (emails, forum posts, etc.).
    
    Args:
        text: Raw text containing questions
        
    Returns:
        List of extracted question strings
    """
    questions = []
    
    # Split into lines
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for question marks
        if '?' in line:
            # Extract sentences with question marks
            sentences = re.split(r'[.!]', line)
            for sentence in sentences:
                if '?' in sentence:
                    question = sentence.strip()
                    # Clean up email artifacts
                    question = re.sub(r'^(Re:|Fwd:|Subject:)', '', question, flags=re.IGNORECASE)
                    question = question.strip()
                    if len(question) > 10:  # Minimum length filter
                        questions.append(question)
        
        # Also look for phrases indicating questions
        question_indicators = [
            r'(how (do|can|should|would|does)|what (is|are|do)|when (is|are|do)|where (is|are|do)|why (is|are|do)|which (is|are|do))',
            r'(can (you|i|we)|could (you|i|we)|should (i|we)|would (you|i|we))',
            r'(is (there|it)|are (there|they))',
        ]
        
        for pattern in question_indicators:
            if re.search(pattern, line, re.IGNORECASE):
                # This line likely contains a question
                if len(line) > 10 and len(line) < 300:
                    questions.append(line)
                    break
    
    return questions


def collect_questions_from_file(file_path: str) -> List[str]:
    """
    Collect questions from a text file.
    
    Args:
        file_path: Path to text file containing emails/posts
        
    Returns:
        List of questions
    """
    logger.info(f"Collecting questions from: {file_path}")
    
    try:
        text = pathlib.Path(file_path).read_text(encoding='utf-8', errors='ignore')
        questions = extract_questions_from_text(text)
        logger.info(f"Extracted {len(questions)} potential questions from {file_path}")
        return questions
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}", exc_info=True)
        return []


def collect_questions_from_folder(folder_path: str) -> List[str]:
    """
    Collect questions from all text files in a folder.
    
    Args:
        folder_path: Path to folder containing text files
        
    Returns:
        List of all questions
    """
    logger.info(f"Collecting questions from folder: {folder_path}")
    
    folder = pathlib.Path(folder_path)
    if not folder.exists():
        logger.warning(f"Folder does not exist: {folder_path}")
        return []
    
    all_questions = []
    
    # Process all .txt files
    for file_path in sorted(folder.glob("*.txt")):
        questions = collect_questions_from_file(str(file_path))
        all_questions.extend(questions)
    
    logger.info(f"Collected {len(all_questions)} total questions from folder")
    return all_questions


def cluster_similar_questions(questions: List[str]) -> Dict[str, List[str]]:
    """
    Group similar questions together using simple text similarity.
    
    Args:
        questions: List of question strings
        
    Returns:
        Dictionary mapping representative questions to similar variants
    """
    # Simple approach: group by key words
    clusters = {}
    
    for question in questions:
        # Normalize
        q_lower = question.lower()
        
        # Extract key terms (simple approach)
        key_terms = set(re.findall(r'\b\w{4,}\b', q_lower))
        
        # Find best matching cluster
        best_match = None
        best_overlap = 0
        
        for rep_question in clusters:
            rep_lower = rep_question.lower()
            rep_terms = set(re.findall(r'\b\w{4,}\b', rep_lower))
            
            overlap = len(key_terms & rep_terms)
            if overlap > best_overlap and overlap >= 2:
                best_overlap = overlap
                best_match = rep_question
        
        if best_match:
            clusters[best_match].append(question)
        else:
            clusters[question] = [question]
    
    return clusters


def generate_faq_with_llm(
    questions: List[str],
    course_context: str = "",
    max_faqs: int = 20
) -> List[Dict[str, str]]:
    """
    Use LLM to generate FAQ entries from collected questions.
    
    Args:
        questions: List of student questions
        course_context: Optional context about the course
        max_faqs: Maximum number of FAQs to generate
        
    Returns:
        List of FAQ dictionaries with 'question', 'answer', 'category'
    """
    # Sample questions if too many
    if len(questions) > 100:
        import random
        questions = random.sample(questions, 100)
    
    questions_text = "\n".join([f"- {q}" for q in questions[:50]])
    
    prompt = f"""
You are helping a professor create a FAQ document for their course.

Below are questions that students have asked via email and forum posts.
Many questions are similar or repeated. 

Your task:
1. Identify the most common/important questions
2. Group similar questions together
3. Write clear, helpful answers
4. Categorize each FAQ

Generate up to {max_faqs} FAQ entries.

Course Context: {course_context if course_context else "General university course"}

Student Questions:
{questions_text}

Return a JSON array of FAQ entries. Each entry should have:
{{
  "category": "Category name (e.g., Assignments, Grading, Schedule, Technical, Policies)",
  "question": "Clear, well-worded version of the question",
  "answer": "Helpful, comprehensive answer"
}}

Return ONLY valid JSON, no other text.
"""

    logger.info(f"Calling LLM to generate FAQ from {len(questions)} questions")
    
    try:
        response = organize_project.call_llm(prompt)
        
        # Parse JSON
        json_text = response.strip()
        if json_text.startswith("```"):
            json_text = re.sub(r"^```(?:json)?\s*", "", json_text)
            json_text = re.sub(r"\s*```$", "", json_text)
            json_text = json_text.strip()
        
        faqs = json.loads(json_text)
        
        if not isinstance(faqs, list):
            logger.error("LLM returned non-list response")
            return []
        
        # Validate structure
        valid_faqs = []
        for faq in faqs:
            if isinstance(faq, dict) and 'question' in faq and 'answer' in faq:
                if 'category' not in faq:
                    faq['category'] = 'General'
                valid_faqs.append(faq)
        
        logger.info(f"Generated {len(valid_faqs)} FAQ entries")
        return valid_faqs
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Error generating FAQ: {e}", exc_info=True)
        return []


def verify_faq_batch(faqs: List[Dict[str, str]]) -> Tuple[List[verification_system.VerificationResult], float]:
    """
    Verify a batch of FAQ entries for quality and completeness.
    
    Args:
        faqs: List of FAQ dictionaries
        
    Returns:
        Tuple of (verification results list, overall confidence)
    """
    logger.info(f"Verifying {len(faqs)} FAQ entries")
    
    results = []
    for i, faq in enumerate(faqs):
        logger.debug(f"Verifying FAQ {i+1}/{len(faqs)}")
        result = verification_system.verify_faq_entry(faq)
        results.append(result)
    
    # Calculate overall confidence
    overall_confidence = sum(r.confidence for r in results) / len(results) if results else 0.0
    logger.info(f"Overall FAQ confidence: {overall_confidence:.1%}")
    
    return results, overall_confidence


def format_faq_as_markdown(faqs: List[Dict[str, str]], title: str = "Course FAQ") -> str:
    """
    Format FAQs as a markdown document.
    
    Args:
        faqs: List of FAQ dictionaries
        title: Document title
        
    Returns:
        Markdown formatted string
    """
    # Group by category
    by_category = {}
    for faq in faqs:
        category = faq.get('category', 'General')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(faq)
    
    # Build markdown
    lines = [
        f"# {title}",
        "",
        f"*Last updated: {organize_project.datetime.now().strftime('%B %d, %Y')}*",
        "",
        "---",
        "",
    ]
    
    for category in sorted(by_category.keys()):
        lines.append(f"## {category}")
        lines.append("")
        
        for i, faq in enumerate(by_category[category], 1):
            lines.append(f"### {i}. {faq['question']}")
            lines.append("")
            lines.append(faq['answer'])
            lines.append("")
    
    return "\n".join(lines)


def post_faq_as_announcement(
    course_id: int,
    faq_content: str,
    title: str = "Course FAQ - Frequently Asked Questions"
) -> Optional[Dict[str, Any]]:
    """
    Post FAQ document as a Canvas announcement.
    
    Args:
        course_id: Canvas course ID
        faq_content: FAQ content (HTML or converted from Markdown)
        title: Announcement title
        
    Returns:
        Announcement object from Canvas API, or None if failed
    """
    logger.info(f"Posting FAQ as announcement to course {course_id}")
    
    # Check token from organize_project module (not the imported copy)
    if not organize_project.CANVAS_TOKEN:
        logger.error("CANVAS_TOKEN not set, cannot post announcement")
        print("❌ Canvas API token not set. Cannot post announcement.")
        return None
    
    # Convert markdown to HTML if needed (simple conversion)
    if not faq_content.startswith('<'):
        # Simple markdown to HTML conversion
        html_content = faq_content
        
        # Convert headers
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        
        # Convert bold
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        html_content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_content)
        
        # Convert line breaks
        html_content = html_content.replace('\n\n', '</p><p>')
        html_content = f'<p>{html_content}</p>'
        
        faq_content = html_content
    
    # Use the same pattern as organize_project.py - use canvas_post helper
    data = {
        "title": title,
        "message": faq_content,
        "is_announcement": "true",
        "published": "true",
    }
    
    try:
        # Use organize_project.canvas_post for consistency
        announcement = organize_project.canvas_post(
            f"/api/v1/courses/{course_id}/discussion_topics",
            data=data
        )
        logger.info(f"Posted announcement successfully: {announcement.get('id')}")
        print(f"✓ Posted announcement to Canvas!")
        print(f"   Announcement ID: {announcement.get('id')}")
        print(f"   Title: {announcement.get('title')}")
        return announcement
        
    except Exception as e:
        logger.error(f"Failed to post announcement: {e}", exc_info=True)
        print(f"❌ Failed to post announcement: {str(e)}")
        return None


def format_faq_as_html(faqs: List[Dict[str, str]], title: str = "Course FAQ") -> str:
    """
    Format FAQs as HTML for Canvas.
    
    Args:
        faqs: List of FAQ dictionaries
        title: Document title
        
    Returns:
        HTML formatted string
    """
    # Group by category
    by_category = {}
    for faq in faqs:
        category = faq.get('category', 'General')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(faq)
    
    # Build HTML
    html = [
        f"<h1>{title}</h1>",
        f"<p><em>Last updated: {organize_project.datetime.now().strftime('%B %d, %Y')}</em></p>",
        "<hr>",
    ]
    
    for category in sorted(by_category.keys()):
        html.append(f"<h2>{category}</h2>")
        
        for faq in by_category[category]:
            html.append(f"<h3>{faq['question']}</h3>")
            html.append(f"<p>{faq['answer']}</p>")
    
    return "\n".join(html)


def generate_faq_document(
    questions_folder: str,
    output_path: str = "course_faq.md",
    course_context: str = "",
    max_faqs: int = 20,
    format: str = "markdown",
    syllabus_folder: str = "sllaybus",
    post_to_canvas: bool = False,
    course_id: Optional[int] = None,
    announcement_title: str = "Course FAQ - Frequently Asked Questions"
) -> Optional[str]:
    """
    Main function: Generate FAQ document from student questions.
    
    Args:
        questions_folder: Path to folder with question files
        output_path: Where to save the FAQ
        course_context: Optional course information (if empty, reads from syllabus)
        max_faqs: Maximum FAQs to generate
        format: Output format ('markdown' or 'html')
        syllabus_folder: Path to syllabus files for context extraction
        post_to_canvas: Whether to post FAQ as Canvas announcement
        course_id: Canvas course ID (required if post_to_canvas=True)
        announcement_title: Title for Canvas announcement
        
    Returns:
        Path to generated file, or None if failed
    """
    logger.info("Starting FAQ generation")
    
    print("\n" + "="*70)
    print("📚 FAQ GENERATOR WITH COURSE CONTEXT")
    print("="*70 + "\n")
    
    # Step 1: Extract course context from syllabus
    if not course_context:
        print("📖 Reading course context from syllabus files...")
        course_context = extract_course_context_from_syllabus(syllabus_folder)
        if course_context:
            print(f"✓ Extracted course context ({len(course_context)} characters)")
            logger.debug(f"Course context: {course_context[:200]}...")
        else:
            print("⚠️  No syllabus found, proceeding without course context")
    else:
        print("✓ Using provided course context")
    
    # Step 2: Collect questions
    print(f"\n📨 Collecting student questions from: {questions_folder}")
    questions = collect_questions_from_folder(questions_folder)
    if not questions:
        logger.error("No questions collected")
        print("❌ No questions found in the folder.")
        return None
    
    print(f"✓ Collected {len(questions)} questions from student communications")
    
    # Step 3: Remove exact duplicates
    unique_questions = list(set(questions))
    print(f"✓ Found {len(unique_questions)} unique questions")
    
    # Step 4: Generate FAQ with LLM
    print(f"\n🤖 Generating FAQ entries (this may take a minute)...")
    faqs = generate_faq_with_llm(unique_questions, course_context, max_faqs)
    
    if not faqs:
        logger.error("Failed to generate FAQ")
        print("❌ Failed to generate FAQ entries")
        return None
    
    print(f"✓ Generated {len(faqs)} FAQ entries")
    
    # Step 5: Verify FAQ quality
    print("\n🔍 Verifying FAQ quality...")
    verification_results, overall_confidence = verify_faq_batch(faqs)
    
    # Display verification summary
    print(f"\n📊 Verification Summary:")
    print(f"   Overall Confidence: {overall_confidence:.1%}")
    
    needs_review = [r for r in verification_results if r.needs_review]
    if needs_review:
        print(f"   ⚠️  {len(needs_review)}/{len(faqs)} FAQs need review")
    else:
        print(f"   ✓ All FAQs passed verification")
    
    # Show issues/warnings
    total_issues = sum(len(r.issues) for r in verification_results)
    total_warnings = sum(len(r.warnings) for r in verification_results)
    
    if total_issues > 0:
        print(f"   ❌ {total_issues} critical issues found")
    if total_warnings > 0:
        print(f"   ⚠️  {total_warnings} warnings found")
    
    # Display detailed issues for FAQs needing review
    if needs_review and (total_issues > 0 or total_warnings > 0):
        print(f"\n📝 Items Needing Attention:")
        for i, result in enumerate(verification_results):
            if result.needs_review:
                faq = faqs[i]
                print(f"\n   FAQ: \"{faq.get('question', 'Unknown')[:60]}...\"")
                if result.issues:
                    for issue in result.issues:
                        print(f"      ❌ {issue}")
                if result.warnings:
                    for warning in result.warnings:
                        print(f"      ⚠️  {warning}")
    
    # Save verification report
    report_path = f"faq_verification_{pathlib.Path(output_path).stem}.txt"
    verification_system.create_review_report(
        verification_results,
        output_path=report_path
    )
    print(f"\n📄 Verification report saved: {report_path}")
    
    # Confidence-based warnings
    if overall_confidence < 0.75:
        print("\n" + "="*70)
        print("⚠️  LOW CONFIDENCE WARNING")
        print("="*70)
        print(f"Overall confidence is {overall_confidence:.1%}, below recommended 75%.")
        print("Please review the FAQ entries before publishing.")
        print("Consider:")
        print("  • Checking that questions were clear and complete")
        print("  • Verifying answers are accurate for your course")
        print("  • Editing any entries flagged above")
        print("="*70 + "\n")
    
    # Step 6: Format and save
    print(f"\n💾 Saving FAQ document...")
    if format == "html":
        content = format_faq_as_html(faqs, "Course FAQ")
        if not output_path.endswith('.html'):
            output_path = output_path.replace('.md', '.html')
    else:
        content = format_faq_as_markdown(faqs, "Course FAQ")
        if not output_path.endswith('.md'):
            output_path += '.md'
    
    pathlib.Path(output_path).write_text(content, encoding='utf-8')
    print(f"✓ FAQ saved to: {output_path}")
    
    # Step 7: Post to Canvas if requested
    if post_to_canvas:
        if not course_id:
            logger.error("Cannot post to Canvas: course_id not provided")
            print("\n❌ Cannot post to Canvas: course_id required")
            print("   Use --course-id parameter or set via GUI")
        else:
            print(f"\n📢 Posting FAQ as Canvas announcement...")
            
            # Use HTML format for announcement
            if format == "html":
                announcement_content = content
            else:
                # Convert markdown to HTML for announcement
                announcement_content = format_faq_as_html(faqs, "Course FAQ")
            
            announcement = post_faq_as_announcement(
                course_id=course_id,
                faq_content=announcement_content,
                title=announcement_title
            )
            
            if announcement:
                # Success message already printed by post_faq_as_announcement
                if 'html_url' in announcement:
                    print(f"   URL: {announcement.get('html_url')}")
            else:
                print("⚠️  Failed to post announcement (FAQ still saved locally)")
    
    # Display preview
    print("\n" + "="*70)
    print("📋 FAQ PREVIEW")
    print("="*70)
    preview_length = 1000
    if len(content) > preview_length:
        print(content[:preview_length] + "\n\n... (truncated, see full file)")
    else:
        print(content)
    print("="*70)
    
    return output_path


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    parser = argparse.ArgumentParser(
        description="Generate FAQ document from student questions"
    )
    parser.add_argument(
        "--questions-folder",
        type=str,
        default="student_questions",
        help="Folder containing text files with student questions",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="course_faq.md",
        help="Output file path (default: course_faq.md)",
    )
    parser.add_argument(
        "--syllabus-folder",
        type=str,
        default="sllaybus",
        help="Folder containing syllabus files for context extraction (default: sllaybus)",
    )
    parser.add_argument(
        "--course-context",
        type=str,
        default="",
        help="Brief description of the course (if empty, will read from syllabus folder)",
    )
    parser.add_argument(
        "--max-faqs",
        type=int,
        default=20,
        help="Maximum number of FAQs to generate (default: 20)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "html"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--post-to-canvas",
        action="store_true",
        help="Post FAQ as Canvas announcement",
    )
    parser.add_argument(
        "--course-id",
        type=int,
        help="Canvas course ID (required if --post-to-canvas is used)",
    )
    parser.add_argument(
        "--announcement-title",
        type=str,
        default="Course FAQ - Frequently Asked Questions",
        help="Title for Canvas announcement (default: 'Course FAQ - Frequently Asked Questions')",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    # Validate Canvas posting requirements
    if args.post_to_canvas and not args.course_id:
        parser.error("--course-id is required when --post-to-canvas is used")
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    result = generate_faq_document(
        questions_folder=args.questions_folder,
        output_path=args.output,
        course_context=args.course_context,
        max_faqs=args.max_faqs,
        format=args.format,
        syllabus_folder=args.syllabus_folder,
        post_to_canvas=args.post_to_canvas,
        course_id=args.course_id,
        announcement_title=args.announcement_title,
    )
    
    if result:
        logger.info("FAQ generation completed successfully")
    else:
        logger.error("FAQ generation failed")
        exit(1)

