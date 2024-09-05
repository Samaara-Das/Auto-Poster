from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from time import sleep

def delete_all_replies(driver, logger, username: str):
    """
    Deletes all replies made by the user.
    
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

                # Click on the menu button (three dots)
                menu_button = reply.find_element(By.XPATH, './/button[@aria-label="More"]')
                menu_button.click()

                # Click on the "Delete" option
                delete_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[@role="menuitem"]//span[text()="Delete"]'))
                )
                delete_option.click()

                # Confirm deletion
                confirm_delete = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="confirmationSheetConfirm"]'))
                )
                confirm_delete.click()

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

def delete_all_likes(driver, logger, username: str):
    """
    Deletes all likes made by the user.
    
    :param driver: The Selenium WebDriver instance
    :param logger: The logger instance
    :param username: The username of the account whose likes should be deleted
    :return: True if the operation was successful, False otherwise
    """
    try:
        # Navigate to the user's profile
        driver.get(f'https://x.com/{username}')
        logger.info(f"Navigated to {username}'s profile")

        # Click on the "Likes" tab
        likes_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@role="tab"]//span[text()="Likes"]'))
        )
        likes_tab.click()
        logger.info("Clicked on the Likes tab")

        unliked_count = 0
        while True:
            try:
                # Find the liked tweet
                liked_tweet = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//article[@data-testid="tweet"]'))
                )

                # Find and click the like button to unlike
                like_button = liked_tweet.find_element(By.XPATH, './/div[@data-testid="like"]')
                like_button.click()

                unliked_count += 1
                logger.info(f"Unliked tweet {unliked_count}")

                # Wait for the unlike action to complete
                sleep(1)

            except TimeoutException:
                # No more liked tweets found
                break

        logger.info(f"Finished unliking tweets. Total unliked: {unliked_count}")
        return True

    except Exception as e:
        logger.exception(f"An error occurred while unliking tweets: {str(e)}")
        return False
