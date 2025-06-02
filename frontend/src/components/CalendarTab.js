import React from 'react';
import { CalendarIcon, ClockIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { useAppContext } from '../context/AppContext';

const CalendarTab = () => {
  const { projects, loading } = useAppContext();

  const liveProjects = projects.filter(p => p.status === 'live');
  const upcomingDeadlines = liveProjects
    .sort((a, b) => new Date(a.deadline) - new Date(b.deadline))
    .map(project => {
      const daysRemaining = Math.max(0, Math.ceil((new Date(project.deadline) - new Date()) / (1000 * 60 * 60 * 24)));
      return { ...project, daysRemaining };
    });

  const getUrgencyColor = (daysRemaining) => {
    if (daysRemaining <= 3) return 'border-red-200 bg-red-50';
    if (daysRemaining <= 7) return 'border-yellow-200 bg-yellow-50';
    if (daysRemaining <= 14) return 'border-orange-200 bg-orange-50';
    return 'border-blue-200 bg-blue-50';
  };

  const getUrgencyBadge = (daysRemaining) => {
    if (daysRemaining <= 3) return 'bg-red-100 text-red-800';
    if (daysRemaining <= 7) return 'bg-yellow-100 text-yellow-800';
    if (daysRemaining <= 14) return 'bg-orange-100 text-orange-800';
    return 'bg-blue-100 text-blue-800';
  };

  if (loading.projects) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Project Timeline</h3>
            <div className="mt-6 space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="h-4 bg-gray-300 rounded w-1/2 mb-2"></div>
                      <div className="h-3 bg-gray-300 rounded w-1/3"></div>
                    </div>
                    <div className="text-right">
                      <div className="h-4 bg-gray-300 rounded w-20 mb-2"></div>
                      <div className="h-3 bg-gray-300 rounded w-16"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">📅 Project Timeline & Deadlines</h3>
            <div className="flex items-center text-sm text-gray-500">
              <CalendarIcon className="h-4 w-4 mr-1" />
              {upcomingDeadlines.length} active projects
            </div>
          </div>

          {upcomingDeadlines.length > 0 ? (
            <div className="space-y-4">
              {upcomingDeadlines.map((project) => (
                <div 
                  key={project.id} 
                  className={`border rounded-lg p-4 transition-all duration-200 hover:shadow-md ${getUrgencyColor(project.daysRemaining)}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <h4 className="text-sm font-medium text-gray-900">{project.name}</h4>
                        <span className={`ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getUrgencyBadge(project.daysRemaining)}`}>
                          {project.daysRemaining === 0 ? 'Last Day!' : 
                           project.daysRemaining === 1 ? '1 day left' : 
                           `${project.daysRemaining} days left`}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        by {project.creator} • {project.category}
                      </p>
                      
                      {/* Progress Bar */}
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>Progress</span>
                          <span>{((project.pledged_amount / project.goal_amount) * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-500 ${
                              (project.pledged_amount / project.goal_amount) >= 1 
                                ? 'bg-green-600' 
                                : (project.pledged_amount / project.goal_amount) >= 0.75 
                                ? 'bg-blue-600' 
                                : 'bg-yellow-600'
                            }`}
                            style={{ width: `${Math.min((project.pledged_amount / project.goal_amount) * 100, 100)}%` }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>${project.pledged_amount.toLocaleString()}</span>
                          <span>${project.goal_amount.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right ml-6">
                      <div className="flex flex-col items-end">
                        <div className="text-sm font-medium text-gray-900">
                          {format(new Date(project.deadline), 'MMM dd, yyyy')}
                        </div>
                        <div className="text-xs text-gray-500">
                          {format(new Date(project.deadline), 'h:mm a')}
                        </div>
                        
                        {/* Time indicator */}
                        <div className="mt-2 flex items-center">
                          <ClockIcon className="h-4 w-4 text-gray-400 mr-1" />
                          <span className="text-xs text-gray-500">
                            {project.daysRemaining === 0 ? 'Ending today' :
                             project.daysRemaining <= 7 ? 'Ending soon' :
                             'Active'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Additional project details */}
                  <div className="mt-4 pt-3 border-t border-gray-200 grid grid-cols-3 gap-4 text-xs text-gray-600">
                    <div>
                      <span className="font-medium">Backers:</span> {project.backers_count.toLocaleString()}
                    </div>
                    <div>
                      <span className="font-medium">Risk Level:</span> 
                      <span className={`ml-1 ${
                        project.risk_level === 'high' ? 'text-red-600' :
                        project.risk_level === 'medium' ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        {project.risk_level}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium">Launched:</span> {format(new Date(project.launched_date), 'MMM dd')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <CalendarIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No active projects</h3>
              <p className="mt-1 text-sm text-gray-500">
                Add some live projects to track their deadlines and progress here.
              </p>
            </div>
          )}

          {/* Quick Stats */}
          {upcomingDeadlines.length > 0 && (
            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-lg font-semibold text-red-600">
                    {upcomingDeadlines.filter(p => p.daysRemaining <= 3).length}
                  </div>
                  <div className="text-xs text-gray-500">Ending Soon</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-yellow-600">
                    {upcomingDeadlines.filter(p => p.daysRemaining <= 7 && p.daysRemaining > 3).length}
                  </div>
                  <div className="text-xs text-gray-500">This Week</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-green-600">
                    {upcomingDeadlines.filter(p => (p.pledged_amount / p.goal_amount) >= 1).length}
                  </div>
                  <div className="text-xs text-gray-500">Funded</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-blue-600">
                    {upcomingDeadlines.filter(p => p.risk_level === 'low').length}
                  </div>
                  <div className="text-xs text-gray-500">Low Risk</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CalendarTab;