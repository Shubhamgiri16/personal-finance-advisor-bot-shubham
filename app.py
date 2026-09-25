import os
from flask import Flask, jsonify
from flask_cors import CORS
from models import db, User
from seed_data import seed_database
from routes.transactions import transactions_bp
from routes.budgets import budgets_bp
from routes.goals import goals_bp
from routes.analytics import analytics_bp
from routes.advisor import advisor_bp
from routes.reports import reports_bp
from routes.settings import settings_bp

def create_app():
    app = Flask(__name__)
    
    # Configure SQLite database
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'advisor.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Enable CORS for all routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
    app.register_blueprint(goals_bp, url_prefix='/api/goals')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(advisor_bp, url_prefix='/api/advisor')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    # Basic routes
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'application': 'Personal Finance Advisor Bot',
            'version': '1.0.0',
            'author': 'Shubham',
            'database': 'SQLite'
        }), 200

    @app.route('/api/auth/me', methods=['GET'])
    def get_current_user():
        user = User.query.first()
        if not user:
            seed_database()
            user = User.query.first()
        return jsonify({
            'user': user.to_dict()
        }), 200

    # Initialize database tables & seed initial data if fresh
    with app.app_context():
        db.create_all()
        if not User.query.first():
            print("Fresh database detected. Seeding sample dataset...")
            seed_database()

    return app

app = create_app()

if __name__ == '__main__':
    print("Starting Personal Finance Advisor Bot Backend on port 5001...")
    app.run(host='127.0.0.1', port=5001, debug=False)
