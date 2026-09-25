from datetime import datetime, timedelta
from models import db, User, Transaction, Budget, SavingsGoal, UserSetting

def seed_database():
    # Clear existing
    db.drop_all()
    db.create_all()

    # 1. Create Default User: Shubham
    user = User(
        name="Shubham",
        email="shubham@example.com",
        monthly_income=50000.0,
        currency="₹"
    )
    db.session.add(user)
    db.session.commit()

    # 2. Create User Settings
    settings = UserSetting(
        user_id=user.id,
        currency="₹",
        monthly_income=50000.0,
        notification_email=True,
        budget_alerts=True,
        theme="dark",
        alert_threshold_percent=85
    )
    db.session.add(settings)

    # Calculate dates relative to today
    today = datetime.now()
    cur_month = today.strftime('%Y-%m')

    # Helper to get date string in current month or offset days
    def get_date_in_cur_month(day_num):
        # ensure day_num doesn't exceed current day of month or month days
        day = min(day_num, 28)
        return f"{cur_month}-{day:02d}"

    # 3. Income Transaction for Current Month (Salary ₹50,000)
    salary_date = f"{cur_month}-01"
    salary = Transaction(
        user_id=user.id,
        type="income",
        category="Salary",
        amount=50000.0,
        description="Monthly Salary Credit",
        date=salary_date
    )
    db.session.add(salary)

    # 4. Current Month Expense Transactions that sum to exactly ₹31,500
    # Rent: 12,000
    # Food: 3,200 (450 + 850 + 600 + 400 + 900)
    # Shopping: 4,500 (1500 + 2000 + 1000)
    # Transport: 2,100 (200 + 450 + 650 + 800)
    # Bills: 3,000 (Electricity & Wifi)
    # Entertainment: 2,000 (Movies & OTT)
    # Healthcare: 1,500 (Pharmacy & Checkup)
    # Education: 1,200 (Online Course & Books)
    # Other: 2,000 (Gifts & Miscellaneous)
    # Total = 31,500 exactly!

    current_month_expenses = [
        # Rent
        {"category": "Rent", "amount": 12000.0, "desc": "Apartment Monthly Rent", "day": 2},
        # Food (total 3,200)
        {"category": "Food", "amount": 450.0, "desc": "Dinner at Bistro", "day": min(today.day, 24)},
        {"category": "Food", "amount": 850.0, "desc": "Grocery Supermarket", "day": min(max(today.day - 2, 1), 22)},
        {"category": "Food", "amount": 600.0, "desc": "Weekly Fresh Fruits & Veggies", "day": 12},
        {"category": "Food", "amount": 400.0, "desc": "Cafe Coffee & Snacks", "day": 8},
        {"category": "Food", "amount": 900.0, "desc": "Weekend Dining Out", "day": 18},
        # Shopping (total 4,500) - exceeds 4,000 budget
        {"category": "Shopping", "amount": 1500.0, "desc": "Clothing & Apparel", "day": min(today.day, 23)},
        {"category": "Shopping", "amount": 2000.0, "desc": "Electronics Accessories & Headphones", "day": 10},
        {"category": "Shopping", "amount": 1000.0, "desc": "Footwear & Shoes", "day": 15},
        # Transport (total 2,100)
        {"category": "Transport", "amount": 200.0, "desc": "Metro Card Recharge", "day": min(today.day, 25)},
        {"category": "Transport", "amount": 450.0, "desc": "Uber Commute to Office", "day": 14},
        {"category": "Transport", "amount": 650.0, "desc": "Cab Ride to Meeting", "day": 9},
        {"category": "Transport", "amount": 800.0, "desc": "Fuel / Petrol Refill", "day": 5},
        # Bills (total 3,000)
        {"category": "Bills", "amount": 1800.0, "desc": "Electricity & Water Bill", "day": 6},
        {"category": "Bills", "amount": 1200.0, "desc": "High Speed Fiber Internet", "day": 7},
        # Entertainment (total 2,000)
        {"category": "Entertainment", "amount": 1200.0, "desc": "IMAX Weekend Movie Tickets", "day": 16},
        {"category": "Entertainment", "amount": 800.0, "desc": "Streaming OTT Subscriptions", "day": 4},
        # Healthcare (total 1,500)
        {"category": "Healthcare", "amount": 1500.0, "desc": "Routine Checkup & Vitamin Supplements", "day": 11},
        # Education (total 1,200)
        {"category": "Education", "amount": 1200.0, "desc": "AI & Deep Learning Course Book", "day": 13},
        # Other (total 2,000)
        {"category": "Other", "amount": 2000.0, "desc": "Birthday Gift for Colleague", "day": 17},
    ]

    for item in current_month_expenses:
        tx = Transaction(
            user_id=user.id,
            type="expense",
            category=item["category"],
            amount=item["amount"],
            description=item["desc"],
            date=get_date_in_cur_month(item["day"])
        )
        db.session.add(tx)

    # 5. Seed Historical Data for past 11 months (to provide full 12-month analytics!)
    for i in range(1, 12):
        past_date = today - timedelta(days=i * 30)
        past_m_str = past_date.strftime('%Y-%m')
        
        # Monthly salary
        past_salary = Transaction(
            user_id=user.id,
            type="income",
            category="Salary",
            amount=50000.0,
            description="Monthly Salary Credit",
            date=f"{past_m_str}-01"
        )
        db.session.add(past_salary)

        # Baseline past expenses with realistic variation
        past_expenses = [
            ("Rent", 12000.0, "Apartment Rent"),
            ("Food", 4800.0 + (i % 3) * 300, "Groceries & Food"),
            ("Transport", 2500.0 + (i % 2) * 200, "Fuel & Commute"),
            ("Bills", 2900.0 + (i % 4) * 100, "Utilities & Internet"),
            ("Shopping", 3500.0 + (i % 5) * 400, "Shopping & Personal"),
            ("Entertainment", 1800.0 + (i % 2) * 300, "Recreation"),
            ("Healthcare", 1000.0 + (i % 3) * 200, "Health & Wellness")
        ]
        for cat, amt, desc in past_expenses:
            past_tx = Transaction(
                user_id=user.id,
                type="expense",
                category=cat,
                amount=amt,
                description=desc,
                date=f"{past_m_str}-{10 + (i % 10):02d}"
            )
            db.session.add(past_tx)

    # 6. Budgets for Current Month
    budgets_data = [
        {"category": "Food", "amount": 5000.0},
        {"category": "Transport", "amount": 3000.0},
        {"category": "Shopping", "amount": 4000.0},     # Spent is 4500, will show exceeded!
        {"category": "Rent", "amount": 12000.0},
        {"category": "Bills", "amount": 3500.0},
        {"category": "Entertainment", "amount": 2500.0},
        {"category": "Healthcare", "amount": 2000.0},
        {"category": "Education", "amount": 2000.0},
    ]

    for b in budgets_data:
        budget = Budget(
            user_id=user.id,
            category=b["category"],
            amount=b["amount"],
            month=cur_month
        )
        db.session.add(budget)

    # 7. Savings Goals
    laptop_target_date = (today + timedelta(days=75)).strftime('%Y-%m-%d')
    emergency_target_date = (today + timedelta(days=180)).strftime('%Y-%m-%d')

    goals_data = [
        {
            "name": "New Laptop",
            "target_amount": 60000.0,
            "current_amount": 35000.0,
            "target_date": laptop_target_date,
            "category": "Tech & Gadgets"
        },
        {
            "name": "Emergency Fund",
            "target_amount": 100000.0,
            "current_amount": 42000.0,
            "target_date": emergency_target_date,
            "category": "Safety Net"
        },
        {
            "name": "Winter Trip to Manali",
            "target_amount": 25000.0,
            "current_amount": 14000.0,
            "target_date": (today + timedelta(days=90)).strftime('%Y-%m-%d'),
            "category": "Travel"
        }
    ]

    for g in goals_data:
        goal = SavingsGoal(
            user_id=user.id,
            name=g["name"],
            target_amount=g["target_amount"],
            current_amount=g["current_amount"],
            target_date=g["target_date"],
            category=g["category"]
        )
        db.session.add(goal)

    db.session.commit()
    print("Database successfully seeded with realistic fintech data for Shubham!")

if __name__ == '__main__':
    from app import app
    with app.app_context():
        seed_database()
