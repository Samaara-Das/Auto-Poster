import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from app.gui.settings_tab import SettingsTab
from app.gui.bot_targets_tab import BotTargetsTab
from app.gui.auto_follow_tab import AutoFollowTab

class MainWindow:
    def __init__(self, master, logger, bot):
        self.master = master
        self.logger = logger
        self.bot = bot

        master.title("Auto Poster")
        master.geometry("700x750")

        self.logger.info("Initializing MainWindow")

        # Create the notebook (tabbed interface)
        notebook = ttk.Notebook(master)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create frames for each tab
        settings_frame = ttk.Frame(notebook)
        bot_targets_frame = ttk.Frame(notebook)
        auto_follow_frame = ttk.Frame(notebook)

        # Add tabs to the notebook
        notebook.add(settings_frame, text="Settings")
        notebook.add(bot_targets_frame, text="Bot Targets")
        notebook.add(auto_follow_frame, text="Auto Follow")

        # Initialize tabs with their respective classes
        SettingsTab(settings_frame, logger, bot)
        BotTargetsTab(bot_targets_frame, logger, bot)
        AutoFollowTab(auto_follow_frame, logger, bot)

        self.logger.info("MainWindow initialization complete")

        # After GUI setup, check if the account is locked
        self.check_account_locked()

    def check_account_locked(self):
        '''This checks if the account is locked and shows a popup message if it is.'''
        self.logger.info("Checking if the account is locked")
        if self.bot.browser.is_account_locked:
            messagebox.showerror("Account Locked", "Your X account has been locked. Please unlock your account.")
