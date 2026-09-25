from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Shubham")
    email = db.Column(db.String(120), nullable=False, default="shubham@example.com")
    monthly_income = db.Column(db.Float, nullable=False, default=50000.0)
    currency = db.Column(db.String(10), nullable=False, default="₹")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade="all, delete-orphan")
    goals = db.relationship('SavingsGoal', backref='user', lazy=True, cascade="all, delete-orphan")
    settings = db.relationship('UserSetting', backref='user', uselist=False, lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'monthly_income': self.monthly_income,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.String(10), nullable=False)  # 'YYYY-MM-DD'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'category': self.category,
            'amount': self.amount,
            'description': self.description or '',
            'date': self.date,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)  # 'YYYY-MM'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'amount': self.amount,
            'month': self.month
        }


class SavingsGoal(db.Model):
    __tablename__ = 'savings_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0.0)
    target_date = db.Column(db.String(10), nullable=False)  # 'YYYY-MM-DD'
    category = db.Column(db.String(50), default="General")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        progress = round((self.current_amount / self.target_amount * 100), 1) if self.target_amount > 0 else 0
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'target_date': self.target_date,
            'category': self.category,
            'progress': min(progress, 100.0),
            'remaining_amount': max(self.target_amount - self.current_amount, 0),
            'is_completed': self.current_amount >= self.target_amount,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserSetting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    currency = db.Column(db.String(10), default="₹")
    monthly_income = db.Column(db.Float, default=50000.0)
    notification_email = db.Column(db.Boolean, default=True)
    budget_alerts = db.Column(db.Boolean, default=True)
    theme = db.Column(db.String(20), default="dark")  # 'dark' or 'light'
    alert_threshold_percent = db.Column(db.Integer, default=85)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'currency': self.currency,
            'monthly_income': self.monthly_income,
            'notification_email': self.notification_email,
            'budget_alerts': self.budget_alerts,
            'theme': self.theme,
            'alert_threshold_percent': self.alert_threshold_percent
        }
