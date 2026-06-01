import re
import json
import zipfile
import os
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.db import get_db

def validate_required_fields(data, fields):
    """Validate that required fields are present and not empty."""
    for field in fields:
        if field not in data or not data[field].strip():
            return False, f"{field} is required"
    return True, None

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_image_url(url):
    """Basic validation for image URL."""
    if not url:
        return True  # Optional field
    pattern = r'^https?://.*\.(jpg|jpeg|png|gif|webp)$'
    return re.match(pattern, url, re.IGNORECASE) is not None

def calculate_interest_match(user1_id, user2_id):
    """Calculate interest match percentage between two users based on mutual followers/following and interests."""
    db = get_db()
    cursor = db.cursor()

    total_score = 0
    max_score = 0

    # 1. Calculate mutual followers (people who follow both users)
    cursor.execute('''
        SELECT COUNT(*) as mutual_followers
        FROM follows f1
        INNER JOIN follows f2 ON f1.follower_id = f2.follower_id
        WHERE f1.following_id = ? AND f2.following_id = ?
    ''', (user1_id, user2_id))
    mutual_followers = cursor.fetchone()['mutual_followers']
    
    # Get total followers for both users to calculate weight
    cursor.execute('SELECT COUNT(*) as count FROM follows WHERE following_id = ?', (user1_id,))
    user1_followers = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM follows WHERE following_id = ?', (user2_id,))
    user2_followers = cursor.fetchone()['count']
    
    max_followers = max(user1_followers, user2_followers)
    if max_followers > 0:
        total_score += (mutual_followers / max_followers) * 40  # 40% weight for mutual followers
        max_score += 40

    # 2. Calculate mutual following (people both users follow)
    cursor.execute('''
        SELECT COUNT(*) as mutual_following
        FROM follows f1
        INNER JOIN follows f2 ON f1.following_id = f2.following_id
        WHERE f1.follower_id = ? AND f2.follower_id = ?
    ''', (user1_id, user2_id))
    mutual_following = cursor.fetchone()['mutual_following']
    
    # Get total following for both users
    cursor.execute('SELECT COUNT(*) as count FROM follows WHERE follower_id = ?', (user1_id,))
    user1_following = cursor.fetchone()['count']
    cursor.execute('SELECT COUNT(*) as count FROM follows WHERE follower_id = ?', (user2_id,))
    user2_following = cursor.fetchone()['count']
    
    max_following = max(user1_following, user2_following)
    if max_following > 0:
        total_score += (mutual_following / max_following) * 40  # 40% weight for mutual following
        max_score += 40

    # 3. Compare interests (20% weight total)
    cursor.execute('SELECT * FROM user_interests WHERE user_id = ?', (user1_id,))
    user1_interests = cursor.fetchone()
    cursor.execute('SELECT * FROM user_interests WHERE user_id = ?', (user2_id,))
    user2_interests = cursor.fetchone()

    if user1_interests and user2_interests:
        interest_matches = 0
        interest_possible = 0

        # Compare hashtags
        if user1_interests['hashtags'] and user2_interests['hashtags']:
            try:
                h1 = set(json.loads(user1_interests['hashtags']))
                h2 = set(json.loads(user2_interests['hashtags']))
                interest_matches += len(h1.intersection(h2))
                interest_possible += max(len(h1), len(h2))
            except (json.JSONDecodeError, TypeError):
                pass

        # Compare music
        if user1_interests['music_liked'] and user2_interests['music_liked']:
            try:
                m1 = set(json.loads(user1_interests['music_liked']))
                m2 = set(json.loads(user2_interests['music_liked']))
                interest_matches += len(m1.intersection(m2))
                interest_possible += max(len(m1), len(m2))
            except (json.JSONDecodeError, TypeError):
                pass

        # Compare celebrities
        if user1_interests['celebrities_followed'] and user2_interests['celebrities_followed']:
            try:
                c1 = set(json.loads(user1_interests['celebrities_followed']))
                c2 = set(json.loads(user2_interests['celebrities_followed']))
                interest_matches += len(c1.intersection(c2))
                interest_possible += max(len(c1), len(c2))
            except (json.JSONDecodeError, TypeError):
                pass

        if interest_possible > 0:
            total_score += (interest_matches / interest_possible) * 20  # 20% weight for interests
            max_score += 20

    # Calculate final percentage
    if max_score > 0:
        return int((total_score / max_score) * 100)
    else:
        # If no data available, return a small random match based on existence
        return 10

def process_zip_file(zip_path, user_id):
    """Extract and parse Instagram activity log data from zip file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract to temp directory
            extract_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f'temp_{user_id}')
            os.makedirs(extract_path, exist_ok=True)
            zip_ref.extractall(extract_path)

            # Parse JSON files (assuming specific structure)
            data = {}
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    if file.endswith('.json'):
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            try:
                                file_data = json.load(f)
                                data.update(file_data)
                            except json.JSONDecodeError:
                                continue

            # Process the data
            interests = {
                'hashtags': [],
                'music_liked': [],
                'trends_followed': [],
                'celebrities_followed': [],
                'posts_liked_count': 0,
                'reels_watched_count': 0,
                'comments_made_count': 0
            }

            if 'likes' in data:
                interests['posts_liked_count'] = len(data['likes'])

            if 'comments' in data:
                interests['comments_made_count'] = len(data['comments'])

            if 'hashtags_used' in data:
                # Strip # prefixes from hashtags to store them consistently
                interests['hashtags'] = [tag.lstrip('#') for tag in data['hashtags_used']]

            if 'music_liked' in data:
                interests['music_liked'] = data['music_liked']

            if 'accounts_followed' in data:
                interests['celebrities_followed'] = data['accounts_followed']

            # Save to database
            db = get_db()
            cursor = db.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO user_interests
                (user_id, hashtags, music_liked, trends_followed, celebrities_followed,
                 posts_liked_count, reels_watched_count, comments_made_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                json.dumps(interests['hashtags']),
                json.dumps(interests['music_liked']),
                json.dumps(interests['trends_followed']),
                json.dumps(interests['celebrities_followed']),
                interests['posts_liked_count'],
                interests['reels_watched_count'],
                interests['comments_made_count']
            ))

            # Update user's profile hashtags to match activity log data
            if interests['hashtags']:
                # Convert hashtag list to comma-separated string for profile_hashtags field
                profile_hashtags_str = ', '.join(interests['hashtags'])
                cursor.execute(
                    'UPDATE users SET profile_hashtags = ? WHERE id = ?',
                    (profile_hashtags_str, user_id)
                )

            # Update global trends
            update_global_trends(interests)

            db.commit()

            # Clean up temp files
            import shutil
            shutil.rmtree(extract_path)

            return True, "Activity logs processed successfully"

    except Exception as e:
        return False, f"Error processing zip file: {str(e)}"

def update_global_trends(interests):
    """Update global trends table with new data."""
    db = get_db()
    cursor = db.cursor()

    # Update hashtags
    for hashtag in interests['hashtags']:
        cursor.execute('''
            INSERT INTO global_trends (trend_type, name, count)
            VALUES ('hashtag', ?, 1)
            ON CONFLICT(trend_type, name) DO UPDATE SET
            count = count + 1,
            last_updated = CURRENT_TIMESTAMP
        ''', ('#' + hashtag,))

    # Update music
    for music in interests['music_liked']:
        cursor.execute('''
            INSERT INTO global_trends (trend_type, name, count)
            VALUES ('music', ?, 1)
            ON CONFLICT(trend_type, name) DO UPDATE SET
            count = count + 1,
            last_updated = CURRENT_TIMESTAMP
        ''', (music,))

    # Update celebrities
    for celeb in interests['celebrities_followed']:
        cursor.execute('''
            INSERT INTO global_trends (trend_type, name, count)
            VALUES ('creator', ?, 1)
            ON CONFLICT(trend_type, name) DO UPDATE SET
            count = count + 1,
            last_updated = CURRENT_TIMESTAMP
        ''', (celeb,))

    db.commit()

def hash_password(password):
    """Hash a password."""
    return generate_password_hash(password)

def check_password(password_hash, password):
    """Check a password against its hash."""
    return check_password_hash(password_hash, password)
