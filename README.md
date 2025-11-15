# Canvas AI Co-Pilot

**User-Friendly GUI for Canvas Course Management**

This application helps professors automate Canvas course management tasks using AI, without requiring any coding knowledge.

## Features

### 📚 Final Project Organizer
- Upload and organize final project materials
- Auto-generate project descriptions and rubrics using AI
- Create Canvas assignments and announcements
- Schedule materials to be released on specific dates

### 📝 Automatic Quiz Generator
- Generate quizzes automatically from lecture transcripts
- Customize number of questions and points
- Set quiz dates (available, due, lock dates)
- Hide correct answers to encourage learning
- Multiple attempts allowed

### 🛡️ **NEW!** Safety & Verification System
- **Automatic quality checks** for all AI-generated content
- **Confidence scoring** (0-100%) for each quiz question
- **Issue detection** - flags critical problems before publishing
- **Human review workflow** - highlights items needing attention
- **Verification reports** - detailed analysis saved automatically

## Installation

### Requirements
- Python 3.8 or higher
- Required packages:

```bash
pip install customtkinter requests openai PyPDF2 python-docx python-pptx
```

## Getting Started

### 1. Get Your API Tokens

#### Canvas API Token
1. Log into Canvas
2. Go to Account → Settings
3. Scroll to "Approved Integrations"
4. Click "+ New Access Token"
5. Give it a purpose (e.g., "Canvas AI Co-Pilot")
6. Copy the token (you won't see it again!)

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key

#### Canvas Course ID
1. Go to your Canvas course
2. Look at the URL: `https://canvas.institution.edu/courses/12345`
3. The number `12345` is your Course ID

### 2. Run the Application

```bash
python3 app.py
```

### 3. Enter Your Information

At the top of the window, enter:
- **Canvas API Token**: Paste your Canvas token
- **OpenAI API Key**: Paste your OpenAI key
- **Canvas Course ID**: Enter your course number

## Using the Tools

### 📚 Final Project Organizer

1. Click the "**📚 Final Project Organizer**" tab
2. Click "**Browse...**" to select your project materials folder
   - Should contain PDFs, DOCX, PPTX files with project instructions
3. Keep "**Preview Only**" checked for testing
4. Click "**🚀 Organize Final Project**"
5. Review the output in the console
6. Uncheck "Preview Only" when ready to upload to Canvas

### 📝 Quiz Generator

1. Click the "**📝 Quiz Generator**" tab
2. Click "**Browse...**" to select your transcripts folder
   - Should contain .vtt transcript files
3. Enter quiz settings:
   - **Quiz Title**: Name for your quiz
   - **Number of Questions**: How many questions to generate (default: 10)
   - **Points per Question**: Points for each question (default: 1)
4. (Optional) Enter dates:
   - **Available From**: When students can start (format: YYYY-MM-DD HH:MM)
   - **Due Date**: When quiz is due (format: YYYY-MM-DD HH:MM)
   - **Lock Date**: When quiz closes (format: YYYY-MM-DD HH:MM)
5. Options:
   - ✅ **Hide Correct Answers**: Recommended! Students won't see answers, encourages learning
   - ⬜ **Publish Quiz Immediately**: Check to make quiz visible to students right away
   - ✅ **Preview Only**: Keep checked for testing
6. Click "**🎯 Generate Quiz**"
7. Review the generated questions in the console
8. Uncheck "Preview Only" when ready to create in Canvas

## Date Format Examples

Dates can be entered in multiple formats:
- `2024-11-20 23:59` (YYYY-MM-DD HH:MM)
- `2024-11-20` (YYYY-MM-DD, assumes midnight)
- `11/20/2024 23:59` (MM/DD/YYYY HH:MM)
- `11/20/2024` (MM/DD/YYYY, assumes midnight)

## Tips for Professors

### General Tips
- **Always test with "Preview Only" first!** This lets you see what will be created without actually posting to Canvas
- The output console shows all actions being taken
- Both tools run in the background, so the app won't freeze

### Quiz Generator Tips
- **Hide Correct Answers**: This is checked by default and highly recommended! Students can see their score and which questions they got wrong, but not the correct answers. This encourages critical thinking.
- **Unlimited Attempts**: Quizzes allow unlimited attempts so students can learn from their mistakes
- **Transcript Quality**: Better transcripts = better questions. Clean up transcripts if needed.
- **Number of Questions**: Start with 5-10 questions for testing
- **Points**: 1 point per question works well for formative assessments

### Final Project Organizer Tips
- **Folder Structure**: Put all project materials (instructions, rubrics, examples) in one folder
- **File Formats**: Works with PDF, DOCX, PPTX files
- **AI Summary**: The AI will read all files and generate a student-friendly overview
- **Review Before Posting**: Always use Preview mode first to review the generated content

## Troubleshooting

### "Failed to extract text"
- Check that files are readable PDFs/DOCX/PPTX
- Try re-saving files in a standard format

### "No transcript text extracted"
- Verify .vtt files are in the selected folder
- Check that files aren't empty

### "API Error"
- Verify your tokens are correct
- Check that you have OpenAI API credits available
- Ensure Canvas token has proper permissions

### Quiz has no answer options
- Make sure you're using the latest version with the fixed Canvas API format
- Delete the old quiz and create a new one

## Security Notes

- API tokens are stored in memory only during the session
- Tokens are displayed as asterisks (*) for security
- Never share your tokens with others
- You can set environment variables `CANVAS_TOKEN` and `OPENAI_API_KEY` to avoid typing them each time

## Support

For issues or questions:
1. Check the output console for error messages
2. Make sure all required packages are installed
3. Verify your API tokens are valid and have proper permissions

## File Structure

```
canvas-copilot/
├── app.py                          # Main GUI application
├── organize_project.py             # Final project organizer backend
├── automatic_quiz_generator.py     # Quiz generator backend
├── verification_system.py          # NEW! Safety & verification
├── faq_generator.py                # FAQ generator
├── rubric_templates.py             # Rubric templates
├── announcement_generator.py       # Announcement generator
├── Transcripts/                    # Put your .vtt transcript files here
├── final_project/                  # Put your project materials here
├── README.md                       # This file
└── SAFETY_VERIFICATION_GUIDE.md   # NEW! Verification system guide
```

## Additional Documentation

- **[SAFETY_VERIFICATION_GUIDE.md](SAFETY_VERIFICATION_GUIDE.md)** - ⚡ **NEW!** Complete guide to safety features
- **[NEW_FEATURES_GUIDE.md](NEW_FEATURES_GUIDE.md)** - FAQ, Rubrics, Announcements guide
- **[QUICK_START.md](QUICK_START.md)** - Quick start for testing features

## Example Workflow

1. **Set Up** (One time)
   - Get Canvas and OpenAI tokens
   - Enter tokens and course ID in the app

2. **Generate Quiz** (Weekly)
   - Export Zoom transcripts to VTT format
   - Put them in `Transcripts/` folder
   - Run quiz generator with Preview mode
   - Review questions, then create for real
   - Publish when ready

3. **Organize Final Project** (Once per semester)
   - Gather all project materials in one folder
   - Run organizer with Preview mode
   - Review AI-generated description and rubric
   - Upload and schedule for real when satisfied

## License

Created for educational purposes to help professors manage Canvas courses more efficiently.

