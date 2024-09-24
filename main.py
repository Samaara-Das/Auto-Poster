from dotenv import load_dotenv
from x_bot import XBot
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import simpledialog
import threading
import sqlite3
import functools
from logger import logger

# Load environment variables
load_dotenv()

def update_credentials(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()
        self.bot.init_credentials(username, password, email)
        self.logger.info(f"Credentials updated for function: {func.__name__}")
        return func(self, *args, **kwargs)
    return wrapper

class TwitterBotGUI:
    def __init__(self, master):
        self.master = master
        self.is_bot_running = False
        master.title("Auto Poster")
        master.geometry("700x750")

        # Initialize logger
        self.logger = logger(__name__)
        self.logger.info("Initializing TwitterBotGUI")

        # Create the tabs
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

        self.create_settings_tab(settings_frame)
        self.create_bot_targets_tab(bot_targets_frame)

        # Create XBot instance with GUI callback
        self.bot = XBot(self.update_gui)

        # Load added profiles from MongoDB and populate the Added People list
        self.load_added_profiles()

        # Load following profiles and populate the Following list
        self.load_following_profiles()

        self.logger.info("TwitterBotGUI initialization complete")

    def create_settings_tab(self, frame):
        # Username input
        ttk.Label(frame, text="X Username:").pack(pady=10)
        self.username_entry = ttk.Entry(frame)
        self.username_entry.pack()

        # Email input
        ttk.Label(frame, text="Email:").pack(pady=10)
        self.email_entry = ttk.Entry(frame)
        self.email_entry.pack()

        # Password input
        ttk.Label(frame, text="X Password:").pack(pady=(10, 5))
        password_frame = ttk.Frame(frame)
        password_frame.pack(pady=(0, 10))
        self.password_entry = ttk.Entry(password_frame, show="*", width=20)
        self.password_entry.pack(side=tk.LEFT)
        self.show_password_var = tk.BooleanVar()
        self.show_password_button = ttk.Checkbutton(password_frame, text="Show", 
                                                    variable=self.show_password_var, 
                                                    command=self.toggle_password_visibility)
        self.show_password_button.pack(side=tk.LEFT, padx=(5, 0))

        # Message input
        ttk.Label(frame, text="Your tweet:").pack(pady=10)
        self.message_box = scrolledtext.ScrolledText(frame, width=40, height=10)
        self.message_box.pack(pady=10)

        # Start button
        self.start_button = ttk.Button(frame, text="Start Bot", command=self.start_bot)
        self.start_button.pack(pady=10)

        # Stop button
        self.stop_button = ttk.Button(frame, text="Stop Bot", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        # Status label
        self.status_label = ttk.Label(frame, text="")
        self.status_label.pack(pady=10)

        # Fill Fields button
        ttk.Button(frame, text="Fill Fields", command=self.fill_fields).pack(pady=10)

        # Delete All Replies and Likes buttons
        ttk.Button(frame, text="Delete All Replies", command=self.delete_replies).pack(pady=5)
        ttk.Button(frame, text="Delete All Likes", command=self.delete_likes).pack(pady=5)

    def toggle_password_visibility(self):
        '''
        If the password is visible, it is hidden. Otherwise, if it is hidden, it is shown.
        '''
        self.logger.info("Toggling password visibility")
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def create_bot_targets_tab(self, frame):
        # Frame for Lists
        lists_container = ttk.Frame(frame)
        lists_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_following_section(lists_container)
        self.create_added_people_section(lists_container)

    def create_following_section(self, container):
        following_section = ttk.LabelFrame(container, text="Following List")
        following_section.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 10))

        # People you're following label
        self.following_label = ttk.Label(following_section, text="People you're following: 0")
        self.following_label.pack(pady=10)

        # Frame for following list
        list_frame = ttk.Frame(following_section)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # People list 
        columns = ("name", "see_tweet", "reply")
        self.reply_list = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        self.reply_list.heading("name", text="Name")
        self.reply_list.heading("see_tweet", text="See Tweet")
        self.reply_list.heading("reply", text="Reply")
        self.reply_list.column("name", width=150)
        self.reply_list.column("see_tweet", width=75, anchor=tk.CENTER)
        self.reply_list.column("reply", width=75, anchor=tk.CENTER)
        self.reply_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the following list
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.reply_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.reply_list.configure(yscrollcommand=scrollbar.set)

        # Get following button
        ttk.Button(following_section, text="Get Following", command=self.get_following).pack(pady=10)

    def create_added_people_section(self, container):
        added_section = ttk.LabelFrame(container, text="Added People")
        added_section.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Added People label
        self.added_people_label = ttk.Label(added_section, text="Added People: 0")
        self.added_people_label.pack(pady=10)

        # Frame for added people list
        new_list_frame = ttk.Frame(added_section)
        new_list_frame.pack(fill=tk.BOTH, expand=True)

        # Added people list
        columns = ("name", "see_tweet", "reply")
        self.added_people_list = ttk.Treeview(new_list_frame, columns=columns, show="headings", height=15)
        self.added_people_list.heading("name", text="Name")
        self.added_people_list.heading("see_tweet", text="See Tweet")
        self.added_people_list.heading("reply", text="Reply")
        self.added_people_list.column("name", width=150)
        self.added_people_list.column("see_tweet", width=75, anchor=tk.CENTER)
        self.added_people_list.column("reply", width=75, anchor=tk.CENTER)
        self.added_people_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the added people list
        new_scrollbar = ttk.Scrollbar(new_list_frame, orient="vertical", command=self.added_people_list.yview)
        new_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.added_people_list.configure(yscrollcommand=new_scrollbar.set)

        # Add/Delete buttons in Added People tab
        self.delete_button = ttk.Button(added_section, text="Delete", command=self.delete_person)
        self.delete_button.pack(pady=10)
        self.update_delete_button_state()

        ttk.Button(added_section, text="Add", command=self.add_person).pack(pady=10)

        # Bind double-click event to toggle radio buttons for both lists
        self.reply_list.bind("<Double-1>", self.toggle_radio_button)
        self.added_people_list.bind("<Double-1>", self.toggle_added_people_radio_button)

    @update_credentials
    def start_bot(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()
        messages = self.message_box.get("1.0", tk.END).strip()

        if not self.is_credentials_valid():
            self.logger.warning("Invalid credentials provided")
            return

        if not messages:
            self.logger.warning("No content provided in the text box")
            messagebox.showerror("Error", "Please enter content in the text box.")
            return
        
        self.logger.info("Starting bot")
        self.bot.content = messages
        self.is_bot_running = True 
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()
        
        # Enable the Stop button and disable the Start button
        self.stop_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.DISABLED)
        self.update_delete_button_state()

    def run_bot(self):
        try:
            self.logger.info("Bot thread started")
            self.bot.run()
        except Exception as e:
            self.logger.exception(f"An error occurred while running the bot: {str(e)}")
            self.update_gui(f"An error occurred: {str(e)}")
        finally:
            self.is_bot_running = False
            self.logger.info("Bot finished running")
            self.update_gui("Bot finished running.")

    def stop_bot(self):
        if hasattr(self, 'bot_thread') and self.bot_thread.is_alive():
            self.logger.info("Stopping bot")
            self.is_bot_running = False
            self.bot.stop_bot()
            self.bot_thread.join(timeout=5)
            self.status_label.config(text="Bot stopped")

            # Initialize the bot again so that the user can start the bot again
            self.bot = XBot(self.update_gui)

            # Disable the Stop button and enable the Start button
            self.stop_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            self.logger.info("Bot stopped successfully")
            self.update_delete_button_state()

    def update_gui(self, action, data=None):
        '''
        This function updates the GUI based on the action and data provided.
        '''
        if action == "update_following_list":
            self.logger.info("Updating following list in the GUI")
            self.reply_list.delete(*self.reply_list.get_children())  # Clear existing items
            for profile in data:
                reply_value = profile.get('reply', True)  # Default to True if 'reply' field is not present
                self.reply_list.insert("", "end", values=(
                    profile['name'],
                    '' if reply_value else '✓',  # See Tweet
                    '✓' if reply_value else ''   # Reply
                ), tags=(profile['link']))
            # Update the label with the following count
            self.following_label.config(text=f"People you're following: {len(data)}")
        elif action == "Bot finished running.":
            self.logger.info("showing the \"bot finished running\" message to the user")
            self.stop_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            self.status_label.config(text=action)
            self.is_bot_running = False
            self.update_delete_button_state()
        else:
            self.status_label.config(text=action)
            if "Verification required" in action:
                self.logger.info("showing a \"verification required\" message to the user")
                messagebox.showwarning("Verification Required", action)

    @update_credentials
    def add_person(self):
        username = simpledialog.askstring("Add Person", "Enter the person's username:")
        if username:
            self.logger.info(f"Attempting to add person: {username} to the GUI and MongoDB database")
            name = self.check_username_exists(username)
            if name:
                profile_link = f"https://x.com/{username}"
                # Scrape profile data
                profile_data = self.bot.browser.scrape_profile_data(profile_link)
                if profile_data:
                    # Save to 'added' collection
                    self.bot.db_manager.save_added_profile(profile_data)
                    # Add to GUI list
                    self.added_people_list.insert("", "end", values=(name, "", "✓"))
                    self.bot.browser.added_people.append({
                        "link": profile_link,
                        "name": name,
                        "reply": True
                    })
                    self.update_added_people_count()
                    self.logger.info(f"Successfully added @{username} to the GUI and MongoDB database")
                    messagebox.showinfo("Success", f"@{username} added successfully.")
                else:
                    self.logger.warning(f"Failed to scrape profile data for @{username}")
                    messagebox.showerror("Error", f"Failed to scrape profile data for @{username}.")
            else:
                self.logger.warning(f"@{username} does not exist")
                messagebox.showerror("Error", f"@{username} does not exist.")

    def update_added_people_count(self):
        count = len(self.bot.browser.added_people)
        self.added_people_label.config(text=f"Added People: {count}")

    def check_username_exists(self, username):
        '''
        This function checks if the username on X exists or not. `False` is returned if it does not exist or an error occurs. The name of the account is returned if it exists.
        '''
        self.logger.info(f"Checking if @{username} exists")
        if not self.is_credentials_valid():
            return False
        
        # Use a separate thread to check the username
        result = [False] 
        thread = threading.Thread(target=lambda: self.check_username_thread(username, result))
        thread.start()
        thread.join(timeout=10) 

        return result[0]

    def check_username_thread(self, username, result):
        '''
        This function checks if the provided username on X exists or not. If it does, the name of the account is returned.
        '''
        try:
            self.logger.info(f"Checking if @{username} exists")
            exists = self.bot.browser.check_user_exists(username)
            result[0] = exists
        except Exception as e:
            self.logger.exception(f"Error checking username: {e}")
            result[0] = False

    def is_credentials_valid(self):
        '''
        This function checks if the username, password and email are valid.
        '''
        self.logger.info("Checking if credentials are valid")
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()

        if not username or not password or not email:
            self.logger.warning(f"Invalid credentials provided. username: {username}, password: {password}, email: {email}")
            messagebox.showerror("Error", "Please enter your X username, password and email.")
            return False
        return True
    
    @update_credentials
    def get_following(self):
        if not self.is_credentials_valid():
            return

        # Start getting following in a separate thread
        self.logger.info("Starting to get following in a separate thread")
        threading.Thread(target=self.bot.get_following, daemon=True).start()

    def fill_fields(self):
        '''
        This function fills the username, email, password and tweet fields automatically with default data. This saves time while testing.
        '''
        try:
            self.logger.info("Attempting to fill fields with default data from the SQL database")
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()
            
            # Fetch user data from the database, including tweet_text
            cursor.execute("SELECT username, email, password, tweet_text FROM user_data LIMIT 1")
            user_data = cursor.fetchone()
            
            if user_data:
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, user_data[0])
                
                self.email_entry.delete(0, tk.END)
                self.email_entry.insert(0, user_data[1])
                
                self.password_entry.delete(0, tk.END)
                self.password_entry.insert(0, user_data[2])
                
                self.message_box.delete("1.0", tk.END)
                self.message_box.insert(tk.END, user_data[3])
                
                self.status_label.config(text="Fields filled successfully")
                self.logger.info("Fields filled successfully with default data")
            else:
                self.status_label.config(text="No data found in the database")
                self.logger.warning("No data found in the database for filling fields")
            
            conn.close()
        except sqlite3.Error as e:
            self.logger.exception(f"Database error while filling fields: {e}")
            self.status_label.config(text=f"Database error: {e}")

    @update_credentials
    def delete_replies(self):
        if not self.is_credentials_valid():
            return

        # Start deleting replies in a separate thread
        self.logger.info("Starting to delete replies in a separate thread")
        threading.Thread(target=self.bot.delete_replies, daemon=True).start()

    @update_credentials
    def delete_likes(self):
        if not self.is_credentials_valid():
            return
        
        # Start deleting likes in a separate thread
        self.logger.info("Starting to delete likes in a separate thread")
        threading.Thread(target=self.bot.delete_likes, daemon=True).start()

    def toggle_radio_button(self, event):
        '''
        This function toggles the See Tweet and Reply columns for a profile in the Following list.
        '''
        self.logger.info("Toggling the See Tweet and Reply columns for a profile in the Following list")
        item = self.reply_list.identify_row(event.y)
        column = self.reply_list.identify_column(event.x)
        
        if column == "#2":  # See Tweet column
            self.logger.info(f"Toggling See Tweet")
            self.reply_list.set(item, "see_tweet", "✓")
            self.reply_list.set(item, "reply", "")
            self.update_profile_reply_status(item, False)
        elif column == "#3":  # Reply column
            self.logger.info(f"Toggling Reply")
            self.reply_list.set(item, "see_tweet", "")
            self.reply_list.set(item, "reply", "✓")
            self.update_profile_reply_status(item, True)

    def toggle_added_people_radio_button(self, event):
        '''
        This function toggles the See Tweet and Reply columns for a profile in the Added People list.
        '''
        self.logger.info("Toggling the See Tweet and Reply columns for a profile in the Added People list")
        item = self.added_people_list.identify_row(event.y)
        column = self.added_people_list.identify_column(event.x)
        
        if column == "#2":  # See Tweet column
            self.logger.info(f"Toggling See Tweet")
            self.added_people_list.set(item, "see_tweet", "✓")
            self.added_people_list.set(item, "reply", "")
            self.update_added_profile_reply_status(item, False)
        elif column == "#3":  # Reply column
            self.logger.info(f"Toggling Reply")
            self.added_people_list.set(item, "see_tweet", "")
            self.added_people_list.set(item, "reply", "✓")
            self.update_added_profile_reply_status(item, True)

    def update_profile_reply_status(self, item, reply_status):
        '''
        This function updates the reply status of a profile in the mongodb database.
        '''
        try:
            profile_link = self.reply_list.item(item, "tags")[0]
            for profile in self.bot.browser.following:
                if profile['link'] == profile_link:
                    profile['reply'] = reply_status
                    self.bot.db_manager.following_collection.update_one(
                        {'link': profile_link},
                        {'$set': {'reply': reply_status}}
                    )
                    self.logger.info(f"Updated reply status to {reply_status} for {profile_link}")
                    break
        except Exception as e:
            self.logger.error(f"Failed to update profile reply status: {e}")

    def update_added_profile_reply_status(self, item, reply_status):
        try:
            name = self.added_people_list.item(item, "values")[0]
            profile = next((p for p in self.bot.browser.added_people if p['name'] == name), None)
            self.logger.info(f"Updating the reply status of {profile['link']} in the Added list to {reply_status} in the mongodb database")
            if profile:
                profile['reply'] = reply_status
                self.bot.db_manager.update_added_profile(profile['link'], reply_status)
        except Exception as e:
            self.logger.error(f"Failed to update reply status: {e}")

    def load_added_profiles(self):
        self.logger.info("Loading added profiles from MongoDB")
        try:
            added_profiles = self.bot.browser.added_people
            for profile in added_profiles:
                self.added_people_list.insert("", "end", values=(
                    profile['name'],
                    '✓' if not profile.get('reply', True) else '',
                    '✓' if profile.get('reply', True) else ''
                ), tags=(profile['link']))
            self.update_added_people_count()
            self.logger.info(f"Successfully loaded {len(added_profiles)} added profiles")
        except Exception as e:
            self.logger.exception(f"Failed to load added profiles: {e}")

    def delete_person(self):
        self.logger.info("Attempting to delete a person from the added people list")
        selected_item = self.added_people_list.selection()
        if not selected_item:
            self.logger.warning("No profile selected for deletion")
            messagebox.showwarning("No Selection", "Please select a profile to delete.")
            return

        for item in selected_item:
            profile_name = self.added_people_list.item(item, "values")[0]
            # Assume 'link' is unique and stored as tag
            profile_link = self.added_people_list.item(item, "tags")[0]
            
            self.logger.info(f"Attempting to delete profile: {profile_name} with link: {profile_link}")
            
            # Delete from MongoDB
            success = self.bot.db_manager.delete_added_profile(profile_link)
            if success:
                # Remove from UI
                self.added_people_list.delete(item)
                self.update_added_people_count()
                self.logger.info(f"Successfully deleted profile: {profile_name}")
                messagebox.showinfo("Success", f"@{profile_name} has been deleted.")
            else:
                self.logger.error(f"Failed to delete profile: {profile_name}")
                messagebox.showerror("Error", f"Failed to delete @ {profile_name}.")

        self.update_delete_button_state()

    def update_delete_button_state(self):
        if self.is_bot_running:
            self.delete_button.config(state=tk.DISABLED)
            self.logger.info("Bot is running, disabling delete button")
        else:
            self.delete_button.config(state=tk.NORMAL)
            self.logger.info("Bot is not running, enabling delete button")

    def load_following_profiles(self):
        '''Loads profiles from the following collection in MongoDB and populates the Following list in the GUI'''
        try:
            following_list = self.bot.browser.following
            for profile in following_list:
                self.reply_list.insert("", "end", values=(
                    profile['name'],
                    '✓' if not profile['reply'] else '',
                    '✓' if profile['reply'] else ''
                ), tags=(profile['link']))
            self.following_label.config(text=f"People you're following: {len(following_list)}")
            self.logger.info("Loaded following profiles into the GUI")
        except Exception as e:
            self.logger.error(f"Failed to load following profiles: {e}")

if __name__ == '__main__':
    root = tk.Tk()
    twitter_bot_gui = TwitterBotGUI(root)
    root.mainloop()
