import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

// API Client with interceptors
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      toast.error('Rate limit exceeded. Please try again later.');
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    }
    return Promise.reject(error);
  }
);

// Query Keys
export const queryKeys = {
  projects: ['projects'],
  projectsWithFilters: (filters) => ['projects', filters],
  projectById: (id) => ['projects', id],
  investments: ['investments'],
  alerts: ['alerts'],
  analytics: ['analytics'],
  recommendations: ['recommendations'],
  health: ['health'],
};

// API Functions
const api = {
  // Projects
  getProjects: async (params = {}) => {
    const { data } = await apiClient.get('/projects', { params });
    return data;
  },
  
  getInfiniteProjects: async ({ pageParam = 1, filters = {} }) => {
    const { data } = await apiClient.get('/projects', {
      params: {
        page: pageParam,
        limit: 12,
        ...filters,
      },
    });
    return {
      projects: data,
      nextPage: data.length === 12 ? pageParam + 1 : undefined,
      hasMore: data.length === 12,
    };
  },

  createProject: async (projectData) => {
    const { data } = await apiClient.post('/projects', projectData);
    return data;
  },

  updateProject: async ({ id, ...projectData }) => {
    const { data } = await apiClient.put(`/projects/${id}`, projectData);
    return data;
  },

  deleteProject: async (id) => {
    const { data } = await apiClient.delete(`/projects/${id}`);
    return data;
  },

  // Batch Processing
  batchAnalyzeProjects: async ({ project_ids, batch_size = 5 }) => {
    const { data } = await apiClient.post('/projects/batch-analyze', {
      project_ids,
      batch_size,
    });
    return data;
  },

  // Investments
  getInvestments: async () => {
    const { data } = await apiClient.get('/investments');
    return data;
  },

  createInvestment: async (investmentData) => {
    const { data } = await apiClient.post('/investments', investmentData);
    return data;
  },

  // Alerts
  getAlerts: async () => {
    const { data } = await apiClient.get('/alerts');
    return data;
  },

  // Analytics
  getAnalytics: async () => {
    const { data } = await apiClient.get('/analytics/advanced');
    return data;
  },

  getRecommendations: async () => {
    const { data } = await apiClient.get('/recommendations');
    return data;
  },

  // Health
  getHealth: async () => {
    const { data } = await apiClient.get('/health');
    return data;
  },
};

// Custom Hooks

// Projects Hooks
export const useProjects = (filters = {}) => {
  return useQuery({
    queryKey: queryKeys.projectsWithFilters(filters),
    queryFn: () => api.getProjects(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useInfiniteProjects = (filters = {}) => {
  return useInfiniteQuery({
    queryKey: ['projects-infinite', filters],
    queryFn: ({ pageParam }) => api.getInfiniteProjects({ pageParam, filters }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.createProject,
    onMutate: async (newProject) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.projects });
      
      // Snapshot the previous value
      const previousProjects = queryClient.getQueryData(queryKeys.projects);
      
      // Optimistically update to the new value
      queryClient.setQueryData(queryKeys.projects, (old) => {
        const optimisticProject = {
          ...newProject,
          id: `temp-${Date.now()}`,
          created_at: new Date().toISOString(),
          status: 'live',
        };
        return [...(old || []), optimisticProject];
      });
      
      return { previousProjects };
    },
    onError: (err, newProject, context) => {
      // Rollback on error
      queryClient.setQueryData(queryKeys.projects, context.previousProjects);
      toast.error('Failed to create project. Please try again.');
    },
    onSuccess: () => {
      toast.success('Project created successfully!');
    },
    onSettled: () => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
  });
};

export const useUpdateProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.updateProject,
    onMutate: async (updatedProject) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.projects });
      
      const previousProjects = queryClient.getQueryData(queryKeys.projects);
      
      queryClient.setQueryData(queryKeys.projects, (old) => {
        return old?.map(project => 
          project.id === updatedProject.id 
            ? { ...project, ...updatedProject }
            : project
        ) || [];
      });
      
      return { previousProjects };
    },
    onError: (err, updatedProject, context) => {
      queryClient.setQueryData(queryKeys.projects, context.previousProjects);
      toast.error('Failed to update project. Please try again.');
    },
    onSuccess: () => {
      toast.success('Project updated successfully!');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.deleteProject,
    onMutate: async (projectId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.projects });
      
      const previousProjects = queryClient.getQueryData(queryKeys.projects);
      
      queryClient.setQueryData(queryKeys.projects, (old) => {
        return old?.filter(project => project.id !== projectId) || [];
      });
      
      return { previousProjects };
    },
    onError: (err, projectId, context) => {
      queryClient.setQueryData(queryKeys.projects, context.previousProjects);
      toast.error('Failed to delete project. Please try again.');
    },
    onSuccess: () => {
      toast.success('Project deleted successfully!');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
    },
  });
};

// Batch Processing Hook
export const useBatchAnalyzeProjects = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.batchAnalyzeProjects,
    onSuccess: (data) => {
      // Invalidate projects to refresh with new AI analysis
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      toast.success(`Batch analysis completed! ${data.stats?.successful_analyses || 0} projects analyzed.`);
    },
    onError: () => {
      toast.error('Batch analysis failed. Please try again.');
    },
  });
};

// Investments Hooks
export const useInvestments = () => {
  return useQuery({
    queryKey: queryKeys.investments,
    queryFn: api.getInvestments,
    staleTime: 5 * 60 * 1000,
  });
};

// Investments Hooks
export const useInvestments = () => {
  return useQuery({
    queryKey: queryKeys.investments,
    queryFn: api.getInvestments,
    staleTime: 5 * 60 * 1000,
  });
};

export const useCreateInvestment = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.createInvestment,
    onMutate: async (newInvestment) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.investments });
      
      const previousInvestments = queryClient.getQueryData(queryKeys.investments);
      
      queryClient.setQueryData(queryKeys.investments, (old) => {
        const optimisticInvestment = {
          ...newInvestment,
          id: `temp-${Date.now()}`,
          investment_date: new Date().toISOString(),
        };
        return [...(old || []), optimisticInvestment];
      });
      
      return { previousInvestments };
    },
    onError: (err, newInvestment, context) => {
      queryClient.setQueryData(queryKeys.investments, context.previousInvestments);
      toast.error('Failed to add investment');
    },
    onSuccess: () => {
      toast.success('Investment added successfully!');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.investments });
    },
  });
};

export const useAddInvestment = () => {
  return useCreateInvestment(); // Alias for backwards compatibility
};

export const useDeleteInvestment = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (investmentId) => {
      const { data } = await apiClient.delete(`/investments/${investmentId}`);
      return data;
    },
    onMutate: async (investmentId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.investments });
      
      const previousInvestments = queryClient.getQueryData(queryKeys.investments);
      
      queryClient.setQueryData(queryKeys.investments, (old) => {
        return old?.filter(investment => investment.id !== investmentId) || [];
      });
      
      return { previousInvestments };
    },
    onError: (err, investmentId, context) => {
      queryClient.setQueryData(queryKeys.investments, context.previousInvestments);
      toast.error('Failed to delete investment');
    },
    onSuccess: () => {
      toast.success('Investment deleted successfully');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.investments });
    },
  });
};

// Alerts Hooks
export const useAlerts = () => {
  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: api.getAlerts,
    staleTime: 2 * 60 * 1000, // 2 minutes for fresher alerts
    refetchInterval: 5 * 60 * 1000, // Auto-refetch every 5 minutes
  });
};

export const useMarkAlertAsRead = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (alertId) => {
      const { data } = await apiClient.patch(`/alerts/${alertId}/read`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts });
      toast.success('Alert marked as read');
    },
    onError: () => {
      toast.error('Failed to mark alert as read');
    },
  });
};

export const useDeleteAlert = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (alertId) => {
      const { data } = await apiClient.delete(`/alerts/${alertId}`);
      return data;
    },
    onMutate: async (alertId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.alerts });
      
      const previousAlerts = queryClient.getQueryData(queryKeys.alerts);
      
      queryClient.setQueryData(queryKeys.alerts, (old) => {
        if (old?.alerts) {
          return {
            ...old,
            alerts: old.alerts.filter(alert => alert.id !== alertId)
          };
        }
        return old;
      });
      
      return { previousAlerts };
    },
    onError: (err, alertId, context) => {
      queryClient.setQueryData(queryKeys.alerts, context.previousAlerts);
      toast.error('Failed to delete alert');
    },
    onSuccess: () => {
      toast.success('Alert deleted successfully');
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts });
    },
  });
};

// Analytics Hooks
export const useAnalytics = () => {
  return useQuery({
    queryKey: queryKeys.analytics,
    queryFn: api.getAnalytics,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useRecommendations = () => {
  return useQuery({
    queryKey: queryKeys.recommendations,
    queryFn: api.getRecommendations,
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

// Health Hook
export const useHealth = () => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.getHealth,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Auto-refetch every minute
  });
};

export default api;