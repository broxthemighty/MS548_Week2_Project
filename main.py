"""
main.py
Author: Matt Lindborg
Course: MS548 - Advanced Programming Concepts and AI
Assignment: Week 2 (prep for Week 3)
Date: 9/17/2025

Purpose:
This is the entry point for the Learnflow Base application.
It wires together the user interface (ui.py) with the service layer (service.py).
The structure follows best practices:
    - Keep main.py minimal (only startup logic).
    - Delegate business logic to service.py.
    - Delegate GUI rendering to ui.py.
This ensures the application remains modular, testable, and extendable.
"""

# --- Imports ---
import tkinter as tk                  # Tkinter for GUI window creation
from service import LearnflowService  # Service layer for business logic
from ui import App                    # GUI class that builds interface


def main():
    """
    Application entry function.
    Creates the root Tkinter window, service instance, and App GUI.
    Starts the event loop to keep the program running until exit.
    """
    # Step 1: create root Tkinter window
    root_window = tk.Tk()

    # Step 2: create service instance (manages state + logs)
    service = LearnflowService()

    # Step 3: build GUI, passing in root window + service
    app = App(root_window, service)

    # Step 4: enter Tkinter event loop (blocks until window closed)
    root_window.mainloop()


# Python standard entry-point guard
if __name__ == "__main__":
    main()
