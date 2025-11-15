"""
Rubric Templates - Pre-built rubrics for common assignment types

This module provides ready-to-use rubric templates for various assignment types
with customization options.
"""

import json
import pathlib
import argparse
import logging
from typing import Dict, Any, List, Optional

import organize_project

logger = logging.getLogger(__name__)

# Module-level variables
CANVAS_BASE_URL = organize_project.CANVAS_BASE_URL
CANVAS_TOKEN = organize_project.CANVAS_TOKEN


# ==================== RUBRIC TEMPLATES ====================

RUBRIC_TEMPLATES = {
    "essay": {
        "name": "Essay Rubric",
        "description": "Standard rubric for essay assignments",
        "total_points": 100,
        "criteria": [
            {
                "name": "Thesis & Argument",
                "description": "Clear thesis statement and well-developed argument",
                "points": 25
            },
            {
                "name": "Evidence & Support",
                "description": "Uses relevant evidence and sources to support claims",
                "points": 25
            },
            {
                "name": "Organization & Structure",
                "description": "Logical flow, clear paragraphs, effective transitions",
                "points": 20
            },
            {
                "name": "Writing Quality",
                "description": "Grammar, spelling, clarity, and style",
                "points": 15
            },
            {
                "name": "Citations & Format",
                "description": "Proper citations and formatting (APA/MLA/Chicago)",
                "points": 15
            }
        ]
    },
    
    "research_paper": {
        "name": "Research Paper Rubric",
        "description": "Comprehensive rubric for research papers",
        "total_points": 100,
        "criteria": [
            {
                "name": "Research Question",
                "description": "Clear, focused, and appropriate research question",
                "points": 15
            },
            {
                "name": "Literature Review",
                "description": "Comprehensive review of relevant literature",
                "points": 20
            },
            {
                "name": "Methodology",
                "description": "Appropriate methods and clear explanation",
                "points": 15
            },
            {
                "name": "Analysis & Findings",
                "description": "Thorough analysis and clear presentation of findings",
                "points": 25
            },
            {
                "name": "Conclusions",
                "description": "Well-supported conclusions and implications",
                "points": 15
            },
            {
                "name": "Writing & Citations",
                "description": "Quality writing, proper citations, formatting",
                "points": 10
            }
        ]
    },
    
    "presentation": {
        "name": "Presentation Rubric",
        "description": "Rubric for oral presentations",
        "total_points": 100,
        "criteria": [
            {
                "name": "Content Quality",
                "description": "Accuracy, depth, and relevance of content",
                "points": 30
            },
            {
                "name": "Organization",
                "description": "Clear structure, logical flow, effective intro/conclusion",
                "points": 20
            },
            {
                "name": "Visual Aids",
                "description": "Quality and effectiveness of slides/materials",
                "points": 15
            },
            {
                "name": "Delivery",
                "description": "Speaking clarity, confidence, eye contact, pacing",
                "points": 20
            },
            {
                "name": "Q&A Handling",
                "description": "Responses to questions, engagement with audience",
                "points": 15
            }
        ]
    },
    
    "group_project": {
        "name": "Group Project Rubric",
        "description": "Rubric for team-based projects",
        "total_points": 100,
        "criteria": [
            {
                "name": "Project Scope & Planning",
                "description": "Clear objectives, comprehensive planning, appropriate scope",
                "points": 20
            },
            {
                "name": "Research & Analysis",
                "description": "Thorough research, insightful analysis, appropriate methods",
                "points": 25
            },
            {
                "name": "Final Deliverable",
                "description": "Quality, completeness, and professionalism of final product",
                "points": 30
            },
            {
                "name": "Team Collaboration",
                "description": "Evidence of effective teamwork and equal contribution",
                "points": 15
            },
            {
                "name": "Documentation",
                "description": "Clear documentation, citations, and supporting materials",
                "points": 10
            }
        ]
    },
    
    "lab_report": {
        "name": "Lab Report Rubric",
        "description": "Rubric for laboratory reports",
        "total_points": 100,
        "criteria": [
            {
                "name": "Introduction & Hypothesis",
                "description": "Clear background, objectives, and hypothesis",
                "points": 15
            },
            {
                "name": "Methods & Procedures",
                "description": "Detailed, reproducible methods description",
                "points": 20
            },
            {
                "name": "Results & Data",
                "description": "Complete data presentation, appropriate tables/graphs",
                "points": 25
            },
            {
                "name": "Analysis & Discussion",
                "description": "Interpretation of results, comparison to expected outcomes",
                "points": 25
            },
            {
                "name": "Conclusions",
                "description": "Summary, implications, and future directions",
                "points": 10
            },
            {
                "name": "Format & Style",
                "description": "Scientific writing style, proper formatting, citations",
                "points": 5
            }
        ]
    },
    
    "case_study": {
        "name": "Case Study Analysis Rubric",
        "description": "Rubric for case study assignments",
        "total_points": 100,
        "criteria": [
            {
                "name": "Problem Identification",
                "description": "Clear identification and articulation of key issues",
                "points": 20
            },
            {
                "name": "Situational Analysis",
                "description": "Thorough analysis of context, stakeholders, constraints",
                "points": 25
            },
            {
                "name": "Alternative Solutions",
                "description": "Multiple viable solutions with pros/cons analysis",
                "points": 20
            },
            {
                "name": "Recommendations",
                "description": "Well-justified recommendations with implementation plan",
                "points": 25
            },
            {
                "name": "Presentation & Writing",
                "description": "Clear writing, professional format, proper citations",
                "points": 10
            }
        ]
    },
    
    "coding_assignment": {
        "name": "Programming Assignment Rubric",
        "description": "Rubric for coding/programming projects",
        "total_points": 100,
        "criteria": [
            {
                "name": "Functionality",
                "description": "Program runs correctly and meets all requirements",
                "points": 40
            },
            {
                "name": "Code Quality",
                "description": "Clean, readable, well-organized code",
                "points": 20
            },
            {
                "name": "Documentation",
                "description": "Comments, docstrings, README file",
                "points": 15
            },
            {
                "name": "Testing",
                "description": "Comprehensive test cases, edge case handling",
                "points": 15
            },
            {
                "name": "Efficiency",
                "description": "Appropriate algorithms, efficient implementation",
                "points": 10
            }
        ]
    },
    
    "ai_appropriate_use": {
        "name": "AI-Assisted Work Rubric",
        "description": "Rubric that accounts for appropriate AI tool usage",
        "total_points": 100,
        "criteria": [
            {
                "name": "Original Thinking",
                "description": "Evidence of student's own analysis and insights",
                "points": 30
            },
            {
                "name": "AI Tool Disclosure",
                "description": "Proper documentation of which AI tools were used and how",
                "points": 10
            },
            {
                "name": "Critical Evaluation",
                "description": "Assessment and verification of AI-generated content",
                "points": 20
            },
            {
                "name": "Synthesis & Integration",
                "description": "Effective integration of AI assistance with own work",
                "points": 20
            },
            {
                "name": "Quality & Accuracy",
                "description": "Final work quality, accuracy, and completeness",
                "points": 20
            }
        ]
    }
}


def get_template(template_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a rubric template by name.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Template dictionary or None if not found
    """
    return RUBRIC_TEMPLATES.get(template_name)


def list_templates() -> List[str]:
    """Get list of all available template names."""
    return list(RUBRIC_TEMPLATES.keys())


def customize_rubric(
    template_name: str,
    total_points: Optional[int] = None,
    criteria_adjustments: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Customize a rubric template.
    
    Args:
        template_name: Name of the template to customize
        total_points: New total points (will scale criteria proportionally)
        criteria_adjustments: Dict mapping criterion names to new point values
        
    Returns:
        Customized rubric dictionary
    """
    template = get_template(template_name)
    if not template:
        raise ValueError(f"Template '{template_name}' not found")
    
    rubric = json.loads(json.dumps(template))  # Deep copy
    
    # Adjust individual criteria first
    if criteria_adjustments:
        for criterion in rubric['criteria']:
            if criterion['name'] in criteria_adjustments:
                criterion['points'] = criteria_adjustments[criterion['name']]
    
    # Scale to new total if requested
    if total_points:
        current_total = sum(c['points'] for c in rubric['criteria'])
        scale_factor = total_points / current_total
        
        for criterion in rubric['criteria']:
            criterion['points'] = round(criterion['points'] * scale_factor)
        
        rubric['total_points'] = total_points
    
    # Recalculate total
    rubric['total_points'] = sum(c['points'] for c in rubric['criteria'])
    
    return rubric


def format_rubric_as_markdown(rubric: Dict[str, Any]) -> str:
    """Format rubric as markdown."""
    lines = [
        f"# {rubric['name']}",
        "",
        f"**Total Points:** {rubric['total_points']}",
        "",
        rubric.get('description', ''),
        "",
        "## Criteria",
        ""
    ]
    
    for i, criterion in enumerate(rubric['criteria'], 1):
        lines.append(f"### {i}. {criterion['name']} ({criterion['points']} points)")
        lines.append("")
        lines.append(criterion['description'])
        lines.append("")
    
    return "\n".join(lines)


def format_rubric_as_html(rubric: Dict[str, Any]) -> str:
    """Format rubric as HTML for Canvas."""
    html = [
        f"<h2>{rubric['name']}</h2>",
        f"<p><strong>Total Points: {rubric['total_points']}</strong></p>",
        f"<p>{rubric.get('description', '')}</p>",
        "<table border='1' style='width:100%; border-collapse:collapse;'>",
        "<tr><th>Criterion</th><th>Points</th><th>Description</th></tr>"
    ]
    
    for criterion in rubric['criteria']:
        html.append(
            f"<tr>"
            f"<td><strong>{criterion['name']}</strong></td>"
            f"<td style='text-align:center;'>{criterion['points']}</td>"
            f"<td>{criterion['description']}</td>"
            f"</tr>"
        )
    
    html.append("</table>")
    return "\n".join(html)


def format_rubric_as_canvas_json(rubric: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format rubric for Canvas API.
    
    Args:
        rubric: Rubric dictionary
        
    Returns:
        Canvas-compatible rubric data
    """
    canvas_rubric = {
        "title": rubric['name'],
        "points_possible": rubric['total_points'],
        "criteria": []
    }
    
    for i, criterion in enumerate(rubric['criteria']):
        canvas_criterion = {
            "description": criterion['name'],
            "long_description": criterion['description'],
            "points": criterion['points'],
            "criterion_use_range": False,
            "ratings": [
                {
                    "description": "Excellent",
                    "points": criterion['points']
                },
                {
                    "description": "Good",
                    "points": round(criterion['points'] * 0.8)
                },
                {
                    "description": "Satisfactory",
                    "points": round(criterion['points'] * 0.6)
                },
                {
                    "description": "Needs Improvement",
                    "points": round(criterion['points'] * 0.4)
                },
                {
                    "description": "Unsatisfactory",
                    "points": 0
                }
            ]
        }
        canvas_rubric['criteria'].append(canvas_criterion)
    
    return canvas_rubric


def save_rubric(
    rubric: Dict[str, Any],
    output_path: str,
    format: str = "markdown"
) -> str:
    """
    Save rubric to file.
    
    Args:
        rubric: Rubric dictionary
        output_path: Output file path
        format: Format ('markdown', 'html', 'json')
        
    Returns:
        Path to saved file
    """
    if format == "markdown":
        content = format_rubric_as_markdown(rubric)
        if not output_path.endswith('.md'):
            output_path += '.md'
    elif format == "html":
        content = format_rubric_as_html(rubric)
        if not output_path.endswith('.html'):
            output_path += '.html'
    elif format == "json":
        content = json.dumps(format_rubric_as_canvas_json(rubric), indent=2)
        if not output_path.endswith('.json'):
            output_path += '.json'
    else:
        raise ValueError(f"Unknown format: {format}")
    
    pathlib.Path(output_path).write_text(content, encoding='utf-8')
    logger.info(f"Saved rubric to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    parser = argparse.ArgumentParser(
        description="Generate rubrics from templates"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available templates",
    )
    parser.add_argument(
        "--template",
        type=str,
        help="Template name to use",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="rubric.md",
        help="Output file path",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "html", "json"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--total-points",
        type=int,
        help="Customize total points",
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable Rubric Templates:")
        print("="*50)
        for name in list_templates():
            template = get_template(name)
            print(f"\n{name}:")
            print(f"  {template['name']}")
            print(f"  {template['description']}")
            print(f"  Total Points: {template['total_points']}")
            print(f"  Criteria: {len(template['criteria'])}")
        print("\n")
        exit(0)
    
    if not args.template:
        print("Error: --template required (or use --list to see options)")
        exit(1)
    
    # Get and customize template
    rubric = customize_rubric(args.template, total_points=args.total_points)
    
    # Save
    output_path = save_rubric(rubric, args.output, args.format)
    print(f"✓ Rubric saved to: {output_path}")
    
    # Preview
    print("\n" + "="*60)
    print("RUBRIC PREVIEW")
    print("="*60)
    print(format_rubric_as_markdown(rubric))
    print("="*60)

