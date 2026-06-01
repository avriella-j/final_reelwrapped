from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.utils.db import get_db
from app.utils.helpers import validate_required_fields, validate_email, validate_image_url, hash_password, check_password
import sqlite3
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin PIN - in production, this should be stored securely (environment variable, etc.)
ADMIN_PIN = "0987654321qwerty"

@admin_bp.route('/auth', methods=['POST'])
def admin_auth():
    pin = request.json.get('pin')
    
    if pin == ADMIN_PIN:
        # Set admin session variables
        session['is_admin'] = True
        session['is_authenticated'] = True
        session['username'] = 'admin'  # Set a default admin username
        return jsonify({'success': True, 'message': 'Authenticated successfully'})
    else:
        return jsonify({'success': False, 'message': 'Invalid PIN'})

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db = get_db()
    cursor = db.cursor()
    
    # Get statistics - handle case where tables might not exist yet
    try:
        cursor.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = cursor.fetchone()['total_users']
    except sqlite3.OperationalError:
        total_users = 0
    
    try:
        cursor.execute('SELECT COUNT(*) as total_trends FROM global_trends')
        total_trends = cursor.fetchone()['total_trends']
    except sqlite3.OperationalError:
        total_trends = 0
    
    try:
        cursor.execute('SELECT COUNT(*) as hashtag_trends FROM global_trends WHERE trend_type = ?', ('hashtag',))
        hashtag_trends = cursor.fetchone()['hashtag_trends']
    except sqlite3.OperationalError:
        hashtag_trends = 0
    
    try:
        cursor.execute('SELECT COUNT(*) as music_trends FROM global_trends WHERE trend_type = ?', ('music',))
        music_trends = cursor.fetchone()['music_trends']
    except sqlite3.OperationalError:
        music_trends = 0
    
    try:
        cursor.execute('SELECT COUNT(*) as creator_trends FROM global_trends WHERE trend_type = ?', ('creator',))
        creator_trends = cursor.fetchone()['creator_trends']
    except sqlite3.OperationalError:
        creator_trends = 0
    
    # Get recent users with additional fields
    cursor.execute('SELECT id, username, email, bio, profile_hashtags, profile_image_url, created_at FROM users ORDER BY created_at DESC LIMIT 10')
    recent_users = cursor.fetchall()
    
    # Get top trends
    cursor.execute('SELECT id, name, trend_type, count FROM global_trends ORDER BY count DESC LIMIT 10')
    top_trends = cursor.fetchall()
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users,
                         total_trends=total_trends,
                         hashtag_trends=hashtag_trends,
                         music_trends=music_trends,
                         creator_trends=creator_trends,
                         recent_users=recent_users,
                         top_trends=top_trends)

@admin_bp.route('/trends')
def manage_trends():
    if not session.get('is_admin'):
        return redirect(url_for('main.support'))
    
    db = get_db()
    cursor = db.cursor()
    
    trend_type = request.args.get('type', 'all')
    
    if trend_type == 'all':
        cursor.execute('SELECT * FROM global_trends ORDER BY count DESC')
    else:
        cursor.execute('SELECT * FROM global_trends WHERE trend_type = ? ORDER BY count DESC', (trend_type,))
    
    trends = cursor.fetchall()
    
    return render_template('admin_trends.html', trends=trends, current_type=trend_type)

@admin_bp.route('/trend/<int:trend_id>/delete', methods=['POST'])
def delete_trend(trend_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('DELETE FROM global_trends WHERE id = ?', (trend_id,))
    db.commit()
    
    flash('Trend deleted successfully', 'success')
    return redirect(url_for('admin.manage_trends'))

@admin_bp.route('/trend/<int:trend_id>/edit', methods=['GET', 'POST'])
def edit_trend(trend_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.support'))
    
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name')
        count = request.form.get('count')
        trend_type = request.form.get('trend_type')
        
        cursor.execute('UPDATE global_trends SET name = ?, count = ?, trend_type = ? WHERE id = ?', 
                      (name, count, trend_type, trend_id))
        db.commit()
        
        flash('Trend updated successfully', 'success')
        return redirect(url_for('admin.dashboard'))
    
    cursor.execute('SELECT * FROM global_trends WHERE id = ?', (trend_id,))
    trend = cursor.fetchone()
    
    if not trend:
        flash('Trend not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin_edit_trend.html', trend=trend)

@admin_bp.route('/users')
def manage_users():
    if not session.get('is_admin'):
        return redirect(url_for('main.support'))
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id, username, email, bio, profile_hashtags, created_at FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    
    return render_template('admin_users.html', users=users)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    db = get_db()
    cursor = db.cursor()
    
    # Delete user data
    cursor.execute('DELETE FROM follows WHERE follower_id = ? OR following_id = ?', (user_id, user_id))
    cursor.execute('DELETE FROM user_interests WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM activity_logs WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.support'))
    
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        bio = request.form.get('bio')
        profile_hashtags = request.form.get('profile_hashtags')
        profile_image_url = request.form.get('profile_image_url')
        
        cursor.execute('UPDATE users SET username = ?, email = ?, bio = ?, profile_hashtags = ?, profile_image_url = ? WHERE id = ?', 
                      (username, email, bio, profile_hashtags, profile_image_url, user_id))
        db.commit()
        
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.dashboard'))
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin_edit_user.html', user=user)

@admin_bp.route('/monetization')
def monetization():
    if not session.get('is_admin'):
        return redirect(url_for('main.support'))
    
    db = get_db()
    cursor = db.cursor()
    
    # Get trends that can be monetized
    cursor.execute('SELECT * FROM global_trends ORDER BY count DESC LIMIT 50')
    trends = cursor.fetchall()
    
    # Get users who might be eligible for monetization
    cursor.execute('SELECT * FROM users WHERE profile_hashtags != "" ORDER BY created_at DESC LIMIT 50')
    users = cursor.fetchall()
    
    return render_template('admin_monetization.html', trends=trends, users=users)

@admin_bp.route('/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Logged out from admin panel', 'info')
    return redirect(url_for('main.support'))
