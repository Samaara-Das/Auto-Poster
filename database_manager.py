from os import getenv
from dotenv import load_dotenv
from urllib.parse import urlparse
from datetime import datetime
from pymongo.mongo_client import MongoClient
from logger import logger

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        pwd = getenv('MONGO_PWD')
        connection_string = f"mongodb+srv://sammy:{pwd}@cluster1.565lfln.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
        self.client = MongoClient(connection_string)
        self.db = self.client['auto_poster']
        self.tweets_collection = self.db['tweets']
        self.following_collection = self.db['following']
        self.added_collection = self.db['added']
        self.logger = logger('database_manager')

    def delete_docs_in_collection(self, collection_name):
        '''This deletes all the documents in a collection'''
        try:
            self.db[collection_name].delete_many({})
            self.logger.info(f"Successfully deleted all documents in {collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to delete documents in {collection_name}. Error: {str(e)}")

    def save_tweet(self, tweet_link, username):
        parsed_url = urlparse(tweet_link)
        tweet_id = parsed_url.path.split('/')[-1]
        
        tweet_data = {
            'tweet_id': tweet_id,
            'tweet_link': tweet_link,
            'username': username,
            'timestamp': datetime.now()
        }
        
        result = self.tweets_collection.update_one(
            {'tweet_id': tweet_id},
            {'$set': tweet_data},
            upsert=True
        )
        
        if result.upserted_id:
            self.logger.info(f"Inserted new tweet: {tweet_id}")
        else:
            self.logger.info(f"Updated existing tweet: {tweet_id}")

    def save_profile(self, data: dict):
        '''This saves an X profile to the following collection. If the profile already exists in the collection, the profile will be updated with the new data'''
        try:
            username = data.get('username')
            result = self.following_collection.update_one(
                {'username': username},
                {'$set': data},
                upsert=True
            )
            if result.upserted_id:
                self.logger.info(f"Successfully saved new profile for: {username}")
            else:
                self.logger.info(f"Updated existing profile for: {username}")
        except Exception as e:
            self.logger.error(f"Failed to save profile. Error: {str(e)}")

    def is_profile_in_following(self, link: str):
        '''This checks if a profile is in the following collection in MongoDB'''
        try:
            existing_profile = self.following_collection.find_one({'link': link})
            if existing_profile is None:
                return False
            else:
                return True
        except Exception as e:
            self.logger.error(f"Failed to check if profile is in collection. Error: {str(e)}")

    def get_following_list(self):
        '''
        This method retrieves a list of all profiles from the 'following' collection in MongoDB.
        
        It performs the following actions:
        1. Queries the 'following' collection in MongoDB.
        2. Returns this list of profiles.

        If an exception occurs during this process:
        - The error is logged.
        - An empty list is returned.

        Returns:
        - A list of dictionaries, where each dictionary represents a profile.
        - An empty list if an error occurs.
        '''
        try:
            following_list = list(self.following_collection.find({}))
            return following_list
        except Exception as e:
            self.logger.error(f"Failed to get following list. Error: {str(e)}")
            return []

    def save_added_profile(self, data: dict):
        '''Saves a profile to the added collection.'''
        try:
            self.added_collection.update_one(
                {'link': data['link']},
                {'$set': data},
                upsert=True
            )
            self.logger.info(f"Added profile: {data['username']}")
        except Exception as e:
            self.logger.error(f"Failed to save added profile. Error: {str(e)}")

    def get_added_list(self):
        '''
        This method retrieves a list of all profiles from the 'added' collection in MongoDB.
        
        It performs the following actions:
        1. Queries the 'added' collection in MongoDB.
        2. Returns this list of profiles.

        If an exception occurs during this process:
        - The error is logged.
        - An empty list is returned.

        Returns:
        - A list of dictionaries, where each dictionary represents a profile.
        - An empty list if an error occurs.
        '''
        try:
            added_profiles = list(self.added_collection.find({}))
            self.logger.info(f"Retrieved {len(added_profiles)} added profiles")
            return added_profiles
        except Exception as e:
            self.logger.error(f"Failed to retrieve added profiles. Error: {str(e)}")
            return []

    def update_added_profile(self, link: str, reply: bool):
        '''Updates the reply field of a profile in the added collection.'''
        try:
            self.added_collection.update_one(
                {'link': link},
                {'$set': {'reply': reply}}
            )
            self.logger.info(f"Updated reply status for profile: {link} to {reply}")
        except Exception as e:
            self.logger.error(f"Failed to update added profile. Error: {str(e)}")

    def delete_added_profile(self, link: str) -> bool:
        '''
        Deletes a profile from the added collection based on the link.
        Returns True if deletion was successful, False otherwise.
        '''
        try:
            result = self.added_collection.delete_one({'link': link})
            if result.deleted_count > 0:
                self.logger.info(f"Successfully deleted profile with link: {link}")
                return True
            else:
                self.logger.warning(f"No profile found with link: {link}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete added profile. Error: {str(e)}")
            return False

