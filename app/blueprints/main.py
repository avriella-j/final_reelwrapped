from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from app.utils.db import get_db
from app.utils.helpers import process_zip_file
import os
import json
import sqlite3

main_bp = Blueprint('main', __name__)

@main_bp.before_request
def require_login():
    allowed_routes = ['auth.login', 'auth.register', 'main.landing', 'main.about', 'main.support']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('auth.login'))

@main_bp.route('/')
def landing():
    return render_template('landing.html')

@main_bp.route('/home')
def home():
    db = get_db()
    cursor = db.cursor()

    # Get query parameters for sorting and filtering
    sort_by = request.args.get('sort', 'popular')
    filter_by = request.args.get('filter', 'all')

    # Determine sorting clause
    if sort_by == 'recent':
        order_clause = ' ORDER BY last_updated DESC'
    elif sort_by == 'alphabetical':
        order_clause = ' ORDER BY name ASC'
    else:  # popular (default)
        order_clause = ' ORDER BY count DESC'

    # Fetch trends by type separately to ensure we get all of each type
    hashtags = []
    music = []
    creators = []

    if filter_by == 'all' or filter_by == 'hashtag':
        cursor.execute(f"SELECT * FROM global_trends WHERE trend_type = 'hashtag'{order_clause}")
        hashtags = cursor.fetchall()

    if filter_by == 'all' or filter_by == 'music':
        cursor.execute(f"SELECT * FROM global_trends WHERE trend_type = 'music'{order_clause}")
        music = cursor.fetchall()

    if filter_by == 'all' or filter_by == 'creator':
        cursor.execute(f"SELECT * FROM global_trends WHERE trend_type = 'creator'{order_clause}")
        creators = cursor.fetchall()

    return render_template('home.html', hashtags=hashtags, music=music, creators=creators, sort_by=sort_by, filter_by=filter_by)

@main_bp.route('/foryou')
def foryou():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    # Check if user has uploaded activity logs
    cursor.execute('SELECT * FROM user_interests WHERE user_id = ?', (user_id,))
    user_interests = cursor.fetchone()

    if not user_interests:
        flash('Please upload your activity logs to see personalized recommendations.', 'info')
        return redirect(url_for('main.profile'))

    # Get personalized trends based on user's interests
    # For simplicity, we'll show global trends but could be filtered by user interests
    cursor.execute('SELECT * FROM global_trends ORDER BY count DESC LIMIT 20')
    trends = cursor.fetchall()

    hashtags = [t for t in trends if t['trend_type'] == 'hashtag']
    music = [t for t in trends if t['trend_type'] == 'music']
    creators = [t for t in trends if t['trend_type'] == 'creator']

    return render_template('foryou.html', hashtags=hashtags, music=music, creators=creators, user_interests=user_interests)

@main_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        # Check if it's profile edit or activity log upload
        if 'profile_image' in request.files or 'bio' in request.form:
            # Handle profile edit (bio and/or image)
            bio = request.form.get('bio', '').strip()
            profile_image = request.files.get('profile_image')

            # Update bio and hashtags
            hashtags = request.form.get('hashtags', '').strip()
            cursor.execute(
                'UPDATE users SET bio = ?, profile_hashtags = ? WHERE id = ?',
                (bio, hashtags, user_id)
            )

            # Handle profile image upload if provided
            if profile_image and profile_image.filename != '':
                # Validate file type
                if not profile_image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    flash('Only image files (PNG, JPG, JPEG, GIF, WebP) are allowed', 'error')
                    return redirect(request.url)

                # Save file
                filename = f"profile_{user_id}_{profile_image.filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                profile_image.save(filepath)

                # Update user profile image
                cursor.execute(
                    'UPDATE users SET profile_image_url = ? WHERE id = ?',
                    (f"/uploads/{filename}", user_id)
                )

            db.commit()
            flash('Profile updated successfully', 'success')
        elif 'activity_log' in request.files:
            # Handle activity log upload
            file = request.files['activity_log']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)

            if not file.filename.endswith('.zip'):
                flash('Only .zip files are allowed', 'error')
                return redirect(request.url)

            # Save file
            filename = f"user_{user_id}_{file.filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process the zip file
            success, message = process_zip_file(filepath, user_id)
            if success:
                # Mark as processed in activity_logs
                cursor.execute(
                    'INSERT INTO activity_logs (user_id, zip_filename, processed) VALUES (?, ?, ?)',
                    (user_id, filename, True)
                )
                db.commit()
                flash(message, 'success')
            else:
                flash(message, 'error')

            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)

        return redirect(url_for('main.profile'))

    # Get user data
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    cursor.execute('SELECT * FROM user_interests WHERE user_id = ?', (user_id,))
    interests = cursor.fetchone()

    cursor.execute('SELECT COUNT(*) as followers FROM follows WHERE following_id = ?', (user_id,))
    followers = cursor.fetchone()['followers']

    cursor.execute('SELECT COUNT(*) as following FROM follows WHERE follower_id = ?', (user_id,))
    user_following = cursor.fetchone()['following']

    cursor.execute('SELECT COUNT(*) as hashtag_following FROM hashtag_follows WHERE user_id = ?', (user_id,))
    hashtag_following = cursor.fetchone()['hashtag_following']

    cursor.execute('SELECT COUNT(*) as music_following FROM music_follows WHERE user_id = ?', (user_id,))
    music_following = cursor.fetchone()['music_following']

    cursor.execute('SELECT COUNT(*) as creator_following FROM creator_follows WHERE user_id = ?', (user_id,))
    creator_following = cursor.fetchone()['creator_following']

    following = user_following + hashtag_following + music_following + creator_following

    return render_template('profile.html', user=user, interests=interests, followers=followers, following=following)

@main_bp.route('/user/<int:user_id>')
def user_detail(user_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.home'))

    cursor.execute('SELECT * FROM user_interests WHERE user_id = ?', (user_id,))
    interests_row = cursor.fetchone()

    # Convert sqlite3.Row to dict for template access and parse JSON
    interests = None
    if interests_row:
        interests = {
            'hashtags': json.loads(interests_row['hashtags']) if interests_row['hashtags'] else [],
            'music_liked': json.loads(interests_row['music_liked']) if interests_row['music_liked'] else [],
            'celebrities_followed': json.loads(interests_row['celebrities_followed']) if interests_row['celebrities_followed'] else [],
            'posts_liked_count': interests_row['posts_liked_count'],
            'reels_watched_count': interests_row['reels_watched_count'],
            'comments_made_count': interests_row['comments_made_count']
        }

    # Check if current user follows this user
    cursor.execute('SELECT * FROM follows WHERE follower_id = ? AND following_id = ?', (current_user_id, user_id))
    is_following = cursor.fetchone() is not None

    # Get followers count
    cursor.execute('SELECT COUNT(*) as followers FROM follows WHERE following_id = ?', (user_id,))
    followers = cursor.fetchone()['followers']

    # Get following count (users + hashtags + music)
    cursor.execute('SELECT COUNT(*) as user_following FROM follows WHERE follower_id = ?', (user_id,))
    user_following = cursor.fetchone()['user_following']

    cursor.execute('SELECT COUNT(*) as hashtag_following FROM hashtag_follows WHERE user_id = ?', (user_id,))
    hashtag_following = cursor.fetchone()['hashtag_following']

    cursor.execute('SELECT COUNT(*) as music_following FROM music_follows WHERE user_id = ?', (user_id,))
    music_following = cursor.fetchone()['music_following']

    cursor.execute('SELECT COUNT(*) as creator_following FROM creator_follows WHERE user_id = ?', (user_id,))
    creator_following = cursor.fetchone()['creator_following']

    following = user_following + hashtag_following + music_following + creator_following

    return render_template('user_detail.html', user=user, interests=interests, is_following=is_following, followers=followers, following=following)

@main_bp.route('/api/followers/<int:user_id>')
def get_followers(user_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT u.id, u.username, u.profile_image_url
        FROM follows f
        JOIN users u ON f.follower_id = u.id
        WHERE f.following_id = ?
        ORDER BY u.username
    ''', (user_id,))

    followers = cursor.fetchall()
    return jsonify([{
        'id': f['id'],
        'username': f['username'],
        'profile_image_url': f['profile_image_url'] or 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIzMCIgZmlsbD0iI2NjYyIvPjwvc3ZnPg=='
    } for f in followers])

@main_bp.route('/api/following/<int:user_id>')
def get_following(user_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()
    cursor = db.cursor()

    # Get user following
    cursor.execute('''
        SELECT u.id, u.username, u.profile_image_url, 'user' as type
        FROM follows f
        JOIN users u ON f.following_id = u.id
        WHERE f.follower_id = ?
        ORDER BY u.username
    ''', (user_id,))

    user_following = cursor.fetchall()

    # Get hashtag following
    cursor.execute('''
        SELECT NULL as id, hashtag_name as username, NULL as profile_image_url, 'hashtag' as type
        FROM hashtag_follows
        WHERE user_id = ?
        ORDER BY hashtag_name
    ''', (user_id,))

    hashtag_following = cursor.fetchall()

    # Get music following
    cursor.execute('''
        SELECT NULL as id, song_name as username, NULL as profile_image_url, 'music' as type
        FROM music_follows
        WHERE user_id = ?
        ORDER BY song_name
    ''', (user_id,))

    music_following = cursor.fetchall()

    # Get creator following
    cursor.execute('''
        SELECT NULL as id, creator_name as username, NULL as profile_image_url, 'creator' as type
        FROM creator_follows
        WHERE user_id = ?
        ORDER BY creator_name
    ''', (user_id,))

    creator_following = cursor.fetchall()

    # Combine and return
    following = user_following + hashtag_following + music_following + creator_following
    return jsonify([{
        'id': f['id'],
        'username': f['username'],
        'profile_image_url': f['profile_image_url'] or 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIzMCIgZmlsbD0iI2NjYyIvPjwvc3ZnPg==',
        'type': f['type']
    } for f in following])

@main_bp.route('/hashtag/<hashtag_name>')
def hashtag_detail(hashtag_name):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    # Prepend # to hashtag_name for database query
    full_hashtag_name = '#' + hashtag_name

    # Get hashtag info
    cursor.execute('SELECT * FROM global_trends WHERE trend_type = ? AND name = ?', ('hashtag', full_hashtag_name))
    hashtag = cursor.fetchone()

    if not hashtag:
        flash('Hashtag not found', 'error')
        return redirect(url_for('main.home'))

    # Get rank
    cursor.execute('SELECT COUNT(*) + 1 as rank FROM global_trends WHERE trend_type = ? AND count > ?', ('hashtag', hashtag['count']))
    rank = cursor.fetchone()['rank']

    # Get users who have this hashtag in their profile
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE profile_hashtags LIKE ?', (f'%{hashtag_name}%',))
    profile_users_count = cursor.fetchone()['count']

    # Get followers count (users following this hashtag)
    cursor.execute('SELECT COUNT(*) as count FROM hashtag_follows WHERE hashtag_name = ?', (hashtag_name,))
    followers_count = cursor.fetchone()['count']

    # Check if current user follows this hashtag
    cursor.execute('SELECT 1 FROM hashtag_follows WHERE user_id = ? AND hashtag_name = ?', (user_id, hashtag_name))
    is_following = cursor.fetchone() is not None

    # Get posts with this hashtag (placeholder data for now)
    posts = []  # This would need a posts table with hashtag associations

    # Get reels with this hashtag (placeholder data for now)
    reels = []  # This would need a reels table with hashtag associations

    return render_template('hashtag.html',
                         hashtag_name=hashtag_name,
                         rank=rank,
                         profile_users_count=profile_users_count,
                         followers_count=followers_count,
                         is_following=is_following,
                         posts=posts,
                         reels=reels)

@main_bp.route('/hashtag/follow/<hashtag_name>', methods=['POST'])
def follow_hashtag(hashtag_name):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            'INSERT INTO hashtag_follows (user_id, hashtag_name) VALUES (?, ?)',
            (user_id, hashtag_name)
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Followed hashtag successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Already following this hashtag'})

@main_bp.route('/hashtag/unfollow/<hashtag_name>', methods=['POST'])
def unfollow_hashtag(hashtag_name):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'DELETE FROM hashtag_follows WHERE user_id = ? AND hashtag_name = ?',
        (user_id, hashtag_name)
    )
    db.commit()

    return jsonify({'success': True, 'message': 'Unfollowed hashtag successfully'})

@main_bp.route('/music/<path:song_name>')
def music_detail(song_name):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    # Get music info from global_trends
    cursor.execute('SELECT * FROM global_trends WHERE trend_type = ? AND name = ?', ('music', song_name))
    music = cursor.fetchone()

    if not music:
        flash('Song not found', 'error')
        return redirect(url_for('main.home'))

    # Get rank
    cursor.execute('SELECT COUNT(*) + 1 as rank FROM global_trends WHERE trend_type = ? AND count > ?', ('music', music['count']))
    rank = cursor.fetchone()['rank']

    # Get users who have this song in their profile
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE profile_hashtags LIKE ?', (f'%{song_name}%',))
    profile_users_count = cursor.fetchone()['count']

    # Get followers count (users following this song)
    cursor.execute('SELECT COUNT(*) as count FROM music_follows WHERE song_name = ?', (song_name,))
    followers_count = cursor.fetchone()['count']

    # Check if current user follows this song
    cursor.execute('SELECT 1 FROM music_follows WHERE user_id = ? AND song_name = ?', (user_id, song_name))
    is_following = cursor.fetchone() is not None

    # Get posts with this song (placeholder data for now)
    posts = []  # This would need a posts table with song associations

    # Get reels with this song (placeholder data for now)
    reels = []  # This would need a reels table with song associations

    return render_template('music.html',
                         song_name=song_name,
                         rank=rank,
                         profile_users_count=profile_users_count,
                         followers_count=followers_count,
                         is_following=is_following,
                         posts=posts,
                         reels=reels)

@main_bp.route('/music/follow/<path:song_name>', methods=['POST'])
def follow_music(song_name):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            'INSERT INTO music_follows (user_id, song_name) VALUES (?, ?)',
            (user_id, song_name)
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Followed song successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Already following this song'})

@main_bp.route('/music/unfollow/<path:song_name>', methods=['POST'])
def unfollow_music(song_name):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'DELETE FROM music_follows WHERE user_id = ? AND song_name = ?',
        (user_id, song_name)
    )
    db.commit()

    return jsonify({'success': True, 'message': 'Unfollowed song successfully'})

@main_bp.route('/creator/<creator_name>')
def creator_detail(creator_name):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    # Prepend @ to creator_name for database query
    full_creator_name = '@' + creator_name

    # Get creator info from global_trends
    cursor.execute('SELECT * FROM global_trends WHERE trend_type = ? AND name = ?', ('creator', full_creator_name))
    creator = cursor.fetchone()

    if not creator:
        flash('Creator not found', 'error')
        return redirect(url_for('main.home'))

    # Update creator name to remove @
    creator_name = creator_name

    # Get rank
    cursor.execute('SELECT COUNT(*) + 1 as rank FROM global_trends WHERE trend_type = ? AND count > ?', ('creator', creator['count']))
    rank = cursor.fetchone()['rank']

    # Get users who have this creator in their profile
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE profile_hashtags LIKE ?', (f'%{creator_name}%',))
    profile_users_count = cursor.fetchone()['count']

    # Get followers count (users following this creator)
    cursor.execute('SELECT COUNT(*) as count FROM creator_follows WHERE creator_name = ?', (creator_name,))
    followers_count = cursor.fetchone()['count']

    # Check if current user follows this creator
    cursor.execute('SELECT 1 FROM creator_follows WHERE user_id = ? AND creator_name = ?', (user_id, creator_name))
    is_following = cursor.fetchone() is not None

    # Get posts with this creator (placeholder data for now)
    posts = []  # This would need a posts table with creator associations

    # Get reels with this creator (placeholder data for now)
    reels = []  # This would need a reels table with creator associations

    return render_template('creator.html',
                         creator_name=creator_name,
                         rank=rank,
                         profile_users_count=profile_users_count,
                         followers_count=followers_count,
                         is_following=is_following,
                         posts=posts,
                         reels=reels)

@main_bp.route('/creator/follow/<creator_name>', methods=['POST'])
def follow_creator(creator_name):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            'INSERT INTO creator_follows (user_id, creator_name) VALUES (?, ?)',
            (user_id, creator_name)
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Followed creator successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Already following this creator'})

@main_bp.route('/creator/unfollow/<creator_name>', methods=['POST'])
def unfollow_creator(creator_name):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'DELETE FROM creator_follows WHERE user_id = ? AND creator_name = ?',
        (user_id, creator_name)
    )
    db.commit()

    return jsonify({'success': True, 'message': 'Unfollowed creator successfully'})

@main_bp.route('/api/trend_users/<trend_type>/<path:trend_name>')
def get_trend_users(trend_type, trend_name):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()
    cursor = db.cursor()

    if trend_type == 'hashtag':
        # Users who have this hashtag in their profile_hashtags
        cursor.execute('''
            SELECT id, username, profile_image_url
            FROM users
            WHERE profile_hashtags LIKE ?
            ORDER BY username
        ''', (f'%{trend_name}%',))
    elif trend_type == 'music':
        # Users who have this song in their profile_hashtags (assuming music is stored there)
        cursor.execute('''
            SELECT id, username, profile_image_url
            FROM users
            WHERE profile_hashtags LIKE ?
            ORDER BY username
        ''', (f'%{trend_name}%',))
    elif trend_type == 'creator':
        # Users who have this creator in their profile_hashtags
        cursor.execute('''
            SELECT id, username, profile_image_url
            FROM users
            WHERE profile_hashtags LIKE ?
            ORDER BY username
        ''', (f'%{trend_name}%',))
    else:
        return jsonify({'error': 'Invalid trend type'}), 400

    users = cursor.fetchall()
    return jsonify([{
        'id': u['id'],
        'username': u['username'],
        'profile_image_url': u['profile_image_url'] or 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIzMCIgZmlsbD0iI2NjYyIvPjwvc3ZnPg=='
    } for u in users])

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/support')
def support():
    return render_template('support.html')

@main_bp.route('/api/trend_followers/<trend_type>/<path:trend_name>')
def get_trend_followers(trend_type, trend_name):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()
    cursor = db.cursor()

    if trend_type == 'hashtag':
        cursor.execute('''
            SELECT u.id, u.username, u.profile_image_url
            FROM hashtag_follows hf
            JOIN users u ON hf.user_id = u.id
            WHERE hf.hashtag_name = ?
            ORDER BY u.username
        ''', (trend_name,))
    elif trend_type == 'music':
        cursor.execute('''
            SELECT u.id, u.username, u.profile_image_url
            FROM music_follows mf
            JOIN users u ON mf.user_id = u.id
            WHERE mf.song_name = ?
            ORDER BY u.username
        ''', (trend_name,))
    elif trend_type == 'creator':
        cursor.execute('''
            SELECT u.id, u.username, u.profile_image_url
            FROM creator_follows cf
            JOIN users u ON cf.user_id = u.id
            WHERE cf.creator_name = ?
            ORDER BY u.username
        ''', (trend_name,))
    else:
        return jsonify({'error': 'Invalid trend type'}), 400

    users = cursor.fetchall()
    return jsonify([{
        'id': u['id'],
        'username': u['username'],
        'profile_image_url': u['profile_image_url'] or 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIzMCIgY3k9IjMwIiByPSIzMCIgZmlsbD0iI2NjYyIvPjwvc3ZnPg=='
    } for u in users])

@main_bp.route('/repost/<int:trend_id>', methods=['POST'])
def repost_trend(trend_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    # Get trend details
    cursor.execute('SELECT * FROM global_trends WHERE id = ?', (trend_id,))
    trend = cursor.fetchone()

    if not trend:
        return jsonify({'success': False, 'message': 'Trend not found'})

    try:
        cursor.execute('''
            INSERT INTO reposts (user_id, trend_id, trend_type, trend_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, trend_id, trend['trend_type'], trend['name']))
        db.commit()
        return jsonify({'success': True, 'message': 'Reposted successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Already reposted'})

@main_bp.route('/unrepost/<int:trend_id>', methods=['POST'])
def unrepost_trend(trend_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    cursor.execute('DELETE FROM reposts WHERE user_id = ? AND trend_id = ?', (user_id, trend_id))
    db.commit()

    return jsonify({'success': True, 'message': 'Unreposted successfully'})

@main_bp.route('/api/reposts/<int:user_id>')
def get_reposts(user_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'error': 'Not logged in'}), 401

    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT r.*, gt.count, gt.last_updated
        FROM reposts r
        JOIN global_trends gt ON r.trend_id = gt.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
    ''', (user_id,))

    reposts = cursor.fetchall()
    return jsonify([{
        'id': r['id'],
        'trend_id': r['trend_id'],
        'trend_type': r['trend_type'],
        'trend_name': r['trend_name'],
        'count': r['count'],
        'created_at': r['created_at']
    } for r in reposts])
