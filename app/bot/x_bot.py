from app.bot.x_controller import XController, VerificationRequiredException
from time import sleep
import app.bot.delete_interactions as delete_interactions
import app.decorators.decorators as decorators
from app.logger.logger import logger
import threading

# These are high level methods that interact with XController methods.
class XBot:
    def __init__(self):
        self.browser = XController()
        self.get_following_lock = threading.Lock()
        self.retry_delay = 5
        self.username = ''
        self.password = ''
        self.email = ''
        self.content = ''
        self.is_running = False
        self.logger = logger(__name__)
        self.stop_event = threading.Event()  # Initialize the stop event

    def is_credentials_valid(self):
        '''This method checks if the email, username and password are valid'''
        self.logger.info("Checking if credentials are valid")
        if not self.username or not self.password or not self.email:
            self.logger.warning(f"Invalid credentials provided. username: {self.username}, password: {self.password}, email: {self.email}")
            return False
        self.logger.info("Credentials are valid")
        return True

    def sign_in(self):
        '''This method signs in to X and goes to the following page of the specified user. It also updates the GUI with a list of the people that the user is following and displays error messages if any occur'''
        try:
            self.browser.sign_in(self.username, self.password, self.email)
        except VerificationRequiredException as ve:
            error_message = str(ve)
            self.logger.error(error_message)
            return False
        except Exception as e:
            error_message = f"An error occurred during initialization: {str(e)}"
            self.logger.error(error_message)
            return False
        return True

    def get_following(self):
        '''This method opens the user's following page, gets the list of people that the user is following and displays it on the GUI'''
        with self.get_following_lock:
            self.browser.go_to_following(self.username)
            self.browser.get_following()

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

        self.browser.db_manager.save_tweet(tweet_link, tweet_author)
        self.logger.info(f"Saved tweet link: {tweet_link} by author: {tweet_author}")

    @decorators.rest
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
            self.browser.open_page(url)
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
            if self.browser.click_reply_button(tweet_element):
                if self.browser.type_reply(self.content) and self.browser.send_reply():
                    self.logger.info(f"Replied to the tweet by {tweet_author} successfully")
                else:
                    self.logger.warning(f"Failed to send reply to {tweet_author}")
        except Exception as e:
            self.logger.exception(f"Error sending reply to tweet by {tweet_author}")

    def run(self):
        '''It initializes the environment, gets the following list, and then opens each profile in the following and added people lists, interacts with the tweet of each profile, and saves it to the database.'''
        self.logger.info("Initializing environment for the bot")
        if not self.sign_in():
            return
        self.get_following()

        self.is_running = True
        self.logger.info("Starting main loop")
        profiles = self.browser.added_people + self.browser.following
        while self.is_running:
            for profile in profiles:
                if not self.is_running:
                    break
                try:
                    self.open_profile(profile)
                    self.interact_with_tweet(profile)
                except Exception as e:
                    error_message = f"An error occurred while processing a profile: {str(e)}"
                    self.logger.exception(f"Error in main loop: {error_message}")
                    sleep(self.retry_delay)
            
            if not self.is_running:
                break
        self.logger.info("Main loop finished")

    def delete_replies(self):
        """Deletes all replies from the user's X account"""
        success = delete_interactions.delete_all_replies(self.browser.driver, self.logger, self.username)
        if success:
            self.logger.info("All replies deleted successfully.")
        else:
            self.logger.error("Failed to delete all replies.")

    def delete_likes(self):
        """Deletes all likes from the user's X account"""
        success = delete_interactions.delete_all_likes(self.browser.driver, self.logger, self.username)
        if success:
            self.logger.info("All likes deleted successfully.")
        else:
            self.logger.error("Failed to delete all likes.")

    def stop_bot(self):
        self.logger.info("Stopping bot")
        self.is_running = False
        self.browser.set_stop_get_following(True)
        self.logger.info("Bot finished running.")


