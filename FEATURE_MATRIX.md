# Feature-to-Pain-Point Matrix

This document maps each code module to the specific faculty pain points it addresses.

---

## 📊 Module Coverage Matrix

| Pain Point | Quiz Gen | FAQ Gen | Proj Org | Rubric | Announce | Verify |
|-----------|:--------:|:-------:|:--------:|:------:|:--------:|:------:|
| 1. Update content with current examples | | | | | | |
| 2. Keep materials synchronized | | | 🟢 | | | |
| 3. Design fair, AI-resistant assessments | 🟡 | | | 🟡 | | 🟢 |
| 4. Develop diverse examples | | | | | | |
| 5. Accessibility adjustments | | | | | | |
| 6. Individualized learning support | | 🟡 | | | | |
| 7. Track participation/engagement | | | | | | |
| 8. Revise rubrics | | | | 🟢 | | 🟢 |
| 9. Ensure alignment of outcomes | 🟢 | | 🟢 | | | |
| 10. Create multimedia materials | | | | | | |
| 11. Balance innovation with integrity | | | | | | 🟢 |
| 12. Write exams efficiently | 🟢 | | | | | 🟢 |
| 13. Implement course updates | | | 🟢 | | 🟢 | |
| 14. Provide support beyond office hours | | 🟢 | | | | |
| 15. Handle routine communication | | 🟢 | | | 🟢 | |
| 16. Respond to repetitive emails | | 🟢 | | | | |
| 17. Manage one-on-one demands | | 🟡 | | | | |
| 18. Grade written reports/projects | | | | | | |
| 19. Provide detailed feedback | | | | | | |
| 20. Grade non-MC exams | | | | | | |
| 21. Maintain AI consistency | | | | | | 🟢 |

**Legend**: 🟢 = Fully Addresses | 🟡 = Partially Addresses | (blank) = Not Addressed

---

## 🔧 Detailed Module Breakdown

### 1. `automatic_quiz_generator.py` (644 lines)

**Primary Functions**:
- Parse lecture transcripts (VTT, TXT, PDF, DOCX)
- Generate N multiple-choice questions via LLM
- Create Canvas quiz with questions
- Schedule quiz (unlock/due/lock dates)
- Verify question quality

**Pain Points Addressed**:
- ✅ #12: Write exams efficiently **(PRIMARY)**
- ✅ #9: Ensure alignment of outcomes **(SECONDARY)**
- 🟡 #3: Design fair assessments (can enhance for AI-resistance)

**Key Features**:
```python
generate_quiz_from_transcripts(
    course_id, transcripts_folder, quiz_title,
    num_questions=10, points_per_question=1,
    unlock_at=None, due_at=None, lock_at=None,
    hide_correct_answers=True, publish=False, dry_run=False
)
```

**Verification Integration**: ✅ Yes
- Structural checks (format, options, correct_index)
- LLM-based correctness verification
- Confidence scoring

**Canvas Integration**: ✅ Full
- Creates quiz via Canvas API
- Uploads questions
- Sets scheduling and visibility

---

### 2. `faq_generator.py` (788 lines)

**Primary Functions**:
- Read student questions from files
- Extract course context from syllabus
- Identify common/important questions
- Generate comprehensive answers
- Post FAQ as Canvas announcement
- Verify FAQ quality

**Pain Points Addressed**:
- ✅ #16: Respond to repetitive emails **(PRIMARY)**
- ✅ #15: Handle routine communication **(PRIMARY)**
- ✅ #14: Support beyond office hours **(SECONDARY)**
- 🟡 #6: Individualized support (FAQs help all students)
- 🟡 #17: Manage one-on-one demands (reduces volume)

**Key Features**:
```python
generate_faq_document(
    questions_folder, output_path="course_faq.md",
    max_faqs=20, format="markdown",
    syllabus_folder="syllabus",
    post_to_canvas=False, course_id=None,
    announcement_title="Course FAQ"
)
```

**Verification Integration**: ✅ Yes
- Checks question/answer quality
- Flags placeholder text
- Verifies category appropriateness

**Canvas Integration**: ✅ Full
- Posts FAQ as announcement
- HTML formatting support

**Unique Strength**: Syllabus context extraction for accurate answers

---

### 3. `organize_project.py` (767 lines)

**Primary Functions**:
- Read project materials (PDF, DOCX, PPTX)
- Extract text from documents
- Generate project overview via LLM
- Create assignment description
- Upload files to Canvas
- Create Canvas assignment with rubric

**Pain Points Addressed**:
- ✅ #2: Keep materials synchronized **(PRIMARY)**
- ✅ #13: Implement course updates **(PRIMARY)**
- ✅ #9: Ensure alignment of outcomes **(SECONDARY)**

**Key Features**:
```python
organize_and_upload(
    course_id, local_folder="final_project",
    canvas_folder_name="Final Project Materials",
    assignment_name="Final Project",
    points=100, dry_run=False
)
```

**Verification Integration**: 🟡 Partial
- Uses LLM for content generation
- No explicit verification layer (could add)

**Canvas Integration**: ✅ Full
- Creates/updates folders
- Uploads files
- Creates assignments with rubrics

**Unique Strength**: Multi-format document parsing (PDF, DOCX, PPTX)

---

### 4. `rubric_templates.py` (module exists)

**Primary Functions**:
- Pre-built rubric templates (essay, presentation, lab, etc.)
- Customize point distribution
- Export to multiple formats (Markdown, HTML, JSON)

**Pain Points Addressed**:
- ✅ #8: Revise rubrics **(PRIMARY)**
- 🟡 #3: Fair assessments (templates can include AI-work criteria)

**Key Features**:
```python
RUBRIC_TEMPLATES = {
    "essay": {...},
    "presentation": {...},
    "lab_report": {...},
    "programming_assignment": {...},
    "group_project": {...},
    "participation": {...}
}

customize_rubric(template_name, total_points=100)
save_rubric(rubric, output_path, format="markdown")
```

**Verification Integration**: ✅ Yes
- `verify_rubric()` checks point distribution
- Validates criterion completeness

**Canvas Integration**: 🟡 Partial
- Exports to Canvas-compatible formats
- Manual import to Canvas needed

**Templates Include**:
1. Essay Writing
2. Presentation
3. Lab Report
4. Programming Assignment
5. Group Project
6. Class Participation

---

### 5. `announcement_generator.py` (439 lines)

**Primary Functions**:
- Parse course schedule file
- Extract week-specific topics
- Generate engaging announcements
- Post to Canvas

**Pain Points Addressed**:
- ✅ #15: Handle routine communication **(PRIMARY)**
- ✅ #13: Implement course updates **(SECONDARY)**

**Key Features**:
```python
generate_weekly_announcement(
    course_id, schedule_file="schedule.txt",
    week_number=1, post_to_canvas=False,
    dry_run=True
)
```

**Verification Integration**: 🟡 Could Add
- Currently no verification
- Could add tone/appropriateness checking

**Canvas Integration**: ✅ Full
- Posts as Canvas announcement
- HTML formatting

**Unique Strength**: Schedule-aware context for timely announcements

---

### 6. `verification_system.py` (626 lines)

**Primary Functions**:
- Verify quiz questions (structure + facts)
- Verify FAQ entries
- Verify rubrics
- LLM-based correctness checking
- Generate review reports

**Pain Points Addressed**:
- ✅ #11: Balance innovation with integrity **(PRIMARY)**
- ✅ #21: Maintain AI consistency **(PRIMARY)**
- ✅ #3: Design fair assessments **(SUPPORTING)**

**Key Features**:
```python
# Structural verification (no LLM)
verify_quiz_question(question) -> VerificationResult
verify_quiz_batch(questions) -> (results, overall_confidence)
verify_faq_entry(faq) -> VerificationResult
verify_rubric(rubric) -> VerificationResult

# LLM-based verification
verify_quiz_answer_correctness(question) -> VerificationResult
verify_with_llm(content, content_type, verification_prompt)

# Reporting
create_review_report(verifications, output_path)
```

**Verification Checks**:

**Quiz Questions**:
- ✓ Question length (10-300 chars)
- ✓ Has question mark
- ✓ Exactly 4 options
- ✓ No duplicate options
- ✓ Valid correct_index (0-3)
- ✓ Balanced option lengths
- ✓ LLM factual correctness

**FAQ Entries**:
- ✓ Question length (>5 chars)
- ✓ Has question mark
- ✓ Answer length (10-1000 chars)
- ✓ No placeholder text (TODO, TBD)
- ✓ Valid category

**Rubrics**:
- ✓ Has criteria (3-10)
- ✓ Point distribution matches total
- ✓ Each criterion has name, description, points
- ✓ No single criterion >50% of total

**VerificationResult Object**:
```python
{
    "content_type": str,
    "confidence": float (0.0-1.0),
    "confidence_label": str (HIGH/GOOD/MODERATE/LOW/VERY LOW),
    "issues": List[str],        # Critical problems
    "warnings": List[str],      # Minor concerns
    "needs_review": bool,       # True if confidence < 0.75
    "timestamp": datetime
}
```

**Canvas Integration**: ❌ None (verification layer only)

**Unique Strength**: Multi-layer safety system (structural + LLM)

---

### 7. `app.py` (1309 lines)

**Primary Function**: User-friendly GUI for all tools

**Components**:
- API configuration (Canvas token, OpenAI key, Course ID)
- 5 tabs (Quiz, FAQ, Rubric, Project, Announcement)
- Output console with live updates
- Preview modes (dry-run)
- Help documentation

**Pain Points Addressed**:
- Makes ALL features accessible to non-technical faculty
- Reduces learning curve
- Provides safety (preview before posting)

**Key UX Features**:
- Token visibility toggle (show/hide)
- Browse buttons for file/folder selection
- Real-time output console
- Clear instructions in each tab
- Comprehensive help dialog

**Canvas Integration**: Coordinates all modules

---

## 📈 Impact Score by Module

| Module | Lines | Pain Points Addressed | Impact Score | Complexity |
|--------|-------|----------------------|--------------|------------|
| `faq_generator.py` | 788 | 5 (3 full, 2 partial) | ⭐⭐⭐⭐⭐ | Medium |
| `automatic_quiz_generator.py` | 644 | 3 (2 full, 1 partial) | ⭐⭐⭐⭐⭐ | Medium |
| `verification_system.py` | 626 | 3 (all full) | ⭐⭐⭐⭐⭐ | High |
| `organize_project.py` | 767 | 3 (all full) | ⭐⭐⭐⭐ | Medium |
| `announcement_generator.py` | 439 | 2 (all full) | ⭐⭐⭐ | Low |
| `rubric_templates.py` | ~200 | 2 (1 full, 1 partial) | ⭐⭐⭐ | Low |
| `app.py` | 1309 | All (UI layer) | ⭐⭐⭐⭐⭐ | Medium |

**Total**: ~4,773 lines of Python code

---

## 🚀 Expansion Opportunities

### Easy Wins (1-2 weeks):
1. **AI-Resistant Question Types** - Enhance quiz generator prompts
2. **Caption Generator** - Use Whisper API for video captions
3. **Alt-Text Generator** - Use GPT-4 Vision for images

### Medium Effort (2-4 weeks):
4. **Feedback Generator** - Rubric + submission → feedback
5. **Engagement Dashboard** - Canvas Analytics integration
6. **Content Updater** - Web search for current examples

### High Effort (1-2 months):
7. **Essay Auto-Grader** - LLM-based with rubric
8. **Student Chatbot** - Q&A system with course context
9. **Personalized Learning Paths** - Adaptive recommendations

---

## 💡 Architecture Insights

### Shared Dependencies:
All modules use:
- `organize_project.call_llm()` for OpenAI API calls
- `verification_system` for quality checks
- Canvas API wrappers (`canvas_get`, `canvas_post`)
- Common file parsing utilities

### Data Flow:
```
User Input (app.py)
    ↓
Module-specific processing
    ↓
LLM generation (organize_project.call_llm)
    ↓
Verification (verification_system)
    ↓
Canvas upload (Canvas API)
    ↓
Output console (app.py)
```

### Safety Layers:
1. **Dry-run mode** - Preview before posting
2. **Verification system** - Structural + LLM checks
3. **Confidence scoring** - Flag low-quality outputs
4. **Human review prompts** - For low-confidence items

---

## 📋 Conclusion

The codebase has **6 major functional modules** + **1 GUI layer**, totaling ~4,800 lines. Each module is well-scoped and addresses specific pain points:

- **Best Coverage**: Communication & assessment creation (5/5 pain points)
- **Good Coverage**: Content organization (3/5 pain points)
- **Opportunity**: Grading & feedback (0/3 pain points) ← Future expansion

The verification system is the **differentiator** - it's what makes this safe for faculty use vs. raw ChatGPT.

