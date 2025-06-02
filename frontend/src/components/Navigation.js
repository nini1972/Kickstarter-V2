import React from 'react';
import { 
  ChartBarIcon, 
  ClockIcon, 
  BanknotesIcon, 
  BellIcon, 
  ArrowTrendingUpIcon, 
  CalendarIcon, 
  LightBulbIcon 
} from '@heroicons/react/24/outline';
import { useAppContext } from '../context/AppContext';

const Navigation = ({ activeTab, setActiveTab }) => {
  const { alerts } = useAppContext();

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: ChartBarIcon },
    { id: 'projects', name: 'Projects', icon: ClockIcon },
    { id: 'investments', name: 'Investments', icon: BanknotesIcon },
    { id: 'alerts', name: 'Smart Alerts', icon: BellIcon, badge: alerts.length },
    { id: 'analytics', name: 'Advanced Analytics', icon: ArrowTrendingUpIcon },
    { id: 'calendar', name: 'Calendar', icon: CalendarIcon },
    { id: 'ai-insights', name: 'AI Insights', icon: LightBulbIcon }
  ];

  return (
    <nav className="bg-white shadow-sm" role="navigation" aria-label="Main navigation">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center relative ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              aria-label={`Switch to ${tab.name} tab`}
              aria-current={activeTab === tab.id ? 'page' : undefined}
            >
              <tab.icon className="h-5 w-5 mr-2" aria-hidden="true" />
              {tab.name}
              {tab.badge > 0 && (
                <span 
                  className="ml-2 bg-red-500 text-white rounded-full px-2 py-1 text-xs font-bold"
                  aria-label={`${tab.badge} new alerts`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;