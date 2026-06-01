from flask import Flask, render_template, send_from_directory
import click
from config import Config
from app.utils.db import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.mutuals import mutuals_bp
    from app.blueprints.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(mutuals_bp)
    app.register_blueprint(admin_bp)

    # Add route to serve uploaded files
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    # Register CLI command
    @app.cli.command("init-db")
    @click.confirmation_option(prompt='This will reset the database. Do you want to continue?')
    def init_db_command():
        """Initialize the database."""
        init_db(app)
        click.echo("Initialized the database.")

    return app
