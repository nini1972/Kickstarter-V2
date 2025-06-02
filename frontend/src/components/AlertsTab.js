import React from 'react';
import { BellIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { useAppContext } from '../context/AppContext';

const AlertsTab = () => {
  const { alerts, fetchAlerts, loading, errors } = useAppContext();

  const getAlertIcon = (alertType) => {
    switch(alertType) {
      case 'funding_surge': return '🚀';
      case 'high_potential': return '⭐';
      case 'deadline_approaching': return '⏰';
      default: return '💡';
    }
  };

  const getAlertPriorityColor = (priority) => {
    switch(priority) {
      case 'high': return 'border-red-200 bg-red-50';
      case 'medium': return 'border-yellow-200 bg-yellow-50';
      case 'low': return 'border-blue-200 bg-blue-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getPriorityBadgeColor = (priority) => {
    switch(priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading.alerts) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">🔔 Smart Investment Alerts</h3>
            </div>
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <div className="w-8 h-8 bg-gray-300 rounded mr-3"></div>
                    <div className="flex-1">
                      <div className="h-4 bg-gray-300 rounded w-1/4 mb-2"></div>
                      <div className="h-4 bg-gray-300 rounded w-3/4"></div>
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

  if (errors.alerts) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading alerts</h3>
              <p className="mt-2 text-sm text-red-700">{errors.alerts}</p>
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
            <h3 className="text-lg leading-6 font-medium text-gray-900">🔔 Smart Investment Alerts</h3>
            <button
              onClick={fetchAlerts}
              disabled={loading.alerts}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              aria-label="Refresh alerts"
            >
              <BellIcon className="h-4 w-4 mr-2" />
              {loading.alerts ? 'Refreshing...' : 'Refresh Alerts'}
            </button>
          </div>
          
          {alerts.length > 0 ? (
            <div className="space-y-4" role="list" aria-label="Investment alerts">
              {alerts.map((alert, index) => (
                <div 
                  key={`${alert.id || index}`} 
                  className={`border rounded-lg p-4 ${getAlertPriorityColor(alert.priority)} transition-colors duration-200`}
                  role="listitem"
                >
                  <div className="flex items-start">
                    <span className="text-2xl mr-3" aria-hidden="true">
                      {getAlertIcon(alert.alert_type)}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityBadgeColor(alert.priority)}`}>
                          {alert.priority} priority
                        </span>
                        <span className="text-xs text-gray-500">
                          {format(new Date(alert.created_at), 'MMM dd, HH:mm')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-800 leading-relaxed">
                        {alert.message}
                      </p>
                      
                      {/* Alert Type Badge */}
                      <div className="mt-2">
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800">
                          {alert.alert_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <BellIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No alerts yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                We'll notify you when promising projects are detected or when important milestones approach.
              </p>
              <div className="mt-6">
                <button
                  onClick={fetchAlerts}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <BellIcon className="h-4 w-4 mr-2" />
                  Check for Alerts
                </button>
              </div>
            </div>
          )}

          {/* Alert Statistics */}
          {alerts.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-lg font-semibold text-red-600">
                    {alerts.filter(a => a.priority === 'high').length}
                  </div>
                  <div className="text-xs text-gray-500">High Priority</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-yellow-600">
                    {alerts.filter(a => a.priority === 'medium').length}
                  </div>
                  <div className="text-xs text-gray-500">Medium Priority</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-blue-600">
                    {alerts.filter(a => a.priority === 'low').length}
                  </div>
                  <div className="text-xs text-gray-500">Low Priority</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlertsTab;