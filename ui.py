"""
ui.py
Author: Matt Lindborg
Course: MS548 - Advanced Programming Concepts and AI
Assignment: Week 2
Date: 9/15/2025

Purpose:
This file defines the Tkinter-based graphical user interface (GUI)
for the Learnflow Base application. The GUI layer is responsible for:
    - Displaying buttons, menus, and text areas to the user.
    - Collecting input via popup dialogs.
    - Rendering summaries and history of entries.
    - Delegating business logic to the LearnflowService (service.py).

This file does NOT contain data storage logic. Instead:
    - It calls service methods to set/get data.
    - It uses the domain model (LearningLog, EntryType) indirectly.
    - It is designed to be event-driven (each button triggers a method).
"""

# --- Imports ---
import tkinter as tk
from tkinter import filedialog   # standard Tkinter dialogs
import json                                  # for save/load functionality
from textblob import TextBlob                # sentiment analysis for Notes
from service import LearnflowService         # service layer abstraction
from domain import EntryType, GoalLog, ReflectionLog
import csv # excel file output


class App:
    """
    The App class defines the GUI layout and event handlers.
    It is initialized with a root Tkinter window and a LearnflowService.
    """

    def __init__(self, root: tk.Tk, service: LearnflowService):
        """
        Constructor initializes the window, builds the layout,
        and renders the initial summary display.
        """
        # hold references to the Tk root and the business service
        self.root = root
        self.service = service

        # configure window title and disable resizing
        self.root.title("Learnflow Base")
        self.root.resizable(False, False)
        self.root.geometry("625x755") # hard coded to not waste space

        # set base background and foreground
        self.root.option_add("*Background", "#2b2b2b")      # dark gray background
        self.root.option_add("*Foreground", "#ffffff")      # white text

        # button colors
        self.root.option_add("*Button.Background", "#444444")
        self.root.option_add("*Button.Foreground", "#ffffff")
        self.root.option_add("*Button.ActiveBackground", "#666666")
        self.root.option_add("*Button.ActiveForeground", "#ffffff")

        # entry box colors
        self.root.option_add("*Entry.Background", "#1e1e1e")
        self.root.option_add("*Entry.Foreground", "#dcdcdc")
        self.root.option_add("*Entry.InsertBackground", "#ffffff")

        # text box colors
        self.root.option_add("*Text.Background", "#1e1e1e")
        self.root.option_add("*Text.Foreground", "#dcdcdc")

        # menu colors
        self.root.option_add("*Menu.Background", "#2b2b2b")
        self.root.option_add("*Menu.Foreground", "#ffffff")
        self.root.option_add("*Menu.ActiveBackground", "#444444")
        self.root.option_add("*Menu.ActiveForeground", "#ffffff")

        # global font setting
        default_font = ("Segoe UI", 10)

        # --- Main container frame ---
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky="nw")
        #main_frame.columnconfigure(0, weight=1)

        # --- Top row: welcome label, Clear button, Drop-down menu ---
        top_frame = tk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(0, weight=1)

        # main title label
        self.display_label = tk.Label(
            top_frame,
            text="Welcome to Learnflow\nPlease choose an option",
            font=("Georgia", 14),
            pady=2,
            justify="left",
        )
        self.display_label.grid(row=0, column=0, sticky="w")

        # summary box shows compact view of Goal/Skill/Session/Notes
        self.summary_box = tk.Text(
            top_frame,
            height=4,
            width=40,
            wrap="word",
            state="disabled",
            font=default_font
        )
        self.summary_box.grid(row=0, column=2, padx=(5, 5), sticky="n")

        # clear button
        self.clear_button = tk.Button(
            top_frame, text="Clear", width=7, command=self.clear_entries
        )
        self.clear_button.grid(row=0, column=1, sticky="w", padx=(5, 10))

        # attach a menubar
        self.build_menu()

        # --- Middle row: buttons for Goal/Skill/Session/Notes ---
        middle_frame = tk.Frame(main_frame)
        middle_frame.grid(row=1, column=0, sticky="nsew", pady=5)

        # image on the left
        try:
            self.image = tk.PhotoImage(file="images\\image2_50pc.png")
            self.image_label = tk.Label(middle_frame, image=self.image)
            self.image_label.pack(side="left", padx=(0, 10))
        except Exception:
            # fail gracefully if image not found
            pass

        # right frame with stacked buttons and log box
        right_frame = tk.Frame(middle_frame)
        right_frame.pack(side="left", anchor="n")

        # button frame
        buttons_frame = tk.Frame(right_frame)
        buttons_frame.pack(side="left", anchor="n", padx=(0, 5))

        # create one button per EntryType
        for et in (EntryType.Goal, EntryType.Skill, EntryType.Session, EntryType.Notes):
            tk.Button(
                buttons_frame,
                text=et.value,
                width=10,
                command=lambda t=et: self.on_add_or_edit_entry(t),
            ).pack(pady=2, anchor="w")

        # --- Bottom row: ai input and responses output box ---
        ai_frame = tk.Frame(main_frame) # llm not integrated yet
        ai_frame.grid(row=3, column=0, sticky="ew", pady=(0, 5), padx=(0, 5))

        # input field for user prompt to AI (currently placeholder)
        self.ai_entry = tk.Entry(
            ai_frame, 
            width=60, 
            font=default_font
            )
        self.ai_entry.insert(0, "Type your question for the AI here...")

        # remove placeholder when clicking into the box
        self.ai_entry.bind("<FocusIn>", self.clear_placeholder)

        # restore placeholder if the box is empty when leaving it
        #self.ai_entry.bind("<FocusOut>", self.restore_placeholder)

        # pressing Enter should submit text
        self.ai_entry.bind("<Return>", self.submit_ai_text)

        # detect typing so we can shift focus logic if needed
        self.ai_entry.bind("<KeyRelease>", self.focus_send_button)

        # location in the frame
        self.ai_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # send button (currently only echoes placeholder response)
        self.ai_send_button = tk.Button(
            ai_frame,
            text="Send",
            command=lambda: self.display_ai_response(self.ai_entry.get())
        )
        self.ai_send_button.pack(side="right")

        # ai ouptut frame
        ai_output_frame = tk.Frame(main_frame)
        ai_output_frame.grid(row=4, column=0, sticky="w", pady=(2, 0))

        # output box for AI responses
        self.ai_output_box = tk.Text(
            ai_output_frame,
            width=86,
            height=6,
            wrap="word",
            state="normal",
            font=default_font
        )
        self.ai_output_box.insert(tk.END, "Placeholder: AI responses will appear here...\n\n")
        self.ai_output_box.config(state="disabled")
        self.ai_output_box.pack(side="left", fill="both", expand=True)

        # enforce minimum window size after widgets load
        # locking in the size to never be smaller than the app content
        #self.root.update_idletasks()
        #self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

        # initial render from service
        self.render_summary()

    # ------------------- VIEW HELPERS -------------------

    def custom_input_popup(self, title: str, prompt: str) -> str | None:
        """
        Custom popup dialog for text input.
        Reused by button handlers to collect user entries.
        """
        popup = tk.Toplevel(self.root)
        popup.title(title)

        # calculate centered popup position relative to root window
        self.center_popup(popup, 300, 150)

        # add label and entry box
        tk.Label(popup, text=prompt, font=("Segoe UI", 9)).pack(pady=10)
        entry = tk.Entry(popup, width=40)
        entry.pack(pady=5)
        entry.focus_set()

        result = {"value": None}

        def on_ok(event=None):
            result["value"] = entry.get()
            popup.destroy()

        tk.Button(popup, text="OK", command=on_ok).pack(pady=10)
        popup.bind("<Return>", on_ok)
        self.root.wait_window(popup)
        return result["value"]
    
    def custom_message_popup(self, title: str, message: str, msg_type: str = "info"):
        """
        Custom message popup to replace default messagebox dialogs.
        - title: window title text
        - message: main message content
        - msg_type: "info", "error", "warning" (affects color scheme)
        """

        # create a popup window
        popup = tk.Toplevel(self.root)
        popup.title(title)

        # center popup relative to main window
        self.center_popup(popup, 300, 150)

        # choose colors based on message type
        if msg_type == "error":
            bg_color = "#5c2b2b"
            fg_color = "#ffcccc"
        elif msg_type == "warning":
            bg_color = "#5c5c2b"
            fg_color = "#ffffcc"
        else:  # info
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"

        popup.configure(bg=bg_color)

        # label for message text
        label = tk.Label(
            popup,
            text=message,
            bg=bg_color,
            fg=fg_color,
            wraplength=260,
            font=("Segoe UI", 9)
        )
        label.pack(pady=15, padx=10)

        # ok button to close popup
        ok_button = tk.Button(
            popup,
            text="OK",
            bg="#444444",
            fg="#ffffff",
            activebackground="#666666",
            activeforeground="#ffffff",
            command=popup.destroy
        )
        ok_button.pack(pady=10)

        # focus button and allow Enter key to close
        ok_button.focus_set()
        popup.bind("<Return>", lambda event=None: popup.destroy())

    def render_summary(self) -> None:
        """
        Render the latest entries (summary) in the bottom output box.
        """
        summary = self.service.summary()

        # update summary box
        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", tk.END)
        for val in summary.values():
            self.summary_box.insert(tk.END, f"{val}\n")
        self.summary_box.config(state="disabled")

    def clear_placeholder(self, event):
        """
        Remove placeholder text when user clicks into the entry box.
        """
        if self.ai_entry.get().strip() == "Type your question for the AI here...":
            self.ai_entry.delete(0, tk.END)
            self.ai_entry.unbind("<FocusIn>")

    '''def restore_placeholder(self, event):
        """
        Restore placeholder text if user leaves the box empty.
        """
        if not self.ai_entry.get().strip():
            self.ai_entry.insert(0, "Type your question for the AI here...")'''

    def submit_ai_text(self, event=None):
        """
        Handle AI entry submission:
        - Append text into the AI output box
        - Append placeholder AI response
        - Keep placeholder behavior intact
        """
        user_input = self.ai_entry.get().strip()

        # ignore if placeholder or empty
        if not user_input or user_input == "Type your question for the AI here...":
            return

        # insert into output box (below existing placeholder message)
        self.ai_output_box.config(state="normal")
        self.ai_output_box.insert(tk.END, f"You: {user_input}\n")

        # insert a fake AI response placeholder
        self.ai_output_box.insert(tk.END, "AI: (placeholder response)\n\n")

        # scroll to bottom and lock text box again
        self.ai_output_box.see(tk.END)
        self.ai_output_box.config(state="disabled")

        # clear entry box and reset placeholder
        self.ai_entry.delete(0, tk.END)
        #self.restore_placeholder(None)

        # shift focus to the Send button after submit
        self.ai_entry.focus_set()

    def focus_send_button(self, event):
        """
        If the user has started typing real text,
        keep focus in the entry box until Enter is pressed.
        """
        current_text = self.ai_entry.get().strip()
        if current_text and current_text != "Type your question for the AI here...":
            # Keep focus in the entry so user can continue typing
            self.ai_entry.focus_set()

    # ------------------- EVENT HANDLERS -------------------
    def on_add_or_edit_entry(self, entry_type: EntryType):
        """
        Event handler for Goal/Skill/Session/Notes buttons.
        Steps:
            - Open custom popup for user input.
            - If Goal → create a GoalLog (with status).
            - If Notes → create a ReflectionLog (with mood analysis).
            - Otherwise → use normal LearningLog via service.
            - Re-render summary output.
        """
        text = self.custom_input_popup("Input", f"Enter your {entry_type.value}:")
        if not text:
            return  # user canceled

        if entry_type == EntryType.Goal:
            # create a GoalLog entry with default status
            goal_log = GoalLog(entry_type, text)
            self.service._state.entries[entry_type].append(goal_log)
            self.service.write_log(goal_log)

        elif entry_type == EntryType.Notes:
            # create a ReflectionLog entry and run mood analysis
            reflection_log = ReflectionLog(entry_type, text)
            mood = self.analyze_mood(text)      # use the TextBlob helper
            reflection_log.mood = mood          # save the detected mood
            self.service._state.entries[entry_type].append(reflection_log)
            self.service.write_log(reflection_log)
        else:
            # use normal service method (LearningLog)
            self.service.set_entry(entry_type, text)

        self.render_summary()

    def clear_entries(self) -> None:
        """
        Clear all entries from the service and refresh display.
        """
        self.service.clear()
        self.render_summary()
        self.custom_message_popup("Cleared", "All entries have been cleared.", msg_type="info")

    def display_ai_response(self, user_input: str):
        """
        Display ai responses to user
        """
        if not user_input.strip():
            return
        self.ai_output_box.config(state="normal")
        self.ai_output_box.insert(tk.END, f"You: {user_input}\n")
        self.ai_output_box.insert(tk.END, "AI: (placeholder response)\n\n")
        self.ai_output_box.config(state="disabled")
        self.ai_output_box.see(tk.END)
        self.ai_entry.delete(0, tk.END)

    # ------------------- MENU & FILE OPS -------------------

    def build_menu(self):
        """
        Build the top menubar with File menu options.
        """
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save", command=self.save_entries) # save data entries in json formatted file
        file_menu.add_command(label="Load", command=self.load_entries) # load data entries in json formatted file
        file_menu.add_command(label="Export CSV", command=self.export_csv)  # export history to Excel-readable format
        file_menu.add_command(label="View History", command=self.show_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        self.root.config(menu=menubar)

        # add Entries menu with entry-related actions
        entries_menu = tk.Menu(menubar, tearoff=0)
        entries_menu.add_command(label="Goal", command=lambda: self.on_add_or_edit_entry(EntryType.Goal))
        entries_menu.add_command(label="Skill", command=lambda: self.on_add_or_edit_entry(EntryType.Skill))
        entries_menu.add_command(label="Session", command=lambda: self.on_add_or_edit_entry(EntryType.Session))
        entries_menu.add_command(label="Notes", command=lambda: self.on_add_or_edit_entry(EntryType.Notes))
        entries_menu.add_separator()
        entries_menu.add_command(label="Clear", command=self.clear_entries)
        menubar.add_cascade(label="Entries", menu=entries_menu)

    def save_entries(self):
        """
        Save all current entries to a JSON file.
        Explicitly writes base attributes and subclass-specific ones.
        - LearningLog → entry_type, text, timestamp, mood
        - GoalLog → adds 'status'
        - ReflectionLog → keeps 'mood'
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return

        history = self.service.snapshot().entries

        from domain import GoalLog, ReflectionLog

        export_dict = {}

        for et, logs in history.items():
            if logs:
                export_dict[et.value] = []
                for rec in logs:
                    # Base record dictionary
                    record_dict = {
                        "entry_type": et.value,
                        "text": rec.text,
                        "timestamp": rec.timestamp,
                        "mood": getattr(rec, "mood", "")
                    }

                    # Add subclass-specific attributes
                    if isinstance(rec, GoalLog):
                        record_dict["status"] = rec.status
                    elif isinstance(rec, ReflectionLog):
                        record_dict["mood"] = rec.mood  # Ensure mood is present

                    export_dict[et.value].append(record_dict)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_dict, f, indent=4)

        self.custom_message_popup("Saved", f"Entries saved to {file_path}", msg_type="info")

    def load_entries(self):
        """
        Load entries from a JSON file.
        Reconstructs the correct class type:
        - GoalLog if 'status' field is present
        - ReflectionLog if entry_type == 'Notes'
        - LearningLog otherwise
        """
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        from domain import GoalLog, ReflectionLog, LearningLog, EntryType

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reset current state before loading
            self.service._state.entries = {e: [] for e in EntryType}

            for etype_str, records in data.items():
                etype = EntryType(etype_str)
                for rec in records:
                    text = rec.get("text", "")
                    timestamp = rec.get("timestamp", "")
                    mood = rec.get("mood", "")

                    if "status" in rec:
                        # Build GoalLog
                        entry = GoalLog(etype, text, timestamp=timestamp, mood=mood, status=rec["status"])
                    elif etype == EntryType.Notes:
                        # Build ReflectionLog
                        entry = ReflectionLog(etype, text, timestamp=timestamp, mood=mood)
                    else:
                        # Build base LearningLog
                        entry = LearningLog(etype, text, timestamp=timestamp, mood=mood)

                    self.service._state.entries[etype].append(entry)

            self.render_summary()
            self.custom_message_popup("Loaded", f"Entries loaded from {file_path}", msg_type="info")

        except Exception as e:
            self.custom_message_popup("Error", "Failed to load file!", msg_type="error")

    def show_history(self):
        """
        Display a popup window with the full history of all entries.
        Derived classes display extra attributes:
            - GoalLog → shows status
            - ReflectionLog → shows mood
        """
        history = self.service.snapshot().entries

        popup = tk.Toplevel(self.root)
        popup.title("History Log")
        self.center_popup(popup, 600, 400)

        scrollbar = tk.Scrollbar(popup)
        scrollbar.pack(side="right", fill="y")

        text_area = tk.Text(popup, wrap="word", yscrollcommand=scrollbar.set)
        text_area.pack(fill="both", expand=True)
        scrollbar.config(command=text_area.yview)

        for etype, records in history.items():
            if records:
                text_area.insert(tk.END, f"{etype.value}:\n")
                for idx, rec in enumerate(records, 1):
                    line = f"  {idx}. [{rec.timestamp}] {rec.text}"

                    # If record is a GoalLog, add status
                    from domain import GoalLog, ReflectionLog
                    if isinstance(rec, GoalLog):
                        line += f" (Status: {rec.status})"

                    # If record is a ReflectionLog, add mood
                    elif isinstance(rec, ReflectionLog):
                        if rec.mood:
                            line += f" (Mood: {rec.mood})"

                    text_area.insert(tk.END, line + "\n")

                text_area.insert(tk.END, "\n")

        text_area.config(state="disabled")

    def center_popup(self, popup, width, height):
        """
        Center any popup relative to the main app window.
        """
        self.root.update_idletasks()

        # grab the info for the root frame
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()

        # calculate horizontal offset: start from the root x position,
        # then add half the root width, and subtract half the popup width
        pos_x = main_x + (main_w // 2) - (width // 2)

        # calculate vertical offset: start from the root y position,
        # then add half the root height, and subtract half the popup height
        pos_y = main_y + (main_h // 2) - (height // 2)

        # apply the new location for the popup by changing it's geometry
        popup.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def export_csv(self):
        """
        Export all entries (history) to a CSV file.
        Columns: EntryType, Timestamp, Text, Mood, Status
        - GoalLog adds Status
        - ReflectionLog adds Mood
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return

        history = self.service.snapshot().entries

        from domain import GoalLog, ReflectionLog

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header row
            writer.writerow(["EntryType", "Timestamp", "Text", "Mood", "Status"])

            # Write one row per log entry
            for etype, records in history.items():
                for rec in records:
                    mood = rec.mood if hasattr(rec, "mood") else ""
                    status = ""

                    # Handle derived class specifics
                    if isinstance(rec, GoalLog):
                        status = rec.status
                    elif isinstance(rec, ReflectionLog):
                        mood = rec.mood  # ReflectionLog should always carry mood

                    writer.writerow([
                        etype.value,
                        rec.timestamp,
                        rec.text,
                        mood,
                        status
                    ])
        self.custom_message_popup("Exported", f"Entries exported to {file_path}", msg_type="info")


    # ------------------- UTILITIES -------------------

    def analyze_mood(self, text: str) -> str:
        """
        Run sentiment analysis on note text using TextBlob.
        Returns one of: "motivated", "stuck", or "neutral".
        Polarity amounts chosen for simplicity.
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.3:      # positive sentiment
            return "motivated"
        elif polarity < -0.3:   # negative sentiment
            return "stuck"
        else:                   # neutral sentiment
            return "neutral"
            
