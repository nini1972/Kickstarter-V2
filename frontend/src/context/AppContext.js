import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';
import toast from 'react-hot-toast';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // Centralized State
  const [projects, setProjects] = useState([]);
  const [investments, setInvestments] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [advancedAnalytics, setAdvancedAnalytics] = useState({});
  const [fundingTrends, setFundingTrends] = useState([]);
  const [alertSettings, setAlertSettings] = useState({});
  const [recommendations, setRecommendations] = useState([]);
  
  // Loading States
  const [loading, setLoading] = useState({
    projects: false,
    investments: false,
    dashboard: false,
    alerts: false,
    analytics: false
  });

  // Error States
  const [errors, setErrors] = useState({});

  // Utility function to update loading state
  const updateLoading = (key, value) => {
    setLoading(prev => ({ ...prev, [key]: value }));
  };

  // Utility function to handle errors
  const handleError = (key, error) => {
    console.error(`Error in ${key}:`, error);
    setErrors(prev => ({ ...prev, [key]: error.message }));
    toast.error(`Failed to load ${key}`);
  };

  // Load data from localStorage on init
  useEffect(() => {
    const loadFromStorage = () => {
      try {
        const savedProjects = localStorage.getItem('kickstarter_projects');
        const savedInvestments = localStorage.getItem('kickstarter_investments');
        const savedDashboard = localStorage.getItem('kickstarter_dashboard');
        const savedAlerts = localStorage.getItem('kickstarter_alerts');
        const savedAnalytics = localStorage.getItem('kickstarter_analytics');
        const savedAlertSettings = localStorage.getItem('kickstarter_alert_settings');

        if (savedProjects) setProjects(JSON.parse(savedProjects));
        if (savedInvestments) setInvestments(JSON.parse(savedInvestments));
        if (savedDashboard) setDashboardStats(JSON.parse(savedDashboard));
        if (savedAlerts) setAlerts(JSON.parse(savedAlerts));
        if (savedAnalytics) setAdvancedAnalytics(JSON.parse(savedAnalytics));
        if (savedAlertSettings) setAlertSettings(JSON.parse(savedAlertSettings));
      } catch (error) {
        console.error('Error loading from localStorage:', error);
      }
    };

    loadFromStorage();
  }, []);

  // Save to localStorage whenever data changes
  useEffect(() => {
    localStorage.setItem('kickstarter_projects', JSON.stringify(projects));
  }, [projects]);

  useEffect(() => {
    localStorage.setItem('kickstarter_investments', JSON.stringify(investments));
  }, [investments]);

  useEffect(() => {
    localStorage.setItem('kickstarter_dashboard', JSON.stringify(dashboardStats));
  }, [dashboardStats]);

  useEffect(() => {
    localStorage.setItem('kickstarter_alerts', JSON.stringify(alerts));
  }, [alerts]);

  useEffect(() => {
    localStorage.setItem('kickstarter_analytics', JSON.stringify(advancedAnalytics));
  }, [advancedAnalytics]);

  useEffect(() => {
    localStorage.setItem('kickstarter_alert_settings', JSON.stringify(alertSettings));
  }, [alertSettings]);

  // API Functions
  const fetchProjects = async (filters = {}) => {
    updateLoading('projects', true);
    try {
      const data = await api.projects.list(filters);
      setProjects(data);
      setErrors(prev => ({ ...prev, projects: null }));
    } catch (error) {
      handleError('projects', error);
    } finally {
      updateLoading('projects', false);
    }
  };

  const fetchInvestments = async (projectId = null) => {
    updateLoading('investments', true);
    try {
      const params = projectId ? { project_id: projectId } : {};
      const data = await api.investments.list(params);
      setInvestments(data);
      setErrors(prev => ({ ...prev, investments: null }));
    } catch (error) {
      handleError('investments', error);
    } finally {
      updateLoading('investments', false);
    }
  };

  const fetchDashboardStats = async () => {
    updateLoading('dashboard', true);
    try {
      const data = await api.dashboard.stats();
      setDashboardStats(data);
      setErrors(prev => ({ ...prev, dashboard: null }));
    } catch (error) {
      handleError('dashboard', error);
    } finally {
      updateLoading('dashboard', false);
    }
  };

  const fetchAlerts = async () => {
    updateLoading('alerts', true);
    try {
      const data = await api.alerts.list();
      setAlerts(data);
      
      // Show browser notifications for high priority alerts
      data.forEach(alert => {
        if (alert.priority === 'high' && "Notification" in window && Notification.permission === "granted") {
          new Notification("🚀 Investment Alert!", {
            body: alert.message,
            icon: '/favicon.ico'
          });
        }
      });
      
      setErrors(prev => ({ ...prev, alerts: null }));
    } catch (error) {
      handleError('alerts', error);
    } finally {
      updateLoading('alerts', false);
    }
  };

  const fetchAdvancedAnalytics = async () => {
    updateLoading('analytics', true);
    try {
      const [analyticsData, trendsData] = await Promise.all([
        api.analytics.advanced(),
        api.analytics.fundingTrends()
      ]);
      
      setAdvancedAnalytics(analyticsData);
      setFundingTrends(trendsData.trends || []);
      setErrors(prev => ({ ...prev, analytics: null }));
    } catch (error) {
      handleError('analytics', error);
    } finally {
      updateLoading('analytics', false);
    }
  };

  const fetchAlertSettings = async () => {
    try {
      const data = await api.alerts.preferences();
      setAlertSettings(data);
    } catch (error) {
      console.error('Failed to fetch alert settings:', error);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const data = await api.recommendations();
      setRecommendations(data.recommendations);
    } catch (error) {
      handleError('recommendations', error);
    }
  };

  // CRUD Operations
  const addProject = async (projectData) => {
    try {
      const data = await api.projects.create(projectData);
      setProjects(prev => [...prev, data]);
      toast.success('Project added successfully!');
      
      // Refresh related data
      await Promise.all([
        fetchDashboardStats(),
        fetchAlerts(),
        fetchAdvancedAnalytics()
      ]);
      
      return data;
    } catch (error) {
      toast.error('Failed to add project');
      throw error;
    }
  };

  const addInvestment = async (investmentData) => {
    try {
      const data = await api.investments.create(investmentData);
      setInvestments(prev => [...prev, data]);
      toast.success('Investment added successfully!');
      
      // Refresh related data
      await Promise.all([
        fetchDashboardStats(),
        fetchAdvancedAnalytics()
      ]);
      
      return data;
    } catch (error) {
      toast.error('Failed to add investment');
      throw error;
    }
  };

  const updateAlertSettings = async (settings) => {
    try {
      await api.alerts.updatePreferences(settings);
      setAlertSettings(settings);
      toast.success('Alert settings updated!');
      
      // Refresh alerts with new settings
      await fetchAlerts();
    } catch (error) {
      toast.error('Failed to update alert settings');
      throw error;
    }
  };

  // Initialize data on mount
  useEffect(() => {
    const initializeData = async () => {
      await Promise.all([
        fetchProjects(),
        fetchInvestments(),
        fetchDashboardStats(),
        fetchAlerts(),
        fetchAdvancedAnalytics(),
        fetchAlertSettings()
      ]);
    };

    initializeData();

    // Set up browser notifications
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }, []);

  // Context value
  const value = {
    // State
    projects,
    investments,
    dashboardStats,
    alerts,
    advancedAnalytics,
    fundingTrends,
    alertSettings,
    recommendations,
    loading,
    errors,
    
    // Setters (for direct state updates if needed)
    setProjects,
    setInvestments,
    setDashboardStats,
    setAlerts,
    setAdvancedAnalytics,
    setFundingTrends,
    setAlertSettings,
    setRecommendations,
    
    // API Functions
    fetchProjects,
    fetchInvestments,
    fetchDashboardStats,
    fetchAlerts,
    fetchAdvancedAnalytics,
    fetchAlertSettings,
    fetchRecommendations,
    
    // CRUD Operations
    addProject,
    addInvestment,
    updateAlertSettings,
    
    // Utility
    updateLoading,
    handleError
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export default AppContext;