from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Transaction, User

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('', methods=['GET'])
def get_transactions():
    user = User.query.first()
    if not user:
        return jsonify([]), 200

    query = Transaction.query.filter_by(user_id=user.id)

    # Filtering
    tx_type = request.args.get('type')
    category = request.args.get('category')
    search = request.args.get('search')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    limit = request.args.get('limit', type=int)

    if tx_type and tx_type != 'all':
        query = query.filter_by(type=tx_type.lower())
    if category and category != 'all':
        query = query.filter_by(category=category)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            (Transaction.description.ilike(search_fmt)) | 
            (Transaction.category.ilike(search_fmt))
        )
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    query = query.order_by(Transaction.date.desc(), Transaction.id.desc())

    if limit:
        txs = query.limit(limit).all()
    else:
        txs = query.all()

    return jsonify([t.to_dict() for t in txs]), 200


@transactions_bp.route('', methods=['POST'])
def add_transaction():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    tx_type = data.get('type', 'expense').lower()
    category = data.get('category', 'Other').strip()
    amount = float(data.get('amount', 0))
    description = data.get('description', '').strip()
    tx_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))

    if amount <= 0:
        return jsonify({'error': 'Amount must be greater than zero'}), 400

    new_tx = Transaction(
        user_id=user.id,
        type=tx_type,
        category=category,
        amount=amount,
        description=description,
        date=tx_date
    )
    db.session.add(new_tx)
    db.session.commit()

    return jsonify({
        'message': 'Transaction recorded successfully',
        'transaction': new_tx.to_dict()
    }), 201


@transactions_bp.route('/<int:tx_id>', methods=['PUT'])
def update_transaction(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
    data = request.get_json() or {}

    if 'type' in data:
        tx.type = data['type'].lower()
    if 'category' in data:
        tx.category = data['category'].strip()
    if 'amount' in data:
        tx.amount = float(data['amount'])
    if 'description' in data:
        tx.description = data['description'].strip()
    if 'date' in data:
        tx.date = data['date']

    db.session.commit()
    return jsonify({'message': 'Transaction updated', 'transaction': tx.to_dict()}), 200


@transactions_bp.route('/<int:tx_id>', methods=['DELETE'])
def delete_transaction(tx_id):
    tx = Transaction.query.get_or_404(tx_id)
    db.session.delete(tx)
    db.session.commit()
    return jsonify({'message': 'Transaction deleted successfully'}), 200
