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
from domain import EntryType                 # entry type enumeration
from service import LearnflowService         # service layer abstraction


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
        for key, val in summary.items():
            self.output_box.insert(tk.END, f"{key}: {val}\n")
        self.output_box.config(state="disabled")

    # ------------------- EVENT HANDLERS -------------------

    def on_add_or_edit_entry(self, entry_type: EntryType):
        """
        Event handler for Goal/Skill/Session/Notes buttons.
        Steps:
            - Open custom popup for user input.
            - If entry_type is Notes, analyze mood with TextBlob.
            - Send entry (and optional mood) to service.
            - Re-render summary output.
        """
        text = self.custom_input("Input", f"Enter your {entry_type.value}:")
        if text:
            # mood tagging only applies to Notes
            mood = ""
            if entry_type == EntryType.Notes:
                mood = self.analyze_mood(text)

            # create entry via service
            self.service.set_entry(entry_type, text)

            # if mood detected, update the last record directly
            if mood:
                self.service._state.entries[entry_type][-1].mood = mood

            self.render_summary()

    def clear_entries(self) -> None:
        """
        Clear all entries from the service and refresh display.
        """
        self.service.clear()
        self.render_summary()
        messagebox.showinfo("Cleared", "All entries have been cleared.")

    # ------------------- MENU & FILE OPS -------------------

    def build_menu(self):
        """
        Build the top menubar with File menu options.
        """
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save", command=self.save_entries)
        file_menu.add_command(label="Load", command=self.load_entries)
        file_menu.add_command(label="View History", command=self.show_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        self.root.config(menu=menubar)

    def save_entries(self):
        """
        Save current state entries to JSON file.
        Uses the raw dict representation for simplicity.
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return

        # build a plain dict for serialization
        export_dict = {
            et.value: [log.__dict__ for log in logs]
            for et, logs in self.service.snapshot().entries.items()
        }
        with open(file_path, "w") as f:
            json.dump(export_dict, f, indent=2)

    def load_entries(self):
        """
        Load entries from a JSON file.
        Restores LearningLog objects from dictionaries.
        """
        file_path = filedialog.askopenfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return

        with open(file_path, "r") as f:
            data = json.load(f)

        # rebuild logs into service
        self.service.clear()
        for key, records in data.items():
            et = EntryType(key)
            for rec in records:
                log = self.service._state.entries[et]
                log.append(
                    # reconstruct LearningLog with timestamp + mood
                    self.service._state.entries[et].__class__.__args__[0](  # type trick
                        et, rec.get("text", ""), rec.get("timestamp", ""), rec.get("mood", "")
                    )
                )

        self.render_summary()

    def show_history(self):
        """
        Display a popup window with the full history of all entries.
        Lists every record with timestamp, text, and optional mood.
        """
        history = self.service.snapshot().entries

        popup = tk.Toplevel(self.root)
        popup.title("History Log")
        popup.geometry("500x300")

        scrollbar = tk.Scrollbar(popup)
        scrollbar.pack(side="right", fill="y")

        text_area = tk.Text(popup, wrap="word", yscrollcommand=scrollbar.set)
        text_area.pack(fill="both", expand=True)
        scrollbar.config(command=text_area.yview)

        for etype, records in history.items():
            if records:
                text_area.insert(tk.END, f"{etype.value}:\n")
                for idx, rec in enumerate(records, 1):
                    ts = rec.timestamp
                    txt = rec.text
                    mood = rec.mood
                    mood_str = f" [Mood: {mood}]" if mood else ""
                    text_area.insert(tk.END, f"  {idx}. {ts} — {txt}{mood_str}\n")
                text_area.insert(tk.END, "\n")

        text_area.config(state="disabled")

    # ------------------- UTILITIES -------------------

    def analyze_mood(self, text: str) -> str:
        """
        Run sentiment analysis on note text using TextBlob.
        Returns one of: "motivated", "stuck", or "neutral".
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.3:
            return "motivated"
        elif polarity < -0.3:
            return "stuck"
        else:
            return "neutral"
