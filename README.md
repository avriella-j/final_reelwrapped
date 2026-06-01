# ReelWrapped

A Flask-based web application that provides Instagram activity summaries and personalized recommendations based on user data.

## Features

- **User Authentication**: Secure login and registration system
- **Activity Log Upload**: Upload Instagram activity logs (.zip files) for analysis
- **Personalized Dashboard**: Get insights into your Instagram usage patterns
- **Global Trends**: Explore trending hashtags, music, and celebrities
- **Find Mutuals**: Discover users with similar interests
- **Profile Management**: Edit profile, change password, delete account
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

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
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

## Usage

### Getting Started
1. Register for a new account or login with existing credentials
2. Upload your Instagram activity logs (download from Instagram settings)
3. Explore your personalized dashboard and global trends
4. Find users with similar interests in the "Find Mutuals" section

### Uploading Activity Logs
1. Go to your Instagram settings
2. Request your data download
3. Once received, upload the .zip file to your profile
4. The app will process and analyze your activity data

## Project Structure

```
reelwrapped/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── blueprints/          # Route blueprints
│   │   ├── auth.py         # Authentication routes
│   │   ├── main.py         # Main app routes
│   │   ├── mutuals.py      # Find mutuals routes
│   │   └── admin.py        # Admin/settings routes
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html       # Base template
│   │   ├── home.html       # Home page
│   │   ├── profile.html    # User profile
│   │   ├── foryou.html     # Personalized feed
│   │   ├── mutuals.html    # Find mutuals page
│   │   ├── admin.html      # Settings page
│   │   ├── login.html      # Login page
│   │   ├── register.html   # Registration page
│   │   └── *.html          # Other templates
│   ├── static/              # Static files
│   │   ├── css/
│   │   │   └── style.css   # Main stylesheet
│   │   └── js/
│   │       └── main.js     # JavaScript functionality
│   └── utils/               # Utility functions
│       ├── db.py           # Database operations
│       └── helpers.py      # Helper functions
├── uploads/                 # Uploaded files directory
├── config.py               # Configuration
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── TODO.md                # Development tasks
```

## Database Schema

The application uses SQLite with the following tables:

- **users**: User accounts
- **activity_logs**: Uploaded activity log files
- **user_interests**: Processed user interests and statistics
- **global_trends**: Aggregated trending data
- **follows**: User follow relationships

## API Endpoints

### Authentication
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout

### Main App
- `GET /` - Home page (global trends)
- `GET /foryou` - Personalized recommendations
- `GET/POST /profile` - User profile and file upload
- `GET /user/<id>` - View other user profiles

### Mutuals
- `GET /mutuals` - Find users with similar interests
- `POST /mutuals/follow/<id>` - Follow a user
- `POST /mutuals/unfollow/<id>` - Unfollow a user

### Admin
- `GET /admin` - Account settings
- `POST /admin/edit` - Edit profile
- `POST /admin/change-password` - Change password
- `POST /admin/delete-account` - Delete account

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- CSRF protection
- File upload validation (.zip only, 16MB limit)
- Input validation and sanitization

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
