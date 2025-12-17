from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name='default'):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.flashcards import flashcards_bp
    from app.routes.study import study_bp
    from app.routes.api import api_bp
    from app.routes.ai import ai_bp
    from app.routes.auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(flashcards_bp, url_prefix='/flashcards')
    app.register_blueprint(study_bp, url_prefix='/study')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(ai_bp)
    app.register_blueprint(auth_bp)
    
    # Custom Jinja2 filters for timezone
    from datetime import timedelta
    
    @app.template_filter('to_ist')
    def to_ist_filter(dt):
        """Convert UTC datetime to IST (UTC+5:30)."""
        if dt is None:
            return ''
        ist_offset = timedelta(hours=5, minutes=30)
        return dt + ist_offset
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

