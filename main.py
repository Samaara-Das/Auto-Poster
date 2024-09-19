from dotenv import load_dotenv
from x_bot import XBot
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import simpledialog
import threading
import sqlite3
import functools

# Load environment variables
load_dotenv()

def update_credentials(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()
        self.bot.init_credentials(username, password, email)
        return func(self, *args, **kwargs)
    return wrapper

class TwitterBotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Auto Poster")
        master.geometry("1100x700")  # Increased width to accommodate radio buttons

        # Create a frame for the main content
        main_frame = ttk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create left, middle, and right frames
        left_frame = ttk.Frame(main_frame)
        middle_frame = ttk.Frame(main_frame)
        right_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))

        # Username input
        ttk.Label(left_frame, text="X Username:").pack(pady=10)
        self.username_entry = ttk.Entry(left_frame)
        self.username_entry.pack()

        # Email input
        ttk.Label(left_frame, text="Email:").pack(pady=10)
        self.email_entry = ttk.Entry(left_frame)
        self.email_entry.pack()

        # Password input
        ttk.Label(left_frame, text="X Password:").pack(pady=(10, 5))
        password_frame = ttk.Frame(left_frame)
        password_frame.pack(pady=(0, 10))
        self.password_entry = ttk.Entry(password_frame, show="*", width=20)
        self.password_entry.pack(side=tk.LEFT)
        self.show_password_var = tk.BooleanVar()
        self.show_password_button = ttk.Checkbutton(password_frame, text="Show", 
                                                    variable=self.show_password_var, 
                                                    command=self.toggle_password_visibility)
        self.show_password_button.pack(side=tk.LEFT, padx=(5, 0))

        # Message input
        ttk.Label(left_frame, text="Your tweet:").pack(pady=10)
        self.message_box = scrolledtext.ScrolledText(left_frame, width=40, height=10)
        self.message_box.pack(pady=10)

        # Start button
        ttk.Button(left_frame, text="Start Bot", command=self.start_bot).pack(pady=10)

        # Stop button
        self.stop_button = ttk.Button(left_frame, text="Stop Bot", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        # Status label
        self.status_label = ttk.Label(left_frame, text="")
        self.status_label.pack(pady=10)

        # People to reply to list (existing list)
        self.following_label = ttk.Label(middle_frame, text="People you're following: 0")
        self.following_label.pack(pady=10)
        
        # Frame for existing list
        list_frame = ttk.Frame(middle_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # People list 
        columns = ("name", "see_tweet", "reply")
        self.reply_list = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        self.reply_list.heading("name", text="Name")
        self.reply_list.heading("see_tweet", text="See Tweet")
        self.reply_list.heading("reply", text="Reply")
        self.reply_list.column("name", width=150)
        self.reply_list.column("see_tweet", width=75, anchor=tk.CENTER)
        self.reply_list.column("reply", width=75, anchor=tk.CENTER)
        self.reply_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the list
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.reply_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.reply_list.configure(yscrollcommand=scrollbar.set)

        # New list label
        self.added_people_label = ttk.Label(right_frame, text="Added People: 0")
        self.added_people_label.pack(pady=10)

        # Frame for new list
        new_list_frame = ttk.Frame(right_frame)
        new_list_frame.pack(fill=tk.BOTH, expand=True)

        # New list (updated with See Tweet and Reply columns)
        columns = ("name", "see_tweet", "reply")
        self.added_people_list = ttk.Treeview(new_list_frame, columns=columns, show="headings", height=20)
        self.added_people_list.heading("name", text="Name")
        self.added_people_list.heading("see_tweet", text="See Tweet")
        self.added_people_list.heading("reply", text="Reply")
        self.added_people_list.column("name", width=150)
        self.added_people_list.column("see_tweet", width=75, anchor=tk.CENTER)
        self.added_people_list.column("reply", width=75, anchor=tk.CENTER)
        self.added_people_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the new list
        new_scrollbar = ttk.Scrollbar(new_list_frame, orient="vertical", command=self.added_people_list.yview)
        new_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.added_people_list.configure(yscrollcommand=new_scrollbar.set)

        # Add button (moved below the new list)
        ttk.Button(right_frame, text="Add", command=self.add_person).pack(pady=10)

        # Bind double-click event to toggle radio buttons for both lists
        self.reply_list.bind("<Double-1>", self.toggle_radio_button)
        self.added_people_list.bind("<Double-1>", self.toggle_added_people_radio_button)

        # Get following button
        ttk.Button(middle_frame, text="Get Following", command=self.get_following).pack(pady=10)

        # Add Fill Fields button
        ttk.Button(left_frame, text="Fill Fields", command=self.fill_fields).pack(pady=10)

        # Add Delete All Replies and Delete All Likes buttons
        ttk.Button(left_frame, text="Delete All Replies", command=self.delete_replies).pack(pady=5)
        ttk.Button(left_frame, text="Delete All Likes", command=self.delete_likes).pack(pady=5)

        # Create XBot instance with GUI callback
        self.bot = XBot(self.update_gui)
        self.is_bot_running = False

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    @update_credentials
    def start_bot(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()
        messages = self.message_box.get("1.0", tk.END).strip()

        if not self.is_credentials_valid():
            return

        if not messages:
            messagebox.showerror("Error", "Please enter content in the text box.")
            return
        
        # Start the bot in a separate thread
        self.bot.init_credentials(username, password, email)
        self.bot.content = messages
        self.is_bot_running = True 
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()
        
        # Enable the Stop button and disable the Start button
        self.stop_button.config(state=tk.NORMAL)
        self.master.nametowidget(self.stop_button.master).nametowidget("!button").config(state=tk.DISABLED)

    def run_bot(self):
        # Add this method
        try:
            self.bot.run()
        except Exception as e:
            self.update_gui(f"An error occurred: {str(e)}")
        finally:
            self.is_bot_running = False
            self.update_gui("Bot finished running.")

    def stop_bot(self):
        if hasattr(self, 'bot_thread') and self.bot_thread.is_alive():
            self.is_bot_running = False
            self.bot.stop_bot()
            self.bot_thread.join(timeout=5)
            self.status_label.config(text="Bot stopped")

            # Initialize the bot again so that the user can start the bot again
            self.bot = XBot(self.update_gui)

            # Disable the Stop button and enable the Start button
            self.stop_button.config(state=tk.DISABLED)
            self.master.nametowidget(self.stop_button.master).nametowidget("!button").config(state=tk.NORMAL)

    def update_gui(self, action, data=None):
        if action == "update_following_list":
            self.reply_list.delete(*self.reply_list.get_children())  # Clear existing items
            for profile in data:
                self.reply_list.insert("", "end", values=(profile['name'], "", '✓' if profile['reply'] else ''), tags=(profile['link']))
            # Update the label with the following count
            self.following_label.config(text=f"People you're following: {len(data)}")
        elif action == "Bot finished running.":
            self.stop_button.config(state=tk.DISABLED)
            self.master.nametowidget(self.stop_button.master).nametowidget("!button").config(state=tk.NORMAL)
            self.status_label.config(text=action)
        else:
            self.status_label.config(text=action)
            if "Verification required" in action:
                messagebox.showwarning("Verification Required", action)

    @update_credentials
    def add_person(self):
        username = simpledialog.askstring("Add Person", "Enter the person's username:")
        if username:
            name = self.check_username_exists(username)
            if name:
                self.added_people_list.insert("", "end", values=(name, "", "✓"))
                self.bot.browser.added_people.append({"link": 'x.com/' + username, "name": name, "reply": True})
                self.update_added_people_count()
                messagebox.showinfo("Success", f"@{username} added successfully.")
            else:
                messagebox.showerror("Error", f"Please enter a valid X username.")

    def update_added_people_count(self):
        count = len(self.added_people_list.get_children())
        self.added_people_label.config(text=f"Added People: {count}")

    def check_username_exists(self, username):
        '''
        This function checks if the username on X exists or not. `False` is returned if it does not exist or an error occurs. The name of the account is returned if it exists.
        '''
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
            exists = self.bot.browser.check_user_exists(username)
            result[0] = exists
        except Exception as e:
            print(f"Error checking username: {e}")
            result[0] = False

    def is_credentials_valid(self):
        '''
        This function checks if the username, password and email are valid.
        '''
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()

        if not username or not password or not email:
            messagebox.showerror("Error", "Please enter your X username, password and email.")
            return False
        return True

    @update_credentials
    def get_following(self):
        if not self.is_credentials_valid():
            return

        # Start getting following in a separate thread
        threading.Thread(target=self.bot.get_following, daemon=True).start()

    def fill_fields(self):
        '''
        This function fills the username, email, password and tweet fields automatically with default data. This saves time while testing.
        '''
        try:
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
            else:
                self.status_label.config(text="No data found in the database")
            
            conn.close()
        except sqlite3.Error as e:
            self.status_label.config(text=f"Database error: {e}")

    @update_credentials
    def delete_replies(self):
        if not self.is_credentials_valid():
            return

        # Start deleting replies in a separate thread
        threading.Thread(target=self.bot.delete_replies, daemon=True).start()

    @update_credentials
    def delete_likes(self):
        if not self.is_credentials_valid():
            return
        
        # Start deleting likes in a separate thread
        threading.Thread(target=self.bot.delete_likes, daemon=True).start()

    def toggle_radio_button(self, event):
        item = self.reply_list.identify_row(event.y)
        column = self.reply_list.identify_column(event.x)
        
        if column == "#2":  # See Tweet column
            self.reply_list.set(item, "see_tweet", "✓")
            self.reply_list.set(item, "reply", "")
            self.update_profile_reply_status(item, False)
        elif column == "#3":  # Reply column
            self.reply_list.set(item, "see_tweet", "")
            self.reply_list.set(item, "reply", "✓")
            self.update_profile_reply_status(item, True)

    def toggle_added_people_radio_button(self, event):
        item = self.added_people_list.identify_row(event.y)
        column = self.added_people_list.identify_column(event.x)
        
        if column == "#2":  # See Tweet column
            self.added_people_list.set(item, "see_tweet", "✓")
            self.added_people_list.set(item, "reply", "")
            self.update_added_profile_reply_status(item, False)
        elif column == "#3":  # Reply column
            self.added_people_list.set(item, "see_tweet", "")
            self.added_people_list.set(item, "reply", "✓")
            self.update_added_profile_reply_status(item, True)

    def update_profile_reply_status(self, item, reply_status):
        profile_link = self.reply_list.item(item, "tags")[0]
        for profile in self.bot.browser.following:
            if profile['link'] == profile_link:
                profile['reply'] = reply_status
                break

    def update_added_profile_reply_status(self, item, reply_status):
        name = self.added_people_list.item(item, "values")[0]
        for profile in self.bot.browser.added_people:
            if profile['name'] == name:
                profile['reply'] = reply_status
                break

if __name__ == '__main__':
    root = tk.Tk()
    twitter_bot_gui = TwitterBotGUI(root)
    root.mainloop()

