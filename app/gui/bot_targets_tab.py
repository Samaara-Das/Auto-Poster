import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading

class BotTargetsTab:
    def __init__(self, frame, logger, bot, process_manager):
        self.frame = frame
        self.logger = logger
        self.bot = bot
        self.process_manager = process_manager  # Reference to ProcessManager
        self.get_following_thread = None  # Reference to the get_following thread
        self.add_person_thread = None      # Reference to the add_person thread

        self.create_widgets()
        self.load_following_profiles()
        self.load_added_profiles()

    def create_widgets(self):
        lists_container = ttk.Frame(self.frame)
        lists_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.create_following_section(lists_container)
        self.create_added_section(lists_container)

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
        self.following_list = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        self.following_list.heading("name", text="Name")
        self.following_list.heading("see_tweet", text="See Tweet")
        self.following_list.heading("reply", text="Reply")
        self.following_list.column("name", width=150)
        self.following_list.column("see_tweet", width=75, anchor=tk.CENTER)
        self.following_list.column("reply", width=75, anchor=tk.CENTER)
        self.following_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for the following list
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.following_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.following_list.configure(yscrollcommand=scrollbar.set)

        # Get Following button
        self.get_following_button = ttk.Button(following_section, text="Get Following", command=self.get_following)
        self.get_following_button.pack(pady=10)

        # Stop Get Following button
        self.stop_get_following_button = ttk.Button(following_section, text="Stop Get Following", command=self.stop_get_following, state=tk.DISABLED)
        self.stop_get_following_button.pack(pady=10)

        # Bind double-click event to toggle radio buttons for list
        self.following_list.bind("<Double-1>", self.toggle_following_radio_button)

    def create_added_section(self, container):
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
        self.added_people_list = ttk.Treeview(
            new_list_frame,
            columns=columns,
            show="headings",
            height=15
        )
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

        # Delete button
        self.delete_button = ttk.Button(added_section, text="Delete", command=self.delete_person)
        self.delete_button.pack(pady=10)
        self.update_delete_button_state()

        # Frame for Add and Stop Add Process buttons
        button_frame = ttk.Frame(added_section)
        button_frame.pack(pady=10)

        # Add button
        self.add_button = ttk.Button(button_frame, text="Add", command=self.add_person)
        self.add_button.pack(side=tk.LEFT, padx=(0, 5))

        # Stop Add Process button
        self.stop_add_process_button = ttk.Button(button_frame, text="Stop Add Process", command=self.stop_add_process, state=tk.DISABLED)
        self.stop_add_process_button.pack(side=tk.LEFT, padx=(5, 0))

        # Bind double-click event to toggle radio buttons for list
        self.added_people_list.bind("<Double-1>", self.toggle_added_radio_button)

    def get_following(self):
        """
        Initiates the process of fetching following profiles in a separate thread to keep the GUI 
        responsive.
        Disables the Get Following button and enables the Stop Get Following button.
        """
        process_name = "Get Following"
        success, message = self.process_manager.request_start(process_name)
        if not success:
            messagebox.showwarning("Process Ongoing", message)
            return

        if not self.bot.is_credentials_valid():
            self.logger.warning(f"Invalid credentials provided. username: {self.bot.username}, password: {self.bot.password}, email: {self.bot.email}")
            messagebox.showerror("Error", "Please enter your X username, password and email in the Settings tab.")
            self.process_manager.clear_process()
            return
        
        if self.check_account_locked():
            self.process_manager.clear_process()
            return

        # Disable Get Following button and enable Stop Get Following button
        self.get_following_button.config(state=tk.DISABLED)
        self.stop_get_following_button.config(state=tk.NORMAL)

        # Start the get_following process in a separate thread
        self.get_following_thread = threading.Thread(target=self._get_following_thread, daemon=True)
        self.get_following_thread.start()

    def _get_following_thread(self):
        """
        The actual method that runs in a separate thread to fetch following profiles.
        After completion, re-enable/disable buttons appropriately.
        """
        try:
            success = self.bot.get_following()
            if success:
                self.logger.info("Get Following process completed successfully.")
            else:
                self.logger.warning("Get Following process did not complete successfully.")
        except Exception as e:
            self.logger.exception(f"An error occurred in Get Following thread: {e}")
        finally:
            # Schedule the UI update on the main thread
            self.frame.after(0, self._reset_get_following_buttons)

    def _reset_get_following_buttons(self):
        """
        Resets the state of the Get Following and Stop Get Following buttons.
        This method should be called from the main thread.
        """
        self.get_following_button.config(state=tk.NORMAL)
        self.stop_get_following_button.config(state=tk.DISABLED)
        self.process_manager.clear_process()

    def add_person(self):
        """
        Initiates the process of adding a person in a separate thread to keep the GUI responsive.
        Disables the Add button and enables the Stop Add Process button.
        """
        process_name = "Add Person"
        success, message = self.process_manager.request_start(process_name)
        if not success:
            messagebox.showwarning("Process Ongoing", message)
            return

        if self.check_account_locked():
            self.process_manager.clear_process()
            return

        # Prompt user for the username to add
        username = simpledialog.askstring("Add Person", "Enter the person's username:")
        if username:
            # Disable Add button and enable Stop Add Process button
            self.add_button.config(state=tk.DISABLED)
            self.stop_add_process_button.config(state=tk.NORMAL)

            # Start the add_person process in a separate thread
            self.add_person_thread = threading.Thread(target=self._add_person_thread, args=(username,), daemon=True)
            self.add_person_thread.start()

    def _add_person_thread(self, username):
        """
        The actual method that runs in a separate thread to add a person.
        After completion, re-enable/disable buttons appropriately.
        """
        try:
            self.logger.info(f"Attempting to add person: {username} to the GUI and MongoDB database")
            name = self.bot.browser.check_user_exists(username)
            if name:
                profile_link = f"https://x.com/{username}"
                # Scrape profile data
                profile_data = self.bot.browser.scrape_profile_data(profile_link)
                if profile_data and not self.bot.browser.stop_add_process:
                    # Update in MongoDB, code and GUI
                    self.bot.browser.db_manager.save_added_profile(profile_data)
                    self.bot.browser.added_people.append(profile_data)
                    # Schedule GUI updates on the main thread
                    self.frame.after(0, self.update_added_people_count)
                    self.frame.after(0, lambda: self.insert_added_people_list(profile_data))
                    self.logger.info(f"Successfully added @{username} to the GUI and MongoDB database")
                    self.frame.after(0, lambda: messagebox.showinfo("Success", f"@{username} added successfully."))
                else:
                    self.logger.warning(f"Failed to scrape profile data for @{username}")
                    self.frame.after(0, lambda: messagebox.showerror("Error", f"Failed to scrape profile data for @{username}."))
            else:
                self.logger.warning(f"@{username} does not exist")
                self.frame.after(0, lambda: messagebox.showerror("Error", f"@{username} does not exist."))
        except Exception as e:
            self.logger.exception(f"An error occurred while adding person @{username}: {e}")
            self.frame.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
        finally:
            # Schedule the UI update on the main thread
            self.frame.after(0, self._reset_add_buttons)

    def _reset_add_buttons(self):
        """
        Resets the state of the Add and Stop Add Process buttons.
        This method should be called from the main thread.
        """
        self.process_manager.clear_process()
        self.add_button.config(state=tk.NORMAL)
        self.stop_add_process_button.config(state=tk.DISABLED)

    def stop_add_process(self):
        """
        Stops the Add process.
        Sets the stop flag in the bot and updates button states.
        """
        self.bot.stop_add_process()

        # Disable Stop Add Process button and enable Add button
        self.stop_add_process_button.config(state=tk.DISABLED)
        self.add_button.config(state=tk.NORMAL)

        self.process_manager.clear_process()
        self.logger.info("Add process has been requested to stop.")

    def toggle_following_radio_button(self, event):
        """
        This function toggles the See Tweet and Reply columns for a profile in the Following list.
        """
        self.logger.info("Toggling the See Tweet and Reply columns for a profile in the Following list")
        item = self.following_list.identify_row(event.y)
        column = self.following_list.identify_column(event.x)

        if column == "#2":  # See Tweet column
            self.logger.info(f"Toggling See Tweet")
            self.following_list.set(item, "see_tweet", "✓")
            self.following_list.set(item, "reply", "")
            self.update_following_profile_reply_status(item, False)
        elif column == "#3":  # Reply column
            self.logger.info(f"Toggling Reply")
            self.following_list.set(item, "see_tweet", "")
            self.following_list.set(item, "reply", "✓")
            self.update_following_profile_reply_status(item, True)

    def toggle_added_radio_button(self, event):
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

    def update_following_profile_reply_status(self, item, reply_status):
        """
        Updates the reply status of a following profile in the database.
        """
        try:
            name = self.following_list.item(item, "values")[0]
            profile = next((p for p in self.bot.browser.following if p['name'] == name), None)
            self.logger.info(f"Updating the reply status of {profile['link']} in the Following list to {reply_status} in the MongoDB database")
            if profile:
                self.bot.browser.db_manager.update_following_profile(profile['link'], reply_status)
        except Exception as e:
            self.logger.error(f"Failed to update profile reply status: {e}")

    def update_added_profile_reply_status(self, item, reply_status):
        """
        Updates the reply status of an added profile in the database.
        """
        try:
            name = self.added_people_list.item(item, "values")[0]
            profile = next((p for p in self.bot.browser.added_people if p['name'] == name), None)
            self.logger.info(f"Updating the reply status of {profile['link']} in the Added list to {reply_status} in the MongoDB database")
            if profile:
                self.bot.browser.db_manager.update_added_profile(profile['link'], reply_status)
        except Exception as e:
            self.logger.error(f"Failed to update reply status: {e}")

    def delete_person(self):
        """
        Deletes selected profiles from the Added People list.
        """
        self.logger.info("Attempting to delete a person from the added people list")
        selected_items = self.added_people_list.selection()
        if not selected_items:
            self.logger.warning("No profile selected for deletion")
            messagebox.showwarning("No Selection", "Please select a profile to delete.")
            return

        for item in selected_items:
            profile_name = self.added_people_list.item(item, "values")[0]
            profile_link = self.added_people_list.item(item, "tags")[0]

            self.logger.info(f"Attempting to delete profile: {profile_name} with link: {profile_link}")
            
            # Remove from MongoDB, code and GUI
            self.bot.browser.db_manager.delete_added_profile(profile_link)
            self.bot.browser.remove_added_person(profile_link)
            self.added_people_list.delete(item)
            self.logger.info(f"Successfully deleted profile: {profile_name}")
            messagebox.showinfo("Success", f"@{profile_name} has been deleted.")

        self.update_delete_button_state()

    def update_delete_button_state(self):
        """
        Updates the state of the Delete button based on whether the bot is running.
        """
        if self.bot.is_running:
            self.delete_button.config(state=tk.DISABLED)
            self.logger.info("Bot is running, disabling delete button")
        else:
            self.delete_button.config(state=tk.NORMAL)
            self.logger.info("Bot is not running, enabling delete button")

    def load_following_profiles(self):
        """
        Populates the Following list in the GUI with the user's following list.
        """
        try:
            following_list = self.bot.browser.following
            for profile in following_list:
                reply_status = '✓' if profile['reply'] else ''
                see_tweet_status = '✓' if not profile['reply'] else ''
                self.following_list.insert("", "end", values=(profile['name'], see_tweet_status, reply_status), tags=(profile['link'],))

            self.following_label.config(text=f"People you're following: {len(following_list)}")
            self.logger.info("Loaded following profiles into the GUI")
        except Exception as e:
            self.logger.error(f"Failed to load following profiles: {e}")

    def load_added_profiles(self):
        """
        Populates the Added list in the GUI with the user's added profiles.
        """
        try:
            added_list = self.bot.browser.added_people
            for profile in added_list:
                self.insert_added_people_list(profile)

            self.added_people_label.config(text=f"Added People: {len(added_list)}")
            self.logger.info("Loaded added profiles into the GUI")
        except Exception as e:
            self.logger.error(f"Failed to load added profiles: {e}")

    def insert_added_people_list(self, profile_data):
        '''Inserts a profile into the Added People list in the GUI'''
        reply_status = '✓' if profile_data['reply'] else ''
        see_tweet_status = '✓' if not profile_data['reply'] else ''
        self.added_people_list.insert("", "end", values=(profile_data['name'], see_tweet_status, reply_status), tags=(profile_data['link'],))

    def check_account_locked(self):
        """
        Checks if the account is locked and shows a popup message if it is.
        Returns True if the account is locked, False otherwise.
        """
        if self.bot.browser.is_account_locked_page_open():
            self.logger.warning("Account is locked.")
            messagebox.showerror("Account Locked", "Your X account has been locked. Please unlock your account.")
            return True
        return False

    def update_added_people_count(self):
        """
        Updates the count of added people in the GUI.
        """
        count = len(self.bot.browser.added_people)
        self.added_people_label.config(text=f"Added People: {count}")

    def stop_get_following(self):
        """
        Stops the Get Following process.
        Sets the stop flag in the bot and updates button states.
        """
        self.bot.browser.set_stop_get_following(True)
        self.logger.info("Get Following process has been requested to stop.")

        # Disable Stop Get Following button and enable Get Following button
        self.stop_get_following_button.config(state=tk.DISABLED)
        self.get_following_button.config(state=tk.NORMAL)

        self.process_manager.clear_process()

    def stop_add_process(self):
        """
        Stops the Add process.
        Sets the stop flag in the bot and updates button states.
        """
        self.bot.browser.set_stop_add_process(True)
        self.logger.info("Add process has been requested to stop.")

        # Disable Stop Add Process button and enable Add button
        self.stop_add_process_button.config(state=tk.DISABLED)
        self.add_button.config(state=tk.NORMAL)

        self.process_manager.clear_process()