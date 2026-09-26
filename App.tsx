import React, { useState, useEffect, useCallback } from 'react';
import { User, DashboardData } from './types';
import { api } from './services/api';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { AddTransactionModal } from './components/AddTransactionModal';
import { WelcomeLanding } from './pages/WelcomeLanding';
import { DashboardPage } from './pages/DashboardPage';
import { TransactionsPage } from './pages/TransactionsPage';
import { BudgetPlannerPage } from './pages/BudgetPlannerPage';
import { SavingsGoalsPage } from './pages/SavingsGoalsPage';
import { AIAdvisorPage } from './pages/AIAdvisorPage';
import { ExpenseAnalysisPage } from './pages/ExpenseAnalysisPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  // Session authentication state (persisted in localStorage or default to landing)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return localStorage.getItem('fin_advisor_authed') === 'true';
  });

  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [addTxModalOpen, setAddTxModalOpen] = useState<boolean>(false);

  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  // Fetch Core Dashboard Data from SQLite backend
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getDashboard();
      setDashboardData(data);
      setUser(data.user);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated, refreshKey, loadData]);

  const handleEnterApp = (profileName?: string) => {
    localStorage.setItem('fin_advisor_authed', 'true');
    setIsAuthenticated(true);
    if (profileName && profileName !== 'Shubham') {
      api.updateSettings({ name: profileName }).catch(console.error);
    }
  };

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  // If not entered / logged in, show WelcomeLanding page
  if (!isAuthenticated) {
    return <WelcomeLanding onEnterApp={handleEnterApp} />;
  }

  const currency = dashboardData?.summary?.currency || '₹';

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col md:flex-row font-['Inter'] selection:bg-indigo-500 selection:text-white">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        user={user}
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col md:pl-72 min-h-screen">
        <Header
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
          onOpenAddTransaction={() => setAddTxModalOpen(true)}
          user={user}
          currentTab={currentTab}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {loading && !dashboardData ? (
            <div className="py-32 flex flex-col items-center justify-center gap-3">
              <span className="animate-spin inline-block w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full" />
              <p className="text-xs text-slate-400">Connecting to localized financial database...</p>
            </div>
          ) : (
            <>
              {currentTab === 'dashboard' && dashboardData && (
                <DashboardPage
                  data={dashboardData}
                  onNavigateTab={setCurrentTab}
                  onOpenAddTransaction={() => setAddTxModalOpen(true)}
                />
              )}

              {currentTab === 'transactions' && (
                <TransactionsPage
                  currency={currency}
                  onOpenAddTransaction={() => setAddTxModalOpen(true)}
                />
              )}

              {currentTab === 'budgets' && (
                <BudgetPlannerPage
                  currency={currency}
                  onNavigateTab={setCurrentTab}
                />
              )}

              {currentTab === 'goals' && (
                <SavingsGoalsPage currency={currency} />
              )}

              {currentTab === 'advisor' && (
                <AIAdvisorPage
                  currency={currency}
                  userName={user?.name || 'Shubham'}
                  onNavigateTab={setCurrentTab}
                />
              )}

              {currentTab === 'expenses' && (
                <ExpenseAnalysisPage currency={currency} />
              )}

              {currentTab === 'reports' && (
                <ReportsPage currency={currency} />
              )}

              {currentTab === 'settings' && (
                <SettingsPage
                  onRefreshAllData={handleRefresh}
                  user={user}
                />
              )}
            </>
          )}
        </main>
      </div>

      {/* Add Transaction Global Modal */}
      <AddTransactionModal
        isOpen={addTxModalOpen}
        onClose={() => setAddTxModalOpen(false)}
        onSuccess={handleRefresh}
        currency={currency}
      />
    </div>
  );
};

export default App;
