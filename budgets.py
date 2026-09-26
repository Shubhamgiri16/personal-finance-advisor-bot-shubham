from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Budget, Transaction, User

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('', methods=['GET'])
def get_budgets():
    user = User.query.first()
    if not user:
        return jsonify([]), 200

    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    budgets = Budget.query.filter_by(user_id=user.id, month=month).all()

    # If no budgets for this specific month, check if there are default budgets
    if not budgets:
        budgets = Budget.query.filter_by(user_id=user.id).all()

    # Fetch expenses for this month to calculate spent & remaining
    expense_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == 'expense',
        Transaction.date.startswith(month)
    ).all()

    spent_by_category = {}
    for tx in expense_txs:
        cat_key = tx.category.lower()
        spent_by_category[cat_key] = spent_by_category.get(cat_key, 0) + tx.amount

    result = []
    total_budgeted = 0
    total_spent = 0

    for b in budgets:
        spent = spent_by_category.get(b.category.lower(), 0)
        remaining = b.amount - spent
        pct = round((spent / b.amount * 100), 1) if b.amount > 0 else 0
        is_exceeded = spent > b.amount
        is_warning = (spent >= b.amount * 0.85) and not is_exceeded

        total_budgeted += b.amount
        total_spent += spent

        result.append({
            'id': b.id,
            'category': b.category,
            'amount': b.amount,
            'spent': spent,
            'remaining': remaining,
            'percentage': pct,
            'is_exceeded': is_exceeded,
            'is_warning': is_warning,
            'month': b.month,
            'alert_message': f"⚠️ You have exceeded your {b.category} budget by {user.currency}{abs(remaining):,.0f}." if is_exceeded else None
        })

    return jsonify({
        'budgets': result,
        'summary': {
            'total_budgeted': total_budgeted,
            'total_spent': total_spent,
            'total_remaining': total_budgeted - total_spent,
            'overall_percentage': round((total_spent / total_budgeted * 100), 1) if total_budgeted > 0 else 0,
            'exceeded_count': sum(1 for item in result if item['is_exceeded'])
        }
    }), 200


@budgets_bp.route('', methods=['POST'])
def create_or_update_budget():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    category = data.get('category', '').strip()
    amount = float(data.get('amount', 0))
    month = data.get('month', datetime.now().strftime('%Y-%m'))

    if not category or amount <= 0:
        return jsonify({'error': 'Valid category and amount required'}), 400

    existing = Budget.query.filter_by(user_id=user.id, category=category, month=month).first()
    if existing:
        existing.amount = amount
        db.session.commit()
        return jsonify({'message': 'Budget updated', 'budget': existing.to_dict()}), 200

    new_budget = Budget(
        user_id=user.id,
        category=category,
        amount=amount,
        month=month
    )
    db.session.add(new_budget)
    db.session.commit()

    return jsonify({'message': 'Budget created', 'budget': new_budget.to_dict()}), 201


@budgets_bp.route('/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Budget deleted successfully'}), 200
