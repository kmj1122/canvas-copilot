"""
Canvas AI Co-Pilot - User-Friendly GUI for Canvas Course Management

This application provides an easy-to-use interface for professors to:
1. Organize and schedule final project materials
2. Generate quizzes automatically from lecture transcripts
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import sys
import os
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Import the backend modules
import organize_project
import automatic_quiz_generator
import faq_generator
import rubric_templates
import announcement_generator


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Canvas AI Co-Pilot")
        self.geometry("1000x800")
        
        # Set appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Add Help button in top right
        self.help_button = ctk.CTkButton(
            self,
            text="❓ Help",
            command=self.show_help_dialog,
            width=80,
            height=32
        )
        self.help_button.place(relx=0.95, rely=0.02, anchor="ne")

        # ========== API Configuration Section ==========
        self.create_api_config_section()

        # ========== Tabbed Interface for Tools ==========
        self.tabview = ctk.CTkTabview(self, width=950, height=500)
        self.tabview.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="nsew")
        
        # Create tabs
        self.tabview.add("Final Project Organizer")
        self.tabview.add("Quiz Generator")
        self.tabview.add("FAQ Generator")
        self.tabview.add("Rubric Templates")
        self.tabview.add("Announcement Generator")
        
        # Populate tabs
        self.create_project_organizer_tab()
        self.create_quiz_generator_tab()
        self.create_faq_generator_tab()
        self.create_rubric_templates_tab()
        self.create_announcement_generator_tab()

        # ========== Output Console ==========
        self.output_label = ctk.CTkLabel(self, text="Output Console:", font=("Arial", 12, "bold"))
        self.output_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.output_textbox = ctk.CTkTextbox(self, wrap="word", height=200)
        self.output_textbox.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="nsew")
        self.output_textbox.configure(state="disabled")
        self.grid_rowconfigure(3, weight=1)

        # Redirect stdout to output console
        sys.stdout = self.OutputRedirector(self.output_textbox)

    def create_api_config_section(self):
        """Create the API configuration section at the top"""
        config_frame = ctk.CTkFrame(self, fg_color="transparent")
        config_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        config_frame.grid_columnconfigure(1, weight=1)

        # Title
        title = ctk.CTkLabel(
            config_frame,
            text="🔑 API Configuration",
            font=("Arial", 16, "bold")
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 5), sticky="w")
        
        # Help text
        help_text = ctk.CTkLabel(
            config_frame,
            text="Enter your API credentials below. These are required to connect to Canvas and use AI features.",
            font=("Arial", 10),
            text_color="gray"
        )
        help_text.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky="w")

        # Canvas Token
        canvas_token_label = ctk.CTkLabel(
            config_frame, 
            text="Canvas API Token:",
            font=("Arial", 11, "bold")
        )
        canvas_token_label.grid(row=2, column=0, padx=(0, 10), pady=5, sticky="w")
        self.canvas_token_entry = ctk.CTkEntry(
            config_frame, 
            width=400, 
            show="*",
            placeholder_text="Get from Canvas → Account → Settings → New Access Token"
        )
        self.canvas_token_entry.grid(row=2, column=1, pady=5, sticky="ew")
        
        # Show/Hide button for Canvas token
        self.canvas_show_var = ctk.BooleanVar(value=False)
        canvas_show_btn = ctk.CTkButton(
            config_frame, 
            text="Show", 
            width=60,
            command=lambda: self.toggle_token_visibility(self.canvas_token_entry, self.canvas_show_var, canvas_show_btn)
        )
        canvas_show_btn.grid(row=2, column=2, padx=(5, 0), pady=5)
        
        if os.getenv("CANVAS_TOKEN"):
            self.canvas_token_entry.insert(0, os.getenv("CANVAS_TOKEN"))

        # OpenAI Token
        openai_token_label = ctk.CTkLabel(
            config_frame, 
            text="OpenAI API Key:",
            font=("Arial", 11, "bold")
        )
        openai_token_label.grid(row=3, column=0, padx=(0, 10), pady=5, sticky="w")
        self.openai_token_entry = ctk.CTkEntry(
            config_frame, 
            width=400, 
            show="*",
            placeholder_text="Get from platform.openai.com → API Keys"
        )
        self.openai_token_entry.grid(row=3, column=1, pady=5, sticky="ew")
        
        # Show/Hide button for OpenAI key
        self.openai_show_var = ctk.BooleanVar(value=False)
        openai_show_btn = ctk.CTkButton(
            config_frame, 
            text="Show", 
            width=60,
            command=lambda: self.toggle_token_visibility(self.openai_token_entry, self.openai_show_var, openai_show_btn)
        )
        openai_show_btn.grid(row=3, column=2, padx=(5, 0), pady=5)
        
        if os.getenv("OPENAI_API_KEY"):
            self.openai_token_entry.insert(0, os.getenv("OPENAI_API_KEY"))

        # Course ID
        course_id_label = ctk.CTkLabel(
            config_frame, 
            text="Canvas Course ID:",
            font=("Arial", 11, "bold")
        )
        course_id_label.grid(row=4, column=0, padx=(0, 10), pady=5, sticky="w")
        self.course_id_entry = ctk.CTkEntry(
            config_frame, 
            width=200,
            placeholder_text="Find in Canvas URL"
        )
        self.course_id_entry.grid(row=4, column=1, pady=5, sticky="w")
        self.course_id_entry.insert(0, "175906")  # Default course ID
        
        # Help label for Course ID
        course_id_help = ctk.CTkLabel(
            config_frame,
            text="(Look for the number in your Canvas course URL: .../courses/XXXXX)",
            font=("Arial", 9),
            text_color="gray"
        )
        course_id_help.grid(row=5, column=1, pady=(0, 5), sticky="w")

    def show_help_dialog(self):
        """Show a comprehensive help dialog"""
        help_window = ctk.CTkToplevel(self)
        help_window.title("Canvas AI Co-Pilot - Help")
        help_window.geometry("700x600")
        help_window.grab_set()  # Make it modal
        
        # Title
        title = ctk.CTkLabel(
            help_window,
            text="🎓 Canvas AI Co-Pilot - Getting Started",
            font=("Arial", 18, "bold")
        )
        title.pack(pady=20)
        
        # Scrollable frame for help content
        scrollable_frame = ctk.CTkScrollableFrame(help_window, width=650, height=450)
        scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        help_sections = [
            ("🔧 Setup (First Time)", [
                "1. Get your Canvas API Token:",
                "   • Log into Canvas",
                "   • Go to Account → Settings → Approved Integrations",
                "   • Click '+ New Access Token'",
                "   • Copy the token and paste it in the API Configuration section",
                "",
                "2. Get your OpenAI API Key:",
                "   • Visit platform.openai.com",
                "   • Create an account or log in",
                "   • Go to API Keys section",
                "   • Create a new key and paste it in the API Configuration section",
                "",
                "3. Find your Course ID:",
                "   • Open your Canvas course",
                "   • Look at the URL: canvas.../courses/XXXXX",
                "   • The number (XXXXX) is your Course ID"
            ]),
            ("📚 Features Overview", [
                "• Final Project Organizer: Create assignments from project materials",
                "• Quiz Generator: Generate quizzes from lecture transcripts",
                "• FAQ Generator: Create FAQs from student questions",
                "• Rubric Templates: Use pre-made rubrics for common assignments",
                "• Announcement Generator: Create weekly announcements from schedule"
            ]),
            ("✨ Best Practices", [
                "1. Always use 'Preview Only' first to review AI-generated content",
                "2. Check the Output Console for detailed results",
                "3. Review all generated content before posting to Canvas",
                "4. Keep your API tokens secure (use the Hide button)",
                "5. Organize your files in folders before using the tools"
            ]),
            ("⚠️ Important Notes", [
                "• AI-generated content should be reviewed before use",
                "• Preview mode shows what will be created without posting",
                "• All tools respect Canvas API rate limits",
                "• Generated files are saved locally for review",
                "• Course ID can be different for each course"
            ]),
            ("🆘 Need More Help?", [
                "• Each tab has specific instructions at the top",
                "• Check the Output Console for error messages",
                "• Ensure API tokens are valid and have necessary permissions",
                "• Contact your Canvas administrator for API access questions"
            ])
        ]
        
        for section_title, section_content in help_sections:
            # Section title
            section_label = ctk.CTkLabel(
                scrollable_frame,
                text=section_title,
                font=("Arial", 14, "bold"),
                anchor="w"
            )
            section_label.pack(pady=(15, 5), padx=10, anchor="w")
            
            # Section content
            for line in section_content:
                content_label = ctk.CTkLabel(
                    scrollable_frame,
                    text=line,
                    font=("Arial", 11),
                    anchor="w",
                    justify="left"
                )
                content_label.pack(pady=1, padx=10, anchor="w")
        
        # Close button
        close_btn = ctk.CTkButton(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=100
        )
        close_btn.pack(pady=15)

    def toggle_token_visibility(self, entry_widget, bool_var, button_widget):
        """Toggle between showing and hiding token text"""
        if bool_var.get():
            # Currently showing, hide it
            entry_widget.configure(show="*")
            button_widget.configure(text="Show")
            bool_var.set(False)
        else:
            # Currently hidden, show it
            entry_widget.configure(show="")
            button_widget.configure(text="Hide")
            bool_var.set(True)

    def create_project_organizer_tab(self):
        """Create the Project Organizer tab"""
        tab = self.tabview.tab("Final Project Organizer")
        
        # Help/Instructions Section
        help_frame = ctk.CTkFrame(tab, fg_color=("#E3F2FD", "#1E3A5F"))
        help_frame.pack(pady=(10, 10), padx=20, fill="x")
        
        help_title = ctk.CTkLabel(
            help_frame,
            text="How to Use Final Project Organizer",
            font=("Arial", 13, "bold")
        )
        help_title.pack(pady=(10, 5), padx=15, anchor="w")
        
        instructions = [
            "1. Prepare: Place all project materials (PDFs, DOCX, PPTX) in a folder",
            "2. Select: Choose your project materials folder using Browse button",
            "3. Preview: Check 'Preview Only' to see what will be generated (recommended first)",
            "4. Generate: The AI will create a project overview and grading rubric",
            "5. Review: Check the output console for generated content",
            "6. Post: Uncheck 'Preview Only' to upload to Canvas when ready"
        ]
        
        for instruction in instructions:
            inst_label = ctk.CTkLabel(
                help_frame,
                text=instruction,
                font=("Arial", 11),
                anchor="w"
            )
            inst_label.pack(pady=2, padx=25, anchor="w")
        
        tip_label = ctk.CTkLabel(
            help_frame,
            text="💡 Tip: Include clear instructions, rubrics, and examples in your materials for best results.",
            font=("Arial", 10, "italic"),
            text_color=("#1976D2", "#64B5F6")
        )
        tip_label.pack(pady=(5, 10), padx=15, anchor="w")

        # Folder selection
        folder_frame = ctk.CTkFrame(tab)
        folder_frame.pack(pady=10, padx=20, fill="x")
        
        folder_label = ctk.CTkLabel(folder_frame, text="Project Materials Folder:")
        folder_label.pack(side="left", padx=(10, 10))
        
        self.project_folder_entry = ctk.CTkEntry(folder_frame, width=400)
        self.project_folder_entry.pack(side="left", padx=5)
        self.project_folder_entry.insert(0, "final_project")
        
        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse...",
            command=self.browse_project_folder,
            width=100
        )
        browse_btn.pack(side="left", padx=5)

        # Options
        options_frame = ctk.CTkFrame(tab)
        options_frame.pack(pady=10, padx=20, fill="x")
        
        self.project_dry_run = ctk.CTkCheckBox(
            options_frame,
            text="Preview Only (Don't Upload)",
            font=("Arial", 12)
        )
        self.project_dry_run.pack(pady=5, padx=10, anchor="w")
        self.project_dry_run.select()  # Default to preview mode

        # Run button
        run_btn = ctk.CTkButton(
            tab,
            text="Organize Final Project",
            command=self.run_project_organizer,
            height=40,
            font=("Arial", 14, "bold")
        )
        run_btn.pack(pady=20)

    def create_quiz_generator_tab(self):
        """Create the Quiz Generator tab"""
        tab = self.tabview.tab("Quiz Generator")
        
        # Help/Instructions Section
        help_frame = ctk.CTkFrame(tab, fg_color=("#E8F5E9", "#1B5E20"))
        help_frame.pack(pady=(10, 10), padx=20, fill="x")
        
        help_title = ctk.CTkLabel(
            help_frame,
            text="How to Use Quiz Generator",
            font=("Arial", 13, "bold")
        )
        help_title.pack(pady=(10, 5), padx=15, anchor="w")
        
        instructions = [
            "1. Prepare: Export lecture transcripts as .txt, .pdf, or .docx files",
            "2. Select: Choose folder containing your transcript files",
            "3. Configure: Set number of questions, points, and quiz title",
            "4. Dates (Optional): Set when quiz opens, due date, and lock date",
            "5. Preview: Use 'Preview Only' to review questions before posting",
            "6. Post: Uncheck preview to create the quiz on Canvas"
        ]
        
        for instruction in instructions:
            inst_label = ctk.CTkLabel(
                help_frame,
                text=instruction,
                font=("Arial", 11),
                anchor="w"
            )
            inst_label.pack(pady=2, padx=25, anchor="w")
        
        tip_label = ctk.CTkLabel(
            help_frame,
            text="💡 Tip: 'Hide Correct Answers' encourages learning. Use dates to schedule automatic quiz releases.",
            font=("Arial", 10, "italic"),
            text_color=("#2E7D32", "#81C784")
        )
        tip_label.pack(pady=(5, 10), padx=15, anchor="w")

        # Transcripts folder
        folder_frame = ctk.CTkFrame(tab)
        folder_frame.pack(pady=10, padx=20, fill="x")
        
        folder_label = ctk.CTkLabel(folder_frame, text="Transcripts Folder:")
        folder_label.pack(side="left", padx=(10, 10))
        
        self.transcripts_folder_entry = ctk.CTkEntry(folder_frame, width=400)
        self.transcripts_folder_entry.pack(side="left", padx=5)
        self.transcripts_folder_entry.insert(0, "Transcripts")
        
        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse...",
            command=self.browse_transcripts_folder,
            width=100
        )
        browse_btn.pack(side="left", padx=5)

        # Quiz settings
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Left column
        left_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Quiz title
        title_label = ctk.CTkLabel(left_col, text="Quiz Title:")
        title_label.pack(anchor="w", pady=(5, 0))
        self.quiz_title_entry = ctk.CTkEntry(left_col, width=350)
        self.quiz_title_entry.pack(fill="x", pady=(0, 10))
        self.quiz_title_entry.insert(0, "Auto-Generated Quiz from Transcripts")
        
        # Number of questions
        num_q_label = ctk.CTkLabel(left_col, text="Number of Questions:")
        num_q_label.pack(anchor="w", pady=(5, 0))
        self.num_questions_entry = ctk.CTkEntry(left_col, width=100)
        self.num_questions_entry.pack(anchor="w", pady=(0, 10))
        self.num_questions_entry.insert(0, "10")
        
        # Points per question
        points_label = ctk.CTkLabel(left_col, text="Points per Question:")
        points_label.pack(anchor="w", pady=(5, 0))
        self.points_per_q_entry = ctk.CTkEntry(left_col, width=100)
        self.points_per_q_entry.pack(anchor="w", pady=(0, 10))
        self.points_per_q_entry.insert(0, "1")

        # Right column - Dates
        right_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        dates_title = ctk.CTkLabel(right_col, text="📅 Quiz Dates (Optional)", font=("Arial", 12, "bold"))
        dates_title.pack(anchor="w", pady=(0, 10))
        
        # Available date
        unlock_label = ctk.CTkLabel(right_col, text="Available From:")
        unlock_label.pack(anchor="w", pady=(5, 0))
        self.unlock_date_entry = ctk.CTkEntry(right_col, width=200, placeholder_text="YYYY-MM-DD HH:MM")
        self.unlock_date_entry.pack(anchor="w", pady=(0, 10))
        
        # Due date
        due_label = ctk.CTkLabel(right_col, text="Due Date:")
        due_label.pack(anchor="w", pady=(5, 0))
        self.due_date_entry = ctk.CTkEntry(right_col, width=200, placeholder_text="YYYY-MM-DD HH:MM")
        self.due_date_entry.pack(anchor="w", pady=(0, 10))
        
        # Lock date
        lock_label = ctk.CTkLabel(right_col, text="Lock Date:")
        lock_label.pack(anchor="w", pady=(5, 0))
        self.lock_date_entry = ctk.CTkEntry(right_col, width=200, placeholder_text="YYYY-MM-DD HH:MM")
        self.lock_date_entry.pack(anchor="w", pady=(0, 10))

        # Options
        options_frame = ctk.CTkFrame(tab)
        options_frame.pack(pady=10, padx=20, fill="x")
        
        self.hide_answers = ctk.CTkCheckBox(
            options_frame,
            text="Hide Correct Answers (Recommended for Learning)",
            font=("Arial", 12)
        )
        self.hide_answers.pack(pady=5, padx=10, anchor="w")
        self.hide_answers.select()  # Default: hide answers
        
        self.publish_quiz = ctk.CTkCheckBox(
            options_frame,
            text="Publish Quiz Immediately",
            font=("Arial", 12)
        )
        self.publish_quiz.pack(pady=5, padx=10, anchor="w")
        
        self.quiz_dry_run = ctk.CTkCheckBox(
            options_frame,
            text="Preview Only (Don't Create Quiz)",
            font=("Arial", 12)
        )
        self.quiz_dry_run.pack(pady=5, padx=10, anchor="w")
        self.quiz_dry_run.select()  # Default to preview mode

        # Run button
        run_btn = ctk.CTkButton(
            tab,
            text="Generate Quiz",
            command=self.run_quiz_generator,
            height=40,
            font=("Arial", 14, "bold")
        )
        run_btn.pack(pady=20)

    def create_faq_generator_tab(self):
        """Create the FAQ Generator tab"""
        tab = self.tabview.tab("FAQ Generator")
        
        # Help/Instructions Section
        help_frame = ctk.CTkFrame(tab, fg_color=("#FFF3E0", "#E65100"))
        help_frame.pack(pady=(10, 10), padx=20, fill="x")
        
        help_title = ctk.CTkLabel(
            help_frame,
            text="How to Use FAQ Generator",
            font=("Arial", 13, "bold")
        )
        help_title.pack(pady=(10, 5), padx=15, anchor="w")
        
        instructions = [
            "1. Collect: Gather student questions from emails, forum posts, or office hours",
            "2. Save: Put questions in text files (.txt) in a folder",
            "3. Select: Choose your questions folder",
            "4. Configure: Set max number of FAQs and output format (Markdown or HTML)",
            "5. Generate: AI reads syllabus for context and creates accurate answers",
            "6. Verify: System checks FAQ quality and flags issues",
            "7. Post (Optional): Check 'Post FAQ as Canvas Announcement' to publish",
            "8. Review: Check output console, verification report, and generated FAQ file"
        ]
        
        for instruction in instructions:
            inst_label = ctk.CTkLabel(
                help_frame,
                text=instruction,
                font=("Arial", 11),
                anchor="w"
            )
            inst_label.pack(pady=2, padx=25, anchor="w")
        
        tip_label = ctk.CTkLabel(
            help_frame,
            text="💡 Tip: Place syllabus files in 'sllaybus' folder for automatic course context extraction.",
            font=("Arial", 10, "italic"),
            text_color=("#E65100", "#FFB74D")
        )
        tip_label.pack(pady=(5, 10), padx=15, anchor="w")

        # Questions folder
        folder_frame = ctk.CTkFrame(tab)
        folder_frame.pack(pady=10, padx=20, fill="x")
        
        folder_label = ctk.CTkLabel(folder_frame, text="Questions Folder:")
        folder_label.pack(side="left", padx=(10, 10))
        
        self.questions_folder_entry = ctk.CTkEntry(folder_frame, width=400)
        self.questions_folder_entry.pack(side="left", padx=5)
        self.questions_folder_entry.insert(0, "student_questions")
        
        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Browse...",
            command=self.browse_questions_folder,
            width=100
        )
        browse_btn.pack(side="left", padx=5)

        # Settings
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.pack(pady=10, padx=20, fill="x")
        
        max_label = ctk.CTkLabel(settings_frame, text="Max FAQs:")
        max_label.pack(side="left", padx=(10, 10))
        
        self.max_faqs_entry = ctk.CTkEntry(settings_frame, width=100)
        self.max_faqs_entry.pack(side="left", padx=5)
        self.max_faqs_entry.insert(0, "20")
        
        format_label = ctk.CTkLabel(settings_frame, text="Format:")
        format_label.pack(side="left", padx=(20, 10))
        
        self.faq_format_var = ctk.StringVar(value="markdown")
        format_dropdown = ctk.CTkOptionMenu(
            settings_frame,
            variable=self.faq_format_var,
            values=["markdown", "html"]
        )
        format_dropdown.pack(side="left", padx=5)

        # Options
        options_frame = ctk.CTkFrame(tab)
        options_frame.pack(pady=10, padx=20, fill="x")
        
        self.post_faq_to_canvas = ctk.CTkCheckBox(
            options_frame,
            text="Post FAQ as Canvas Announcement",
            font=("Arial", 12)
        )
        self.post_faq_to_canvas.pack(pady=5, padx=10, anchor="w")

        # Run button
        run_btn = ctk.CTkButton(
            tab,
            text="Generate FAQ",
            command=self.run_faq_generator,
            height=40,
            font=("Arial", 14, "bold")
        )
        run_btn.pack(pady=20)

    def create_rubric_templates_tab(self):
        """Create the Rubric Templates tab"""
        tab = self.tabview.tab("Rubric Templates")   
        
        # Help/Instructions Section
        help_frame = ctk.CTkFrame(tab, fg_color=("#F3E5F5", "#4A148C"))
        help_frame.pack(pady=(10, 10), padx=20, fill="x")
        
        help_title = ctk.CTkLabel(
            help_frame,
            text="How to Use Rubric Templates",
            font=("Arial", 13, "bold")
        )
        help_title.pack(pady=(10, 5), padx=15, anchor="w")
        
        instructions = [
            "1. Choose: Select a rubric template from the dropdown (essay, presentation, lab, etc.)",
            "2. Customize: Set total points for the assignment",
            "3. Format: Choose output format (Markdown, HTML, or JSON)",
            "4. Generate: Click to create the rubric file",
            "5. Review: Check the output console for rubric preview",
            "6. Use: Copy rubric to Canvas or customize further as needed"
        ]
        
        for instruction in instructions:
            inst_label = ctk.CTkLabel(
                help_frame,
                text=instruction,
                font=("Arial", 11),
                anchor="w"
            )
            inst_label.pack(pady=2, padx=25, anchor="w")
        
        tip_label = ctk.CTkLabel(
            help_frame,
            text="💡 Tip: Templates provide starting points. Edit the generated file to match your needs.",
            font=("Arial", 10, "italic"),
            text_color=("#6A1B9A", "#CE93D8")
        )
        tip_label.pack(pady=(5, 10), padx=15, anchor="w")

        # Template selection
        template_frame = ctk.CTkFrame(tab)
        template_frame.pack(pady=10, padx=20, fill="x")
        
        template_label = ctk.CTkLabel(template_frame, text="Rubric Template:")
        template_label.pack(side="left", padx=(10, 10))
        
        self.rubric_template_var = ctk.StringVar(value="essay")
        template_dropdown = ctk.CTkOptionMenu(
            template_frame,
            variable=self.rubric_template_var,
            values=list(rubric_templates.list_templates())
        )
        template_dropdown.pack(side="left", padx=5)

        # Settings
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.pack(pady=10, padx=20, fill="x")
        
        points_label = ctk.CTkLabel(settings_frame, text="Total Points:")
        points_label.pack(side="left", padx=(10, 10))
        
        self.rubric_points_entry = ctk.CTkEntry(settings_frame, width=100)
        self.rubric_points_entry.pack(side="left", padx=5)
        self.rubric_points_entry.insert(0, "100")
        
        format_label = ctk.CTkLabel(settings_frame, text="Format:")
        format_label.pack(side="left", padx=(20, 10))
        
        self.rubric_format_var = ctk.StringVar(value="markdown")
        format_dropdown = ctk.CTkOptionMenu(
            settings_frame,
            variable=self.rubric_format_var,
            values=["markdown", "html", "json"]
        )
        format_dropdown.pack(side="left", padx=5)

        # Run button
        run_btn = ctk.CTkButton(
            tab,
            text="Generate Rubric",
            command=self.run_rubric_generator,
            height=40,
            font=("Arial", 14, "bold")
        )
        run_btn.pack(pady=20)

    def create_announcement_generator_tab(self):
        """Create the Announcement Generator tab"""
        tab = self.tabview.tab("Announcement Generator")
        
        # Help/Instructions Section
        help_frame = ctk.CTkFrame(tab, fg_color=("#FCE4EC", "#880E4F"))
        help_frame.pack(pady=(10, 10), padx=20, fill="x")
        
        help_title = ctk.CTkLabel(
            help_frame,
            text="How to Use Announcement Generator",
            font=("Arial", 13, "bold")
        )
        help_title.pack(pady=(10, 5), padx=15, anchor="w")
        
        instructions = [
            "1. Prepare: Create a schedule file (.txt or .md) with weekly topics and dates",
            "2. Select: Choose your schedule file",
            "3. Week: Enter the week number to generate announcement for",
            "4. Preview: Use 'Preview Only' to see the announcement first",
            "5. Post: Check 'Post to Canvas' and uncheck preview to publish",
            "6. Review: Check output console for announcement content"
        ]
        
        for instruction in instructions:
            inst_label = ctk.CTkLabel(
                help_frame,
                text=instruction,
                font=("Arial", 11),
                anchor="w"
            )
            inst_label.pack(pady=2, padx=25, anchor="w")
        
        tip_label = ctk.CTkLabel(
            help_frame,
            text="💡 Tip: Schedule file format: 'Week X: Topic - Date'. AI will create engaging announcements.",
            font=("Arial", 10, "italic"),
            text_color=("#AD1457", "#F48FB1")
        )
        tip_label.pack(pady=(5, 10), padx=15, anchor="w")

        # Schedule file
        file_frame = ctk.CTkFrame(tab)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        file_label = ctk.CTkLabel(file_frame, text="Schedule File:")
        file_label.pack(side="left", padx=(10, 10))
        
        self.schedule_file_entry = ctk.CTkEntry(file_frame, width=400)
        self.schedule_file_entry.pack(side="left", padx=5)
        self.schedule_file_entry.insert(0, "schedule.txt")
        
        browse_btn = ctk.CTkButton(
            file_frame,
            text="Browse...",
            command=self.browse_schedule_file,
            width=100
        )
        browse_btn.pack(side="left", padx=5)

        # Settings
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.pack(pady=10, padx=20, fill="x")
        
        week_label = ctk.CTkLabel(settings_frame, text="Week Number:")
        week_label.pack(side="left", padx=(10, 10))
        
        self.week_number_entry = ctk.CTkEntry(settings_frame, width=100)
        self.week_number_entry.pack(side="left", padx=5)
        self.week_number_entry.insert(0, "1")

        # Options
        options_frame = ctk.CTkFrame(tab)
        options_frame.pack(pady=10, padx=20, fill="x")
        
        self.post_announcement = ctk.CTkCheckBox(
            options_frame,
            text="Post to Canvas",
            font=("Arial", 12)
        )
        self.post_announcement.pack(pady=5, padx=10, anchor="w")
        
        self.announcement_dry_run = ctk.CTkCheckBox(
            options_frame,
            text="Preview Only",
            font=("Arial", 12)
        )
        self.announcement_dry_run.pack(pady=5, padx=10, anchor="w")
        self.announcement_dry_run.select()

        # Run button
        run_btn = ctk.CTkButton(
            tab,
            text="Generate Announcement",
            command=self.run_announcement_generator,
            height=40,
            font=("Arial", 14, "bold")
        )
        run_btn.pack(pady=20)

    def browse_project_folder(self):
        """Browse for project materials folder"""
        folder_path = filedialog.askdirectory(title="Select Final Project Materials Folder")
        if folder_path:
            self.project_folder_entry.delete(0, "end")
            self.project_folder_entry.insert(0, folder_path)

    def browse_transcripts_folder(self):
        """Browse for transcripts folder"""
        folder_path = filedialog.askdirectory(title="Select Transcripts Folder")
        if folder_path:
            self.transcripts_folder_entry.delete(0, "end")
            self.transcripts_folder_entry.insert(0, folder_path)

    def browse_questions_folder(self):
        """Browse for questions folder"""
        folder_path = filedialog.askdirectory(title="Select Questions Folder")
        if folder_path:
            self.questions_folder_entry.delete(0, "end")
            self.questions_folder_entry.insert(0, folder_path)

    def browse_schedule_file(self):
        """Browse for schedule file"""
        file_path = filedialog.askopenfilename(
            title="Select Schedule File",
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if file_path:
            self.schedule_file_entry.delete(0, "end")
            self.schedule_file_entry.insert(0, file_path)

    def parse_date(self, date_str: str) -> str:
        """Convert user-friendly date to ISO format"""
        if not date_str or date_str.strip() == "":
            return None
        
        try:
            # Try parsing various formats
            for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d", "%m/%d/%Y %H:%M", "%m/%d/%Y"]:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def clear_output(self):
        """Clear the output console"""
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.configure(state="disabled")

    def run_project_organizer(self):
        """Run the final project organizer"""
        self.clear_output()
        
        # Validate inputs
        canvas_token = self.canvas_token_entry.get().strip()
        openai_key = self.openai_token_entry.get().strip()
        course_id = self.course_id_entry.get().strip()
        local_folder = self.project_folder_entry.get().strip()
        
        if not canvas_token:
            messagebox.showerror("Error", "Please enter your Canvas API Token")
            return
        if not openai_key:
            messagebox.showerror("Error", "Please enter your OpenAI API Key")
            return
        if not course_id or not course_id.isdigit():
            messagebox.showerror("Error", "Please enter a valid Course ID")
            return
        if not local_folder:
            messagebox.showerror("Error", "Please select a project materials folder")
            return
        
        # Set environment variables
        organize_project.CANVAS_TOKEN = canvas_token
        organize_project.OPENAI_API_KEY = openai_key
        
        dry_run = self.project_dry_run.get() == 1
        
        # Run in separate thread
        threading.Thread(
            target=self.run_project_organizer_thread,
            args=(int(course_id), local_folder, dry_run, canvas_token, openai_key),
            daemon=True
        ).start()

    def run_project_organizer_thread(self, course_id, local_folder, dry_run, canvas_token, openai_key):
        """Thread function for project organizer"""
        try:
            print("=" * 60)
            print("📚 FINAL PROJECT ORGANIZER")
            print("=" * 60)
            
            self.run_organizer_subprocess(
                course_id=course_id,
                local_folder=local_folder,
                dry_run=dry_run,
                canvas_token=canvas_token,
                openai_key=openai_key,
            )
            
            print("\n" + "=" * 60)
            print("✅ Process completed successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def run_organizer_subprocess(self, course_id: int, local_folder: str, dry_run: bool,
                                 canvas_token: str, openai_key: str) -> None:
        """Invoke organize_project.py in a fresh process (safer for C extensions)."""
        script_path = Path(__file__).resolve().parent / "organize_project.py"
        if not script_path.exists():
            raise FileNotFoundError(f"Could not find organize_project.py at {script_path}")
        
        args = [
            sys.executable,
            str(script_path),
            "--course-id", str(course_id),
            "--local-folder", local_folder,
        ]
        if dry_run:
            args.append("--dry-run")
        
        env = os.environ.copy()
        env["CANVAS_TOKEN"] = canvas_token
        env["OPENAI_API_KEY"] = openai_key
        
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            text=True,
            cwd=str(script_path.parent),
        )
        
        assert process.stdout is not None
        for line in process.stdout:
            print(line.rstrip())
        process.wait()
        
        if process.returncode != 0:
            raise RuntimeError(
                f"organize_project.py exited with code {process.returncode}. "
                "See output above for details."
            )

    def run_quiz_generator(self):
        """Run the quiz generator"""
        self.clear_output()
        
        # Validate inputs
        canvas_token = self.canvas_token_entry.get().strip()
        openai_key = self.openai_token_entry.get().strip()
        course_id = self.course_id_entry.get().strip()
        transcripts_folder = self.transcripts_folder_entry.get().strip()
        quiz_title = self.quiz_title_entry.get().strip()
        
        if not canvas_token:
            messagebox.showerror("Error", "Please enter your Canvas API Token")
            return
        if not openai_key:
            messagebox.showerror("Error", "Please enter your OpenAI API Key")
            return
        if not course_id or not course_id.isdigit():
            messagebox.showerror("Error", "Please enter a valid Course ID")
            return
        if not transcripts_folder:
            messagebox.showerror("Error", "Please select a transcripts folder")
            return
        if not quiz_title:
            messagebox.showerror("Error", "Please enter a quiz title")
            return
        
        try:
            num_questions = int(self.num_questions_entry.get())
            points_per_q = int(self.points_per_q_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Number of questions and points must be integers")
            return
        
        # Set tokens in both modules
        organize_project.CANVAS_TOKEN = canvas_token
        organize_project.OPENAI_API_KEY = openai_key
        automatic_quiz_generator.CANVAS_TOKEN = canvas_token
        automatic_quiz_generator.OPENAI_API_KEY = openai_key
        
        # Parse dates
        unlock_at = self.parse_date(self.unlock_date_entry.get())
        due_at = self.parse_date(self.due_date_entry.get())
        lock_at = self.parse_date(self.lock_date_entry.get())
        
        hide_answers = self.hide_answers.get() == 1
        publish = self.publish_quiz.get() == 1
        dry_run = self.quiz_dry_run.get() == 1
        
        # Run in separate thread
        threading.Thread(
            target=self.run_quiz_generator_thread,
            args=(
                int(course_id), transcripts_folder, quiz_title,
                num_questions, points_per_q, unlock_at, due_at, lock_at,
                hide_answers, publish, dry_run
            ),
            daemon=True
        ).start()

    def run_quiz_generator_thread(
        self, course_id, transcripts_folder, quiz_title,
        num_questions, points_per_q, unlock_at, due_at, lock_at,
        hide_answers, publish, dry_run
    ):
        """Thread function for quiz generator"""
        try:
            print("=" * 60)
            print("📝 AUTOMATIC QUIZ GENERATOR")
            print("=" * 60)
            
            automatic_quiz_generator.generate_quiz_from_transcripts(
                course_id=course_id,
                transcripts_folder=transcripts_folder,
                quiz_title=quiz_title,
                num_questions=num_questions,
                points_per_question=points_per_q,
                unlock_at=unlock_at,
                due_at=due_at,
                lock_at=lock_at,
                hide_correct_answers=hide_answers,
                publish=publish,
                dry_run=dry_run,
            )
            
            print("\n" + "=" * 60)
            print("✅ Process completed successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    def run_faq_generator(self):
        """Run the FAQ generator"""
        self.clear_output()
        
        canvas_token = self.canvas_token_entry.get().strip()
        openai_key = self.openai_token_entry.get().strip()
        course_id = self.course_id_entry.get().strip()
        questions_folder = self.questions_folder_entry.get().strip()
        
        if not openai_key:
            messagebox.showerror("Error", "Please enter your OpenAI API Key")
            return
        if not questions_folder:
            messagebox.showerror("Error", "Please select a questions folder")
            return
        
        post_to_canvas = self.post_faq_to_canvas.get() == 1
        
        # Validate Canvas requirements if posting
        if post_to_canvas:
            if not canvas_token:
                messagebox.showerror("Error", "Canvas API token required to post announcement")
                return
            if not course_id or not course_id.isdigit():
                messagebox.showerror("Error", "Valid Course ID required to post announcement")
                return
        
        try:
            max_faqs = int(self.max_faqs_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Max FAQs must be an integer")
            return
        
        # Set tokens
        organize_project.CANVAS_TOKEN = canvas_token
        organize_project.OPENAI_API_KEY = openai_key
        faq_generator.CANVAS_TOKEN = canvas_token
        faq_generator.OPENAI_API_KEY = openai_key
        
        format_type = self.faq_format_var.get()
        
        # Run in separate thread
        threading.Thread(
            target=self.run_faq_generator_thread,
            args=(questions_folder, max_faqs, format_type, post_to_canvas, int(course_id) if course_id else None),
            daemon=True
        ).start()

    def run_faq_generator_thread(self, questions_folder, max_faqs, format_type, post_to_canvas, course_id):
        """Thread function for FAQ generator"""
        try:
            print("=" * 60)
            print("❓ FAQ GENERATOR")
            print("=" * 60)
            
            faq_generator.generate_faq_document(
                questions_folder=questions_folder,
                output_path=f"course_faq.{format_type}",
                max_faqs=max_faqs,
                format=format_type,
                syllabus_folder="sllaybus",  # Auto-read course context from syllabus
                post_to_canvas=post_to_canvas,
                course_id=course_id,
                announcement_title="Course FAQ - Frequently Asked Questions"
            )
            
            print("\n" + "=" * 60)
            print("✅ Process completed successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    def run_rubric_generator(self):
        """Run the rubric generator"""
        self.clear_output()
        
        template_name = self.rubric_template_var.get()
        
        try:
            total_points = int(self.rubric_points_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Total points must be an integer")
            return
        
        format_type = self.rubric_format_var.get()
        
        # Run in separate thread
        threading.Thread(
            target=self.run_rubric_generator_thread,
            args=(template_name, total_points, format_type),
            daemon=True
        ).start()

    def run_rubric_generator_thread(self, template_name, total_points, format_type):
        """Thread function for rubric generator"""
        try:
            print("=" * 60)
            print("📋 RUBRIC GENERATOR")
            print("=" * 60)
            
            # Get and customize template
            rubric = rubric_templates.customize_rubric(
                template_name,
                total_points=total_points
            )
            
            # Save
            ext = "md" if format_type == "markdown" else format_type
            output_path = rubric_templates.save_rubric(
                rubric,
                f"rubric_{template_name}.{ext}",
                format=format_type
            )
            
            # Display
            print(f"\n✓ Rubric saved to: {output_path}")
            print("\n" + "=" * 60)
            print("RUBRIC PREVIEW")
            print("=" * 60)
            print(rubric_templates.format_rubric_as_markdown(rubric))
            print("=" * 60)
            
            print("\n" + "=" * 60)
            print("✅ Process completed successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    def run_announcement_generator(self):
        """Run the announcement generator"""
        self.clear_output()
        
        openai_key = self.openai_token_entry.get().strip()
        canvas_token = self.canvas_token_entry.get().strip()
        course_id = self.course_id_entry.get().strip()
        schedule_file = self.schedule_file_entry.get().strip()
        
        if not openai_key:
            messagebox.showerror("Error", "Please enter your OpenAI API Key")
            return
        if not schedule_file:
            messagebox.showerror("Error", "Please select a schedule file")
            return
        
        try:
            week_number = int(self.week_number_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Week number must be an integer")
            return
        
        post = self.post_announcement.get() == 1
        dry_run = self.announcement_dry_run.get() == 1
        
        if post and not dry_run:
            if not canvas_token:
                messagebox.showerror("Error", "Canvas API token required to post announcements")
                return
            if not course_id or not course_id.isdigit():
                messagebox.showerror("Error", "Valid Course ID required to post announcements")
                return
        
        # Set tokens
        organize_project.CANVAS_TOKEN = canvas_token
        organize_project.OPENAI_API_KEY = openai_key
        announcement_generator.CANVAS_TOKEN = canvas_token
        announcement_generator.OPENAI_API_KEY = openai_key
        
        # Run in separate thread
        threading.Thread(
            target=self.run_announcement_generator_thread,
            args=(int(course_id) if course_id else None, schedule_file, week_number, post, dry_run),
            daemon=True
        ).start()

    def run_announcement_generator_thread(self, course_id, schedule_file, week_number, post, dry_run):
        """Thread function for announcement generator"""
        try:
            print("=" * 60)
            print("📢 ANNOUNCEMENT GENERATOR")
            print("=" * 60)
            
            announcement_generator.generate_weekly_announcement(
                course_id=course_id,
                schedule_file=schedule_file,
                week_number=week_number,
                post_to_canvas=post,
                dry_run=dry_run
            )
            
            print("\n" + "=" * 60)
            print("✅ Process completed successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    class OutputRedirector:
        """Redirect stdout to the textbox"""
        def __init__(self, widget):
            self.widget = widget

        def write(self, text):
            self.widget.configure(state="normal")
            self.widget.insert("end", text)
            self.widget.see("end")
            self.widget.configure(state="disabled")

        def flush(self):
            pass


if __name__ == "__main__":
    app = App()
    app.mainloop()
