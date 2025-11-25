from flask import Flask, render_template
from config import Config
from extensions import db, bcrypt, login_manager
from flask_migrate import Migrate
from models import User, Book, BookCopy, Reservation, BorrowedBooks, Review

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Initialize Extensions FIRST
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # Initialize Migrations
    migrate = Migrate(app, db)

    # Login Manager Configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 2. Register Blueprints AFTER Extensions
    from routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from routes.books import bp as books_bp 
    app.register_blueprint(books_bp, url_prefix='/books')
    
    from routes.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    from routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    # --- API BLUEPRINT ---
    from routes.api import api as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    # ---------------------

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)