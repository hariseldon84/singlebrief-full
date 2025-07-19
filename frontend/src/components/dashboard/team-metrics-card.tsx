'use client'

import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react'

// Mock chart data
const weeklyMetrics = [
  { day: 'Mon', queries: 12, responses: 28, satisfaction: 4.2 },
  { day: 'Tue', queries: 15, responses: 35, satisfaction: 4.5 },
  { day: 'Wed', queries: 8, responses: 18, satisfaction: 4.1 },
  { day: 'Thu', queries: 18, responses: 42, satisfaction: 4.7 },
  { day: 'Fri', queries: 22, responses: 51, satisfaction: 4.6 },
  { day: 'Sat', queries: 5, responses: 8, satisfaction: 4.3 },
  { day: 'Sun', queries: 3, responses: 5, satisfaction: 4.0 },
]

export function TeamMetricsCard() {
  const totalQueries = weeklyMetrics.reduce((sum, day) => sum + day.queries, 0)
  const totalResponses = weeklyMetrics.reduce((sum, day) => sum + day.responses, 0)
  const avgSatisfaction = weeklyMetrics.reduce((sum, day) => sum + day.satisfaction, 0) / weeklyMetrics.length
  const responseRate = ((totalResponses / totalQueries) * 100).toFixed(1)

  const maxQueries = Math.max(...weeklyMetrics.map(d => d.queries))

  return (
    <div className="bg-white rounded-lg shadow-soft border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-medium text-gray-900">Team Performance</h3>
        </div>
        <select className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary">
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>Last 90 days</option>
        </select>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="text-center p-4 bg-primary-50 rounded-md">
          <p className="text-2xl font-semibold text-primary">{totalQueries}</p>
          <p className="text-sm text-neutral">Total Queries</p>
          <div className="flex items-center justify-center space-x-1 mt-1">
            <TrendingUp className="h-3 w-3 text-success" />
            <span className="text-xs text-success">+12%</span>
          </div>
        </div>
        
        <div className="text-center p-4 bg-success-50 rounded-md">
          <p className="text-2xl font-semibold text-success">{responseRate}%</p>
          <p className="text-sm text-neutral">Response Rate</p>
          <div className="flex items-center justify-center space-x-1 mt-1">
            <TrendingUp className="h-3 w-3 text-success" />
            <span className="text-xs text-success">+5%</span>
          </div>
        </div>
        
        <div className="text-center p-4 bg-highlight-50 rounded-md">
          <p className="text-2xl font-semibold text-highlight">{avgSatisfaction.toFixed(1)}</p>
          <p className="text-sm text-neutral">Satisfaction</p>
          <div className="flex items-center justify-center space-x-1 mt-1">
            <TrendingDown className="h-3 w-3 text-red-500" />
            <span className="text-xs text-red-500">-0.1</span>
          </div>
        </div>
      </div>

      {/* Simple Bar Chart */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-gray-900">Daily Query Volume</h4>
        <div className="space-y-2">
          {weeklyMetrics.map((day, index) => (
            <div key={index} className="flex items-center space-x-3">
              <span className="text-xs font-medium text-neutral w-8">{day.day}</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(day.queries / maxQueries) * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium text-gray-900 w-6">{day.queries}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <button className="w-full text-sm text-primary hover:text-primary-700 font-medium transition-colors">
          View Detailed Analytics →
        </button>
      </div>
    </div>
  )
}