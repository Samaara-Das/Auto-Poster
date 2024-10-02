from datetime import datetime, timedelta
from app.logger.logger import logger, DEBUG
from selenium.webdriver.common.window import WindowTypes
from app.configuration.configuration import Config

from apscheduler.schedulers.background import BackgroundScheduler
import threading
import time

sec_multiplier = 60

class AutoFollow:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger(__name__, DEBUG)
        self.window_handle = None  # To store the new window handle
        self.scheduler = BackgroundScheduler()
        self.scheduler_lock = threading.Lock()
        self.is_running = False
        self.follows_done = 0  # Counter for follows done in the current cycle
        self.time_span = None  # New attribute to store the time span

    def create_new_window(self):
        """Creates a new window to run the auto follow process"""
        try:
            driver = self.bot.browser.driver
            new_window = driver.switch_to.new_window(WindowTypes.WINDOW)
            self.window_handle = new_window
            self.logger.info("Opened and switched to a new window.")

        except Exception as e:
            self.logger.exception(f"Failed to create a new window: {e}")

    def sign_in(self):
        """Signs in to X if user is logged out."""
        self.bot.browser.sign_in(self.bot.username, self.bot.password, self.bot.email)

    def open_connect_page(self):
        """Opens the connect page."""
        try:
            self.bot.browser.driver.get('https://x.com/i/connect_people')
            self.logger.info("Opened the connect page.")
        except Exception as e:
            self.logger.exception(f"Failed to open the connect page: {e}")

    def calculate_rest_time(self, total_follow_count, follow_at_once):
        """
        Calculates the rest time between each auto-follow batch in seconds, accounting for the duration of a single auto-follow batch.

        Args:
            total_follow_count (int): Total number of follows to perform.
            follow_at_once (int): Number of follows to perform in each batch.

        Returns:
            float: The calculated rest time in seconds between each auto-follow batch.

        Note:
            If the calculation results in a rest time that is too short to account for the batch duration, it logs an error and raises a ValueError.
        """
        time_span_seconds = self.time_span * sec_multiplier  # Convert minutes to seconds
        total_batches = total_follow_count / follow_at_once
        if total_batches == 0:
            self.logger.error("Total batches calculated as 0. Check follow_at_once and total_follow_count values.")
            raise ValueError(f"Total batches calculated as 0. follow_at_once: {follow_at_once}, total_follow_count: {total_follow_count}")
        
        # Assume each follow batch takes 1.5 * follow_at_once seconds
        process_duration = Config.FOLLOW_DURATION * follow_at_once  
        self.logger.debug(f"Assumed process duration per batch: {process_duration} seconds.")

        # Calculate raw rest_time without accounting for process duration
        raw_rest_time = time_span_seconds / total_batches
        self.logger.debug(f"Raw rest_time (without process duration): {raw_rest_time} seconds.")

        # Adjust rest_time by subtracting process duration to ensure batches do not overlap
        adjusted_rest_time = raw_rest_time - process_duration
        self.logger.debug(f"Adjusted rest_time (accounting for process duration): {adjusted_rest_time} seconds.")

        # Ensure the adjusted rest_time meets the minimum requirement
        # MIN_REST_TIME = 60  # Minimum 60 seconds between batches
        # if adjusted_rest_time < MIN_REST_TIME:
        #     self.logger.error(
        #         f"Calculated rest_time {adjusted_rest_time} seconds is too short after accounting for process duration."
        #     )
        #     raise ValueError(
        #         "rest_time between follow batches is too short after accounting for process duration. "
        #         "Please reduce 'Follow at once' or increase the time span."
        #     )
        
        self.logger.debug(f"Final calculated rest_time: {adjusted_rest_time} seconds between each batch.")
        return adjusted_rest_time

    def schedule_auto_follow_process(self, total_follow_count, keywords, follow_at_once):
        """
        Starts the auto follow process.
        
        Follows `follow_at_once` users at intervals within the `self.time_span` time span
        to reach a total of `total_follow_count` follows within the time span. The process continues indefinitely.
        """
        try:
            with self.scheduler_lock:
                if self.is_running:
                    self.logger.warning("Auto follow process is already running.")
                    return

                self.is_running = True
                self.follows_done = 0

                # calculate the rest time between auto-follow batches
                rest_time = self.calculate_rest_time(total_follow_count, follow_at_once)

                # this outer loop starts a new time span (eg: 24 hours)
                while self.is_running:
                    self.logger.info(f"Starting new time span at {datetime.now()}")
                    time_span_start_time = datetime.now()
                    time_span_end_time = time_span_start_time + timedelta(minutes=self.time_span)
                    
                    # this inner loop is responsible for executing auto-follow batches within the current time span
                    while datetime.now() <= time_span_end_time:
                        self.follow_batch(follow_at_once, keywords, total_follow_count)
                        
                        if self.follows_done >= total_follow_count:
                            self.logger.info(f"Reached the total follow count of {total_follow_count} for this time span.")
                            break
                        
                        time.sleep(rest_time)
                    
                    # wait for the next time span to start
                    time_to_next_span = (time_span_end_time - datetime.now()).total_seconds()
                    if time_to_next_span > 0:
                        time.sleep(time_to_next_span)
                    
                    # reset for the next time span
                    self.follows_done = 0

        except Exception as e:
            self.logger.exception(f"Error in auto follow process: {e}")
            self.is_running = False

    def follow_batch(self, follow_at_once, keywords, total_follow_count):
        """
        Follows a batch of users based on the given keywords and `follow_at_once` value.
        
        Args:
            follow_at_once (int): Number of users to follow in this batch.
            keywords (list): List of keywords to filter users.
            total_follow_count (int): Total number of users to follow per time span.
        """
        try:
            self.logger.info(f"Starting follow batch of {follow_at_once} users.")

            # open the connect page
            self.open_connect_page()

            # follow people
            followed_profiles = self.bot.browser.auto_follow(keywords, follow_at_once, total_follow_count, self.follows_done)
            self.follows_done += followed_profiles
            self.logger.info(f"Followed {followed_profiles} users. Total followed in this time span: {self.follows_done}/{total_follow_count}")
            return followed_profiles

        except Exception as e:
            self.logger.exception(f"Error during follow batch: {e}")
            return 0
        
    def reset_follows_done(self):
        """
        Resets the follows_done counter after each time span.
        """
        with self.scheduler_lock:
            self.follows_done = 0
            self.logger.info("Follows done counter has been reset for the next time span.")

    def stop_auto_following(self):
        """Stops the auto follow process."""
        with self.scheduler_lock:
            if not self.is_running:
                self.logger.warning("Auto follow process is not running.")
                return

            try:
                self.scheduler.remove_job('auto_follow_job')
                self.scheduler.remove_job('reset_follow_counter_job')
                self.logger.info("Scheduled jobs removed.")
            except Exception as e:
                self.logger.warning(f"Error removing scheduled jobs: {e}")

            self.scheduler.shutdown(wait=False)
            self.is_running = False
            self.follows_done = 0  # Reset counter when stopping
            self.logger.info("Auto follow process stopped.")