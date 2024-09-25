
import tkinter as tk
from tkinter import ttk, messagebox
import threading

class AutoFollowTab:
    def __init__(self, frame, logger, bot):
        self.frame = frame
        self.logger = logger
        self.bot = bot

        self.create_widgets()

    def create_widgets(self):
        # Status label
        self.auto_follow_status_label = ttk.Label(self.frame, text="Auto Follow is not running.")
        self.auto_follow_status_label.pack(pady=20)

        # Start and Stop buttons
        self.start_auto_follow_button = ttk.Button(
            self.frame,
            text="Start Auto Follow",
            command=self.start_auto_follow
        )
        self.start_auto_follow_button.pack(pady=10)

        self.stop_auto_follow_button = ttk.Button(
            self.frame,
            text="Stop Auto Follow",
            command=self.stop_auto_follow,
            state=tk.DISABLED
        )
        self.stop_auto_follow_button.pack(pady=10)

    def start_auto_follow(self):
        """
        Handler for starting the auto follow process.
        """
        if not self.is_credentials_valid():
            return

        if self.bot.is_running:
            self.logger.warning("Bot is already running.")
            messagebox.showwarning("Warning", "Bot is already running.")
            return

        self.logger.info("Starting Auto Follow process")
        self.auto_follow_status_label.config(text="Auto Follow is running...")
        self.start_auto_follow_button.config(state=tk.DISABLED)
        self.stop_auto_follow_button.config(state=tk.NORMAL)

        # Start the auto follow process in a separate thread
        self.auto_follow_thread = threading.Thread(target=self.run_auto_follow, daemon=True)
        self.auto_follow_thread.start()

    def run_auto_follow(self):
        """
        The method that contains the logic for auto following.
        """
        try:
            self.bot.start_auto_following()
            self.logger.info("Auto Follow process completed successfully.")
            self.update_auto_follow_status("Auto Follow completed.")
        except Exception as e:
            self.logger.exception(f"An error occurred during Auto Follow: {e}")
            self.update_auto_follow_status(f"Error: {e}")

    def stop_auto_follow(self):
        """
        Handler for stopping the auto follow process.
        """
        if hasattr(self, 'auto_follow_thread') and self.auto_follow_thread.is_alive():
            self.logger.info("Stopping Auto Follow process")
            self.bot.stop_auto_following()  # Ensure your bot has a method to stop the process
            self.auto_follow_thread.join(timeout=5)
            self.update_auto_follow_status("Auto Follow has been stopped.")
            self.start_auto_follow_button.config(state=tk.NORMAL)
            self.stop_auto_follow_button.config(state=tk.DISABLED)
        else:
            self.logger.warning("Auto Follow process is not running.")
            messagebox.showwarning("Warning", "Auto Follow process is not running.")

    def update_auto_follow_status(self, message):
        """
        Updates the status label in the Auto Follow tab.
        """
        self.auto_follow_status_label.config(text=message)
        if "Error" in message or "stopped" in message.lower() or "completed" in message.lower():
            self.start_auto_follow_button.config(state=tk.NORMAL)
            self.stop_auto_follow_button.config(state=tk.DISABLED)

    def is_credentials_valid(self):
        # Implementation to validate user credentials before starting auto follow
        return True