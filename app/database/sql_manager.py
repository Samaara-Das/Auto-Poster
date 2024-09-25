import sqlite3

db_path = 'app/database/user_data.db'

def setup_database():
    '''This function sets up a sqlite database with hardcoded user information to start the Auto Poster app. This is meant to be run only once to initialize the user_data.db file. This automatically fills up the user credentials in the GUI to save time.'''
    conn = sqlite3.connect(db_path)
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

def get_user_data():
    '''
    This function fetches the user data from the database.
    It returns a dictionary with the username, email, password and tweet_text.
    '''
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch user data from the database, including tweet_text
    cursor.execute("SELECT username, email, password, tweet_text FROM user_data LIMIT 1")
    user_data = cursor.fetchone()
    conn.close()
    return {'username': user_data[0], 'email': user_data[1], 'password': user_data[2], 'tweet_text': user_data[3]}
