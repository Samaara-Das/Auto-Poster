import sqlite3

def setup_database():
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

if __name__ == '__main__':
    setup_database()
    print("Database setup complete.")