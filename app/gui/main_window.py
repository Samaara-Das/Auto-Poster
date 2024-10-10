import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from app.gui.settings_tab import SettingsTab
from app.gui.bot_targets_tab import BotTargetsTab
from app.gui.auto_follow_tab import AutoFollowTab
from app.gui.process_manager import ProcessManager

class MainWindow:
    def __init__(self, master, logger, bot):
        self.master = master
        self.logger = logger
        self.bot = bot

        # Initialize ProcessManager
        self.process_manager = ProcessManager()

        master.title("Auto Poster")
        
        # Set window size
        window_width = 700
        window_height = 750

        # Get screen dimensions
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()

        # Calculate position for center of the screen
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)

        # Set the position of the window to the center of the screen
        master.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.logger.info("Initializing MainWindow")

        # Create a frame to hold the notebook
        main_frame = ttk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create the notebook (tabbed interface)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create frames for each tab
        settings_frame = ttk.Frame(notebook)
        bot_targets_frame = ttk.Frame(notebook)
        auto_follow_frame = ttk.Frame(notebook)

        # Add tabs to the notebook
        notebook.add(settings_frame, text="Settings")
        notebook.add(bot_targets_frame, text="Bot Targets")
        notebook.add(auto_follow_frame, text="Auto Follow")

        # Initialize tabs with their respective classes and pass ProcessManager
        SettingsTab(settings_frame, logger, bot, self.process_manager)
        BotTargetsTab(bot_targets_frame, logger, bot, self.process_manager)
        AutoFollowTab(auto_follow_frame, logger, bot, self.process_manager)

        self.logger.info("MainWindow initialization complete")

        # After GUI setup, check if the account is locked
        self.check_account_locked()

    def check_account_locked(self):
        '''This checks if the account is locked and shows a popup message if it is.'''
        self.logger.info("Checking if the account is locked")
        if self.bot.browser.is_account_locked:
            messagebox.showerror("Account Locked", "Your X account has been locked. Please unlock your account.")