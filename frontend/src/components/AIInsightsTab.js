import React from 'react';
import { LightBulbIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { useAppContext } from '../context/AppContext';

const AIInsightsTab = () => {
  const { recommendations, fetchRecommendations, loading, errors } = useAppContext();

  if (errors.recommendations) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading AI insights</h3>
              <p className="mt-2 text-sm text-red-700">{errors.recommendations}</p>
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
            <h3 className="text-lg leading-6 font-medium text-gray-900">🤖 AI-Powered Investment Insights</h3>
            <button
              onClick={fetchRecommendations}
              disabled={loading.recommendations}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              aria-label="Generate new AI recommendations"
            >
              <LightBulbIcon className="h-4 w-4 mr-2" />
              {loading.recommendations ? 'Generating...' : 'Get New Recommendations'}
            </button>
          </div>
          
          {recommendations && recommendations.length > 0 ? (
            <div className="space-y-4">
              {recommendations.map((rec, index) => (
                <div 
                  key={index} 
                  className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors duration-200"
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                        <span className="text-indigo-600 font-semibold text-sm">{index + 1}</span>
                      </div>
                    </div>
                    <div className="ml-3 flex-1">
                      <p className="text-sm text-gray-800 leading-relaxed">{rec}</p>
                    </div>
                  </div>
                </div>
              ))}
              
              {/* AI Confidence Indicator */}
              <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>🤖 Generated by GPT-4 Advanced Analysis</span>
                  <span>Confidence Level: High</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <LightBulbIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No AI insights yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Click the button above to get AI-powered investment insights and portfolio optimization recommendations.
              </p>
              <div className="mt-6">
                <button
                  onClick={fetchRecommendations}
                  disabled={loading.recommendations}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  <LightBulbIcon className="h-4 w-4 mr-2" />
                  {loading.recommendations ? 'Generating...' : 'Generate AI Insights'}
                </button>
              </div>
            </div>
          )}

          {/* AI Features Info */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-4">🎯 What our AI analyzes:</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <p className="ml-3 text-sm text-gray-600">Portfolio diversification across tech categories</p>
                </div>
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <p className="ml-3 text-sm text-gray-600">Risk distribution and balance optimization</p>
                </div>
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                  <p className="ml-3 text-sm text-gray-600">Funding velocity and market momentum</p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                  <p className="ml-3 text-sm text-gray-600">Historical success patterns and trends</p>
                </div>
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-2 h-2 bg-indigo-500 rounded-full mt-2"></div>
                  <p className="ml-3 text-sm text-gray-600">Creator credibility and project quality</p>
                </div>
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                  <p className="ml-3 text-sm text-gray-600">Exit strategies and timing recommendations</p>
                </div>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
              <div className="ml-3">
                <p className="text-xs text-yellow-800">
                  <strong>Investment Disclaimer:</strong> AI recommendations are for informational purposes only and should not be considered as financial advice. 
                  Always conduct your own research and consider consulting with a financial advisor before making investment decisions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIInsightsTab;