'''
These functions are utility functions which can be used.
'''
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep
import sqlite3

def delete_all_replies(driver, logger, username: str):
    """
    Deletes all replies made by the user. (Not functional)
    
    :param driver: The Selenium WebDriver instance
    :param logger: The logger instance
    :param username: The username of the account whose replies should be deleted
    :return: True if the operation was successful, False otherwise
    """
    try:
        # Navigate to the user's profile
        driver.get(f'https://x.com/{username}')
        logger.info(f"Navigated to {username}'s profile")

        # Click on the "Replies" tab
        replies_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@role="tab"]//span[text()="Replies"]'))
        )
        replies_tab.click()
        logger.info("Clicked on the Replies tab")

        deleted_count = 0
        while True:
            try:
                # Find the user's reply
                reply = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f'//article[@data-testid="tweet"]//div[@data-testid="User-Name"]//a[contains(@href, "/{username}")]//ancestor::article[@data-testid="tweet"]'))
                )
                logger.info(f"Found reply")

                # Click on the menu button (three dots)
                menu_button = reply.find_element(By.XPATH, '//button[@aria-label="More"]')
                menu_button.click()
                logger.info("Clicked on the menu button")

                # Click on the "Delete" option
                delete_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@role="menuitem"]//span[text()="Delete"]'))
                )
                delete_option.click()
                logger.info("Clicked on the delete option")

                # Confirm deletion
                confirm_delete = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="confirmationSheetConfirm"]'))
                )
                confirm_delete.click()
                logger.info("Clicked on the confirm delete button")

                deleted_count += 1
                logger.info(f"Deleted reply {deleted_count}")

                # Wait for the deletion to complete
                sleep(2)

            except TimeoutException:
                # No more replies found
                break

        logger.info(f"Finished deleting replies. Total deleted: {deleted_count}")
        return True

    except Exception as e:
        logger.exception(f"An error occurred while deleting replies: {str(e)}")
        return False

def delete_all_likes(driver, logger, username):
    """
    Attempts to delete all likes for a given user. (Not functional)

    NOTE: This function currently works incorrectly. Only the first tweet gets unliked and not the rest.

    :param driver: The Selenium WebDriver instance
    :param logger: The logger instance
    :param username: The username of the account whose likes should be deleted
    """
    try:
        # Navigate to the user's profile
        driver.get(f"https://x.com/{username}")
        logger.info(f"Navigated to {username}'s profile")

        # Wait for and click on the Likes tab
        likes_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@href="/' + username + '/likes"]'))
        )
        likes_tab.click()
        logger.info("Clicked on the Likes tab")

        # Initialize counter
        unliked_count = 0

        while True:
            try:
                # Find the first liked tweet
                tweet = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, '//article[@data-testid="tweet"]'))
                )

                # Scroll the tweet into view
                driver.execute_script("arguments[0].scrollIntoView(true);", tweet)
                sleep(1)  # Short pause to allow the page to settle

                # Find and click the unlike button
                unlike_button = WebDriverWait(tweet, 5).until(
                    EC.element_to_be_clickable((By.XPATH, './/button[@data-testid="unlike"]'))
                )
                unlike_button.click()
                unliked_count += 1
                logger.info(f"Unliked tweet {unliked_count}")

                # Short pause to allow the unlike action to complete
                sleep(0.5)

            except TimeoutException:
                logger.info("No more liked tweets found. Exiting.")
                break

        logger.info(f"Unliking process completed. Total unliked: {unliked_count}")

    except Exception as e:
        logger.exception(f"An error occurred while unliking tweets: {str(e)}")

def setup_database():
    '''This function sets up a sqlite database with hardcoded user information to start the Auto Poster app. This is meant to be run only once to initialize the user_data.db file. This automatically fills up the user credentials in the GUI to save time.'''
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()


    # Create the user_data table with the new tweet_text field
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_data (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        tweet_text TEXT NOT NULL
    )
    ''')

    # Insert hardcoded data including the tweet text
    cursor.execute('''
    INSERT OR REPLACE INTO user_data (id, username, email, password, tweet_text)
    VALUES (1, 'fakerfaker680', 'fakerfaker680@gmail.com', '1304Sammy#', 'cool')
    ''')

    conn.commit()
    conn.close()

    print("Database setup complete.")

