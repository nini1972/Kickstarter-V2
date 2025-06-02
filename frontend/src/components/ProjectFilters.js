import React, { useState } from 'react';
import { FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';

const ProjectFilters = ({ filters, onFiltersChange, onClear }) => {
  const [isOpen, setIsOpen] = useState(false);

  const categories = [
    'Technology', 'Design', 'Games', 'Film & Video', 'Music', 
    'Art', 'Food', 'Publishing', 'Fashion', 'Comics', 'Crafts'
  ];

  const riskLevels = ['low', 'medium', 'high'];
  const statuses = ['live', 'successful', 'failed', 'upcoming'];

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters };
    
    if (key === 'categories') {
      if (!newFilters.categories) newFilters.categories = [];
      const index = newFilters.categories.indexOf(value);
      if (index > -1) {
        newFilters.categories.splice(index, 1);
      } else {
        newFilters.categories.push(value);
      }
      if (newFilters.categories.length === 0) {
        delete newFilters.categories;
      }
    } else if (key === 'risk_levels') {
      if (!newFilters.risk_levels) newFilters.risk_levels = [];
      const index = newFilters.risk_levels.indexOf(value);
      if (index > -1) {
        newFilters.risk_levels.splice(index, 1);
      } else {
        newFilters.risk_levels.push(value);
      }
      if (newFilters.risk_levels.length === 0) {
        delete newFilters.risk_levels;
      }
    } else if (key === 'status') {
      if (newFilters.status === value) {
        delete newFilters.status;
      } else {
        newFilters.status = value;
      }
    } else {
      if (value === '' || value === null || value === undefined) {
        delete newFilters[key];
      } else {
        newFilters[key] = value;
      }
    }
    
    onFiltersChange(newFilters);
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.categories?.length) count += filters.categories.length;
    if (filters.risk_levels?.length) count += filters.risk_levels.length;
    if (filters.status) count += 1;
    if (filters.search) count += 1;
    if (filters.min_funding || filters.max_funding) count += 1;
    if (filters.sort_by) count += 1;
    return count;
  };

  const activeFilters = getActiveFilterCount();

  return (
    <div className="bg-white border-b border-gray-200">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Search */}
            <div className="flex-1 min-w-0">
              <input
                type="text"
                placeholder="Search projects..."
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            {/* Sort */}
            <select
              value={filters.sort_by || 'created_at'}
              onChange={(e) => handleFilterChange('sort_by', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="created_at">Newest First</option>
              <option value="deadline">Deadline</option>
              <option value="pledged_amount">Funding Amount</option>
              <option value="success_probability">Success Probability</option>
              <option value="name">Name (A-Z)</option>
            </select>

            {/* Filter Toggle */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className={`inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium ${
                activeFilters > 0 
                  ? 'text-indigo-700 bg-indigo-50 border-indigo-300' 
                  : 'text-gray-700 bg-white hover:bg-gray-50'
              } focus:outline-none focus:ring-1 focus:ring-indigo-500`}
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filters
              {activeFilters > 0 && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  {activeFilters}
                </span>
              )}
            </button>

            {/* Clear Filters */}
            {activeFilters > 0 && (
              <button
                onClick={onClear}
                className="inline-flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
              >
                <XMarkIcon className="h-4 w-4 mr-1" />
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Expanded Filters */}
        {isOpen && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* Categories */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Categories
                </label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {categories.map((category) => (
                    <label key={category} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.categories?.includes(category) || false}
                        onChange={() => handleFilterChange('categories', category)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">{category}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Risk Levels */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Risk Level
                </label>
                <div className="space-y-2">
                  {riskLevels.map((risk) => (
                    <label key={risk} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.risk_levels?.includes(risk) || false}
                        onChange={() => handleFilterChange('risk_levels', risk)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{risk}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <div className="space-y-2">
                  {statuses.map((status) => (
                    <label key={status} className="flex items-center">
                      <input
                        type="radio"
                        name="status"
                        checked={filters.status === status}
                        onChange={() => handleFilterChange('status', status)}
                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{status}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Funding Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Funding Range ($)
                </label>
                <div className="space-y-2">
                  <input
                    type="number"
                    placeholder="Min funding"
                    value={filters.min_funding || ''}
                    onChange={(e) => handleFilterChange('min_funding', e.target.value ? parseInt(e.target.value) : null)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <input
                    type="number"
                    placeholder="Max funding"
                    value={filters.max_funding || ''}
                    onChange={(e) => handleFilterChange('max_funding', e.target.value ? parseInt(e.target.value) : null)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectFilters;