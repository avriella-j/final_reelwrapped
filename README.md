# ReelWrapped

A Flask-based web application that provides Instagram activity summaries and personalized recommendations based on user data.

## Features

- **User Authentication**: Secure login and registration system
- **Activity Log Upload**: Upload Instagram activity logs (.zip files) for analysis
- **Personalized Dashboard**: Get insights into your Instagram usage patterns
- **Global Trends**: Explore trending hashtags, music, and creators on the home feed
- **Trend Pages**: View and follow hashtags, music, and creators
- **Reposts**: Repost trends from the home feed and view them on your profile
- **Find Mutuals**: Discover users with similar interests; search and follow users
- **Profile Management**: Edit bio, hashtags, and profile image; upload activity logs
- **Admin Panel**: PIN-protected dashboard to manage trends, users, and monetization insights
- **About & Support**: Public landing, about, and support pages (admin sign-in via Support)
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Styling**: Custom CSS with Instagram-inspired gradient design
- **Templates**: Jinja2

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd reelwrapped
   ```

2. Create a virtual environment (this project uses `.venv`):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python run.py
   ```

5. Open your browser and navigate to `http://localhost:5000`

6. (Optional) Initialize or reset the database:
   ```bash
   flask --app run init-db
   ```

## Usage

### Getting Started
1. Visit the landing page, then register or log in
2. Upload your Instagram activity logs from your profile (download from Instagram settings)
3. Browse global trends on **Home**, personalized picks on **For You**, and your **Profile**
4. Find users with similar interests under **Find Mutuals**
5. Admins can sign in from the **Support** page (PIN required)

### Uploading Activity Logs
1. Go to your Instagram settings
2. Request your data download
3. Once received, upload the .zip file to your profile
4. The app will process and analyze your activity data

## Project Structure

```
ReelWrapped/
├── app/
│   ├── __init__.py              # Flask app factory, blueprints, error handlers
│   ├── blueprints/
│   │   ├── auth.py              # Login, register, logout
│   │   ├── main.py              # Home, profile, trends, APIs
│   │   ├── mutuals.py           # Find mutuals (/mutuals)
│   │   └── admin.py             # Admin panel (/admin)
│   ├── templates/
│   │   ├── base.html
│   │   ├── landing.html         # Public landing (/)
│   │   ├── home.html            # Global trends (/home)
│   │   ├── foryou.html
│   │   ├── profile.html
│   │   ├── user_detail.html
│   │   ├── mutuals.html
│   │   ├── hashtag.html
│   │   ├── music.html
│   │   ├── creator.html
│   │   ├── about.html
│   │   ├── support.html         # FAQ + admin PIN sign-in
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── admin_dashboard.html
│   │   ├── admin_trends.html
│   │   ├── admin_edit_trend.html
│   │   ├── admin_users.html
│   │   ├── admin_edit_user.html
│   │   ├── admin_monetization.html  # Used by /admin/monetization (add if missing)
│   │   ├── admin.html           # Legacy / planned (see TODO.md)
│   │   ├── manage_trends.html
│   │   ├── manage_profiles.html
│   │   ├── edit_trend.html
│   │   ├── 404.html
│   │   └── 500.html
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css        # Main stylesheet
│   │   │   └── admin.css        # Admin / support styles
│   │   └── js/
│   │       └── main.js
│   └── utils/
│       ├── db.py                # SQLite schema and connection
│       └── helpers.py           # Validation, zip processing, matching
├── uploads/                     # Profile images (runtime; created on upload)
├── config.py
├── run.py                       # Entry point
├── requirements.txt
├── README.md
├── TODO.md
├── .gitignore                   # bandit-report.* (local scan output)
├── reelwrapped.db               # SQLite DB (runtime; path from config.py)
├── .venv/                       # Local virtualenv (not in repo)
├── __pycache__/                 # Python bytecode (local)
└── bandit-report.*              # Security scan output (gitignored)
```

## Database Schema

The application uses SQLite (`reelwrapped.db` at the project root). Tables created by `init_db` in `app/utils/db.py`:

- **users**: Accounts (username, email, password hash, bio, profile image, hashtags)
- **activity_logs**: Uploaded activity log metadata
- **user_interests**: Parsed interests and activity counts (JSON fields)
- **global_trends**: Aggregated trends (`hashtag`, `music`, `creator`, `topic`)
- **follows**: User-to-user follows
- **hashtag_follows**: User follows for hashtags
- **music_follows**: User follows for songs

The app also queries **creator_follows** and **reposts** for creator follows and the repost feature; ensure these exist in your database if you use those features.

## API Endpoints

### Authentication
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout

### Main App
- `GET /` - Landing page (public)
- `GET /home` - Global trends feed
- `GET /foryou` - Personalized recommendations
- `GET/POST /profile` - Profile, bio/image edit, activity log upload
- `GET /user/<user_id>` - View another user's profile
- `GET /about` - About page (public)
- `GET /support` - Support page (public; admin PIN sign-in)
- `GET /hashtag/<name>` - Hashtag trend detail
- `POST /hashtag/follow/<name>` - Follow a hashtag
- `POST /hashtag/unfollow/<name>` - Unfollow a hashtag
- `GET /music/<song_name>` - Music trend detail
- `POST /music/follow/<song_name>` - Follow a song
- `POST /music/unfollow/<song_name>` - Unfollow a song
- `GET /creator/<creator_name>` - Creator trend detail
- `POST /creator/follow/<creator_name>` - Follow a creator
- `POST /creator/unfollow/<creator_name>` - Unfollow a creator
- `POST /repost/<trend_id>` - Repost a trend (JSON)
- `POST /unrepost/<trend_id>` - Remove a repost (JSON)
- `GET /api/followers/<user_id>` - Followers list (JSON)
- `GET /api/following/<user_id>` - Following list (JSON)
- `GET /api/reposts/<user_id>` - User reposts (JSON)
- `GET /api/trend_users/<type>/<name>` - Users associated with a trend (JSON)
- `GET /api/trend_followers/<type>/<name>` - Followers of a trend (JSON)
- `GET /uploads/<filename>` - Served upload files

### Mutuals (`/mutuals` prefix)
- `GET /mutuals/` - Find users with similar interests
- `GET /mutuals/search` - Search users (JSON)
- `POST /mutuals/follow/<user_id>` - Follow a user
- `POST /mutuals/unfollow/<user_id>` - Unfollow a user

### Admin (`/admin` prefix; requires admin session)
- `POST /admin/auth` - Admin PIN authentication (JSON)
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/trends` - Manage global trends
- `GET/POST /admin/trend/<trend_id>/edit` - Edit a trend
- `POST /admin/trend/<trend_id>/delete` - Delete a trend
- `GET /admin/users` - Manage users
- `GET/POST /admin/user/<user_id>/edit` - Edit a user
- `POST /admin/user/<user_id>/delete` - Delete a user
- `GET /admin/monetization` - Monetization insights view
- `GET /admin/logout` - End admin session

## Security Features

- Password hashing with Werkzeug
- Session-based authentication (users and admin)
- Admin access gated by PIN (`ADMIN_PIN` in config or environment)
- File upload validation (activity logs: `.zip` only, 16MB max; profile images: common image types)
- Input validation and sanitization in helpers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This application is for educational purposes only. Always respect user privacy and data protection laws when handling personal data.
