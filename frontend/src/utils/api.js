// API utility functions with authentication for Kickstarter Investment Tracker
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

// Get auth token from localStorage
const getAuthToken = () => {
  return localStorage.getItem('auth_token');
};

// Create authenticated headers
const createAuthHeaders = () => {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (token && token !== 'demo-token-for-testing') {
    headers.Authorization = `Bearer ${token}`;
  }
  
  return headers;
};

// Generic API call function
export const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: createAuthHeaders(),
    ...options,
  };

  // If there's a body, stringify it
  if (config.body && typeof config.body !== 'string') {
    config.body = JSON.stringify(config.body);
  }

  try {
    const response = await fetch(url, config);
    
    // If unauthorized, clear the token and reload
    if (response.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
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