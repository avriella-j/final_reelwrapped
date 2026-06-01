import sqlite3
from flask import g, current_app
import json
from datetime import datetime
import time

def get_db():
    if 'db' not in g:
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        # Add timeout and isolation level for better concurrency
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=30.0,  # 30 second timeout
            isolation_level=None  # Enable autocommit mode
        )
        g.db.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA synchronous=NORMAL')
        g.db.execute('PRAGMA cache_size=1000')
        g.db.execute('PRAGMA temp_store=memory')
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Create Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                profile_image_url TEXT,
                bio TEXT,
                profile_hashtags TEXT
            )
        ''')

        # Create ActivityLogs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                zip_filename TEXT NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Create UserInterests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                hashtags TEXT,  -- JSON array
                music_liked TEXT,  -- JSON array
                trends_followed TEXT,  -- JSON array
                celebrities_followed TEXT,  -- JSON array
                posts_liked_count INTEGER DEFAULT 0,
                reels_watched_count INTEGER DEFAULT 0,
                comments_made_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Create GlobalTrends table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trend_type TEXT NOT NULL,  -- hashtag/music/creator/topic
                name TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(trend_type, name)
            )
        ''')

        # Create Follows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL,
                following_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (follower_id) REFERENCES users (id),
                FOREIGN KEY (following_id) REFERENCES users (id),
                UNIQUE(follower_id, following_id)
            )
        ''')

        # Create HashtagFollows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hashtag_follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                hashtag_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, hashtag_name)
            )
        ''')

        # Create MusicFollows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, song_name)
            )
        ''')

        db.commit()

        # Seed sample users
        seed_sample_users(cursor)
        db.commit()

def seed_sample_users(cursor):
    sample_users = [
        ('alex_johnson', 'alex@example.com', 'hashedpass1', None),
        ('sarah_smith', 'sarah@example.com', 'hashedpass2', None),
        ('mike_davis', 'mike@example.com', 'hashedpass3', None),
        ('emma_wilson', 'emma@example.com', 'hashedpass4', None),
        ('chris_brown', 'chris@example.com', 'hashedpass5', None),
        ('lisa_garcia', 'lisa@example.com', 'hashedpass6', None),
        ('david_miller', 'david@example.com', 'hashedpass7', None),
        ('anna_taylor', 'anna@example.com', 'hashedpass8', None),
        ('james_anderson', 'james@example.com', 'hashedpass9', None),
        ('olivia_martinez', 'olivia@example.com', 'hashedpass10', None),
        ('ryan_thomas', 'ryan@example.com', 'hashedpass11', None),
        ('sophia_lopez', 'sophia@example.com', 'hashedpass12', None),
        ('noah_garcia', 'noah@example.com', 'hashedpass13', None),
        ('mia_rodriguez', 'mia@example.com', 'hashedpass14', None),
        ('ethan_lee', 'ethan@example.com', 'hashedpass15', None),
    ]

    for username, email, password_hash, profile_image_url in sample_users:
        try:
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, profile_image_url) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, profile_image_url)
            )
        except sqlite3.IntegrityError:
            pass  # User already exists

    # Seed some sample interests and trends
    sample_interests = [
        (1, '["#travel", "#foodie", "#photography"]', '["Song A - Artist B", "Song C - Artist D"]', '["#summer2024", "#beachvibes"]', '["@creator1", "@influencer2"]', 50, 30, 20),
        (2, '["#fitness", "#gym", "#health"]', '["Song E - Artist F", "Song G - Artist H"]', '["#workout", "#motivation"]', '["@fitnessguru", "@healthcoach"]', 40, 25, 15),
        (3, '["#art", "#design", "#creative"]', '["Song I - Artist J", "Song K - Artist L"]', '["#digitalart", "#inspiration"]', '["@artist1", "@designer2"]', 60, 35, 25),
        (4, '["#music", "#concert", "#live"]', '["Song M - Artist N", "Song O - Artist P"]', '["#livemusic", "#festival"]', '["@musician1", "@band2"]', 70, 40, 30),
        (5, '["#tech", "#coding", "#innovation"]', '["Song Q - Artist R", "Song S - Artist T"]', '["#ai", "#startup"]', '["@techinfluencer", "@coder1"]', 45, 20, 10),
    ]

    for user_id, hashtags, music, trends, celebs, likes, reels, comments in sample_interests:
        cursor.execute(
            'INSERT OR REPLACE INTO user_interests (user_id, hashtags, music_liked, trends_followed, celebrities_followed, posts_liked_count, reels_watched_count, comments_made_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, hashtags, music, trends, celebs, likes, reels, comments)
        )

    # Seed global trends
    sample_trends = [
        ('hashtag', '#travel', 100),
        ('hashtag', '#foodie', 80),
        ('hashtag', '#fitness', 90),
        ('music', 'Song A - Artist B', 50),
        ('creator', '@creator1', 60),
        ('topic', '#summer2024', 70),
    ]

    for trend_type, name, count in sample_trends:
        cursor.execute(
            'INSERT OR REPLACE INTO global_trends (trend_type, name, count) VALUES (?, ?, ?)',
            (trend_type, name, count)
        )
