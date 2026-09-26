from flask import Blueprint, request, jsonify
from datetime import datetime
from models import User
from ai_advisor import chat_with_advisor, generate_advice_cards

advisor_bp = Blueprint('advisor', __name__)

@advisor_bp.route('/cards', methods=['GET'])
def get_advisor_cards():
    user = User.query.first()
    if not user:
        return jsonify([]), 200

    month = request.args.get('month')
    cards = generate_advice_cards(user.id, month)
    return jsonify(cards), 200


@advisor_bp.route('/chat', methods=['POST'])
def chat():
    user = User.query.first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    reply = chat_with_advisor(user.id, message)

    return jsonify({
        'reply': reply,
        'timestamp': datetime.now().isoformat(),
        'user_name': user.name
    }), 200


@advisor_bp.route('/quick-prompts', methods=['GET'])
def get_quick_prompts():
    prompts = [
        "How can I save more money this month?",
        "What is my financial health score and how can I improve it?",
        "Where did most of my money go this month?",
        "Check my 50/30/20 budget breakdown.",
        "Can I afford to buy a gadget for ₹15,000?",
        "How long will it take to reach my laptop goal?"
    ]
    return jsonify(prompts), 200
