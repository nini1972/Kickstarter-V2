import React, { useState, useCallback, useMemo } from 'react';
import { CheckCircleIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

import { useInView } from 'react-intersection-observer';
import { useInfiniteProjects, useDeleteProject, useBatchAnalyzeProjects } from '../hooks/useQuery';
import ProjectFilters from './ProjectFilters';
import toast from 'react-hot-toast';

const ProjectsTab = () => {
  const [filters, setFilters] = useState({});
  const [selectedProjects, setSelectedProjects] = useState(new Set());

  // Infinite query for projects
  const {
    data,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useInfiniteProjects(filters);

  // Mutations
  const deleteProjectMutation = useDeleteProject();
  const batchAnalyzeMutation = useBatchAnalyzeProjects();

  // Intersection observer for infinite scrolling
  const { ref, inView } = useInView({
    threshold: 0,
    rootMargin: '100px',
  });

  // Load next page when in view
  React.useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Flatten all pages into a single array
  const projects = useMemo(() => {
    return data?.pages?.flatMap(page => page.projects) || [];
  }, [data]);

  // Filter handlers
  const handleFiltersChange = useCallback((newFilters) => {
    setFilters(newFilters);
    setSelectedProjects(new Set()); // Clear selection when filters change
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
    setSelectedProjects(new Set());
  }, []);

  // Project selection handlers
  const toggleProjectSelection = (projectId) => {
    const newSelection = new Set(selectedProjects);
    if (newSelection.has(projectId)) {
      newSelection.delete(projectId);
    } else {
      newSelection.add(projectId);
    }
    setSelectedProjects(newSelection);
  };

  const selectAllProjects = () => {
    setSelectedProjects(new Set(projects.map(p => p.id)));
  };

  const clearSelection = () => {
    setSelectedProjects(new Set());
  };

  // Batch operations
  const handleBatchAnalyze = async () => {
    if (selectedProjects.size === 0) {
      toast.error('Please select projects to analyze');
      return;
    }

    try {
      await batchAnalyzeMutation.mutateAsync({
        project_ids: Array.from(selectedProjects),
        batch_size: Math.min(selectedProjects.size, 5),
      });
      clearSelection();
    } catch (error) {
      console.error('Batch analysis failed:', error);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        await deleteProjectMutation.mutateAsync(projectId);
        setSelectedProjects(prev => {
          const newSet = new Set(prev);
          newSet.delete(projectId);
          return newSet;
        });
      } catch (error) {
        console.error('Delete failed:', error);
      }
    }
  };

  // Utility functions
  const getRiskColor = (risk) => {
    switch(risk?.toLowerCase()) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'successful': return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'live': return <ClockIcon className="h-5 w-5 text-blue-500" />;
      case 'failed': return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default: return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  // Loading skeleton
  const LoadingSkeleton = () => (
    <div className="animate-pulse">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="px-4 py-4 sm:px-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="h-5 w-5 bg-gray-300 rounded"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-300 rounded w-1/2"></div>
              <div className="h-3 bg-gray-300 rounded w-1/3"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  // Error state
  if (isError) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading projects</h3>
              <p className="mt-2 text-sm text-red-700">
                {error?.message || 'An unexpected error occurred'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        {/* Header */}
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg leading-6 font-medium text-gray-900">Your Projects</h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Track all your Kickstarter investments with advanced filtering and batch operations
              </p>
            </div>
            {selectedProjects.size > 0 && (
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-700">
                  {selectedProjects.size} selected
                </span>
                <button
                  onClick={handleBatchAnalyze}
                  disabled={batchAnalyzeMutation.isPending}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {batchAnalyzeMutation.isPending ? 'Analyzing...' : 'Batch Analyze'}
                </button>
                <button
                  onClick={clearSelection}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Filters */}
        <ProjectFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onClear={clearFilters}
        />

        {/* Bulk Actions */}
        {projects.length > 0 && (
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={selectAllProjects}
                  className="text-sm text-indigo-600 hover:text-indigo-900"
                >
                  Select All ({projects.length})
                </button>
                {selectedProjects.size > 0 && (
                  <button
                    onClick={clearSelection}
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Deselect All
                  </button>
                )}
              </div>
              <div className="text-sm text-gray-500">
                Showing {projects.length} projects
              </div>
            </div>
          </div>
        )}

        {/* Projects List */}
        <ul className="divide-y divide-gray-200" role="list">
          {isLoading && <LoadingSkeleton />}
          
          {projects.map((project, index) => {
            const isSelected = selectedProjects.has(project.id);
            
            return (
              <li 
                key={`${project.id}-${index}`} 
                className={`px-4 py-4 sm:px-6 hover:bg-gray-50 transition-colors duration-200 ${
                  isSelected ? 'bg-indigo-50' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    {/* Selection checkbox */}
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleProjectSelection(project.id)}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded mr-4"
                    />
                    
                    <div className="flex-shrink-0" aria-hidden="true">
                      {getStatusIcon(project.status)}
                    </div>
                    <div className="ml-4 flex-1">
                      <div className="flex items-center">
                        <h4 className="text-sm font-medium text-indigo-600 truncate">{project.name}</h4>
                        <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskColor(project.risk_level)}`}>
                          {project.risk_level} risk
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">
                        by {project.creator} • {project.category}
                      </p>
                      <div className="text-sm text-gray-500">
                        <span className="font-medium">${project.pledged_amount?.toLocaleString()}</span>
                        {' '}of ${project.goal_amount?.toLocaleString()}
                        {' '}• {project.backers_count} backers
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end">
                    <p className="text-sm text-gray-500">Deadline</p>
                    <p className="text-sm font-medium text-gray-900">
                      {project.deadline ? new Date(project.deadline).toLocaleDateString() : 'No deadline'}
                    </p>
                    <div className="mt-1 flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        project.status === 'live' ? 'bg-green-100 text-green-800' :
                        project.status === 'successful' ? 'bg-blue-100 text-blue-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {project.status}
                      </span>
                      <button
                        onClick={() => handleDeleteProject(project.id)}
                        className="text-xs text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* AI Analysis */}
                {project.ai_analysis && (
                  <div className="mt-3 bg-gray-50 rounded-lg p-3">
                    <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
                      <div>
                        <span className="font-medium">Success Probability:</span>
                        {' '}{project.ai_analysis.success_probability}%
                      </div>
                      <div>
                        <span className="font-medium">Recommendation:</span>
                        {' '}{project.ai_analysis.recommendation}
                      </div>
                    </div>
                    {project.ai_analysis.strengths && project.ai_analysis.strengths.length > 0 && (
                      <div className="mt-2">
                        <span className="text-xs font-medium text-gray-600">Strengths: </span>
                        <span className="text-xs text-gray-600">
                          {project.ai_analysis.strengths.slice(0, 2).join(', ')}
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </li>
            );
          })}

          {/* Infinite scroll trigger */}
          {hasNextPage && (
            <li ref={ref} className="px-4 py-4 text-center">
              {isFetchingNextPage ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                  <span className="ml-2 text-sm text-gray-500">Loading more projects...</span>
                </div>
              ) : (
                <span className="text-sm text-gray-500">Scroll to load more</span>
              )}
            </li>
          )}

          {/* Empty state */}
          {!isLoading && projects.length === 0 && (
            <li className="px-4 py-12 text-center">
              <div className="text-gray-500">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No projects found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {Object.keys(filters).length > 0 
                    ? "Try adjusting your filters or add your first project to get started!"
                    : "Add your first project to get started with tracking your investments!"
                  }
                </p>
              </div>
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default React.memo(ProjectsTab);