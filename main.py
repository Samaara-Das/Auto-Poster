from dotenv import load_dotenv
from x_bot import XBot
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter import simpledialog

# Load environment variables
load_dotenv()

class TwitterBotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Auto Poster")
        master.geometry("700x600")  # Increased width to accommodate the new list

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

        # Password input
        password_frame = ttk.Frame(left_frame)
        password_frame.pack(fill=tk.X, pady=10)
        ttk.Label(password_frame, text="X Password:").pack(side=tk.LEFT)
        self.password_entry = ttk.Entry(password_frame, show="*")
        self.password_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.show_password_var = tk.BooleanVar()
        self.show_password_button = ttk.Checkbutton(password_frame, text="Show", 
                                                    variable=self.show_password_var, 
                                                    command=self.toggle_password_visibility)
        self.show_password_button.pack(side=tk.RIGHT)

        # Message input
        ttk.Label(left_frame, text="Your tweet:").pack(pady=10)
        self.message_box = scrolledtext.ScrolledText(left_frame, width=40, height=10)
        self.message_box.pack(pady=10)

        # Start button
        ttk.Button(left_frame, text="Start Bot", command=self.start_bot).pack(pady=20)

        # People to reply to list
        ttk.Label(right_frame, text="People to reply to").pack(pady=10)
        self.reply_list = tk.Listbox(right_frame, width=30, height=20)
        self.reply_list.pack(pady=10)

        # Add and Remove buttons for the list
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Add", command=self.add_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove", command=self.remove_person).pack(side=tk.LEFT)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def start_bot(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        messages = self.message_box.get("1.0", tk.END).strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        if not messages:
            messagebox.showerror("Error", "Please enter content in the text box.")
            return
        bot = XBot(username, password, messages)
        bot.run()

    def add_person(self):
        person = simpledialog.askstring("Add Person", "Enter the person's username:")
        if person:
            self.reply_list.insert(tk.END, person)

    def remove_person(self):
        selected = self.reply_list.curselection()
        if selected:
            self.reply_list.delete(selected)

if __name__ == '__main__':
    root = tk.Tk()
    twitter_bot_gui = TwitterBotGUI(root)
    root.mainloop()

