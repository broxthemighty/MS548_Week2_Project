# ui.py
import tkinter as tk
from tkinter import messagebox
from domain import EntryType
from service import LearnflowService
import json
from tkinter import filedialog
from textblob import TextBlob

class App:
    def __init__(self, root: tk.Tk, service: LearnflowService):
        self.root = root
        self.service = service

        self.root.title("Learnflow Base")
        self.root.resizable(False, False)

        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)

        # --- Top row: label + Clear + Exit ---
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

        # --- Drop Down Menu: Save + Load + Exit
        self.build_menu()

        # --- Middle row: buttons + (optional) image ---
        side_frame = tk.Frame(main_frame)
        side_frame.grid(row=1, column=0, sticky="w")

        buttons_frame = tk.Frame(side_frame)
        buttons_frame.pack(side="left", anchor="n", padx=(0, 5))

        # Buttons are purely UI: they call service via handlers
        for et in (EntryType.Goal, EntryType.Skill, EntryType.Session, EntryType.Notes):
            tk.Button(
                buttons_frame,
                text=et.value,
                width=10,
                command=lambda t=et: self.on_add_or_edit_entry(t),
            ).pack(pady=2, anchor="w")

        # If you have an image, keep it view-only
        try:
            self.image = tk.PhotoImage(file="images\\image2_50pc.png")
            tk.Label(side_frame, image=self.image).pack(side="left", anchor="n")
        except Exception:
            # Fail soft if image not present
            pass

        # --- Bottom row: Text output ---
        output_frame = tk.Frame(main_frame)
        output_frame.grid(row=2, column=0, sticky="ew", pady=10)

        scrollbar = tk.Scrollbar(output_frame)
        scrollbar.pack(side="right", fill="y")

        self.output_box = tk.Text(
            output_frame, height=6, wrap="word", state="disabled", yscrollcommand=scrollbar.set
        )
        self.output_box.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.output_box.yview)

        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())

        # Initial render from service
        self.render_summary()

    # ---------- View-only helpers ----------
    def custom_input(self, title: str, prompt: str) -> str | None:
        popup = tk.Toplevel(self.root)
        popup.title(title)
        w, h = 300, 150
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (w // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 4) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")

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
        summary = self.service.summary()  # dict[str, str]
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", tk.END)
        for key, val in summary.items():
            self.output_box.insert(tk.END, f"{key}: {val}\n")
        self.output_box.config(state="disabled")

    # ---------- Event handlers (UI -> Service) ----------
    def on_add_or_edit_entry(self, entry_type: EntryType):
        text = self.custom_input("Input", f"Enter your {entry_type.value}:")
        if text:
            self.service.set_entry(entry_type, text)

            # Sentiment analysis for Notes only
            if entry_type == EntryType.Notes:
                mood = analyze_mood(text)
                self.service.set_entry("Mood", mood)

            self.render_summary()

    def clear_entries(self) -> None:
        self.service.clear()
        self.render_summary()
        messagebox.showinfo("Cleared", "All entries have been cleared.")

    def build_menu(self):
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save", command=self.save_entries)
        file_menu.add_command(label="Load", command=self.load_entries)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        self.root.config(menu=menubar)

    def save_entries(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not file_path:
            return
        with open(file_path, "w") as f:
            json.dump(self.service.snapshot().entries, f)

    def load_entries(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if not file_path:
            return
        with open(file_path, "r") as f:
            data = json.load(f)
        for k, v in data.items():
            self.service.set_entry(k, v)
        self.render_summary()

    def analyze_mood(text: str) -> str:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 = negative, +1 = positive
        if polarity > 0.3:
            return "motivated"
        elif polarity < -0.3:
            return "stuck"
        else:
            return "neutral"