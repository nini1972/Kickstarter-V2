import React, { memo } from 'react';
import { BanknotesIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { useAppContext } from '../context/AppContext';

const InvestmentsTab = memo(() => {
  const { investments, projects, loading, errors } = useAppContext();

  if (loading.investments) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Your Investments</h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">Track your financial commitments</p>
          </div>
          <div className="animate-pulse">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {['Project', 'Amount', 'Date', 'Expected Return', 'Notes'].map((header) => (
                      <th key={header} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {[...Array(3)].map((_, i) => (
                    <tr key={i}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="h-4 bg-gray-300 rounded w-32"></div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="h-4 bg-gray-300 rounded w-16"></div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="h-4 bg-gray-300 rounded w-20"></div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="h-4 bg-gray-300 rounded w-16"></div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="h-4 bg-gray-300 rounded w-24"></div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (errors.investments) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading investments</h3>
              <p className="mt-2 text-sm text-red-700">{errors.investments}</p>
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
          <h3 className="text-lg leading-6 font-medium text-gray-900">Your Investments</h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">Track your financial commitments</p>
        </div>
        
        {investments.length > 0 ? (
          <>
            {/* Mobile Card View - Hidden on larger screens */}
            <div className="block md:hidden">
              <div className="space-y-4 p-4">
                {investments.map((investment) => {
                  const project = projects.find(p => p.id === investment.project_id);
                  const roi = investment.expected_return && investment.amount 
                    ? ((investment.expected_return - investment.amount) / investment.amount * 100).toFixed(1)
                    : null;
                  
                  return (
                    <div key={investment.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {project?.name || 'Unknown Project'}
                        </h4>
                        <span className="text-lg font-semibold text-indigo-600">
                          ${investment.amount?.toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="space-y-2 text-sm text-gray-600">
                        <div className="flex justify-between">
                          <span>Date:</span>
                          <span>{format(new Date(investment.investment_date), 'MMM dd, yyyy')}</span>
                        </div>
                        
                        {investment.expected_return && (
                          <div className="flex justify-between">
                            <span>Expected Return:</span>
                            <span className="font-medium">${investment.expected_return.toLocaleString()}</span>
                          </div>
                        )}
                        
                        {roi && (
                          <div className="flex justify-between">
                            <span>ROI:</span>
                            <span className={`font-medium ${
                              parseFloat(roi) > 0 ? 'text-green-600' : 
                              parseFloat(roi) < 0 ? 'text-red-600' : 'text-gray-600'
                            }`}>
                              {roi > 0 ? '+' : ''}{roi}%
                            </span>
                          </div>
                        )}
                        
                        {investment.reward_tier && (
                          <div className="flex justify-between">
                            <span>Tier:</span>
                            <span className="font-medium">{investment.reward_tier}</span>
                          </div>
                        )}
                        
                        {project && (
                          <div className="flex justify-between">
                            <span>Status:</span>
                            <span className={`font-medium ${
                              project.status === 'successful' ? 'text-green-600' :
                              project.status === 'live' ? 'text-blue-600' :
                              'text-red-600'
                            }`}>
                              {project.status}
                            </span>
                          </div>
                        )}
                        
                        {investment.notes && (
                          <div className="mt-2 pt-2 border-t border-gray-200">
                            <span className="text-xs text-gray-500">Notes:</span>
                            <p className="text-sm text-gray-700 mt-1">{investment.notes}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Desktop Table View - Hidden on mobile */}
            <div className="hidden md:block">
              <div className="table-container overflow-x-auto">
                <table 
                  className="min-w-full divide-y divide-gray-200"
                  role="table"
                  aria-label="Investment details"
                >
                  <thead className="bg-gray-50">
                    <tr role="row">
                      <th 
                        scope="col" 
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Project
                      </th>
                      <th 
                        scope="col" 
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Amount
                      </th>
                      <th 
                        scope="col" 
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Date
                      </th>
                      <th 
                        scope="col" 
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Expected Return
                      </th>
                      <th 
                        scope="col" 
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        ROI
                      </th>
                      <th 
                        scope="col" 
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        Notes
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {investments.map((investment) => {
                      const project = projects.find(p => p.id === investment.project_id);
                      const roi = investment.expected_return && investment.amount 
                        ? ((investment.expected_return - investment.amount) / investment.amount * 100).toFixed(1)
                        : null;
                      
                      return (
                        <tr key={investment.id} className="hover:bg-gray-50" role="row">
                          <td className="px-6 py-4 whitespace-nowrap" role="cell">
                            <div className="flex items-center">
                              <div>
                                <div className="text-sm font-medium text-gray-900">
                                  {project?.name || 'Unknown Project'}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {investment.reward_tier || 'No tier specified'}
                                </div>
                                {project && (
                                  <div className="text-xs text-gray-400">
                                    {project.category} • {project.status}
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" role="cell">
                            <div className="text-sm text-gray-900 font-medium">
                              ${investment.amount?.toLocaleString()}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" role="cell">
                            <div className="text-sm text-gray-900">
                              {format(new Date(investment.investment_date), 'MMM dd, yyyy')}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" role="cell">
                            <div className="text-sm text-gray-900">
                              {investment.expected_return 
                                ? `$${investment.expected_return.toLocaleString()}` 
                                : 'N/A'
                              }
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" role="cell">
                            {roi ? (
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                parseFloat(roi) > 0 
                                  ? 'bg-green-100 text-green-800' 
                                  : parseFloat(roi) < 0 
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {roi > 0 ? '+' : ''}{roi}%
                              </span>
                            ) : (
                              <span className="text-sm text-gray-500">N/A</span>
                            )}
                          </td>
                          <td className="px-6 py-4" role="cell">
                            <div className="text-sm text-gray-900 max-w-xs truncate" title={investment.notes}>
                              {investment.notes || 'No notes'}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="px-6 py-12 text-center">
            <BanknotesIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No investments yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Add your first investment to start tracking your portfolio performance!
            </p>
          </div>
        )}
      </div>
    </div>
  );
});

InvestmentsTab.displayName = 'InvestmentsTab';

export default InvestmentsTab;