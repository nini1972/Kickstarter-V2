import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { AppProvider } from './context/AppContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import LoginForm from './components/LoginForm';
import Header from './components/Header';
import Navigation from './components/Navigation';
import Dashboard from './components/Dashboard';
import ProjectsTab from './components/ProjectsTab';
import InvestmentsTab from './components/InvestmentsTab';
import AlertsTab from './components/AlertsTab';
import AnalyticsTab from './components/AnalyticsTab';
import CalendarTab from './components/CalendarTab';
import AIInsightsTab from './components/AIInsightsTab';
import AddProjectModal from './components/modals/AddProjectModal';
import AddInvestmentModal from './components/modals/AddInvestmentModal';
import AlertSettingsModal from './components/modals/AlertSettingsModal';
import './App.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors (client errors)
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        // Retry up to 3 times for other errors
        return failureCount < 3;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showAddProject, setShowAddProject] = useState(false);
  const [showAddInvestment, setShowAddInvestment] = useState(false);
  const [showAlertSettings, setShowAlertSettings] = useState(false);
  
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login form if not authenticated
  if (!isAuthenticated) {
    return <LoginForm />;
  }

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'projects':
        return <ProjectsTab />;
      case 'investments':
        return <InvestmentsTab />;
      case 'alerts':
        return <AlertsTab />;
      case 'analytics':
        return <AnalyticsTab />;
      case 'calendar':
        return <CalendarTab />;
      case 'ai-insights':
        return <AIInsightsTab />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      <Header 
        onAddProject={() => setShowAddProject(true)}
        onAddInvestment={() => setShowAddInvestment(true)}
        onShowAlertSettings={() => setShowAlertSettings(true)}
      />
      
      <Navigation 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
      />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {renderActiveTab()}
      </main>

      {/* Modals */}
      {showAddProject && (
        <AddProjectModal 
          isOpen={showAddProject}
          onClose={() => setShowAddProject(false)}
        />
      )}

      {showAddInvestment && (
        <AddInvestmentModal 
          isOpen={showAddInvestment}
          onClose={() => setShowAddInvestment(false)}
        />
      )}

      {showAlertSettings && (
        <AlertSettingsModal 
          isOpen={showAlertSettings}
          onClose={() => setShowAlertSettings(false)}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppProvider>
          <AppContent />
          <ReactQueryDevtools initialIsOpen={false} />
        </AppProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;