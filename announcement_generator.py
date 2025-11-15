"""
Announcement Generator - Auto-create weekly announcements from schedule

This module generates weekly course announcements based on the course schedule,
highlighting upcoming assignments, deadlines, and important dates.
"""

import os
import re
import json
import pathlib
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import organize_project

# Module-level variables
CANVAS_BASE_URL = organize_project.CANVAS_BASE_URL
CANVAS_TOKEN = organize_project.CANVAS_TOKEN
OPENAI_API_KEY = organize_project.OPENAI_API_KEY

logger = logging.getLogger(__name__)


def canvas_post(path: str, data: Dict[str, Any]) -> Any:
    """Helper to call Canvas POST endpoints."""
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
    resp = organize_project.requests.post(
        f"{CANVAS_BASE_URL}{path}",
        headers=headers,
        data=data
    )
    resp.raise_for_status()
    return resp.json()


def extract_schedule_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract schedule items from syllabus or schedule document.
    
    Args:
        text: Raw text from schedule document
        
    Returns:
        List of schedule items with dates and descriptions
    """
    schedule_items = []
    
    # Common date patterns
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
        r'(\d{1,2}/\d{1,2})',          # MM/DD
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}',  # Month DD
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',  # Day of week
    ]
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for dates
        for pattern in date_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                schedule_items.append({
                    'date_text': matches[0],
                    'description': line,
                    'raw_line': line
                })
                break
    
    return schedule_items


def get_upcoming_items(
    schedule_items: List[Dict[str, Any]],
    days_ahead: int = 7
) -> List[Dict[str, Any]]:
    """
    Filter schedule items to only upcoming events.
    
    Args:
        schedule_items: List of schedule items
        days_ahead: How many days ahead to look
        
    Returns:
        List of upcoming items
    """
    # For now, return all items since date parsing is complex
    # In production, would parse dates and filter
    return schedule_items[:10]  # Return first 10 items


def generate_announcement_with_llm(
    schedule_items: List[Dict[str, Any]],
    week_number: Optional[int] = None,
    custom_message: str = ""
) -> str:
    """
    Use LLM to generate a weekly announcement.
    
    Args:
        schedule_items: List of upcoming schedule items
        week_number: Week number (optional)
        custom_message: Custom message to include (optional)
        
    Returns:
        Generated announcement text
    """
    schedule_text = "\n".join([
        f"- {item['description']}"
        for item in schedule_items
    ])
    
    week_text = f"Week {week_number}" if week_number else "this week"
    
    prompt = f"""
You are helping a professor write a weekly course announcement.

Generate a friendly, professional announcement for {week_text}.

The announcement should:
1. Greet students warmly
2. Highlight key items from the schedule below
3. Remind students of upcoming deadlines
4. Include any important notes or changes
5. End with encouragement

Schedule items for {week_text}:
{schedule_text}

{f"Custom message from professor: {custom_message}" if custom_message else ""}

Write the announcement in a warm, encouraging tone. Keep it concise (2-3 paragraphs).
Format it in HTML for Canvas (use <p>, <strong>, <ul>, <li> tags).
"""

    logger.info(f"Calling LLM to generate announcement for {week_text}")
    
    try:
        response = organize_project.call_llm(prompt)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating announcement: {e}", exc_info=True)
        return ""


def post_canvas_announcement(
    course_id: int,
    title: str,
    message: str,
    publish: bool = True
) -> Dict[str, Any]:
    """
    Post announcement to Canvas.
    
    Args:
        course_id: Canvas course ID
        title: Announcement title
        message: Announcement message (HTML)
        publish: Whether to publish immediately
        
    Returns:
        Canvas announcement object
    """
    data = {
        "title": title,
        "message": message,
        "is_announcement": "true",
        "published": "true" if publish else "false",
    }
    
    logger.info(f"Posting announcement to Canvas: {title}")
    announcement = canvas_post(
        f"/api/v1/courses/{course_id}/discussion_topics",
        data=data
    )
    
    logger.info(f"Posted announcement ID: {announcement.get('id')}")
    return announcement


def generate_weekly_announcement(
    course_id: Optional[int],
    schedule_file: str,
    week_number: Optional[int] = None,
    custom_message: str = "",
    post_to_canvas: bool = False,
    dry_run: bool = True
) -> Optional[str]:
    """
    Main function: Generate weekly announcement.
    
    Args:
        course_id: Canvas course ID (required if posting)
        schedule_file: Path to schedule file
        week_number: Week number (optional)
        custom_message: Custom message to include
        post_to_canvas: Whether to post to Canvas
        dry_run: If True, don't actually post
        
    Returns:
        Generated announcement text
    """
    logger.info("Starting announcement generation")
    
    # Step 1: Read schedule
    if not pathlib.Path(schedule_file).exists():
        logger.error(f"Schedule file not found: {schedule_file}")
        print(f"❌ Schedule file not found: {schedule_file}")
        return None
    
    text = pathlib.Path(schedule_file).read_text(encoding='utf-8', errors='ignore')
    print(f"✓ Read schedule from: {schedule_file}")
    
    # Step 2: Extract schedule items
    schedule_items = extract_schedule_from_text(text)
    print(f"✓ Found {len(schedule_items)} schedule items")
    
    if not schedule_items:
        logger.warning("No schedule items found")
        print("⚠️ No schedule items found in the file")
        return None
    
    # Step 3: Get upcoming items
    upcoming = get_upcoming_items(schedule_items, days_ahead=7)
    print(f"✓ Identified {len(upcoming)} upcoming items")
    
    # Step 4: Generate announcement
    print("⏳ Generating announcement...")
    announcement = generate_announcement_with_llm(
        upcoming,
        week_number=week_number,
        custom_message=custom_message
    )
    
    if not announcement:
        logger.error("Failed to generate announcement")
        print("❌ Failed to generate announcement")
        return None
    
    print("✓ Generated announcement")
    
    # Display preview
    print("\n" + "="*60)
    print("ANNOUNCEMENT PREVIEW")
    print("="*60)
    print(announcement)
    print("="*60 + "\n")
    
    # Step 5: Post to Canvas if requested
    if post_to_canvas and not dry_run:
        if not course_id:
            logger.error("course_id required to post to Canvas")
            print("❌ Course ID required to post to Canvas")
            return announcement
        
        if not CANVAS_TOKEN:
            logger.error("CANVAS_TOKEN not set")
            print("❌ Canvas API token not set")
            return announcement
        
        week_text = f"Week {week_number}" if week_number else "This Week"
        title = f"Weekly Update - {week_text}"
        
        try:
            result = post_canvas_announcement(
                course_id,
                title,
                announcement,
                publish=True
            )
            print(f"✓ Posted announcement to Canvas (ID: {result.get('id')})")
            print(f"  URL: {CANVAS_BASE_URL}/courses/{course_id}/discussion_topics/{result.get('id')}")
        except Exception as e:
            logger.error(f"Failed to post announcement: {e}", exc_info=True)
            print(f"❌ Failed to post announcement: {e}")
    elif dry_run:
        print("[DRY RUN] Announcement not posted to Canvas")
    
    return announcement


def generate_semester_announcements(
    schedule_file: str,
    output_folder: str,
    num_weeks: int = 15
) -> List[str]:
    """
    Generate announcements for entire semester.
    
    Args:
        schedule_file: Path to schedule file
        output_folder: Where to save announcements
        num_weeks: Number of weeks in semester
        
    Returns:
        List of paths to generated files
    """
    logger.info(f"Generating {num_weeks} weeks of announcements")
    
    # Read schedule
    text = pathlib.Path(schedule_file).read_text(encoding='utf-8', errors='ignore')
    all_items = extract_schedule_from_text(text)
    
    output_dir = pathlib.Path(output_folder)
    output_dir.mkdir(exist_ok=True)
    
    saved_files = []
    items_per_week = len(all_items) // num_weeks if all_items else 0
    
    for week in range(1, num_weeks + 1):
        print(f"\nGenerating Week {week} announcement...")
        
        # Get items for this week
        start_idx = (week - 1) * items_per_week
        end_idx = start_idx + items_per_week
        week_items = all_items[start_idx:end_idx] if all_items else []
        
        if not week_items:
            logger.warning(f"No items for week {week}")
            continue
        
        # Generate
        announcement = generate_announcement_with_llm(week_items, week_number=week)
        
        if announcement:
            # Save to file
            filename = f"week_{week:02d}_announcement.html"
            filepath = output_dir / filename
            filepath.write_text(announcement, encoding='utf-8')
            saved_files.append(str(filepath))
            print(f"  ✓ Saved: {filename}")
    
    print(f"\n✓ Generated {len(saved_files)} announcements in {output_folder}")
    return saved_files


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    parser = argparse.ArgumentParser(
        description="Generate weekly course announcements"
    )
    parser.add_argument(
        "--schedule-file",
        type=str,
        required=True,
        help="Path to schedule file (text, markdown, or syllabus)",
    )
    parser.add_argument(
        "--course-id",
        type=int,
        help="Canvas course ID (required if posting)",
    )
    parser.add_argument(
        "--week-number",
        type=int,
        help="Week number for the announcement",
    )
    parser.add_argument(
        "--custom-message",
        type=str,
        default="",
        help="Custom message to include",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post announcement to Canvas",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview only, don't post to Canvas (default)",
    )
    parser.add_argument(
        "--generate-semester",
        action="store_true",
        help="Generate announcements for entire semester",
    )
    parser.add_argument(
        "--output-folder",
        type=str,
        default="announcements",
        help="Output folder for generated announcements",
    )
    parser.add_argument(
        "--num-weeks",
        type=int,
        default=15,
        help="Number of weeks (for semester generation)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.generate_semester:
        # Generate entire semester
        files = generate_semester_announcements(
            args.schedule_file,
            args.output_folder,
            args.num_weeks
        )
        logger.info(f"Generated {len(files)} announcements")
    else:
        # Generate single announcement
        result = generate_weekly_announcement(
            course_id=args.course_id,
            schedule_file=args.schedule_file,
            week_number=args.week_number,
            custom_message=args.custom_message,
            post_to_canvas=args.post,
            dry_run=args.dry_run or not args.post,
        )
        
        if result:
            logger.info("Announcement generation completed successfully")
        else:
            logger.error("Announcement generation failed")
            exit(1)

