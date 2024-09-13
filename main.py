from dotenv import load_dotenv
from x_bot import XBot
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import simpledialog
import threading
import sqlite3

# Load environment variables
load_dotenv()

class TwitterBotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Auto Poster")
        master.geometry("700x600")

        # Create a frame for the main content
        main_frame = ttk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create left and right frames
        left_frame = ttk.Frame(main_frame)
        right_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

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
        ttk.Button(left_frame, text="Start Bot", command=self.start_bot).pack(pady=20)

        # Status label
        self.status_label = ttk.Label(left_frame, text="")
        self.status_label.pack(pady=10)

        # People to reply to list
        self.following_label = ttk.Label(right_frame, text="People you're following: 0")
        self.following_label.pack(pady=10)
        self.reply_list = tk.Listbox(right_frame, width=30, height=20)
        self.reply_list.pack(pady=10)

        # Scrollbar for the list
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.reply_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.reply_list.configure(yscrollcommand=scrollbar.set)

        # Add and Remove buttons for the list
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Add", command=self.add_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove", command=self.remove_person).pack(side=tk.LEFT)

        # Get following button
        ttk.Button(right_frame, text="Get Following", command=self.get_following).pack(pady=10)

        # Add Fill Fields button
        ttk.Button(left_frame, text="Fill Fields", command=self.fill_fields).pack(pady=10)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def start_bot(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()
        messages = self.message_box.get("1.0", tk.END).strip()

        if not username or not password or not email:
            messagebox.showerror("Error", "Please enter your X username, password and email.")
            return

        if not messages:
            messagebox.showerror("Error", "Please enter content in the text box.")
            return

        # Create XBot instance with GUI callback
        bot = XBot(username, password, email, messages, self.update_gui)
        
        # Start the bot in a separate thread
        threading.Thread(target=bot.run, daemon=True).start()

    def update_gui(self, action, data=None):
        if action == "update_following_list":
            self.reply_list.delete(0, tk.END)  # Clear existing items
            for username in data:
                self.reply_list.insert(tk.END, username)
            # Update the label with the following count
            following_count = len(data)
            self.following_label.config(text=f"People you're following: {following_count}")
        else:
            self.status_label.config(text=action)
            if "Verification required" in action:
                messagebox.showwarning("Verification Required", action)

    def add_person(self):
        person = simpledialog.askstring("Add Person", "Enter the person's username:")
        if person:
            self.reply_list.insert(tk.END, person)

    def remove_person(self):
        selected = self.reply_list.curselection()
        if selected:
            self.reply_list.delete(selected)

    def get_following(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        email = self.email_entry.get()

        if not username or not password or not email:
            messagebox.showerror("Error", "Please enter your X username, password and email.")
            return

        # Create XBot instance
        bot = XBot(username, password, email, "", self.update_gui)
        
        # Start getting following in a separate thread
        threading.Thread(target=bot.get_following, daemon=True).start()

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

if __name__ == '__main__':
    root = tk.Tk()
    twitter_bot_gui = TwitterBotGUI(root)
    root.mainloop()

