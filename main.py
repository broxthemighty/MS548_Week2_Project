# main.py
import tkinter as tk
from service import LearnflowService
from ui import App

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root, LearnflowService())
    root.mainloop()
