import json
from database_manager import DatabaseManager
from x_controller import XController, VerificationRequiredException
from time import sleep

# These are high level methods that interact with XController methods.
class XBot:
    def __init__(self, username, password, email, content, gui_callback):
        self.db_manager = DatabaseManager()
        self.browser = XController()
        self.max_retries = 3
        self.retry_delay = 5
        self.profile_delay = 2
        self.username = username
        self.password = password
        self.email = email
        self.content = content
        self.gui_callback = gui_callback  # New: callback function for GUI updates

    def initialize_environment(self):
        '''This method clears the processed profiles, signs in to X and goes to the following page of the specified user. It also updates the GUI with a list of the people that the user is following and displays error messages if any occur'''
        with open('processed_profiles.json', 'w') as f:
            json.dump([], f)
        try:
            self.browser.sign_in(self.username, self.password, self.email)
            self.get_following()
        except VerificationRequiredException as ve:
            error_message = str(ve)
            self.gui_callback(error_message)  # Use the callback to update GUI
            return False
        except Exception as e:
            error_message = f"An error occurred during initialization: {str(e)}"
            self.gui_callback(error_message)  # Use the callback to update GUI
            return False
        return True

    def get_following(self):
        '''This method gets the list of people that the user is following and displays it on the GUI'''
        self.browser.go_to_following(self.username)
        self.browser.get_following_usernames()
        self.gui_callback("update_following_list", self.browser.following)

    def interact_with_tweet(self):
        tweet_element = self.browser.scroll_to_latest_post()
        if not tweet_element:
            print("Failed to find the latest non-ad and non-pinned tweet")
            return

        self.like_and_reply(tweet_element, tweet_author)

        tweet_link = self.browser.get_tweet_link(tweet_element)
        tweet_author = self.browser.get_tweet_author(tweet_element)
        if not (tweet_link and tweet_author):
            print(f"Failed to get tweet link for {tweet_author}")
            return

        self.db_manager.save_tweet(tweet_link, tweet_author)
        print(f"Saved tweet link: {tweet_link} by author: {tweet_author}")

    def open_profile(self, profile_url):
        """
        Opens the profile of the next person in the list of people that the user is following.
        Returns True if the profile is opened, False otherwise.
        """
        try:
            # Open the X profile
            self.browser.driver.get(profile_url)
            self.browser.logger.info(f"Opened profile: {profile_url}")
            return True
        except Exception as e:
            self.browser.logger.exception(f"Failed to open profile. Error: {str(e)}")
            return False

    def like_and_reply(self, tweet_element, tweet_author):
        for attempt in range(self.max_retries):
            if self.browser.like_tweet(tweet_element):
                print(f"Liked the tweet by {tweet_author} successfully")
                self.send_reply(tweet_element, tweet_author)
                break
            elif attempt < self.max_retries - 1:
                print(f"Failed to like tweet, retrying in {self.retry_delay} seconds...")
                sleep(self.retry_delay)
            else:
                print(f"Failed to like the tweet by {tweet_author} after {self.max_retries} attempts")

    def send_reply(self, tweet_element, tweet_author):
        if self.browser.click_reply_button(tweet_element):
            if self.browser.type_reply(self.content) and self.browser.send_reply():
                print(f"Replied to the tweet by {tweet_author} successfully")
            else:
                print(f"Failed to send reply to {tweet_author}")
        else:
            print(f"Failed to open reply dialog for {tweet_author}")

    def cleanup(self):
        self.browser.close_current_tab()
        sleep(self.profile_delay)

    def run(self):
        if not self.initialize_environment():
            return  # Exit the method if initialization fails

        while True:
            for profile in self.browser.following:
                try:
                    self.open_profile(profile)
                    self.interact_with_tweet()
                except Exception as e:
                    error_message = f"An error occurred while processing a profile: {str(e)}"
                    self.gui_callback(error_message)  # Use the callback to update GUI
                    self.browser.logger.exception("Error in main loop")
                    sleep(self.retry_delay)
            
            break # if for loop broken, break the while loop

        self.browser.driver.stop_client()
        self.browser.driver.close()
        self.browser.driver.quit()
        self.gui_callback("Bot finished running.")  # Notify GUI that the bot has finished
