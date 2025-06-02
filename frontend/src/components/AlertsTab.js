import React, { useState } from 'react';
import { useAlerts, useMarkAlertAsRead, useDeleteAlert } from '../hooks/useQuery';
import { CheckIcon, TrashIcon, BellAlertIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const AlertsTab = () => {
  const { data: alerts, isLoading, error } = useAlerts();
  const markAsReadMutation = useMarkAlertAsRead();
  const deleteAlertMutation = useDeleteAlert();
  
  const [filter, setFilter] = useState('all'); // 'all', 'unread', 'read'
  
  const handleMarkAsRead = (id) => {
    markAsReadMutation.mutate(id, {
      onSuccess: () => {
        toast.success('Alert marked as read');
      },
      onError: (error) => {
        toast.error(`Failed to mark alert as read: ${error.message}`);
      }
    });
  };
  
  const handleDeleteAlert = (id) => {
    if (window.confirm('Are you sure you want to delete this alert?')) {
      deleteAlertMutation.mutate(id, {
        onSuccess: () => {
          toast.success('Alert deleted successfully');
        },
        onError: (error) => {
          toast.error(`Failed to delete alert: ${error.message}`);
        }
      });
    }
  };
  
  // Filter alerts based on selected filter
  const filteredAlerts = alerts?.filter(alert => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !alert.read;
    if (filter === 'read') return alert.read;
    return true;
  }) || [];
  
  // Count unread alerts
  const unreadCount = alerts?.filter(alert => !alert.read).length || 0;
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="text-red-500 text-center p-4">
        Error loading alerts: {error.message}
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Alerts</h2>
          <div className="flex items-center">
            {unreadCount > 0 && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 mr-4">
                {unreadCount} unread
              </span>
            )}
            <div className="flex border border-gray-300 rounded-md">
              <button
                onClick={() => setFilter('all')}
                className={`px-4 py-2 text-sm font-medium ${
                  filter === 'all'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                } rounded-l-md`}
              >
                All
              </button>
              <button
                onClick={() => setFilter('unread')}
                className={`px-4 py-2 text-sm font-medium ${
                  filter === 'unread'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                } border-l border-gray-300`}
              >
                Unread
              </button>
              <button
                onClick={() => setFilter('read')}
                className={`px-4 py-2 text-sm font-medium ${
                  filter === 'read'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                } border-l border-gray-300 rounded-r-md`}
              >
                Read
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="overflow-hidden">
        <ul className="divide-y divide-gray-200">
          {filteredAlerts.length > 0 ? (
            filteredAlerts.map((alert) => (
              <li
                key={alert.id}
                className={`p-4 hover:bg-gray-50 ${!alert.read ? 'bg-blue-50' : ''}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center ${
                      alert.priority === 'high' ? 'bg-red-100' :
                      alert.priority === 'medium' ? 'bg-yellow-100' : 'bg-green-100'
                    }`}>
                      <BellAlertIcon className={`h-6 w-6 ${
                        alert.priority === 'high' ? 'text-red-600' :
                        alert.priority === 'medium' ? 'text-yellow-600' : 'text-green-600'
                      }`} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{alert.title}</p>
                      <p className="mt-1 text-sm text-gray-500">{alert.message}</p>
                      <p className="mt-1 text-xs text-gray-400">
                        {alert.created_at ? new Date(alert.created_at).toDateString() : 'No date'} {alert.created_at ? new Date(alert.created_at).toTimeString().slice(0, 5) : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    {!alert.read && (
                      <button
                        onClick={() => handleMarkAsRead(alert.id)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Mark as read"
                      >
                        <CheckIcon className="h-5 w-5" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteAlert(alert.id)}
                      className="text-red-600 hover:text-red-900"
                      title="Delete alert"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </li>
            ))
          ) : (
            <li className="p-4 text-center text-gray-500">
              No alerts found for the selected filter.
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default AlertsTab;