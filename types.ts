export interface User {
  id: number;
  name: string;
  email: string;
  monthly_income: number;
  currency: string;
  created_at?: string;
}

export interface Transaction {
  id: number;
  user_id: number;
  type: 'income' | 'expense';
  category: string;
  amount: number;
  description: string;
  date: string;
  created_at?: string;
}

export interface Budget {
  id: number;
  category: string;
  amount: number;
  spent: number;
  remaining: number;
  percentage: number;
  is_exceeded: boolean;
  is_warning: boolean;
  month: string;
  alert_message?: string;
}

export interface BudgetSummary {
  total_budgeted: number;
  total_spent: number;
  total_remaining: number;
  overall_percentage: number;
  exceeded_count: number;
}

export interface SavingsGoal {
  id: number;
  user_id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  category: string;
  progress: number;
  remaining_amount: number;
  is_completed: boolean;
  created_at?: string;
}

export interface HealthScoreBreakdownItem {
  score: number;
  max: number;
  label: string;
}

export interface HealthScore {
  score: number;
  rating: string;
  message: string;
  savings_rate: number;
  expense_ratio: number;
  breakdown: {
    savings_rate_score: HealthScoreBreakdownItem;
    expense_ratio_score: HealthScoreBreakdownItem;
    budget_discipline_score: HealthScoreBreakdownItem;
    goals_progress_score: HealthScoreBreakdownItem;
  };
  total_income: number;
  total_expenses: number;
  total_savings: number;
}

export interface CategoryBreakdownItem {
  name: string;
  amount: number;
  percentage: number;
  color: string;
}

export interface AdviceCard {
  id: string;
  type: 'saving' | 'insight' | 'goal' | 'alert' | 'warning' | 'success';
  title: string;
  subtitle: string;
  content: string;
  badge: string;
  action_label?: string;
  action_link?: string;
}

export interface DashboardData {
  user: User;
  summary: {
    total_income: number;
    total_expenses: number;
    total_savings: number;
    savings_rate: number;
    currency: string;
  };
  health_score: HealthScore;
  category_breakdown: CategoryBreakdownItem[];
  recent_transactions: Transaction[];
  advice_cards: AdviceCard[];
}

export interface TrendPoint {
  label: string;
  date?: string;
  month?: string;
  income: number;
  expenses: number;
  savings: number;
}

export interface ExpenseAnalysisData {
  total_monthly_expenses: number;
  average_daily_spending: number;
  highest_spending_category: { name: string; amount: number };
  lowest_spending_category: { name: string; amount: number };
  month_over_month_change_pct: number;
  previous_month_expenses: number;
  category_breakdown: {
    category: string;
    total: number;
    count: number;
    percentage: number;
    average_per_transaction: number;
  }[];
  day_of_week_distribution: { day: string; amount: number }[];
}

export interface MonthlyReportData {
  user: { name: string; email: string; currency: string };
  month: string;
  summary: {
    total_income: number;
    total_expenses: number;
    total_savings: number;
    savings_rate: number;
    top_spending_category: { name: string; amount: number };
  };
  categories: { category: string; amount: number; percentage: number }[];
  transaction_count: number;
}

export interface UserSettings {
  id: number;
  user_id: number;
  currency: string;
  monthly_income: number;
  notification_email: boolean;
  budget_alerts: boolean;
  theme: string;
  alert_threshold_percent: number;
}
