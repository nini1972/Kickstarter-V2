import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useAppContext } from '../../context/AppContext';

const AlertSettingsModal = ({ isOpen, onClose }) => {
  const { alertSettings, updateAlertSettings, loading } = useAppContext();

  const [formData, setFormData] = useState({
    notification_frequency: 'instant',
    min_funding_velocity: 0.1,
    preferred_categories: ['Technology'],
    max_risk_level: 'medium',
    min_success_probability: 0.6,
    browser_notifications: true,
    email_notifications: false
  });

  useEffect(() => {
    if (alertSettings && Object.keys(alertSettings).length > 0) {
      setFormData({
        notification_frequency: alertSettings.notification_frequency || 'instant',
        min_funding_velocity: alertSettings.min_funding_velocity || 0.1,
        preferred_categories: alertSettings.preferred_categories || ['Technology'],
        max_risk_level: alertSettings.max_risk_level || 'medium',
        min_success_probability: alertSettings.min_success_probability || 0.6,
        browser_notifications: alertSettings.browser_notifications !== false,
        email_notifications: alertSettings.email_notifications === true
      });
    }
  }, [alertSettings]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await updateAlertSettings({
        ...formData,
        user_id: 'default_user'
      });
      onClose();
    } catch (error) {
      console.error('Failed to update alert settings:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : 
               type === 'number' ? parseFloat(value) : value
    }));
  };

  const handleCategoryChange = (category, checked) => {
    setFormData(prev => ({
      ...prev,
      preferred_categories: checked 
        ? [...prev.preferred_categories, category]
        : prev.preferred_categories.filter(c => c !== category)
    }));
  };

  if (!isOpen) return null;

  const categories = ['Technology', 'Design', 'Games', 'Film', 'Music', 'Arts', 'Food', 'Fashion'];

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
      <div className="relative p-5 border w-11/12 md:w-2/3 lg:w-1/2 max-w-2xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">🔔 Alert Settings</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Notification Frequency */}
          <div>
            <label htmlFor="notification_frequency" className="block text-sm font-medium text-gray-700 mb-2">
              Notification Frequency
            </label>
            <select
              id="notification_frequency"
              name="notification_frequency"
              value={formData.notification_frequency}
              onChange={handleInputChange}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="instant">Instant (Real-time)</option>
              <option value="daily">Daily Summary</option>
              <option value="weekly">Weekly Summary</option>
            </select>
            <p className="mt-1 text-sm text-gray-500">
              How often you want to receive alert notifications
            </p>
          </div>

          {/* Funding Velocity Threshold */}
          <div>
            <label htmlFor="min_funding_velocity" className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Funding Velocity ({(formData.min_funding_velocity * 100).toFixed(1)}% per day)
            </label>
            <input
              type="range"
              id="min_funding_velocity"
              name="min_funding_velocity"
              min="0.01"
              max="2.0"
              step="0.01"
              value={formData.min_funding_velocity}
              onChange={handleInputChange}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.1%</span>
              <span>1.0%</span>
              <span>2.0%</span>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Alert when projects fund faster than this rate
            </p>
          </div>

          {/* Success Probability Threshold */}
          <div>
            <label htmlFor="min_success_probability" className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Success Probability ({(formData.min_success_probability * 100).toFixed(0)}%)
            </label>
            <input
              type="range"
              id="min_success_probability"
              name="min_success_probability"
              min="0.1"
              max="1.0"
              step="0.05"
              value={formData.min_success_probability}
              onChange={handleInputChange}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>10%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Only alert for projects with AI-predicted success above this threshold
            </p>
          </div>

          {/* Risk Level */}
          <div>
            <label htmlFor="max_risk_level" className="block text-sm font-medium text-gray-700 mb-2">
              Maximum Risk Level
            </label>
            <select
              id="max_risk_level"
              name="max_risk_level"
              value={formData.max_risk_level}
              onChange={handleInputChange}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="low">Low Risk Only</option>
              <option value="medium">Medium Risk & Below</option>
              <option value="high">All Risk Levels</option>
            </select>
            <p className="mt-1 text-sm text-gray-500">
              Maximum risk level for projects to generate alerts
            </p>
          </div>

          {/* Preferred Categories */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Preferred Categories
            </label>
            <div className="grid grid-cols-2 gap-3">
              {categories.map((category) => (
                <label key={category} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={formData.preferred_categories.includes(category)}
                    onChange={(e) => handleCategoryChange(category, e.target.checked)}
                    className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                  />
                  <span className="text-sm text-gray-700">{category}</span>
                </label>
              ))}
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Select categories you're interested in receiving alerts for
            </p>
          </div>

          {/* Notification Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Notification Methods
            </label>
            <div className="space-y-3">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  name="browser_notifications"
                  checked={formData.browser_notifications}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                />
                <div>
                  <span className="text-sm font-medium text-gray-700">Browser Notifications</span>
                  <p className="text-xs text-gray-500">Get instant desktop notifications</p>
                </div>
              </label>
              
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  name="email_notifications"
                  checked={formData.email_notifications}
                  onChange={handleInputChange}
                  className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                />
                <div>
                  <span className="text-sm font-medium text-gray-700">Email Notifications</span>
                  <p className="text-xs text-gray-500">Receive alerts via email (coming soon)</p>
                </div>
              </label>
            </div>
          </div>

          {/* Alert Preview */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Alert Preview</h4>
            <div className="text-sm text-blue-800">
              <p>You'll receive <strong>{formData.notification_frequency}</strong> notifications for:</p>
              <ul className="mt-2 space-y-1 text-xs">
                <li>• Projects funding faster than <strong>{(formData.min_funding_velocity * 100).toFixed(1)}%</strong> per day</li>
                <li>• Projects with <strong>{(formData.min_success_probability * 100).toFixed(0)}%+</strong> success probability</li>
                <li>• <strong>{formData.max_risk_level}</strong> risk level and below</li>
                <li>• Categories: <strong>{formData.preferred_categories.join(', ')}</strong></li>
              </ul>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading.alerts}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading.alerts ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AlertSettingsModal;