import sys
import unittest
import json
import urllib.request
import urllib.parse

# Set UTF-8 for Windows PowerShell output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5001/api"
VITE_URL = "http://localhost:5173/api"

class TestPersonalFinanceAdvisorAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Reset database to exact demo baseline before running test suite
        req = urllib.request.Request(f"{BASE_URL}/settings/reset", data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req) as resp:
            pass
        print("[SETUP] Database reset to clean demo baseline (Income: 50k, Expenses: 31.5k)")

    def make_request(self, endpoint, method="GET", data=None, use_vite_proxy=False):
        base = VITE_URL if use_vite_proxy else BASE_URL
        url = f"{base}{endpoint}"
        headers = {}
        encoded_data = None
        
        if data is not None:
            encoded_data = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'

        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        with urllib.request.urlopen(req) as response:
            status = response.status
            content_type = response.headers.get('Content-Type', '')
            raw_body = response.read()
            if 'application/json' in content_type:
                return status, json.loads(raw_body.decode('utf-8'))
            return status, raw_body

    def test_01_health_check(self):
        status, body = self.make_request("/health")
        self.assertEqual(status, 200)
        self.assertEqual(body['status'], 'healthy')
        self.assertEqual(body['application'], 'Personal Finance Advisor Bot')
        print("[PASS] Health Check")

    def test_02_current_user(self):
        status, body = self.make_request("/auth/me")
        self.assertEqual(status, 200)
        self.assertIn('user', body)
        self.assertEqual(body['user']['name'], 'Shubham')
        print(f"[PASS] User Profile: {body['user']['name']} ({body['user']['email']})")

    def test_03_dashboard_metrics(self):
        status, body = self.make_request("/analytics/dashboard")
        self.assertEqual(status, 200)
        summary = body['summary']
        
        # Verify baseline numbers from Capstone specifications
        self.assertEqual(summary['total_income'], 50000.0)
        self.assertEqual(summary['total_expenses'], 31500.0)
        self.assertEqual(summary['total_savings'], 18500.0)
        self.assertEqual(summary['savings_rate'], 37.0)
        
        health = body['health_score']
        self.assertGreaterEqual(health['score'], 75)
        self.assertIn('breakdown', health)
        
        print(f"[PASS] Dashboard Metrics: Income=INR {summary['total_income']}, Expenses=INR {summary['total_expenses']}, Savings=INR {summary['total_savings']}, Rate={summary['savings_rate']}%, Health Score={health['score']}/100")

    def test_04_trends_endpoints(self):
        for period in ['7d', '30d', '6m', '12m']:
            status, body = self.make_request(f"/analytics/trends?period={period}")
            self.assertEqual(status, 200)
            self.assertIsInstance(body, list)
            self.assertGreater(len(body), 0)
        print("[PASS] Multi-period Trends (7d, 30d, 6m, 12m)")

    def test_05_expense_analysis(self):
        status, body = self.make_request("/analytics/expenses")
        self.assertEqual(status, 200)
        self.assertEqual(body['total_monthly_expenses'], 31500.0)
        self.assertGreater(body['average_daily_spending'], 0)
        self.assertIn('highest_spending_category', body)
        self.assertIn('category_breakdown', body)
        self.assertIn('day_of_week_distribution', body)
        print(f"[PASS] Expense Analysis: Avg Daily=INR {body['average_daily_spending']}/day, Highest={body['highest_spending_category']['name']}")

    def test_06_transactions_crud_flow(self):
        # 1. Add new expense
        new_tx = {
            "type": "expense",
            "category": "Food",
            "amount": 750.0,
            "description": "Dinner Buffet with Team",
            "date": "2026-09-24"
        }
        status, res = self.make_request("/transactions", method="POST", data=new_tx)
        self.assertEqual(status, 201)
        created_tx = res['transaction']
        tx_id = created_tx['id']
        self.assertEqual(created_tx['amount'], 750.0)

        # 2. Update transaction
        update_data = {"amount": 800.0, "description": "Updated Dinner Buffet"}
        status, res = self.make_request(f"/transactions/{tx_id}", method="PUT", data=update_data)
        self.assertEqual(status, 200)
        self.assertEqual(res['transaction']['amount'], 800.0)

        # 3. Delete transaction to restore original state
        status, res = self.make_request(f"/transactions/{tx_id}", method="DELETE")
        self.assertEqual(status, 200)
        print(f"[PASS] Transactions CRUD: Created ID #{tx_id}, Updated, and Deleted")

    def test_07_budgets_and_alerts(self):
        status, body = self.make_request("/budgets")
        self.assertEqual(status, 200)
        budgets = body['budgets']
        
        # Verify Shopping budget exceeded alert
        shopping_budget = next((b for b in budgets if b['category'] == 'Shopping'), None)
        self.assertIsNotNone(shopping_budget)
        self.assertTrue(shopping_budget['is_exceeded'])
        self.assertIn('exceeded your Shopping budget', shopping_budget['alert_message'])
        print(f"[PASS] Budget Exceeded Alert: Shopping Spent=INR {shopping_budget['spent']} vs Budget=INR {shopping_budget['amount']} ({shopping_budget['alert_message']})")

    def test_08_goals_and_contributions(self):
        status, body = self.make_request("/goals")
        self.assertEqual(status, 200)
        self.assertGreater(len(body), 0)
        
        laptop_goal = next((g for g in body if g['name'] == 'New Laptop'), None)
        self.assertIsNotNone(laptop_goal)
        self.assertEqual(laptop_goal['target_amount'], 60000.0)
        self.assertEqual(laptop_goal['current_amount'], 35000.0)
        self.assertAlmostEqual(laptop_goal['progress'], 58.3, delta=0.5)

        # Contribute ₹2,000 toward laptop goal
        status, res = self.make_request(f"/goals/{laptop_goal['id']}/contribute", method="POST", data={"amount": 2000})
        self.assertEqual(status, 200)
        self.assertEqual(res['goal']['current_amount'], 37000.0)

        # Revert contribution back to 35,000
        self.make_request(f"/goals/{laptop_goal['id']}", method="PUT", data={"current_amount": 35000.0})
        print(f"[PASS] Savings Goals & Contributions: New Laptop tested (target 60k, initial 35k, progress 58.3%)")

    def test_09_ai_advisor_cards(self):
        status, cards = self.make_request("/advisor/cards")
        self.assertEqual(status, 200)
        self.assertEqual(len(cards), 4)
        card_types = [c['type'] for c in cards]
        self.assertIn('saving', card_types)
        self.assertIn('insight', card_types)
        self.assertIn('goal', card_types)
        print("[PASS] AI Advice Cards Generated: Saving Opportunity, Spending Insight, Goal Progress, Budget Alert")

    def test_10_ai_advisor_conversational_chat(self):
        queries = [
            "How can I save more money this month?",
            "What is my financial health score and how do I improve it?",
            "Check my 50/30/20 budget breakdown.",
            "Can I afford to buy a gadget for 15,000?",
            "Where did most of my money go this month?"
        ]
        
        for q in queries:
            status, res = self.make_request("/advisor/chat", method="POST", data={"message": q})
            self.assertEqual(status, 200)
            self.assertIn('reply', res)
            self.assertGreater(len(res['reply']), 100)
            print(f"[PASS] AI Advisor Chat: query '{q[:32]}...' returned {len(res['reply'])} chars")

    def test_11_reports_and_pdf_generation(self):
        # 1. Summary
        status, rep = self.make_request("/reports/summary")
        self.assertEqual(status, 200)
        self.assertEqual(rep['summary']['total_income'], 50000.0)

        # 2. CSV
        status, csv_data = self.make_request("/reports/download-csv")
        self.assertEqual(status, 200)
        csv_text = csv_data.decode('utf-8')
        self.assertIn("Personal Finance Advisor Bot", csv_text)

        # 3. PDF
        status, pdf_data = self.make_request("/reports/download-pdf")
        self.assertEqual(status, 200)
        self.assertTrue(pdf_data.startswith(b'%PDF'))
        self.assertGreater(len(pdf_data), 3000)
        print(f"[PASS] Reports & Export: Monthly Summary, CSV Export, and ReportLab PDF Export ({len(pdf_data)} bytes)")

    def test_12_vite_proxy_connectivity(self):
        status, body = self.make_request("/health", use_vite_proxy=True)
        self.assertEqual(status, 200)
        self.assertEqual(body['application'], 'Personal Finance Advisor Bot')
        
        status, dash = self.make_request("/analytics/dashboard", use_vite_proxy=True)
        self.assertEqual(status, 200)
        self.assertEqual(dash['user']['name'], 'Shubham')
        print("[PASS] Vite Reverse Proxy: Frontend :5173 successfully proxies /api to Flask :5001")

if __name__ == '__main__':
    print("=" * 70)
    print("RUNNING AUTOMATED E2E TEST SUITE FOR PERSONAL FINANCE ADVISOR BOT")
    print("=" * 70)
    unittest.main()
