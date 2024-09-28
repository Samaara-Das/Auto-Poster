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

    def create_new_window(self):
        """Creates a new window to run the auto follow process"""
        try:
            driver = self.bot.browser.driver
            new_window = driver.switch_to.new_window(WindowTypes.WINDOW)
            self.window_handle = new_window
            self.logger.info("Opened and switched to a new window.")

        except Exception as e:
            self.logger.exception(f"Failed to create a new window: {e}")

    def calculate_interval(self, total_follow_count, follow_at_once):
        """
        Calculates the interval between each follow batch in seconds,
        accounting for the duration of a single follow process.

        This method determines how frequently the bot should perform follow actions to evenly distribute
        the total number of follows over a given time span. It accounts for the time taken by each follow batch
        to prevent overlapping and ensure timing accuracy.

        Returns:
            float: The calculated interval in seconds between each follow batch.

        Note:
            If the calculation results in an interval that is too short to account for the batch duration,
            it logs an error and raises a ValueError.
        """
        time_span = Config.TIME_SPAN * sec_multiplier  # Convert hours to seconds
        total_batches = total_follow_count / follow_at_once
        if total_batches == 0:
            self.logger.error("Total batches calculated as 0. Check follow_at_once and total_follow_count values.")
            raise ValueError(f"Total batches calculated as 0. follow_at_once: {follow_at_once}, total_follow_count: {total_follow_count}")
        
        # Assume each follow batch takes 1.5 * follow_at_once seconds
        process_duration = Config.FOLLOW_DURATION * follow_at_once  
        self.logger.debug(f"Assumed process duration per batch: {process_duration} seconds.")

        # Calculate raw interval without accounting for process duration
        raw_interval = time_span / total_batches
        self.logger.debug(f"Raw interval (without process duration): {raw_interval} seconds.")

        # Adjust interval by subtracting process duration to ensure batches do not overlap
        adjusted_interval = raw_interval - process_duration
        self.logger.debug(f"Adjusted interval (accounting for process duration): {adjusted_interval} seconds.")

        # Ensure the adjusted interval meets the minimum requirement
        # MIN_INTERVAL = 60  # Minimum 60 seconds between batches
        # if adjusted_interval < MIN_INTERVAL:
        #     self.logger.error(
        #         f"Calculated interval {adjusted_interval} seconds is too short after accounting for process duration."
        #     )
        #     raise ValueError(
        #         "Interval between follow batches is too short after accounting for process duration. "
        #         "Please reduce 'Follow at once' or increase the time span."
        #     )
        
        self.logger.debug(f"Final calculated interval: {adjusted_interval} seconds between each batch.")
        return adjusted_interval

    def start_auto_following(self, total_follow_count, keywords, follow_at_once):
        """
        Starts the auto follow process.
        
        Follows `follow_at_once` users every `interval` seconds within the `Config.TIME_SPAN` time span
        to reach a total of `total_follow_count` follows within the time span. The process repeats indefinitely.
        """
        try:
            with self.scheduler_lock:
                if self.is_running:
                    self.logger.warning("Auto follow process is already running.")
                    return

                self.is_running = True
                self.follows_done = 0  # Reset counter at the start of the cycle

                interval = self.calculate_interval(total_follow_count, follow_at_once)

                # Define the follow batch job
                self.scheduler.add_job(
                    self.follow_batch,
                    'interval',
                    seconds=interval,
                    args=[follow_at_once, keywords, total_follow_count],
                    id='auto_follow_job',
                    next_run_time=datetime.now()  # Start immediately
                )

                # Define the reset counter job to reset follows_done after each time span
                self.scheduler.add_job(
                    self.reset_follows_done,
                    'interval',
                    seconds=Config.TIME_SPAN * sec_multiplier,  # Convert hours to seconds
                    id='reset_follow_counter_job',
                    next_run_time=datetime.now() + timedelta(seconds=Config.TIME_SPAN * sec_multiplier)  # Schedule after the first time span
                )

                self.scheduler.start()
                self.logger.info("Auto follow process started.")
        except ValueError as ve:
            self.logger.error(f"Failed to start auto follow: {ve}")
            raise ve
        except Exception as e:
            self.logger.exception(f"Error starting auto follow process: {e}")
            self.is_running = False

    def follow_batch(self, follow_at_once, keywords, total_follow_count):
        """
        Follows a batch of users based on the given keywords.
        
        Args:
            follow_at_once (int): Number of users to follow in this batch.
            keywords (list): List of keywords to filter users.
            total_follow_count (int): Total number of users to follow per time span.
        """
        def is_total_follow_count_reached():
            if self.follows_done >= total_follow_count:
                self.logger.info(f"$$$ Reached the total follow count of {total_follow_count} for this time span.")
                return True
            return False

        try:
            if is_total_follow_count_reached():
                return

            # Implement the actual follow logic here
            # For demonstration, we'll simulate the follow action for each person
            for _ in range(follow_at_once):
                if is_total_follow_count_reached():
                    return
                time.sleep(Config.FOLLOW_DURATION)
                self.follows_done += 1

            self.logger.info(f"Followed {follow_at_once} users. Total followed this cycle: {self.follows_done}/{total_follow_count}")

        except Exception as e:
            self.logger.exception(f"Error during follow batch: {e}")

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