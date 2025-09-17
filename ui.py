"""
ui.py
Author: Matt Lindborg
Course: MS548 - Advanced Programming Concepts and AI
Assignment: Week 2 (prep for Week 3)
Date: 9/17/2025

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
from tkinter import messagebox, filedialog   # standard Tkinter dialogs
import json                                  # for save/load functionality
from textblob import TextBlob                # sentiment analysis for Notes
from service import LearnflowService         # service layer abstraction
from domain import EntryType, GoalLog, ReflectionLog
import csv


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

        # --- Main container frame ---
        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)

        # --- Top row: welcome label + Clear button + Drop-down menu ---
        top_frame = tk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(0, weight=1)

        self.display_label = tk.Label(
            top_frame,
            text="Welcome to Learnflow\nPlease choose an option",
            font=("Arial", 12),
            pady=2,
            justify="left",
        )
        self.display_label.grid(row=0, column=0, sticky="w")

        self.clear_button = tk.Button(
            top_frame, text="Clear", width=7, command=self.clear_entries
        )
        self.clear_button.grid(row=0, column=1, sticky="e", padx=(0, 63))

        # attach a menubar for Save/Load/Exit/History
        self.build_menu()

        # --- Middle row: buttons for Goal/Skill/Session/Notes ---
        side_frame = tk.Frame(main_frame)
        side_frame.grid(row=1, column=0, sticky="w")

        buttons_frame = tk.Frame(side_frame)
        buttons_frame.pack(side="left", anchor="n", padx=(0, 5))

        # create one button per EntryType
        for et in (EntryType.Goal, EntryType.Skill, EntryType.Session, EntryType.Notes):
            tk.Button(
                buttons_frame,
                text=et.value,
                width=10,
                command=lambda t=et: self.on_add_or_edit_entry(t),
            ).pack(pady=2, anchor="w")

        # optional image display beside the buttons
        try:
            self.image = tk.PhotoImage(file="images\\image2_50pc.png")
            tk.Label(side_frame, image=self.image).pack(side="left", anchor="n")
        except Exception:
            # fail gracefully if image not found
            pass

        # --- Bottom row: output box with scrollbar ---
        output_frame = tk.Frame(main_frame)
        output_frame.grid(row=2, column=0, sticky="ew", pady=10)

        scrollbar = tk.Scrollbar(output_frame)
        scrollbar.pack(side="right", fill="y")

        self.output_box = tk.Text(
            output_frame,
            height=6,
            wrap="word",
            state="disabled",
            yscrollcommand=scrollbar.set,
        )
        self.output_box.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.output_box.yview)

        # enforce minimum window size after widgets load
        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

        # initial render from service
        self.render_summary()

    # ------------------- VIEW HELPERS -------------------

    def custom_input(self, title: str, prompt: str) -> str | None:
        """
        Custom popup dialog for text input.
        Reused by button handlers to collect user entries.
        """
        popup = tk.Toplevel(self.root)
        popup.title(title)

        # calculate centered popup position relative to root window
        w, h = 300, 150
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (w // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 4) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")

        # add label + entry box
        tk.Label(popup, text=prompt, font=("Arial", 12)).pack(pady=10)
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

    def render_summary(self) -> None:
        """
        Render the latest entries (summary) in the bottom output box.
        Only shows the most recent entry per type.
        """
        summary = self.service.summary()
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        for val in summary.values():
            self.output_box.insert(tk.END, f"{val}\n")
        self.output_box.config(state="disabled")

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
        text = self.custom_input("Input", f"Enter your {entry_type.value}:")
        if not text:
            return  # user canceled

        if entry_type == EntryType.Goal:
            # Create a GoalLog entry with default status
            goal_log = GoalLog(entry_type, text)
            self.service._state.entries[entry_type].append(goal_log)
            self.service.write_log(goal_log)

        elif entry_type == EntryType.Notes:
            # Create a ReflectionLog entry and run mood analysis
            reflection_log = ReflectionLog(entry_type, text)
            reflection_log.analyze_mood()
            self.service._state.entries[entry_type].append(reflection_log)
            self.service.write_log(reflection_log)

        else:
            # Fallback: use normal service method (LearningLog)
            self.service.set_entry(entry_type, text)

        self.render_summary()

    def clear_entries(self) -> None:
        """
        Clear all entries from the service and refresh display.
        """
        self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
        self.service.clear()
        self.render_summary()
        self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
        messagebox.showinfo("Cleared", "All entries have been cleared.")

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

    def save_entries(self):
        """
        Save all current entries to a JSON file.
        Explicitly writes base attributes and subclass-specific ones.
        - LearningLog → entry_type, text, timestamp, mood
        - GoalLog → adds 'status'
        - ReflectionLog → keeps 'mood'
        """
        self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
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

        self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
        messagebox.showinfo("Saved", f"Entries saved to {file_path}")

    def load_entries(self):
        """
        Load entries from a JSON file.
        Reconstructs the correct class type:
        - GoalLog if 'status' field is present
        - ReflectionLog if entry_type == 'Notes'
        - LearningLog otherwise
        """
        self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
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
            self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
            messagebox.showinfo("Loaded", f"Entries loaded from {file_path}")

        except Exception as e:
            self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
            messagebox.showerror("Error", f"Failed to load entries:\n{e}")

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
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()

        pos_x = main_x + (main_w // 2) - (width // 2)
        pos_y = main_y + (main_h // 2) - (height // 2)

        popup.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def export_csv(self):
        """
        Export all entries (history) to a CSV file.
        Columns: EntryType, Timestamp, Text, Mood, Status
        - GoalLog adds Status
        - ReflectionLog adds Mood
        """
        self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")]
        )
        if not file_path:
            return

        history = self.service.snapshot().entries

        from domain import GoalLog, ReflectionLog

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            import csv
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
        self.root.eval('tk::PlaceWindow %s center' % self.root.winfo_toplevel())
        messagebox.showinfo("Exported", f"Entries exported to {file_path}")


    # ------------------- UTILITIES -------------------

    def analyze_mood(self, text: str) -> str:
        """
        Run sentiment analysis on note text using TextBlob.
        Returns one of: "motivated", "stuck", or "neutral".
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.3:      # positive sentiment
            return "motivated"
        elif polarity < -0.3:   # negative sentiment
            return "stuck"
        else:                   # neutral sentiment
            return "neutral"
            
