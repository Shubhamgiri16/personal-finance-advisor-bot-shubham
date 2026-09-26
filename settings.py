from flask import Blueprint, request, jsonify
from models import db, User, UserSetting, Transaction, Budget, SavingsGoal
from seed_data import seed_database

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('', methods=['GET'])
def get_settings():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    setting = UserSetting.query.filter_by(user_id=user.id).first()
    if not setting:
        setting = UserSetting(user_id=user.id)
        db.session.add(setting)
        db.session.commit()

    return jsonify({
        'user': user.to_dict(),
        'settings': setting.to_dict()
    }), 200


@settings_bp.route('', methods=['PUT'])
def update_settings():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    setting = UserSetting.query.filter_by(user_id=user.id).first()
    if not setting:
        setting = UserSetting(user_id=user.id)
        db.session.add(setting)

    data = request.get_json() or {}

    if 'name' in data:
        user.name = data['name'].strip()
    if 'email' in data:
        user.email = data['email'].strip()
    if 'monthly_income' in data:
        user.monthly_income = float(data['monthly_income'])
        setting.monthly_income = float(data['monthly_income'])
    if 'currency' in data:
        user.currency = data['currency'].strip()
        setting.currency = data['currency'].strip()
    if 'notification_email' in data:
        setting.notification_email = bool(data['notification_email'])
    if 'budget_alerts' in data:
        setting.budget_alerts = bool(data['budget_alerts'])
    if 'theme' in data:
        setting.theme = data['theme']
    if 'alert_threshold_percent' in data:
        setting.alert_threshold_percent = int(data['alert_threshold_percent'])

    db.session.commit()
    return jsonify({
        'message': 'Settings updated successfully',
        'user': user.to_dict(),
        'settings': setting.to_dict()
    }), 200


@settings_bp.route('/reset', methods=['POST'])
def reset_data():
    """Reset to clean initial sample state with Shubham's data"""
    seed_database()
    return jsonify({'message': 'Financial data reset to initial demo state successfully'}), 200


@settings_bp.route('/clear', methods=['POST'])
def clear_all_data():
    """Clear all transactions, budgets and goals except user profile"""
    user = User.query.first()
    if user:
        Transaction.query.filter_by(user_id=user.id).delete()
        Budget.query.filter_by(user_id=user.id).delete()
        SavingsGoal.query.filter_by(user_id=user.id).delete()
        db.session.commit()
    return jsonify({'message': 'All financial activity data cleared successfully'}), 200
