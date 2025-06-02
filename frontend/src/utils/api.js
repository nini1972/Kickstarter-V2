// API utility functions with secure cookie-based authentication for Kickstarter Investment Tracker
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : 'http://localhost:8001/api';

// Create authenticated headers - no longer need Authorization header with httpOnly cookies
const createAuthHeaders = () => {
  return {
    'Content-Type': 'application/json',
  };
};

// Generic API call function with secure cookie authentication
export const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: createAuthHeaders(),
    credentials: 'include', // CRITICAL: Include httpOnly cookies for authentication
    ...options,
  };

  // If there's a body, stringify it
  if (config.body && typeof config.body !== 'string') {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(url, config);
    
    // If unauthorized, redirect to login (cookies have expired or been cleared)
    if (response.status === 401) {
      // With cookie-based auth, we just need to reload the page
      // The AuthContext will detect the missing cookies and show login
      window.location.reload();
      return;
    }
    
    // If the response is not ok, throw an error
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || `HTTP error! status: ${response.status}`);
    }
    
    // Parse JSON response
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error);
    throw error;
  }
};

// Specific API functions
export const api = {
  // Health check
  health: () => apiCall('/health'),
  
  // Projects
  projects: {
    list: (params = {}) => {
      const searchParams = new URLSearchParams(params);
      return apiCall(`/projects?${searchParams}`);
    },
    get: (id) => apiCall(`/projects/${id}`),
    create: (data) => apiCall('/projects', { method: 'POST', body: data }),
    update: (id, data) => apiCall(`/projects/${id}`, { method: 'PUT', body: data }),
    delete: (id) => apiCall(`/projects/${id}`, { method: 'DELETE' }),
    stats: () => apiCall('/projects/stats'),
    batchAnalyze: (data) => apiCall('/projects/batch-analyze', { method: 'POST', body: data }),
  },
  
  // Investments
  investments: {
    list: (params = {}) => {
      const searchParams = new URLSearchParams(params);
      return apiCall(`/investments?${searchParams}`);
    },
    get: (id) => apiCall(`/investments/${id}`),
    create: (data) => apiCall('/investments', { method: 'POST', body: data }),
    update: (id, data) => apiCall(`/investments/${id}`, { method: 'PUT', body: data }),
    delete: (id) => apiCall(`/investments/${id}`, { method: 'DELETE' }),
    stats: () => apiCall('/investments/stats'),
    analytics: () => apiCall('/investments/analytics'),
  },
  
  // Analytics
  analytics: {
    dashboard: () => apiCall('/analytics/dashboard'),
    fundingTrends: (days = 30) => apiCall(`/analytics/funding-trends?days=${days}`),
    roiPredictions: () => apiCall('/analytics/roi-predictions'),
    risk: () => apiCall('/analytics/risk'),
    marketInsights: () => apiCall('/analytics/market-insights'),
    
    // Legacy endpoints for backward compatibility
    advanced: () => apiCall('/analytics/advanced').catch(() => null), // May not exist in new API
    fundingTrendsLegacy: () => apiCall('/analytics/funding-trends').catch(() => null), // Fallback
  },
  
  // Alerts
  alerts: {
    list: (limit = 20) => apiCall(`/alerts?limit=${limit}`),
    preferences: () => apiCall('/alerts/preferences'),
    updatePreferences: (data) => apiCall('/alerts/preferences', { method: 'PUT', body: data }),
  },
  
  // Recommendations
  recommendations: (limit = 10) => apiCall(`/recommendations?limit=${limit}`),
  
  // Dashboard (legacy endpoint)
  dashboard: {
    stats: () => {
      // Try the new analytics endpoint first, then fall back to legacy
      return apiCall('/analytics/dashboard').catch(() => 
        apiCall('/dashboard/stats').catch(() => ({
          total_projects: 0,
          total_investments: 0,
          total_invested: 0,
          success_rate: 0,
          avg_investment: 0,
          risk_distribution: [],
          category_distribution: [],
        }))
      );
    },
  },
};

export default api;