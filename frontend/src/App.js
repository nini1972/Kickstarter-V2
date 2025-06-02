import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { AppProvider } from './context/AppContext';
import ErrorBoundary from './components/ErrorBoundary';
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

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showAddProject, setShowAddProject] = useState(false);
  const [showAddInvestment, setShowAddInvestment] = useState(false);
  const [showAlertSettings, setShowAlertSettings] = useState(false);

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
      <AppProvider>
        <AppContent />
      </AppProvider>
    </ErrorBoundary>
  );
}

export default App;