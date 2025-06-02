import React from 'react';
import { CheckCircleIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { useAppContext } from '../context/AppContext';

const ProjectsTab = () => {
  const { projects, loading, errors } = useAppContext();

  const getRiskColor = (risk) => {
    switch(risk) {
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

  if (loading.projects) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Your Projects</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Track all your Kickstarter investments</p>
          </div>
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
        </div>
      </div>
    );
  }

  if (errors.projects) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading projects</h3>
              <p className="mt-2 text-sm text-red-700">{errors.projects}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Your Projects</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">Track all your Kickstarter investments</p>
        </div>
        <ul className="divide-y divide-gray-200" role="list">
          {projects.map((project) => (
            <li key={project.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50 transition-colors duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0" aria-hidden="true">
                    {getStatusIcon(project.status)}
                  </div>
                  <div className="ml-4">
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
                    {format(new Date(project.deadline), 'MMM dd, yyyy')}
                  </p>
                  <div className="mt-1">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      project.status === 'live' ? 'bg-green-100 text-green-800' :
                      project.status === 'successful' ? 'bg-blue-100 text-blue-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {project.status}
                    </span>
                  </div>
                </div>
              </div>
              {project.ai_analysis && (
                <div className="mt-3 bg-gray-50 rounded-lg p-3">
                  <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
                    <div>
                      <span className="font-medium">Success Probability:</span>
                      {' '}{(project.ai_analysis.success_probability * 100).toFixed(0)}%
                    </div>
                    <div>
                      <span className="font-medium">Sentiment Score:</span>
                      {' '}{(project.ai_analysis.sentiment_score * 100).toFixed(0)}%
                    </div>
                  </div>
                  {project.ai_analysis.key_factors && project.ai_analysis.key_factors.length > 0 && (
                    <div className="mt-2">
                      <span className="text-xs font-medium text-gray-600">Key Factors: </span>
                      <span className="text-xs text-gray-600">
                        {project.ai_analysis.key_factors.slice(0, 2).join(', ')}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </li>
          ))}
          {projects.length === 0 && (
            <li className="px-4 py-12 text-center">
              <div className="text-gray-500">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No projects yet</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Add your first project to get started with tracking your investments!
                </p>
              </div>
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default ProjectsTab;