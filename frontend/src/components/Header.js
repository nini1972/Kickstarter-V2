import React from 'react';
import { ArrowTrendingUpIcon, BellIcon, PlusIcon, BanknotesIcon, Cog6ToothIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import { useAppContext } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';

const Header = ({ onAddProject, onAddInvestment, onShowAlertSettings }) => {
  const { alerts } = useAppContext();
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <ArrowTrendingUpIcon className="h-8 w-8 text-indigo-600 mr-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Kickstarter Investment Tracker</h1>
              {user && (
                <p className="text-sm text-gray-500">Welcome, {user.username || user.email}</p>
              )}
            </div>
            {alerts.length > 0 && (
              <div className="ml-4 flex items-center">
                <BellIcon className="h-6 w-6 text-red-500 animate-pulse" />
                <span className="ml-1 bg-red-500 text-white rounded-full px-2 py-1 text-xs font-bold">
                  {alerts.length}
                </span>
              </div>
            )}
          </div>
          <div className="flex space-x-4">
            <button
              onClick={onShowAlertSettings}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              aria-label="Alert Settings"
            >
              <Cog6ToothIcon className="h-4 w-4 mr-2" />
              Alert Settings
            </button>
            <button
              onClick={onAddProject}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              aria-label="Add New Project"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Add Project
            </button>
            <button
              onClick={onAddInvestment}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              aria-label="Add New Investment"
            >
              <BanknotesIcon className="h-4 w-4 mr-2" />
              Add Investment
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;