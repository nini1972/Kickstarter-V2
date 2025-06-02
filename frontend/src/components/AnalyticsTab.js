import React, { memo, useState, useEffect } from 'react';
import { ArrowTrendingUpIcon, ChartBarIcon, LightBulbIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useAppContext } from '../context/AppContext';

const AnalyticsTab = memo(() => {
  const { advancedAnalytics, fundingTrends, loading, errors } = useAppContext();
  
  // Responsive chart dimensions
  const [chartDimensions, setChartDimensions] = useState({
    width: '100%',
    height: 400
  });

  useEffect(() => {
    const updateChartDimensions = () => {
      const screenWidth = window.innerWidth;
      if (screenWidth < 640) { // Mobile
        setChartDimensions({ width: '100%', height: 300 });
      } else if (screenWidth < 768) { // Tablet
        setChartDimensions({ width: '100%', height: 350 });
      } else { // Desktop
        setChartDimensions({ width: '100%', height: 400 });
      }
    };

    updateChartDimensions();
    window.addEventListener('resize', updateChartDimensions);
    
    return () => window.removeEventListener('resize', updateChartDimensions);
  }, []);

  if (loading.analytics) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="space-y-6">
          {/* Analytics Cards Loading */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white overflow-hidden shadow rounded-lg animate-pulse">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-6 w-6 bg-gray-300 rounded"></div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <div className="h-4 bg-gray-300 rounded mb-2"></div>
                      <div className="h-6 bg-gray-300 rounded"></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Chart Loading */}
          <div className="bg-white overflow-hidden shadow rounded-lg animate-pulse">
            <div className="px-4 py-5 sm:p-6">
              <div className="h-6 bg-gray-300 rounded mb-6 w-1/3"></div>
              <div className="h-96 bg-gray-300 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (errors.analytics) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading analytics</h3>
              <p className="mt-2 text-sm text-red-700">{errors.analytics}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="space-y-6">
        {/* Advanced Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ArrowTrendingUpIcon className="h-6 w-6 text-green-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">ROI Prediction</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {advancedAnalytics.roi_prediction || 0}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-6 w-6 text-blue-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Avg Funding Velocity</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {advancedAnalytics.funding_velocity || 0}%/day
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <LightBulbIcon className="h-6 w-6 text-yellow-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Market Sentiment</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {(advancedAnalytics.market_sentiment * 100 || 0).toFixed(0)}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-6 w-6 text-purple-400" aria-hidden="true" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Diversification Score</dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {(advancedAnalytics.diversification_score * 100 || 0).toFixed(0)}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Risk-Adjusted Return */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 overflow-hidden shadow rounded-lg">
          <div className="p-5 text-white">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ArrowTrendingUpIcon className="h-8 w-8 text-white" aria-hidden="true" />
              </div>
              <div className="ml-5">
                <h3 className="text-lg font-medium">Risk-Adjusted Return</h3>
                <p className="text-3xl font-bold">
                  {advancedAnalytics.risk_adjusted_return || 0}%
                </p>
                <p className="text-sm opacity-90">
                  Predicted return adjusted for portfolio risk level
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Funding Trends Chart */}
        {fundingTrends && fundingTrends.length > 0 && (
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-6">
                📈 Funding Velocity vs Success Probability
              </h3>
              
              {/* Responsive Chart Container */}
              <div className="w-full" style={{ minHeight: chartDimensions.height }}>
                <ResponsiveContainer 
                  width={chartDimensions.width} 
                  height={chartDimensions.height}
                >
                  <BarChart 
                    data={fundingTrends}
                    margin={{
                      top: 20,
                      right: 30,
                      left: 20,
                      bottom: window.innerWidth < 640 ? 80 : 60
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      tick={{ fontSize: window.innerWidth < 640 ? 10 : 12 }}
                      interval={0}
                      angle={window.innerWidth < 640 ? -45 : -30}
                      textAnchor="end"
                      height={window.innerWidth < 640 ? 80 : 60}
                    />
                    <YAxis tick={{ fontSize: window.innerWidth < 640 ? 10 : 12 }} />
                    <Tooltip 
                      formatter={(value, name) => [
                        `${value.toFixed(1)}${name.includes('Velocity') ? '%/day' : '%'}`, 
                        name
                      ]}
                      contentStyle={{
                        backgroundColor: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '0.375rem',
                        fontSize: window.innerWidth < 640 ? '12px' : '14px'
                      }}
                    />
                    <Legend 
                      wrapperStyle={{ fontSize: window.innerWidth < 640 ? '12px' : '14px' }}
                    />
                    <Bar 
                      dataKey="velocity" 
                      fill="#3B82F6" 
                      name="Funding Velocity (%/day)"
                      radius={[2, 2, 0, 0]}
                    />
                    <Bar 
                      dataKey="success_probability" 
                      fill="#10B981" 
                      name="Success Probability (%)"
                      radius={[2, 2, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              
              {/* Chart Description for Screen Readers */}
              <div className="sr-only" aria-label="Chart description">
                Bar chart showing funding velocity versus success probability for {fundingTrends.length} projects. 
                Funding velocity ranges from {Math.min(...fundingTrends.map(t => t.velocity)).toFixed(1)} to {Math.max(...fundingTrends.map(t => t.velocity)).toFixed(1)} percent per day. 
                Success probability ranges from {Math.min(...fundingTrends.map(t => t.success_probability)).toFixed(1)} to {Math.max(...fundingTrends.map(t => t.success_probability)).toFixed(1)} percent.
              </div>
            </div>
          </div>
        )}

        {/* AI Recommendations */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              🤖 AI Portfolio Recommendations
            </h3>
            {advancedAnalytics.recommended_actions && advancedAnalytics.recommended_actions.length > 0 ? (
              <div className="space-y-3">
                {advancedAnalytics.recommended_actions.map((action, index) => (
                  <div key={index} className="flex items-start p-3 bg-blue-50 rounded-lg">
                    <span className="flex-shrink-0 h-6 w-6 text-indigo-600" aria-hidden="true">💡</span>
                    <p className="ml-3 text-sm text-gray-700 leading-relaxed">{action}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <LightBulbIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-gray-500">
                  Add more investments to get personalized AI recommendations for portfolio optimization.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Portfolio Health Score */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5 text-center">
              <div className="text-2xl font-bold text-green-600">
                {advancedAnalytics.market_sentiment ? (advancedAnalytics.market_sentiment * 100).toFixed(0) : 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">Portfolio Confidence</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                <div 
                  className="bg-green-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(advancedAnalytics.market_sentiment || 0) * 100}%` }}
                  role="progressbar"
                  aria-valuenow={(advancedAnalytics.market_sentiment || 0) * 100}
                  aria-valuemin="0"
                  aria-valuemax="100"
                  aria-label={`Portfolio confidence: ${((advancedAnalytics.market_sentiment || 0) * 100).toFixed(0)}%`}
                ></div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5 text-center">
              <div className="text-2xl font-bold text-blue-600">
                {advancedAnalytics.diversification_score ? (advancedAnalytics.diversification_score * 100).toFixed(0) : 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">Diversification Level</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(advancedAnalytics.diversification_score || 0) * 100}%` }}
                  role="progressbar"
                  aria-valuenow={(advancedAnalytics.diversification_score || 0) * 100}
                  aria-valuemin="0"
                  aria-valuemax="100"
                  aria-label={`Diversification level: ${((advancedAnalytics.diversification_score || 0) * 100).toFixed(0)}%`}
                ></div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5 text-center">
              <div className="text-2xl font-bold text-purple-600">
                {advancedAnalytics.funding_velocity || 0}
              </div>
              <div className="text-sm text-gray-500 mt-1">Avg Funding Speed (%/day)</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                <div 
                  className="bg-purple-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min((advancedAnalytics.funding_velocity || 0) * 10, 100)}%` }}
                  role="progressbar"
                  aria-valuenow={Math.min((advancedAnalytics.funding_velocity || 0) * 10, 100)}
                  aria-valuemin="0"
                  aria-valuemax="100"
                  aria-label={`Average funding speed: ${advancedAnalytics.funding_velocity || 0}% per day`}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

AnalyticsTab.displayName = 'AnalyticsTab';

export default AnalyticsTab;