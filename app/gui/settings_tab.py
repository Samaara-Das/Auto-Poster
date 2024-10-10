import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import app.database.sql_manager as sql_manager
import app.bot.delete_interactions as delete_interactions

class SettingsTab:
    def __init__(self, frame, logger, bot, process_manager):
        self.frame = frame
        self.logger = logger
        self.bot = bot
        self.process_manager = process_manager  # Reference to ProcessManager

        self.username_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.message_var = tk.StringVar()

        self.username_var.trace_add('write', self.update_bot_username)
        self.email_var.trace_add('write', self.update_bot_email)
        self.password_var.trace_add('write', self.update_bot_password)

        self.max_following = None
        self.create_widgets()
    
    def create_widgets(self):
        # Username input
        ttk.Label(self.frame, text="X Username:").pack(pady=10)
        self.username_entry = ttk.Entry(self.frame, textvariable=self.username_var)
        self.username_entry.pack()

        # Email input
        ttk.Label(self.frame, text="Email:").pack(pady=10)
        self.email_entry = ttk.Entry(self.frame, textvariable=self.email_var)
        self.email_entry.pack()

        # Password input
        ttk.Label(self.frame, text="X Password:").pack(pady=(10, 5))
        password_frame = ttk.Frame(self.frame)
        password_frame.pack(pady=(0, 10))
        self.password_entry = ttk.Entry(password_frame, textvariable=self.password_var, show="*", width=20)
        self.password_entry.pack(side=tk.LEFT)
        self.show_password_var = tk.BooleanVar()
        self.show_password_button = ttk.Checkbutton(
            password_frame,
            text="Show",
            variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        self.show_password_button.pack(side=tk.LEFT, padx=(5, 0))

        # Message input
        ttk.Label(self.frame, text="Your tweet:").pack(pady=10)
        self.message_box = scrolledtext.ScrolledText(self.frame, width=40, height=10)
        self.message_box.pack(pady=10)

        # Start button
        self.start_button = ttk.Button(self.frame, text="Start Bot", command=self.start_bot)
        self.start_button.pack(pady=10)

        # Stop button
        self.stop_button = ttk.Button(
            self.frame,
            text="Stop Bot",
            command=self.stop_bot,
            state=tk.DISABLED
        )
        self.stop_button.pack(pady=10)

        # Status label
        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.pack(pady=10)

        # Fill Fields button
        ttk.Button(self.frame, text="Fill Fields", command=self.fill_fields).pack(pady=10)

        # Delete All Replies and Likes buttons
        ttk.Button(self.frame, text="Delete All Replies", command=self.delete_replies).pack(pady=5)
        ttk.Button(self.frame, text="Delete All Likes", command=self.delete_likes).pack(pady=5)

        # Frame for Unfollow section
        unfollow_frame = ttk.Frame(self.frame)
        unfollow_frame.pack(pady=5, fill=tk.X, padx=10)

        # Unfollow Button
        self.unfollow_button = ttk.Button(
            unfollow_frame,
            text="Unfollow",
            command=self.unfollow_users
        )
        self.unfollow_button.pack(side=tk.LEFT)

        # Label for input
        ttk.Label(unfollow_frame, text="Number to Unfollow:").pack(side=tk.LEFT, padx=(10, 5))

        # Validation for digits only
        vcmd = (self.frame.register(self.validate_digits), '%P')

        # Unfollow Entry
        self.unfollow_entry = ttk.Entry(unfollow_frame, validate='key', validatecommand=vcmd, width=10)
        self.unfollow_entry.pack(side=tk.LEFT)

        # Optional: Tooltip or Label to show max value
        self.max_label = ttk.Label(unfollow_frame, text=f"Max: {self.max_following}")
        self.max_label.pack(side=tk.LEFT, padx=(5, 0))

    def validate_digits(self, P):
        """
        Validates that `P` contains only digits and is less than or equal to max_following.
        """
        if P.isdigit() and (int(P) <= self.max_following if P and self.max_following is not None else True):
            return True
        elif P == "":
            return True
        else:
            self.logger.warning("Invalid input for unfollow count.")
            return False

    def update_max_following(self):
        """
        Retrieves the total number of users the bot is following and updates the max_following attribute. Updates the max_label too.
        """
        try:
            self.max_following = self.bot.get_total_following()
            self.logger.info(f"Total following count retrieved: {self.max_following}")
        except Exception as e:
            self.logger.exception(f"Failed to retrieve following count: {str(e)}")
            self.max_following = 0
            messagebox.showerror("Error", "Unable to retrieve following count.")

        # Update max_label if it exists
        if hasattr(self, 'max_label'):
            self.max_label.config(text=f"Max: {self.max_following}")

    def update_bot_username(self, *args):
        new_username = self.username_var.get()
        self.bot.username = new_username
        self.logger.debug(f"Bot username updated to: {new_username}")

    def update_bot_email(self, *args):
        new_email = self.email_var.get()
        self.bot.email = new_email
        self.logger.debug(f"Bot email updated to: {new_email}")

    def update_bot_password(self, *args):
        new_password = self.password_var.get()
        self.bot.password = new_password
        self.logger.debug("Bot password updated.")

    def toggle_password_visibility(self):
        """
        If the password is visible, hide it. Otherwise, show it.
        """
        self.logger.info("Toggling password visibility")
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def start_bot(self):
        process_name = "Start Bot"
        success, message = self.process_manager.request_start(process_name)
        if not success:
            messagebox.showwarning("Process Ongoing", message)
            return

        if not self.bot.is_credentials_valid():
            self.logger.warning(f"Invalid credentials provided. username: {self.bot.username}, password: {self.bot.password}, email: {self.bot.email}")
            messagebox.showerror("Error", "Please enter your X username, password and email.")
            self.process_manager.clear_process()
            return
        
        if not self.is_message_valid():
            self.logger.warning("Invalid message provided")
            messagebox.showerror("Error", "Please enter your tweet.")
            self.process_manager.clear_process()
            return
        
        if self.check_account_locked():
            self.process_manager.clear_process()
            return
        
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()
        self.toggle_start_stop_buttons()

    def run_bot(self):
        '''
        This method runs the bot.
        '''
        try:
            self.logger.info("Bot thread started")
            self.bot.run()
        except Exception as e:
            self.logger.exception(f"An error occurred while running the bot: {str(e)}")
        finally:
            self.toggle_start_stop_buttons()
            self.process_manager.clear_process()
            self.logger.info("Bot finished running")

    def stop_bot(self):
        self.bot.stop_bot()
        self.toggle_start_stop_buttons()
        self.process_manager.clear_process()

    def toggle_start_stop_buttons(self):
        if self.is_bot_running:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.logger.info("Bot finished running")

    @property
    def is_bot_running(self):
        return hasattr(self, 'bot_thread') and self.bot_thread.is_alive()

    def is_message_valid(self):
        '''
        This function checks if the message is valid. If it is, it updates self.bot.content.
        '''
        self.logger.info("Checking if message is valid")
        message = self.message_box.get("1.0", tk.END).strip()
        if not message:
            self.logger.warning("No content provided in the text box")
            messagebox.showerror("Error", "Please enter content in the text box.")
            return False
        self.bot.content = message 
        return True

    def delete_replies(self):
        if not self.check_account_locked():
            delete_interactions.delete_all_replies(self.bot.browser.driver, self.logger, self.bot.username)

    def delete_likes(self):
        if not self.check_account_locked():
            delete_interactions.delete_all_likes(self.bot.browser.driver, self.logger, self.bot.username)

    def fill_fields(self):
        '''
        This function fills the username, email, password and tweet fields automatically with default data. This saves time while testing.
        '''
        user_data = sql_manager.get_user_data()
        self.username_var.set(user_data['username'])
        self.email_var.set(user_data['email'])
        self.password_var.set(user_data['password'])
        self.message_box.insert(tk.END, user_data['tweet_text'])

    def check_account_locked(self):
        '''
        This function checks if the account is locked and shows a popup message if it is. Returns True if the account is locked, False otherwise.
        '''
        if self.bot.browser.is_account_locked_page_open():
            self.logger.warning("Account is locked.")
            messagebox.showerror("Account Locked", "Your X account has been locked. Please unlock your account.")
            return True
        return False

    def unfollow_users(self):
        """
        Initiates the unfollow process using the bot with the specified number of users to unfollow.
        """
        if not self.process_manager.request_start("Unfollow Users"):
            messagebox.showwarning("Process Ongoing", "An unfollow process is already running.")
            return

        # Retrieve and validate the number from the entry
        unfollow_count = self.unfollow_entry.get()
        if not unfollow_count:
            self.logger.warning("Unfollow count not provided.")
            messagebox.showerror("Error", "Please enter the number of users to unfollow.")
            self.process_manager.clear_process()
            return
        
        if not self.bot.is_credentials_valid():
            self.logger.warning(f"Invalid credentials provided. username: {self.bot.username}, password: {self.bot.password}, email: {self.bot.email}")
            messagebox.showerror("Error", "Please enter your X username, password and email.")
            self.process_manager.clear_process()
            return
        
        if self.check_account_locked():
            self.process_manager.clear_process()
            return

        unfollow_count = int(unfollow_count)

        # Get the current following count
        self.update_max_following()
        if unfollow_count > self.max_following:
            self.logger.warning("Unfollow count exceeds total following.")
            messagebox.showerror("Error", f"Cannot unfollow more than {self.max_following} users.")
            self.process_manager.clear_process()
            return

        self.status_label.config(text=f"Unfollowing {unfollow_count} users...")
        self.logger.info(f"Starting the unfollow process for {unfollow_count} users.")

        self.unfollow_thread = threading.Thread(target=self.run_unfollow, args=(unfollow_count,), daemon=True)
        self.unfollow_thread.start()

    def run_unfollow(self, count):
        """
        Runs the unfollow process in a separate thread for a specified count.   
        """
        try:
            self.bot.unfollow_users(count)
            self.update_max_following()
            self.logger.info(f"Successfully unfollowed {count} users.")
            messagebox.showinfo("Success", f"Successfully unfollowed {count} users.")
        except Exception as e:
            self.logger.exception(f"An error occurred during unfollowing: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.status_label.config(text="")
            self.process_manager.clear_process()