#  https://drive.google.com/file/d/1_4IJDf8XaiCFWjlSXmybaTNmwBZfnkco/view?usp=drive_link

# This is Demo video link of my project



# 💰 Personal Finance Advisor Bot
> **Capstone Project — B.Tech Artificial Intelligence & Data Science**  
> **Student:** Shubham  
> **Tech Stack:** React 19 • TypeScript • Vite • Tailwind CSS • Recharts • Python 3 • Flask • SQLite • ReportLab

---

## 🌟 Executive Overview
**Personal Finance Advisor Bot** is a modern, responsive, full-stack fintech platform designed to empower individuals with intelligent wealth tracking and algorithmic personal finance management. Unlike basic trackers, it features a **dedicated Python rule-based AI Financial Advisor engine** that parses live SQLite database records to formulate hyper-personalized recommendations, calculate dynamic financial health scores, forecast goal milestones, and audit budget variances—without requiring third-party paid APIs or cloud dependencies.

---

## 🚀 Key Features

### 1. 🛡️ Algorithmic Financial Health Score (0 – 100)
- Dynamically calculated from live transactions:
  - **Savings Rate Score (30 pts):** Benchmarked against high-discipline thresholds (>30% savings).
  - **Expense-to-Income Discipline (25 pts):** Strict evaluation against the 50/30/20 guideline.
  - **Budget Adherence (25 pts):** Real-time monitoring of category ceilings.
  - **Goal Milestone Velocity (20 pts):** Progress rate on designated savings targets.
- Displays an interactive circular progress gauge with rating badges (`Strong`, `Excellent`, `Moderate`).

### 2. 🤖 Conversational AI Financial Advisor
- Fully local, autonomous rule-based engine in Python.
- Analyzes actual categorized expenditures and cash reserves.
- Interactively answers queries like:
  - *"How can I save more money this month?"*
  - *"What is my financial health score and how do I improve it?"*
  - *"Check my 50/30/20 budget breakdown."*
  - *"Can I afford to purchase a gadget for ₹15,000 right now?"*
  - *"Where did most of my money go this month?"*
- Features pre-loaded dynamic advice cards:
  - 💰 **Saving Opportunity:** Identifies discretionary leakage (e.g. Shopping, dining out).
  - 📊 **Spending Insight:** Computes category wallet share (e.g. Food represents 22% of total outflow).
  - 🎯 **Goal Progress:** Real-time completion velocity and remaining months projection.
  - ⚠️ **Budget Alert:** Warns immediately when expenses exceed or approach planned caps.

### 3. 📊 Interactive Visual Analytics & Trends
- **Income vs Expenses Chart:** Dual-area gradient charts with instant switching between:
  - `Last 7 Days`
  - `Last 30 Days`
  - `Last 6 Months`
  - `Last 12 Months`
- **Where Your Money Goes:** Donut chart breakdown with dynamic category legends and center total display.
- **Weekly Spend Distribution:** Day-of-week line chart capturing weekly spending velocity.
- **Category Deep Dive:** Comparative bar charts and ticket-size frequency metrics.

### 4. 💳 Transaction Management & Modal
- Dedicated modal for adding Income and Expenses in ₹ INR.
- Dynamic categories: *Food, Transport, Shopping, Rent, Bills, Entertainment, Healthcare, Education, Salary, Freelance, Other*.
- Instant SQLite synchronization, state updates, and celebratory confetti animations on milestones.
- Filter by transaction type, category, date range, and keyword search.

### 5. 🎯 Savings Goals & Micro-Contributions
- Pre-seeded with goals:
  - **New Laptop:** Target ₹60,000 | Saved ₹35,000 (58% completed)
  - **Emergency Fund:** Target ₹1,00,000 | Saved ₹42,000 (42% completed)
  - **Winter Trip to Manali:** Target ₹25,000 | Saved ₹14,000
- "+ Add Money" modal allowing incremental allocations with particle confetti celebrations.

### 6. 📑 Compliance-Grade Reports & Statement Export
- Monthly statement summaries.
- **CSV Export:** Download full itemized logs in comma-separated values format.
- **PDF Export:** Professional, printable PDF statements generated server-side using **ReportLab**.

### 7. ⚙️ Preferences & Administration
- Multi-currency support (₹, $, €, £, ¥).
- Baseline salary parameter configuration.
- Alert threshold triggers (85% budget warning).
- **Reset to Demo Data:** One-click restoration of Shubham's default capstone dataset with confirmation dialog.

---

## 🏗️ Architecture & Project Structure

```
├── backend/
│   ├── app.py                 # Main Flask app, CORS, Blueprints, proxy endpoints
│   ├── models.py              # SQLite SQLAlchemy models (User, Transaction, Budget, SavingsGoal, Settings)
│   ├── seed_data.py           # Pre-seeds Shubham's ₹50,000 salary, ₹31,500 expenses, budgets, & goals
│   ├── ai_advisor.py          # Rule-based AI Financial Advisor engine & Health Score algorithm
│   └── routes/
│       ├── transactions.py    # CRUD & filtering for transactions
│       ├── budgets.py         # Category budgets & spent/remaining calculations
│       ├── goals.py           # Goals tracking & incremental contributions
│       ├── analytics.py       # Dashboard stats, 7d/30d/6m/12m trends, & expense deep dives
│       ├── advisor.py         # AI chatbot endpoint & dynamic recommendation cards
│       ├── reports.py         # Statement generator, CSV and ReportLab PDF downloads
│       └── settings.py        # Preferences, settings, and database reset logic
│
└── frontend/
    ├── src/
    │   ├── App.tsx            # Main application controller with tab routing
    │   ├── main.tsx           # React DOM root mounting
    │   ├── types.ts           # Comprehensive TypeScript interfaces
    │   ├── index.css          # Tailwind CSS v4 styling & fintech glassmorphism
    │   ├── services/
    │   │   └── api.ts         # Centralized typed API service connecting to Flask
    │   ├── components/
    │   │   ├── Sidebar.tsx    # Desktop sidebar & mobile navigation drawer
    │   │   ├── Header.tsx     # Breadcrumb, Quick Add Transaction, & Notification bell
    │   │   ├── HealthScoreCard.tsx     # Circular SVG score gauge & breakdown factors
    │   │   ├── IncomeExpenseChart.tsx  # Recharts 7d/30d/6m/12m Area Chart
    │   │   ├── ExpenseBreakdownDonut.tsx # Donut chart & category legend
    │   │   ├── RecentTransactionsTable.tsx # Color-coded recent transactions table
    │   │   ├── AdviceCardsGrid.tsx     # Dynamic AI advice cards
    │   │   └── AddTransactionModal.tsx # Fast transaction logger with confetti
    │   └── pages/
    │       ├── WelcomeLanding.tsx      # Welcome / Login screen with simulated auth
    │       ├── DashboardPage.tsx       # Main executive overview
    │       ├── TransactionsPage.tsx    # Filterable ledger & audit table
    │       ├── BudgetPlannerPage.tsx   # Budget progress bars & exceeded alerts
    │       ├── SavingsGoalsPage.tsx    # Target tracking & contributions
    │       ├── AIAdvisorPage.tsx       # Conversational AI chatbot interface
    │       ├── ExpenseAnalysisPage.tsx # Statistical metrics & weekly distributions
    │       ├── ReportsPage.tsx         # Statement review, CSV, & PDF downloads
    │       └── SettingsPage.tsx        # Preferences & database administration
    ├── vite.config.ts         # Vite configuration with React, Tailwind, & /api proxy
    └── package.json           # Frontend dependencies
```

---

## 💻 How to Run Locally

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**

### Step 1: Start the Backend (Flask)
```powershell
cd backend
python -m pip install -r requirements.txt # or: pip install Flask Flask-SQLAlchemy flask-cors reportlab
python app.py
```
> The backend will initialize SQLite (`advisor.db`), automatically seed demo records, and serve on `http://127.0.0.1:5001`.

### Step 2: Start the Frontend (Vite)
In a separate terminal:
```powershell
cd frontend
npm install
npm run dev
```
> The frontend will launch at `http://localhost:5173/`. All `/api` requests are automatically routed to `http://127.0.0.1:5001` via the Vite reverse proxy.

---

## 🧪 Verified Demonstration Values (Matching Capstone Prompt)
- **User:** Shubham (`shubham@example.com`)
- **Total Income:** ₹50,000
- **Total Expenses:** ₹31,500 (Rent: ₹12,000, Food: ₹3,200, Shopping: ₹4,500, Transport: ₹2,100, Bills: ₹3,000, Entertainment: ₹2,000, Healthcare: ₹1,500, Education: ₹1,200, Other: ₹2,000)
- **Total Savings:** ₹18,500
- **Savings Rate:** 37.0%
- **Financial Health Score:** 84 / 100 (`Strong`)
- **Budget Exceeded Warning:** Shopping (Spent ₹4,500 vs Budget ₹4,000 — ⚠️ Over by ₹500)
- **Savings Goals:**
  - New Laptop: Target ₹60,000 | Saved ₹35,000 (58.3%)
  - Emergency Fund: Target ₹1,00,000 | Saved ₹42,000 (42.0%)
 


This project is not done by virtual environment for running this paste this command in powershell
new terminal 
cd "C:\Users\om\Documents\Advisor bot Shubham"
.\venv\Scripts\Activate.ps1
python backend\app.py


2nd step again in new terminal
cd "C:\Users\om\Documents\Advisor bot Shubham\frontend"
npm run dev


and it will run 

