import json
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.utils.db import get_db
from app.utils.helpers import calculate_interest_match

mutuals_bp = Blueprint('mutuals', __name__, url_prefix='/mutuals')

@mutuals_bp.route('/')
def mutuals():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    # Get query parameter for sorting
    sort_by = request.args.get('sort', 'match')

    # Get users with similar interests and follower/following counts
    cursor.execute('''
        SELECT u.id, u.username, u.profile_image_url,
               ui.hashtags, ui.music_liked, ui.celebrities_followed,
               (SELECT COUNT(*) FROM follows WHERE following_id = u.id) as followers,
               (SELECT COUNT(*) FROM follows WHERE follower_id = u.id) as following
        FROM users u
        LEFT JOIN user_interests ui ON u.id = ui.user_id
        WHERE u.id != ?
        ORDER BY u.id
        LIMIT 20
    ''', (user_id,))

    users = cursor.fetchall()

    # Process interests to be lists instead of JSON strings
    processed_users = []
    for user in users:
        user_dict = dict(user)  # Convert sqlite3.Row to dict

        # Process hashtags
        if user_dict['hashtags']:
            try:
                user_dict['hashtags'] = json.loads(user_dict['hashtags'])
            except (json.JSONDecodeError, TypeError):
                user_dict['hashtags'] = []
        else:
            user_dict['hashtags'] = []

        # Process music_liked
        if user_dict['music_liked']:
            try:
                user_dict['music_liked'] = json.loads(user_dict['music_liked'])
            except (json.JSONDecodeError, TypeError):
                user_dict['music_liked'] = []
        else:
            user_dict['music_liked'] = []

        # Process celebrities_followed
        if user_dict['celebrities_followed']:
            try:
                user_dict['celebrities_followed'] = json.loads(user_dict['celebrities_followed'])
            except (json.JSONDecodeError, TypeError):
                user_dict['celebrities_followed'] = []
        else:
            user_dict['celebrities_followed'] = []

        processed_users.append(user_dict)

    users = processed_users

    # Calculate match percentages and check follow status
    user_matches = []
    for user in users:
        match_percent = calculate_interest_match(user_id, user['id'])

        # Check if current user is following this user
        cursor.execute('SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?',
                      (user_id, user['id']))
        is_following = cursor.fetchone() is not None

        user_matches.append({
            'user': user,
            'match_percent': match_percent,
            'is_following': is_following
        })

    # Sort based on the sort parameter
    if sort_by == 'followers':
        user_matches.sort(key=lambda x: x['user']['followers'], reverse=True)
    elif sort_by == 'alphabetical':
        user_matches.sort(key=lambda x: x['user']['username'].lower())
    else:  # match (default)
        user_matches.sort(key=lambda x: x['match_percent'], reverse=True)

    return render_template('mutuals.html', user_matches=user_matches, sort_by=sort_by)

@mutuals_bp.route('/follow/<int:user_id>', methods=['POST'])
def follow(user_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    if current_user_id == user_id:
        return jsonify({'success': False, 'message': 'Cannot follow yourself'})

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            'INSERT INTO follows (follower_id, following_id) VALUES (?, ?)',
            (current_user_id, user_id)
        )
        db.commit()
        return jsonify({'success': True, 'message': 'Followed successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Already following'})

@mutuals_bp.route('/unfollow/<int:user_id>', methods=['POST'])
def unfollow(user_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'DELETE FROM follows WHERE follower_id = ? AND following_id = ?',
        (current_user_id, user_id)
    )
    db.commit()

    return jsonify({'success': True, 'message': 'Unfollowed successfully'})

@mutuals_bp.route('/search')
def search():
    query = request.args.get('q', '')
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([])

    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT u.id, u.username, u.profile_image_url
        FROM users u
        WHERE u.username LIKE ? AND u.id != ?
        LIMIT 10
    ''', (f'%{query}%', user_id))

    users = cursor.fetchall()
    return jsonify([{
        'id': user['id'],
        'username': user['username'],
        'profile_image_url': user['profile_image_url']
    } for user in users])

