import re
from datetime import datetime
from sqlalchemy import func
from models import db, User, Transaction, Budget, SavingsGoal

def get_current_month():
    return datetime.now().strftime('%Y-%m')

def calculate_financial_health_score(user_id, month=None):
    if not month:
        month = get_current_month()
        
    user = User.query.get(user_id)
    if not user:
        return {'score': 70, 'rating': 'Good', 'message': 'No user profile found.'}

    # 1. Calculate Income & Expenses for the month
    income_txs = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.type == 'income',
        Transaction.date.startswith(month)
    ).all()
    total_income = sum(t.amount for t in income_txs)
    
    # Fallback to monthly_income setting if no income tx recorded for the month
    if total_income == 0 and user.monthly_income:
        total_income = user.monthly_income

    expense_txs = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date.startswith(month)
    ).all()
    total_expenses = sum(t.amount for t in expense_txs)
    total_savings = max(total_income - total_expenses, 0)
    savings_rate = (total_savings / total_income * 100) if total_income > 0 else 0
    expense_ratio = (total_expenses / total_income * 100) if total_income > 0 else 100

    # 2. Savings Rate Factor (max 30 pts)
    # Target savings rate: > 30% gets full 30 pts
    if savings_rate >= 35:
        sr_score = 30
    elif savings_rate >= 25:
        sr_score = 25
    elif savings_rate >= 15:
        sr_score = 18
    elif savings_rate >= 5:
        sr_score = 10
    else:
        sr_score = 4

    # 3. Expense to Income Ratio Factor (max 25 pts)
    # Target: <= 50% gets 25 pts, <= 70% gets 20 pts
    if expense_ratio <= 50:
        er_score = 25
    elif expense_ratio <= 65:
        er_score = 20
    elif expense_ratio <= 80:
        er_score = 14
    elif expense_ratio <= 95:
        er_score = 8
    else:
        er_score = 2

    # 4. Budget Discipline Factor (max 25 pts)
    budgets = Budget.query.filter_by(user_id=user_id, month=month).all()
    if not budgets:
        # Check if there are default budgets
        budgets = Budget.query.filter_by(user_id=user_id).all()
        
    if budgets:
        budget_scores = []
        for b in budgets:
            cat_spent = sum(t.amount for t in expense_txs if t.category.lower() == b.category.lower())
            if cat_spent <= b.amount:
                budget_scores.append(1.0)
            elif cat_spent <= b.amount * 1.15:
                budget_scores.append(0.6)
            else:
                budget_scores.append(0.2)
        bd_score = round(sum(budget_scores) / len(budget_scores) * 25)
    else:
        bd_score = 18  # default neutral score

    # 5. Financial Goals Progress Factor (max 20 pts)
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()
    if goals:
        avg_progress = sum(min(g.current_amount / g.target_amount, 1.0) for g in goals if g.target_amount > 0) / len(goals)
        fg_score = round(avg_progress * 20)
    else:
        fg_score = 12

    total_score = min(max(sr_score + er_score + bd_score + fg_score, 0), 100)

    # Narrative message
    if total_score >= 85:
        rating = "Excellent"
        message = "Your financial health is outstanding! You have exceptional savings discipline and balanced spending habits."
    elif total_score >= 75:
        rating = "Strong"
        message = "Your financial health is strong. Keep maintaining your current savings discipline."
    elif total_score >= 60:
        rating = "Moderate"
        message = "Your financial health is stable, but there is clear room to optimize discretionary spending."
    else:
        rating = "Needs Attention"
        message = "Warning: High expense-to-income ratio or budget overruns detected. Focus on curbing non-essential expenses."

    return {
        'score': total_score,
        'rating': rating,
        'message': message,
        'savings_rate': round(savings_rate, 1),
        'expense_ratio': round(expense_ratio, 1),
        'breakdown': {
            'savings_rate_score': {'score': sr_score, 'max': 30, 'label': 'Savings Rate'},
            'expense_ratio_score': {'score': er_score, 'max': 25, 'label': 'Expense Discipline'},
            'budget_discipline_score': {'score': bd_score, 'max': 25, 'label': 'Budget Adherence'},
            'goals_progress_score': {'score': fg_score, 'max': 20, 'label': 'Goal Progress'}
        },
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_savings': total_savings
    }


def generate_advice_cards(user_id, month=None):
    if not month:
        month = get_current_month()

    currency = "₹"
    user = User.query.get(user_id)
    if user and user.currency:
        currency = user.currency

    # Fetch expenses for current month
    expense_txs = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date.startswith(month)
    ).all()
    total_expenses = sum(t.amount for t in expense_txs)

    income_txs = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.type == 'income',
        Transaction.date.startswith(month)
    ).all()
    total_income = sum(t.amount for t in income_txs)
    if total_income == 0 and user and user.monthly_income:
        total_income = user.monthly_income

    # Category breakdown
    category_totals = {}
    for tx in expense_txs:
        category_totals[tx.category] = category_totals.get(tx.category, 0) + tx.amount

    cards = []

    # 1. Saving Opportunity Card
    discretionary_categories = ['Shopping', 'Entertainment', 'Food', 'Other']
    discretionary_sum = sum(category_totals.get(cat, 0) for cat in discretionary_categories)
    potential_savings = round(discretionary_sum * 0.25) if discretionary_sum > 0 else 3500

    cards.append({
        'id': 'saving-opp',
        'type': 'saving',
        'title': '💰 Saving Opportunity',
        'subtitle': 'Discretionary Optimization',
        'content': f"You could potentially save {currency}{potential_savings:,.0f} this month by reducing discretionary spending in Shopping and Entertainment.",
        'badge': 'High Impact',
        'action_label': 'Review Discretionary Spend',
        'action_link': '/expenses'
    })

    # 2. Spending Insight Card
    if category_totals and total_expenses > 0:
        top_cat = max(category_totals.items(), key=lambda x: x[1])
        pct = round((top_cat[1] / total_expenses) * 100)
        cards.append({
            'id': 'spending-insight',
            'type': 'insight',
            'title': '📊 Spending Insight',
            'subtitle': 'Category Allocation',
            'content': f"{top_cat[0]} represents {pct}% of your total expenses ({currency}{top_cat[1]:,.0f}).",
            'badge': f"{pct}% of Total",
            'action_label': 'View Category Breakdown',
            'action_link': '/expenses'
        })
    else:
        cards.append({
            'id': 'spending-insight',
            'type': 'insight',
            'title': '📊 Spending Insight',
            'subtitle': 'Category Allocation',
            'content': "Food represents 22% of your total expenses.",
            'badge': 'Balanced',
            'action_label': 'View Expenses',
            'action_link': '/expenses'
        })

    # 3. Goal Progress Card
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()
    if goals:
        # Find active incomplete goal or highest progress
        active_goal = next((g for g in goals if g.current_amount < g.target_amount), goals[0])
        progress = round((active_goal.current_amount / active_goal.target_amount * 100), 1) if active_goal.target_amount > 0 else 0
        cards.append({
            'id': 'goal-progress',
            'type': 'goal',
            'title': '🎯 Goal Progress',
            'subtitle': active_goal.name,
            'content': f"You're {progress:.0f}% of the way toward your {active_goal.name} savings goal ({currency}{active_goal.current_amount:,.0f} / {currency}{active_goal.target_amount:,.0f}).",
            'badge': f"{progress:.0f}% Reached",
            'action_label': 'Add Funds to Goal',
            'action_link': '/goals'
        })
    else:
        cards.append({
            'id': 'goal-progress',
            'type': 'goal',
            'title': '🎯 Goal Progress',
            'subtitle': 'Financial Milestone',
            'content': "You're 58% of the way toward your laptop savings goal.",
            'badge': '58% Reached',
            'action_label': 'Create Goal',
            'action_link': '/goals'
        })

    # 4. Budget Alert Card
    budgets = Budget.query.filter_by(user_id=user_id).all()
    exceeded_budgets = []
    near_budgets = []
    for b in budgets:
        spent = category_totals.get(b.category, 0)
        if spent > b.amount:
            exceeded_budgets.append((b.category, spent, b.amount, spent - b.amount))
        elif spent >= b.amount * 0.85:
            near_budgets.append((b.category, spent, b.amount))

    if exceeded_budgets:
        top_ex = exceeded_budgets[0]
        cards.append({
            'id': 'budget-alert',
            'type': 'alert',
            'title': '⚠️ Budget Alert',
            'subtitle': f'{top_ex[0]} Exceeded',
            'content': f"{top_ex[0]} expenses ({currency}{top_ex[1]:,.0f}) have exceeded your monthly budget of {currency}{top_ex[2]:,.0f} by {currency}{top_ex[3]:,.0f}.",
            'badge': 'Over Budget',
            'action_label': 'Adjust Budget',
            'action_link': '/budgets'
        })
    elif near_budgets:
        top_near = near_budgets[0]
        cards.append({
            'id': 'budget-alert',
            'type': 'warning',
            'title': '⚠️ Budget Alert',
            'subtitle': f'{top_near[0]} Near Limit',
            'content': f"{top_near[0]} expenses ({currency}{top_near[1]:,.0f}) have reached {round(top_near[1]/top_near[2]*100)}% of your monthly limit.",
            'badge': 'Approaching Limit',
            'action_label': 'Monitor Budget',
            'action_link': '/budgets'
        })
    else:
        cards.append({
            'id': 'budget-alert',
            'type': 'success',
            'title': '✅ Budget Health',
            'subtitle': 'All Targets Safe',
            'content': "All your monthly expense categories are well within their planned budget allocations. Keep it up!",
            'badge': 'On Track',
            'action_label': 'View Budgets',
            'action_link': '/budgets'
        })

    return cards


def chat_with_advisor(user_id, message):
    """
    Intelligent rule-based AI Financial Advisor engine in Python.
    Analyzes live SQLite user data and generates personalized, dynamic answers.
    """
    msg_clean = message.lower().strip()
    month = get_current_month()
    user = User.query.get(user_id)
    currency = user.currency if user else "₹"
    
    # Live stats
    health_data = calculate_financial_health_score(user_id, month)
    score = health_data['score']
    rating = health_data['rating']
    total_income = health_data['total_income']
    total_expenses = health_data['total_expenses']
    total_savings = health_data['total_savings']
    savings_rate = health_data['savings_rate']

    # Transactions & categories
    expense_txs = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.date.startswith(month)
    ).all()
    
    category_totals = {}
    for tx in expense_txs:
        category_totals[tx.category] = category_totals.get(tx.category, 0) + tx.amount

    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    top_cat = sorted_categories[0] if sorted_categories else ("None", 0)

    # Budgets
    budgets = Budget.query.filter_by(user_id=user_id).all()
    exceeded = []
    for b in budgets:
        spent = category_totals.get(b.category, 0)
        if spent > b.amount:
            exceeded.append((b.category, spent, b.amount, spent - b.amount))

    # Goals
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()

    # Rule matching and query parsing:

    # 1. Saving advice / How to save more
    if any(k in msg_clean for k in ['save more', 'save money', 'saving opportunity', 'how to save', 'cut cost', 'cut expenses', 'increase savings']):
        high_discretionary = []
        for cat, amt in sorted_categories:
            if cat in ['Shopping', 'Food', 'Entertainment', 'Other']:
                high_discretionary.append((cat, amt))
        
        disc_text = ""
        potential = 0
        if high_discretionary:
            for cat, amt in high_discretionary:
                cut = round(amt * 0.25)
                potential += cut
                disc_text += f"- **{cat}**: Currently {currency}{amt:,.0f}. Aim to trim by 20-30% (~{currency}{cut:,.0f}).\n"
        else:
            disc_text = f"- **Discretionary Purchases**: Keep non-essential spending under 15% of your income.\n"
            potential = 3500

        budget_suggestion = ""
        if exceeded:
            ex_names = ", ".join([f"{e[0]} (over by {currency}{e[3]:,.0f})" for e in exceeded])
            budget_suggestion = f"\n⚠️ **Immediate Priority**: You have overspent in {ex_names}. Cap further spending in these categories immediately."

        response = (
            f"### 💡 Personalized Savings Strategy for {datetime.now().strftime('%B %Y')}\n\n"
            f"Based on your current spending, your **{top_cat[0]}** ({currency}{top_cat[1]:,.0f}) and other discretionary expenses represent a major portion of your outflow.\n\n"
            f"Here is your actionable plan to save an extra **{currency}{potential:,.0f}** this month:\n\n"
            f"{disc_text}\n"
            f"**Action Steps:**\n"
            f"1. **Enforce Budget Caps**: Set a strict ceiling for flexible categories like Food and Shopping.\n"
            f"2. **The 48-Hour Rule**: Wait 48 hours before any non-essential purchase over {currency}1,000.\n"
            f"3. **Automate Transfers**: Transfer your target savings of **{currency}{round(total_income * 0.2):,.0f}** immediately on payday rather than saving what's left over.{budget_suggestion}"
        )
        return response

    # 2. Health Score questions
    if any(k in msg_clean for k in ['health score', 'financial health', 'score', 'rating', 'how healthy']):
        bd = health_data['breakdown']
        response = (
            f"### 🏥 Financial Health Score Analysis: **{score}/100** ({rating})\n\n"
            f"{health_data['message']}\n\n"
            f"**Detailed Breakdown:**\n"
            f"- **Savings Rate**: {savings_rate}% → Score: {bd['savings_rate_score']['score']}/{bd['savings_rate_score']['max']} pts\n"
            f"- **Expense Discipline**: {health_data['expense_ratio']}% of income → Score: {bd['expense_ratio_score']['score']}/{bd['expense_ratio_score']['max']} pts\n"
            f"- **Budget Adherence**: Score: {bd['budget_discipline_score']['score']}/{bd['budget_discipline_score']['max']} pts\n"
            f"- **Goal Milestones**: Score: {bd['goals_progress_score']['score']}/{bd['goals_progress_score']['max']} pts\n\n"
            f"**To reach 85+ (Excellent):**\n"
            f"- Keep your expense-to-income ratio below 60%.\n"
            f"- Eliminate budget overruns in categories like {exceeded[0][0] if exceeded else 'Shopping'}."
        )
        return response

    # 3. Budget & 50/30/20 Rule
    if any(k in msg_clean for k in ['budget', '50/30/20', 'rule', 'over budget', 'limits']):
        needs_cats = ['Rent', 'Bills', 'Healthcare', 'Education']
        wants_cats = ['Shopping', 'Food', 'Entertainment', 'Transport', 'Other']
        needs_amt = sum(category_totals.get(c, 0) for c in needs_cats)
        wants_amt = sum(category_totals.get(c, 0) for c in wants_cats)
        
        needs_pct = round((needs_amt / total_income * 100), 1) if total_income > 0 else 0
        wants_pct = round((wants_amt / total_income * 100), 1) if total_income > 0 else 0

        alert_text = ""
        if exceeded:
            alert_text = "\n\n⚠️ **Active Overruns:**\n" + "\n".join([f"- **{e[0]}**: Spent {currency}{e[1]:,.0f} vs Budget {currency}{e[2]:,.0f} (+{currency}{e[3]:,.0f})" for e in exceeded])

        response = (
            f"### 📊 50/30/20 Rule & Budget Audit\n\n"
            f"For your monthly income of **{currency}{total_income:,.0f}**, here is how your current spending aligns with gold-standard financial rules:\n\n"
            f"- **Needs (Target ≤ 50%)**: {currency}{needs_amt:,.0f} (**{needs_pct}%** of income) - {'✅ Great' if needs_pct <= 50 else '⚠️ High'}\n"
            f"- **Wants (Target ≤ 30%)**: {currency}{wants_amt:,.0f} (**{wants_pct}%** of income) - {'✅ Healthy' if wants_pct <= 30 else '⚠️ Exceeding guideline'}\n"
            f"- **Savings & Debt (Target ≥ 20%)**: {currency}{total_savings:,.0f} (**{savings_rate}%** of income) - {'✅ Outstanding' if savings_rate >= 20 else '⚠️ Below target'}"
            f"{alert_text}\n\n"
            f"**Recommendation**: Regularly review your Budget Planner page to lock limits before the 15th of each month."
        )
        return response

    # 4. Spending Summary / Where did money go?
    if any(k in msg_clean for k in ['where did', 'spend', 'spending', 'highest', 'summary', 'overview', 'breakdown', 'expenses']):
        cat_lines = ""
        for cat, amt in sorted_categories[:5]:
            pct = round((amt / total_expenses * 100), 1) if total_expenses > 0 else 0
            cat_lines += f"- **{cat}**: {currency}{amt:,.0f} ({pct}%)\n"

        response = (
            f"### 💳 Spending Summary for {datetime.now().strftime('%B %Y')}\n\n"
            f"- **Total Income**: {currency}{total_income:,.0f}\n"
            f"- **Total Expenses**: {currency}{total_expenses:,.0f}\n"
            f"- **Net Savings**: {currency}{total_savings:,.0f} (Savings Rate: **{savings_rate}%**)\n\n"
            f"**Top Spending Categories:**\n{cat_lines}\n"
            f"Your single largest outflow is **{top_cat[0]}** at {currency}{top_cat[1]:,.0f}. Daily spending averages roughly **{currency}{round(total_expenses / max(datetime.now().day, 1)):,.0f}/day**."
        )
        return response

    # 5. Goal progress / Laptop / Emergency Fund
    if any(k in msg_clean for k in ['goal', 'laptop', 'emergency fund', 'target', 'milestone']):
        if goals:
            goal_lines = ""
            for g in goals:
                prog = round((g.current_amount / g.target_amount * 100), 1) if g.target_amount > 0 else 0
                rem = max(g.target_amount - g.current_amount, 0)
                months_needed = round(rem / max(total_savings, 1000), 1) if total_savings > 0 else "N/A"
                goal_lines += (
                    f"**{g.name}**\n"
                    f"- Saved: {currency}{g.current_amount:,.0f} / {currency}{g.target_amount:,.0f} ({prog}%)\n"
                    f"- Remaining: {currency}{rem:,.0f} (~{months_needed} months at current savings rate)\n\n"
                )
            response = (
                f"### 🎯 Savings Goals Status\n\n"
                f"{goal_lines}"
                f"**Tip**: You have {currency}{total_savings:,.0f} in surplus this month. Contributing an extra {currency}5,000 will shave weeks off your timeline!"
            )
        else:
            response = "You don't have any active savings goals yet. Head over to the **Savings Goals** tab to set targets for a Laptop, Vacation, or Emergency Fund!"
        return response

    # 6. Affordability check (e.g., "Can I afford...")
    numbers_found = re.findall(r'(\d+[\d,]*)', msg_clean)
    if 'afford' in msg_clean or 'buy' in msg_clean:
        cost = 15000  # default
        if numbers_found:
            cost = float(numbers_found[0].replace(',', ''))
        
        can_afford = total_savings >= cost
        remaining_after = total_savings - cost

        if can_afford:
            response = (
                f"### 🛒 Affordability Assessment for {currency}{cost:,.0f}\n\n"
                f"**Verdict**: ✅ **Yes, you can afford it from your current month's savings.**\n\n"
                f"- Current Monthly Savings Buffer: **{currency}{total_savings:,.0f}**\n"
                f"- Remaining Buffer after purchase: **{currency}{remaining_after:,.0f}**\n\n"
                f"**Advisor Advice**: Ensure you do not touch your Emergency Fund for discretionary purchases. If this is a 'want', verify if it delays your active goals."
            )
        else:
            response = (
                f"### 🛒 Affordability Assessment for {currency}{cost:,.0f}\n\n"
                f"**Verdict**: ⚠️ **Not recommended right now.**\n\n"
                f"- Your current available monthly surplus is **{currency}{total_savings:,.0f}**, which is {currency}{cost - total_savings:,.0f} short.\n"
                f"- Consider creating a dedicated **Savings Goal** for this item and setting aside {currency}{round(cost / 3):,.0f}/month over the next 3 months."
            )
        return response

    # 7. Default comprehensive advisor response
    response = (
        f"### 🤖 AI Financial Advisor at your service, {user.name if user else 'Shubham'}!\n\n"
        f"Here is your current financial pulse:\n"
        f"- **Monthly Income**: {currency}{total_income:,.0f}\n"
        f"- **Current Spending**: {currency}{total_expenses:,.0f} ({health_data['expense_ratio']}% of income)\n"
        f"- **Monthly Surplus**: {currency}{total_savings:,.0f} (Savings Rate: **{savings_rate}%**)\n"
        f"- **Financial Health Score**: **{score}/100** ({rating})\n\n"
        f"You can ask me questions like:\n"
        f"1. *\"How can I save more money this month?\"*\n"
        f"2. *\"What is my financial health score and how can I improve it?\"*\n"
        f"3. *\"Check my 50/30/20 budget breakdown.\"*\n"
        f"4. *\"Can I afford a purchase of {currency}12,000?\"*\n"
        f"5. *\"How are my savings goals progressing?\"*"
    )
    return response
