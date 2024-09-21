from database_manager import DatabaseManager
from x_controller import XController, VerificationRequiredException, rest
from time import sleep
from delete_reactions import delete_all_replies, delete_all_likes
from logger import logger
import threading

# These are high level methods that interact with XController methods.
class XBot:
    def __init__(self, gui_callback):
        self.db_manager = DatabaseManager()
        self.browser = XController()
        self.get_following_lock = threading.Lock()
        self.max_retries = 3
        self.retry_delay = 5
        self.profile_delay = 2
        self.username = ''
        self.password = ''
        self.email = ''
        self.content = ''
        self.gui_callback = gui_callback
        self.is_running = False
        self.logger = logger(__name__)

    def init_credentials(self, username, password, email):
        '''this sets the username, password and email attributes to the values passed in'''
        self.username = username
        self.password = password
        self.email = email
        self.logger.info(f"Initialized credentials for {self.username}.")

    def initialize_environment(self):
        '''This method signs in to X and goes to the following page of the specified user. It also updates the GUI with a list of the people that the user is following and displays error messages if any occur'''
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
        '''This method opens the user's following page, gets the list of people that the user is following and displays it on the GUI'''
        with self.get_following_lock:
            self.browser.go_to_following(self.username)
            self.browser.get_following()
            self.gui_callback("update_following_list", self.db_manager.get_following_list())

    def interact_with_tweet(self, profile):
        '''This method opens the profile page of the person passed in, scrolls to the latest tweet, likes the tweet, and replies to it if it's allowed. The tweet is then saved to the database.'''
        self.browser.reload_page(mins_to_wait=2)
        tweet_element = self.browser.scroll_to_latest_post()
        if not tweet_element:
            self.logger.warning("Failed to find the latest non-ad and non-pinned tweet")
            return

        tweet_link = self.browser.get_tweet_link(tweet_element)
        tweet_author = self.browser.get_tweet_author(tweet_element)
        if not (tweet_link and tweet_author):
            self.logger.warning(f"Failed to get tweet link for {tweet_author}")
            return
        
        self.like_tweet(tweet_element, tweet_author)
        if profile['reply']:
            self.reply_to_tweet(tweet_element, tweet_author)

        self.db_manager.save_tweet(tweet_link, tweet_author)
        self.logger.info(f"Saved tweet link: {tweet_link} by author: {tweet_author}")

    @rest
    def open_profile(self, profile):
        """
        Opens the X profile of the person passed in.
        Returns True if the profile is opened, False otherwise.
        """
        try:
            # Ensure the URL is complete
            url = profile['link']
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            # Open the X profile
            self.browser.driver.get(url)
            self.logger.info(f"Opened profile: {url}")
            return True
        except Exception as e:
            self.logger.exception(f"Failed to open profile. Error: {str(e)}")
            return False

    def like_tweet(self, tweet_element, tweet_author):
        if self.browser.like_tweet(tweet_element):
            self.logger.info(f"Liked the tweet by {tweet_author} successfully")
            return True
        else:
            self.logger.warning(f"Failed to like the tweet by {tweet_author}")
            return False

    def reply_to_tweet(self, tweet_element, tweet_author):
        try:
            self.logger.info(f"Replying to the tweet by {tweet_author}")
            self.send_reply(tweet_element, tweet_author)
        except Exception as e:
            self.logger.exception(f"Error replying to tweet by {tweet_author}")

    def send_reply(self, tweet_element, tweet_author):
        if self.browser.click_reply_button(tweet_element):
            if self.browser.type_reply(self.content) and self.browser.send_reply():
                self.logger.info(f"Replied to the tweet by {tweet_author} successfully")
            else:
                self.logger.warning(f"Failed to send reply to {tweet_author}")
        else:
            self.logger.warning(f"Failed to open reply dialog for {tweet_author}")

    def run(self):
        '''It initializes the environment, gets the following list, and then opens each profile in the following and added people lists, interacts with the tweet of each profile, and saves it to the database.'''
        self.logger.info("Initializing environment for the bot")
        if not self.initialize_environment():
            return  # Exit the method if initialization fails

        self.is_running = True
        self.logger.info("Getting following list")
        self.get_following() # Call this to get any new profiles that the user might have followed
        following_list = self.db_manager.get_following_list()
        self.logger.info("Starting main loop")
        while self.is_running:
            for profile in self.browser.added_people + following_list:
                if not self.is_running:
                    break
                try:
                    self.open_profile(profile)
                    self.interact_with_tweet(profile)
                except Exception as e:
                    error_message = f"An error occurred while processing a profile: {str(e)}"
                    self.gui_callback(error_message)
                    self.logger.exception("Error in main loop")
                    sleep(self.retry_delay)
            
            if not self.is_running:
                break
        self.logger.info("Main loop finished")

    def delete_replies(self):
        """Invokes the delete_all_replies function"""
        success = delete_all_replies(self.browser.driver, self.logger, self.username)
        if success:
            self.gui_callback("All replies deleted successfully.")
        else:
            self.gui_callback("Failed to delete all replies.")

    def delete_likes(self):
        """Invokes the delete_all_likes function"""
        delete_all_likes(self.browser.driver, self.logger, self.username)
        self.gui_callback("Attempt to delete all likes completed.")

    def stop_bot(self):
        self.logger.info("Stopping bot")
        self.is_running = False
        if hasattr(self, 'browser'):
            self.browser.close_browser()

