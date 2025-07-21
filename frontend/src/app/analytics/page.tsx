import { BarChart3, TrendingUp, TrendingDown, Activity, Users, MessageSquare, Clock, Target } from 'lucide-react'

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-neutral">Performance metrics and insights</p>
        </div>
        <div className="flex items-center space-x-3">
          <select className="rounded-md border border-gray-300 px-3 py-2 text-sm">
            <option>Last 7 days</option>
            <option>Last 30 days</option>
            <option>Last 90 days</option>
            <option>Last year</option>
          </select>
          <button className="flex items-center space-x-2 px-4 py-2 text-sm bg-primary text-white rounded-md hover:bg-primary-700">
            <BarChart3 className="h-4 w-4" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Total Queries</p>
              <p className="text-2xl font-semibold text-gray-900">1,247</p>
            </div>
            <div className="h-12 w-12 bg-primary-50 rounded-lg flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-primary" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-success mr-1" />
            <span className="text-success">+23%</span>
            <span className="text-neutral ml-1">vs last period</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Response Time</p>
              <p className="text-2xl font-semibold text-gray-900">1.2s</p>
            </div>
            <div className="h-12 w-12 bg-success-50 rounded-lg flex items-center justify-center">
              <Clock className="h-6 w-6 text-success" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingDown className="h-4 w-4 text-success mr-1" />
            <span className="text-success">-0.3s</span>
            <span className="text-neutral ml-1">faster</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Accuracy Rate</p>
              <p className="text-2xl font-semibold text-gray-900">94.2%</p>
            </div>
            <div className="h-12 w-12 bg-highlight-50 rounded-lg flex items-center justify-center">
              <Target className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-success mr-1" />
            <span className="text-success">+2.1%</span>
            <span className="text-neutral ml-1">improvement</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Active Users</p>
              <p className="text-2xl font-semibold text-gray-900">87</p>
            </div>
            <div className="h-12 w-12 bg-soft-50 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-success mr-1" />
            <span className="text-success">+12</span>
            <span className="text-neutral ml-1">new users</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Query Volume Chart */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Query Volume</h3>
          <div className="h-64 flex items-end justify-center space-x-2">
            {[85, 92, 78, 95, 88, 102, 96].map((height, index) => (
              <div key={index} className="flex flex-col items-center">
                <div 
                  className="w-8 bg-primary rounded-t"
                  style={{ height: `${height}px` }}
                ></div>
                <span className="text-xs text-neutral mt-2">
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index]}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Response Time Trend */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Response Time Trend</h3>
          <div className="h-64 flex items-center justify-center">
            <svg className="w-full h-full" viewBox="0 0 300 200">
              <polyline
                fill="none"
                stroke="#1A2D64"
                strokeWidth="2"
                points="20,180 60,160 100,140 140,120 180,110 220,100 260,95"
              />
              <circle cx="20" cy="180" r="3" fill="#1A2D64" />
              <circle cx="60" cy="160" r="3" fill="#1A2D64" />
              <circle cx="100" cy="140" r="3" fill="#1A2D64" />
              <circle cx="140" cy="120" r="3" fill="#1A2D64" />
              <circle cx="180" cy="110" r="3" fill="#1A2D64" />
              <circle cx="220" cy="100" r="3" fill="#1A2D64" />
              <circle cx="260" cy="95" r="3" fill="#1A2D64" />
            </svg>
          </div>
          <div className="flex justify-between text-xs text-neutral mt-2">
            <span>7 days ago</span>
            <span>Today</span>
          </div>
        </div>
      </div>

      {/* Usage Patterns & Top Queries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage Patterns */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Patterns</h3>
          <div className="space-y-4">
            {[
              { time: '9:00 AM', usage: 85, label: 'Morning standup queries' },
              { time: '11:00 AM', usage: 95, label: 'Mid-morning peak' },
              { time: '2:00 PM', usage: 70, label: 'Post-lunch activity' },
              { time: '4:00 PM', usage: 88, label: 'End-of-day planning' },
              { time: '6:00 PM', usage: 40, label: 'Evening wind-down' },
            ].map((pattern, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-medium text-gray-900 w-16">{pattern.time}</span>
                  <div className="flex-1">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-primary h-2 rounded-full" 
                        style={{ width: `${pattern.usage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
                <span className="text-sm text-neutral">{pattern.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Query Categories */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Query Categories</h3>
          <div className="space-y-3">
            {[
              { category: 'Project Status', count: 342, percentage: 28 },
              { category: 'Team Updates', count: 298, percentage: 24 },
              { category: 'Technical Questions', count: 267, percentage: 21 },
              { category: 'Meeting Summaries', count: 189, percentage: 15 },
              { category: 'Resource Requests', count: 151, percentage: 12 },
            ].map((query, index) => (
              <div key={index} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{query.category}</p>
                  <p className="text-xs text-neutral">{query.count} queries</p>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-highlight h-2 rounded-full" 
                      style={{ width: `${query.percentage * 3}px` }}
                    ></div>
                  </div>
                  <span className="text-sm text-neutral w-8">{query.percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Insights */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="h-16 w-16 bg-success-50 rounded-full flex items-center justify-center mx-auto mb-3">
              <TrendingUp className="h-8 w-8 text-success" />
            </div>
            <h4 className="text-lg font-semibold text-gray-900">Response Quality</h4>
            <p className="text-sm text-neutral mt-1">94.2% satisfaction rate with 8% improvement this month</p>
          </div>
          <div className="text-center">
            <div className="h-16 w-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-3">
              <Activity className="h-8 w-8 text-primary" />
            </div>
            <h4 className="text-lg font-semibold text-gray-900">System Health</h4>
            <p className="text-sm text-neutral mt-1">99.8% uptime with average 1.2s response time</p>
          </div>
          <div className="text-center">
            <div className="h-16 w-16 bg-highlight-50 rounded-full flex items-center justify-center mx-auto mb-3">
              <Target className="h-8 w-8 text-highlight" />
            </div>
            <h4 className="text-lg font-semibold text-gray-900">Goal Achievement</h4>
            <p className="text-sm text-neutral mt-1">87% of queries resolved on first attempt</p>
          </div>
        </div>
      </div>
    </div>
  )
}