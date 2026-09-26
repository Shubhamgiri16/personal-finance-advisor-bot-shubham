from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, Transaction, Budget, SavingsGoal, User
from ai_advisor import calculate_financial_health_score, generate_advice_cards

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'No user found'}), 404

    month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    # Current month income
    income_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == 'income',
        Transaction.date.startswith(month)
    ).all()
    total_income = sum(t.amount for t in income_txs)
    if total_income == 0 and user.monthly_income:
        total_income = user.monthly_income

    # Current month expenses
    expense_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == 'expense',
        Transaction.date.startswith(month)
    ).all()
    total_expenses = sum(t.amount for t in expense_txs)
    total_savings = max(total_income - total_expenses, 0)
    savings_rate = round((total_savings / total_income * 100), 1) if total_income > 0 else 0

    # Financial Health Score
    health_data = calculate_financial_health_score(user.id, month)

    # Category breakdown for donut chart
    category_totals = {}
    for tx in expense_txs:
        category_totals[tx.category] = category_totals.get(tx.category, 0) + tx.amount

    category_breakdown = []
    # Distinct colors for categories
    category_colors = {
        'Rent': '#6366F1',       # Indigo
        'Food': '#F59E0B',       # Amber
        'Shopping': '#EC4899',   # Pink
        'Transport': '#06B6D4',  # Cyan
        'Bills': '#3B82F6',      # Blue
        'Entertainment': '#8B5CF6', # Purple
        'Healthcare': '#10B981', # Emerald
        'Education': '#F97316',  # Orange
        'Other': '#64748B'       # Slate
    }

    for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = round((amt / total_expenses * 100), 1) if total_expenses > 0 else 0
        category_breakdown.append({
            'name': cat,
            'amount': amt,
            'percentage': pct,
            'color': category_colors.get(cat, '#94A3B8')
        })

    # Recent transactions (top 5)
    recent_txs = Transaction.query.filter_by(user_id=user.id)\
        .order_by(Transaction.date.desc(), Transaction.id.desc())\
        .limit(6).all()

    # Advice cards
    advice_cards = generate_advice_cards(user.id, month)

    return jsonify({
        'user': {
            'name': user.name,
            'email': user.email,
            'currency': user.currency,
            'monthly_income': user.monthly_income
        },
        'summary': {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'total_savings': total_savings,
            'savings_rate': savings_rate,
            'currency': user.currency
        },
        'health_score': health_data,
        'category_breakdown': category_breakdown,
        'recent_transactions': [t.to_dict() for t in recent_txs],
        'advice_cards': advice_cards
    }), 200


@analytics_bp.route('/trends', methods=['GET'])
def get_trends():
    user = User.query.first()
    if not user:
        return jsonify([]), 200

    period = request.args.get('period', '6m')
    today = datetime.now()

    if period == '7d':
        # Past 7 days
        points = []
        for i in range(6, -1, -1):
            day_dt = today - timedelta(days=i)
            day_str = day_dt.strftime('%Y-%m-%d')
            day_label = day_dt.strftime('%a %d')

            income = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
                .filter(Transaction.user_id == user.id, Transaction.type == 'income', Transaction.date == day_str).scalar()
            expenses = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
                .filter(Transaction.user_id == user.id, Transaction.type == 'expense', Transaction.date == day_str).scalar()

            points.append({
                'label': day_label,
                'date': day_str,
                'income': float(income),
                'expenses': float(expenses),
                'savings': float(income - expenses)
            })
        return jsonify(points), 200

    elif period == '30d':
        # Past 30 days grouped in 5-day intervals or daily
        points = []
        for i in range(29, -1, -3):
            day_start = today - timedelta(days=i)
            day_end = today - timedelta(days=max(i-2, 0))
            start_str = day_start.strftime('%Y-%m-%d')
            end_str = day_end.strftime('%Y-%m-%d')
            label = day_start.strftime('%d %b')

            income = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
                .filter(Transaction.user_id == user.id, Transaction.type == 'income', Transaction.date >= start_str, Transaction.date <= end_str).scalar()
            expenses = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
                .filter(Transaction.user_id == user.id, Transaction.type == 'expense', Transaction.date >= start_str, Transaction.date <= end_str).scalar()

            points.append({
                'label': label,
                'date': start_str,
                'income': float(income),
                'expenses': float(expenses),
                'savings': float(income - expenses)
            })
        return jsonify(points), 200

    else:
        # Monthly points (6m or 12m)
        months_count = 12 if period == '12m' else 6
        points = []
        for i in range(months_count - 1, -1, -1):
            target_dt = today - timedelta(days=i * 30)
            m_str = target_dt.strftime('%Y-%m')
            label = target_dt.strftime('%b %Y')

            income = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
                .filter(Transaction.user_id == user.id, Transaction.type == 'income', Transaction.date.startswith(m_str)).scalar()
            expenses = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
                .filter(Transaction.user_id == user.id, Transaction.type == 'expense', Transaction.date.startswith(m_str)).scalar()

            if float(income) == 0 and i == 0:
                income = user.monthly_income

            points.append({
                'label': label,
                'month': m_str,
                'income': float(income),
                'expenses': float(expenses),
                'savings': float(income - expenses)
            })
        return jsonify(points), 200


@analytics_bp.route('/expenses', methods=['GET'])
def get_expense_analysis():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'No user found'}), 404

    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    today = datetime.now()

    # Expenses this month
    expense_txs = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.type == 'expense',
        Transaction.date.startswith(month)
    ).all()

    total_monthly_expenses = sum(t.amount for t in expense_txs)
    current_day = max(today.day if today.strftime('%Y-%m') == month else 30, 1)
    avg_daily_spending = round(total_monthly_expenses / current_day, 1)

    # Category totals & counts
    category_stats = {}
    day_of_week_spend = {'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0}

    for tx in expense_txs:
        if tx.category not in category_stats:
            category_stats[tx.category] = {'total': 0.0, 'count': 0}
        category_stats[tx.category]['total'] += tx.amount
        category_stats[tx.category]['count'] += 1

        try:
            tx_dt = datetime.strptime(tx.date, '%Y-%m-%d')
            dow_name = tx_dt.strftime('%a')
            if dow_name in day_of_week_spend:
                day_of_week_spend[dow_name] += tx.amount
        except Exception:
            pass

    sorted_categories = sorted(category_stats.items(), key=lambda x: x[1]['total'], reverse=True)

    highest_category = {
        'name': sorted_categories[0][0] if sorted_categories else 'N/A',
        'amount': sorted_categories[0][1]['total'] if sorted_categories else 0
    }
    lowest_category = {
        'name': sorted_categories[-1][0] if sorted_categories else 'N/A',
        'amount': sorted_categories[-1][1]['total'] if sorted_categories else 0
    }

    # Month over month calculation
    prev_month_dt = today - timedelta(days=32)
    prev_month_str = prev_month_dt.strftime('%Y-%m')
    prev_month_expenses = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
        .filter(Transaction.user_id == user.id, Transaction.type == 'expense', Transaction.date.startswith(prev_month_str)).scalar()
    prev_expenses = float(prev_month_expenses)

    mom_change_pct = 0.0
    if prev_expenses > 0:
        mom_change_pct = round(((total_monthly_expenses - prev_expenses) / prev_expenses * 100), 1)

    category_breakdown = []
    for cat, data in sorted_categories:
        pct = round((data['total'] / total_monthly_expenses * 100), 1) if total_monthly_expenses > 0 else 0
        avg_per_tx = round(data['total'] / data['count'], 1) if data['count'] > 0 else 0
        category_breakdown.append({
            'category': cat,
            'total': data['total'],
            'count': data['count'],
            'percentage': pct,
            'average_per_transaction': avg_per_tx
        })

    day_of_week_list = [{'day': k, 'amount': v} for k, v in day_of_week_spend.items()]

    return jsonify({
        'total_monthly_expenses': total_monthly_expenses,
        'average_daily_spending': avg_daily_spending,
        'highest_spending_category': highest_category,
        'lowest_spending_category': lowest_category,
        'month_over_month_change_pct': mom_change_pct,
        'previous_month_expenses': prev_expenses,
        'category_breakdown': category_breakdown,
        'day_of_week_distribution': day_of_week_list
    }), 200
