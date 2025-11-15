import customtkinter as ctk
from tkinter import filedialog
import canvas_logic
import sys
import os
import threading

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Canvas AI Co-Pilot")
        self.geometry("800x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # --- Input Fields ---
        self.token_label = ctk.CTkLabel(self, text="Canvas Token:")
        self.token_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.token_entry = ctk.CTkEntry(self, width=400)
        self.token_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        if os.getenv("CANVAS_TOKEN"):
            self.token_entry.insert(0, os.getenv("CANVAS_TOKEN"))

        self.course_id_label = ctk.CTkLabel(self, text="Course ID:")
        self.course_id_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.course_id_entry = ctk.CTkEntry(self)
        self.course_id_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.folder_label = ctk.CTkLabel(self, text="Local Folder:")
        self.folder_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.folder_entry = ctk.CTkEntry(self)
        self.folder_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.browse_button = ctk.CTkButton(self, text="Browse", command=self.browse_folder)
        self.browse_button.grid(row=2, column=2, padx=10, pady=5)

        # --- Run Button ---
        self.run_button = ctk.CTkButton(self, text="Run", command=self.run_script)
        self.run_button.grid(row=3, column=1, pady=10)

        # --- Output Text Area ---
        self.output_textbox = ctk.CTkTextbox(self, wrap="word")
        self.output_textbox.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.output_textbox.configure(state="disabled")

        # Redirect stdout
        sys.stdout = self.redirector(self.output_textbox)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, folder_path)

    def run_script(self):
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.configure(state="disabled")

        token = self.token_entry.get()
        course_id = int(self.course_id_entry.get())
        local_folder = self.folder_entry.get()

        canvas_logic.CANVAS_TOKEN = token

        # Run the logic in a separate thread to keep the UI responsive
        threading.Thread(target=self.run_canvas_logic, args=(course_id, local_folder)).start()

    def run_canvas_logic(self, course_id, local_folder):
        try:
            print("--- Starting Final Project Scheduling ---")
            canvas_logic.schedule_final_project_package(course_id, local_folder)
            print("\n--- Starting Final Project Explainer Generation ---")
            canvas_logic.generate_and_post_final_project_explainer(course_id, local_folder=local_folder, dry_run=True)
            print("\n--- Script Finished ---")
        except Exception as e:
            print(f"\n--- ERROR ---")
            print(str(e))

    class redirector:
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
