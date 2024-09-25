from app.bot.x_bot import XBot
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import simpledialog
import threading
import sqlite3
import app.gui.main_window as main_window
import app.logger.logger as logger

def main():
    root = tk.Tk()

    _logger = logger.logger("MainApp")

    bot = XBot()

    # Initialize the main window with bot and logger
    app = main_window.MainWindow(root, _logger, bot)
    root.mainloop()

if __name__ == "__main__":
    main()

