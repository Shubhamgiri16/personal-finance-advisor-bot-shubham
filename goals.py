from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, SavingsGoal, User

goals_bp = Blueprint('goals', __name__)

@goals_bp.route('', methods=['GET'])
def get_goals():
    user = User.query.first()
    if not user:
        return jsonify([]), 200

    goals = SavingsGoal.query.filter_by(user_id=user.id).order_by(SavingsGoal.id.asc()).all()
    return jsonify([g.to_dict() for g in goals]), 200


@goals_bp.route('', methods=['POST'])
def create_goal():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    target_amount = float(data.get('target_amount', 0))
    current_amount = float(data.get('current_amount', 0))
    target_date = data.get('target_date', '')
    category = data.get('category', 'General')

    if not name or target_amount <= 0 or not target_date:
        return jsonify({'error': 'Name, valid target amount, and target date required'}), 400

    new_goal = SavingsGoal(
        user_id=user.id,
        name=name,
        target_amount=target_amount,
        current_amount=current_amount,
        target_date=target_date,
        category=category
    )
    db.session.add(new_goal)
    db.session.commit()

    return jsonify({'message': 'Goal created successfully', 'goal': new_goal.to_dict()}), 201


@goals_bp.route('/<int:goal_id>', methods=['PUT'])
def update_goal(goal_id):
    goal = SavingsGoal.query.get_or_404(goal_id)
    data = request.get_json() or {}

    if 'name' in data:
        goal.name = data['name'].strip()
    if 'target_amount' in data:
        goal.target_amount = float(data['target_amount'])
    if 'current_amount' in data:
        goal.current_amount = float(data['current_amount'])
    if 'target_date' in data:
        goal.target_date = data['target_date']
    if 'category' in data:
        goal.category = data['category']

    db.session.commit()
    return jsonify({'message': 'Goal updated successfully', 'goal': goal.to_dict()}), 200


@goals_bp.route('/<int:goal_id>/contribute', methods=['POST'])
def contribute_to_goal(goal_id):
    goal = SavingsGoal.query.get_or_404(goal_id)
    data = request.get_json() or {}
    amount = float(data.get('amount', 0))

    if amount <= 0:
        return jsonify({'error': 'Contribution amount must be greater than zero'}), 400

    goal.current_amount += amount
    db.session.commit()

    return jsonify({
        'message': f"Added ₹{amount:,.0f} to {goal.name}!",
        'goal': goal.to_dict()
    }), 200


@goals_bp.route('/<int:goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    goal = SavingsGoal.query.get_or_404(goal_id)
    db.session.delete(goal)
    db.session.commit()
    return jsonify({'message': 'Goal deleted successfully'}), 200
