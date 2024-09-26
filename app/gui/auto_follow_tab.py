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
        self.create_status_label()
        self.create_control_buttons()
        self.create_follow_inputs()
        self.create_keywords_section()

    def create_status_label(self):
        """
        Creates and packs the status label.
        """
        self.auto_follow_status_label = ttk.Label(self.frame, text="Auto Follow is not running.")
        self.auto_follow_status_label.pack(pady=20)

    def create_control_buttons(self):
        """
        Creates and packs the Start and Stop buttons.
        """
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

    def create_follow_inputs(self):
        """
        Creates and packs the follow-related input fields.
        """
        self.create_follow_at_time_input()
        self.create_follow_in_24_hours_input()

    def create_follow_at_time_input(self):
        """
        Creates and packs the 'Follow at a time' input section.
        """
        follow_at_time_frame = ttk.Frame(self.frame)
        follow_at_time_frame.pack(pady=10)
        
        ttk.Label(follow_at_time_frame, text="(Max 100) Follow at a time:").pack(side=tk.LEFT)
        
        self.follow_at_time_var = tk.StringVar()
        self.follow_at_time_entry = ttk.Entry(
            follow_at_time_frame, 
            textvariable=self.follow_at_time_var, 
            width=20,
            validate="key",
            validatecommand=(self.frame.register(self.validate_follow_at_time_input), '%P')
        )
        self.follow_at_time_entry.pack(side=tk.LEFT, padx=(5, 0))

        self.follow_at_time_warning = ttk.Label(follow_at_time_frame, text="", foreground="red")
        self.follow_at_time_warning.pack(side=tk.LEFT, padx=(5, 0))

    def create_follow_in_24_hours_input(self):
        """
        Creates and packs the 'Follow in 24 hours' input section.
        """
        follow_in_24_hours_frame = ttk.Frame(self.frame)
        follow_in_24_hours_frame.pack(pady=10)
        
        ttk.Label(follow_in_24_hours_frame, text="(Max 400) Follow in 24 hours:").pack(side=tk.LEFT)
        
        self.follow_in_24_hours_var = tk.StringVar()
        self.follow_in_24_hours_entry = ttk.Entry(
            follow_in_24_hours_frame, 
            textvariable=self.follow_in_24_hours_var, 
            width=20,
            validate="key",
            validatecommand=(self.frame.register(self.validate_follow_in_24_hours_input), '%P')
        )
        self.follow_in_24_hours_entry.pack(side=tk.LEFT, padx=(5, 0))

        self.follow_in_24_hours_warning = ttk.Label(follow_in_24_hours_frame, text="", foreground="red")
        self.follow_in_24_hours_warning.pack(side=tk.LEFT, padx=(5, 0))

    def create_keywords_section(self):
        """
        Creates and packs the keywords management section.
        """
        keywords_frame = ttk.Frame(self.frame)
        keywords_frame.pack(pady=(10, 0))

        ttk.Label(keywords_frame, text="Keywords:").pack(anchor=tk.W)

        self.keywords_listbox = tk.Listbox(keywords_frame, height=5, width=30)
        self.keywords_listbox.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        keywords_scrollbar = ttk.Scrollbar(keywords_frame, orient=tk.VERTICAL, command=self.keywords_listbox.yview)
        keywords_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.keywords_listbox.config(yscrollcommand=keywords_scrollbar.set)

        keywords_input_frame = ttk.Frame(keywords_frame)
        keywords_input_frame.pack(fill=tk.X, pady=(5, 0))

        self.keyword_entry = ttk.Entry(keywords_input_frame, width=20)
        self.keyword_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        add_keyword_button = ttk.Button(keywords_input_frame, text="Add", command=self.add_keyword)
        add_keyword_button.pack(side=tk.LEFT, padx=(5, 0))

        delete_keyword_button = ttk.Button(keywords_input_frame, text="Delete", command=self.remove_keyword)
        delete_keyword_button.pack(side=tk.LEFT, padx=(5, 0))

    def are_settings_valid(self):
        '''This method checks if the follow at a time and follow in 24 hours are valid'''
        # Check if follow_at_time is valid and not empty
        follow_at_time = self.follow_at_time_var.get().strip()
        if not follow_at_time or not self.validate_follow_at_time_input(follow_at_time):
            self.logger.warning("Invalid or empty 'Follow at a time' value")
            messagebox.showerror("Error", "Please enter a valid 'Follow at a time' value.")
            return False

        # Check if follow_in_24_hours is valid and not empty
        follow_in_24_hours = self.follow_in_24_hours_var.get().strip()
        if not follow_in_24_hours or not self.validate_follow_in_24_hours_input(follow_in_24_hours):
            self.logger.warning("Invalid or empty 'Follow in 24 hours' value")
            messagebox.showerror("Error", "Please enter a valid 'Follow in 24 hours' value.")
            return False

        return True

    def add_keyword(self):
        keyword = self.keyword_entry.get().strip()
        if keyword and keyword not in self.keywords_listbox.get(0, tk.END):
            self.keywords_listbox.insert(tk.END, keyword)
            self.keyword_entry.delete(0, tk.END)
        elif not keyword:
            messagebox.showwarning("Warning", "Please enter a keyword.")
        else:
            messagebox.showwarning("Warning", "This keyword already exists in the list.")

    def remove_keyword(self):
        selected_indices = self.keywords_listbox.curselection()
        if selected_indices:
            for index in reversed(selected_indices):
                self.keywords_listbox.delete(index)
        else:
            messagebox.showwarning("Warning", "Please select a keyword to remove.")

    def start_auto_follow(self):
        """
        Handler for starting the auto follow process.
        """
        if not self.bot.is_credentials_valid(): # check if the credentials are valid just in case they have to be used to sign in to X
            messagebox.showwarning("Warning", "Credentials are not valid. Go to Settings tab to set them up.")
            return
        
        if not self.are_settings_valid():
            return

        self.logger.info("Starting Auto Follow process")
        self.auto_follow_status_label.config(text="Auto Follow is running...")
        self.start_auto_follow_button.config(state=tk.DISABLED)
        self.stop_auto_follow_button.config(state=tk.NORMAL)

        # TODO: Open a new browser window


        # Start the auto follow process in a separate thread
        self.auto_follow_thread = threading.Thread(target=self.run_auto_follow, daemon=True)
        self.auto_follow_thread.start()

    def run_auto_follow(self):
        """
        The method that contains the logic for auto following.
        """
        try:
            total_follow_count = self.follow_in_24_hours_var.get()
            keywords = self.keywords_listbox.get(0, tk.END)
            follow_at_time = self.follow_at_time_var.get()
            self.bot.start_auto_following(total_follow_count=total_follow_count, keywords=keywords, follow_at_time=follow_at_time)
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

    def validate_follow_at_time_input(self, P: str):
        """
        Validates that the input is a non-empty string of digits and does not exceed 100.

        Args:
            P (str): The proposed new value of the entry widget.

        Returns:
            bool: True if valid (empty or digits only and <= 100), False otherwise.
        """
        if P.isdigit():
            if int(P) <= 100:
                self.follow_at_time_warning.config(text="")
                return True
            else:
                self.follow_at_time_warning.config(text="Max 100 allowed.")
                return False
        elif P == "":
            self.follow_at_time_warning.config(text="")
            return True
        else:
            self.follow_at_time_warning.config(text="Invalid input.")
            return False

    def validate_follow_in_24_hours_input(self, P: str) -> bool:
        """
        Validates that the input is a non-empty string of digits and does not exceed 400.

        Args:
            P (str): The proposed new value of the entry widget.

        Returns:
            bool: True if valid (empty or digits only and <= 400), False otherwise.
        """
        if P.isdigit():
            if int(P) <= 400:
                self.follow_in_24_hours_warning.config(text="")
                return True
            else:
                self.follow_in_24_hours_warning.config(text="Max 400 allowed.")
                return False
        elif P == "":
            self.follow_in_24_hours_warning.config(text="")
            return True
        else:
            self.follow_in_24_hours_warning.config(text="Invalid input.")
            return False