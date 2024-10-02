import tkinter as tk
import app.bot.auto_follow as auto_follow
from tkinter import ttk, messagebox
import threading


class AutoFollowTab:
    def __init__(self, frame, logger, bot):
        self.frame = frame
        self.logger = logger
        self.bot = bot
        self.auto_follow = auto_follow.AutoFollow(bot)

        self.create_widgets()

    def create_widgets(self):
        self.create_status_label()
        self.create_control_buttons()
        self.create_follow_inputs()
        self.create_time_span_input() 
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
            command=self.start_auto_follow,
            state=tk.NORMAL
        )
        self.start_auto_follow_button.pack(pady=10)

        self.stop_auto_follow_button = ttk.Button(
            self.frame,
            text="Stop Auto Follow",
            command=self.stop_auto_follow,
            state=tk.DISABLED
        )
        self.stop_auto_follow_button.pack(pady=10)

    def create_time_span_input(self):
        """
        Creates and packs the 'Time Span in Minutes' input section.
        """
        time_span_frame = ttk.Frame(self.frame)
        time_span_frame.pack(pady=10)
        
        ttk.Label(time_span_frame, text="Time Span in Minutes:").pack(side=tk.LEFT)
        
        self.time_span_var = tk.StringVar()
        self.time_span_entry = ttk.Entry(   
            time_span_frame, 
            textvariable=self.time_span_var, 
            width=20,
            validate="key",
            validatecommand=(self.frame.register(self.validate_time_span_input), '%P')
        )
        self.time_span_entry.pack(side=tk.LEFT, padx=(5, 0))

        self.time_span_warning = ttk.Label(time_span_frame, text="", foreground="red")
        self.time_span_warning.pack(side=tk.LEFT, padx=(5, 0))

    def create_follow_inputs(self):
        """
        Creates and packs the follow-related input fields.
        """
        self.create_follow_at_once_input()
        self.create_follow_in_time_span_input()

    def create_follow_at_once_input(self):
        """
        Creates and packs the 'Follow at a time' input section.
        """
        follow_at_once_frame = ttk.Frame(self.frame)
        follow_at_once_frame.pack(pady=10)
        
        ttk.Label(follow_at_once_frame, text="(Max 100) Maximum people to follow at once:").pack(side=tk.LEFT)
        
        self.follow_at_once_var = tk.StringVar()
        self.follow_at_once_entry = ttk.Entry(
            follow_at_once_frame, 
            textvariable=self.follow_at_once_var, 
            width=20,
            validate="key",
            validatecommand=(self.frame.register(self.validate_follow_at_once_input), '%P')
        )
        self.follow_at_once_entry.pack(side=tk.LEFT, padx=(5, 0))

        self.follow_at_once_warning = ttk.Label(follow_at_once_frame, text="", foreground="red")
        self.follow_at_once_warning.pack(side=tk.LEFT, padx=(5, 0))

    def create_follow_in_time_span_input(self):
        """
        Creates and packs the 'Follow in 24 hours' input section.
        """
        follow_in_time_span_frame = ttk.Frame(self.frame)
        follow_in_time_span_frame.pack(pady=10)
        
        ttk.Label(follow_in_time_span_frame, text="(Max 400) Maximum people to follow in 24 hrs:").pack(side=tk.LEFT)
        
        self.follow_in_time_span_var = tk.StringVar()
        self.follow_in_time_span_entry = ttk.Entry(
            follow_in_time_span_frame, 
            textvariable=self.follow_in_time_span_var, 
            width=20,
            validate="key",
            validatecommand=(self.frame.register(self.validate_follow_in_time_span_input), '%P')
        )
        self.follow_in_time_span_entry.pack(side=tk.LEFT, padx=(5, 0))

        self.follow_in_time_span_warning = ttk.Label(follow_in_time_span_frame, text="", foreground="red")
        self.follow_in_time_span_warning.pack(side=tk.LEFT, padx=(5, 0))

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
        '''This method checks if the follow_at_once, follow_in_time_span, time_span inputs are valid'''
        # Check if follow_at_once is valid and not empty
        follow_at_once = self.follow_at_once_var.get().strip()
        if not follow_at_once or not self.validate_follow_at_once_input(follow_at_once):
            self.logger.warning("Invalid or empty 'Follow at once' value")
            messagebox.showerror("Error", "Please enter a valid 'Follow at once' value.")
            return False

        # Check if follow_in_time_span is valid and not empty
        follow_in_time_span = self.follow_in_time_span_var.get().strip()
        if not follow_in_time_span or not self.validate_follow_in_time_span_input(follow_in_time_span):
            self.logger.warning("Invalid or empty 'Follow in 24 hours' value")
            messagebox.showerror("Error", "Please enter a valid 'Follow in 24 hours' value.")
            return False
        
        # Check if the follow_at_once is not greater than the follow_in_time_span
        if int(follow_at_once) > int(follow_in_time_span):
            self.logger.warning("'Follow at a time' is greater than 'Follow in 24 hours'")
            messagebox.showerror("Error", "Please enter a valid 'Follow at a time' value which is less than 'Follow in 24 hours' value.")
            return False
        
        # Check if time_span is valid and not empty
        time_span = self.time_span_var.get().strip()
        if not time_span or not self.validate_time_span_input(time_span):
            self.logger.warning("Invalid or empty 'Time Span in Hours' value")
            messagebox.showerror("Error", "Please enter a valid 'Time Span in Hours' value.")
            return False

        return True

    def add_keyword(self):
        """Adds a new keyword to the keywords list."""
        keyword = self.keyword_entry.get().strip()
        if keyword and keyword not in self.keywords_listbox.get(0, tk.END):
            self.keywords_listbox.insert(tk.END, keyword)
            self.keyword_entry.delete(0, tk.END)
        elif not keyword:
            messagebox.showwarning("Warning", "Please enter a keyword.")
        else:
            messagebox.showwarning("Warning", "This keyword already exists in the list.")

    def remove_keyword(self):
        """Removes the selected keyword from the keywords list."""
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

        try:
            follow_at_once = int(self.follow_at_once_var.get())
            total_follow_count = int(self.follow_in_time_span_var.get())
            time_span = int(self.time_span_var.get())

            # Set the time_span attribute of AutoFollow
            self.auto_follow.time_span = time_span

            # Calculate required rest time to distribute follows evenly over the time span
            rest_time = self.auto_follow.calculate_rest_time(total_follow_count, follow_at_once)

        except ValueError as ve:
            self.logger.warning(f"Rest time calculation failed: {ve}")
            messagebox.showerror("Error", f"{ve}")
            return
        except Exception as e:
            self.logger.exception(f"Unexpected error during rest time calculation: {e}")
            messagebox.showerror("Error", "An unexpected error occurred during rest time calculation.")
            return

        self.logger.info("Starting Auto Follow process")
        self.auto_follow_status_label.config(text="Auto Follow is running...")
        
        # Update button states
        self.start_auto_follow_button.config(state=tk.DISABLED)
        self.stop_auto_follow_button.config(state=tk.NORMAL)
        self.frame.update_idletasks()

        # Create a new window to run the auto follow process
        self.auto_follow.create_new_window()
        self.auto_follow.sign_in()

        # Start the auto follow process in a separate thread
        self.auto_follow_thread = threading.Thread(target=self.run_auto_follow, daemon=True)
        self.auto_follow_thread.start()

    def run_auto_follow(self):
        """
        The method that contains the logic for auto following.
        """
        try:
            total_follow_count = int(self.follow_in_time_span_var.get())
            keywords = list(self.keywords_listbox.get(0, tk.END))
            follow_at_once = int(self.follow_at_once_var.get())
            self.auto_follow.schedule_auto_follow_process(
                total_follow_count=total_follow_count, 
                keywords=keywords, 
                follow_at_once=follow_at_once
            )
            self.logger.info("Auto Follow process completed successfully.")
            self.update_auto_follow_status("Auto Follow completed.")
        except ValueError as ve:
            self.logger.exception(f"Invalid input values: {ve}")
            self.update_auto_follow_status(f"Error: Invalid input values. Please check your inputs.")
        except Exception as e:
            self.logger.exception(f"An error occurred during Auto Follow: {e}")
            self.update_auto_follow_status(f"Error: {e}")

    def stop_auto_follow(self):
        """
        Handler for stopping the auto follow process.
        """
        if hasattr(self, 'auto_follow_thread') and self.auto_follow_thread.is_alive():
            self.logger.info("Stopping Auto Follow process")
            self.auto_follow.stop_auto_following()
            self.auto_follow_thread.join(timeout=5)
            self.update_auto_follow_status("Auto Follow has been stopped.")
            
            # Update button states
            self.stop_auto_follow_button.config(state=tk.DISABLED)
            self.start_auto_follow_button.config(state=tk.NORMAL)
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

    def validate_time_span_input(self, P: str):
        """
        Validates that the input is a non-empty string of digits greater than 0.

        Args:
            P (str): The proposed new value of the entry widget.

        Returns:
            bool: True if valid (non-empty and digits > 0), False otherwise.
        """
        if P.isdigit() and int(P) > 0:
            self.time_span_warning.config(text="")
            return True
        elif P == "":
            self.time_span_warning.config(text="")
            return True
        else:
            self.time_span_warning.config(text="Invalid input. Enter a positive integer.")
            return False

    def validate_follow_at_once_input(self, P: str):
        """
        Validates that the input is a non-empty string of digits and does not exceed 100.

        Args:
            P (str): The proposed new value of the entry widget.

        Returns:
            bool: True if valid (empty or digits only and <= 100), False otherwise.
        """
        if P.isdigit():
            if int(P) <= 100:
                self.follow_at_once_warning.config(text="")
                return True
            else:
                self.follow_at_once_warning.config(text="Max 100 allowed.")
                return False
        elif P == "":
            self.follow_at_once_warning.config(text="")
            return True
        else:
            self.follow_at_once_warning.config(text="Invalid input.")
            return False

    def validate_follow_in_time_span_input(self, P: str) -> bool:
        """
        Validates that the input is a non-empty string of digits and does not exceed 400.

        Args:
            P (str): The proposed new value of the entry widget.

        Returns:
            bool: True if valid (empty or digits only and <= 400), False otherwise.
        """
        if P.isdigit():
            if int(P) <= 400:
                self.follow_in_time_span_warning.config(text="")
                return True
            else:
                self.follow_in_time_span_warning.config(text="Max 400 allowed.")
                return False
        elif P == "":
            self.follow_in_time_span_warning.config(text="")
            return True
        else:
            self.follow_in_time_span_warning.config(text="Invalid input.")
            return False