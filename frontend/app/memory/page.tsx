import { Database, Brain, Settings, Trash2, Download, Upload, Eye, EyeOff } from 'lucide-react'

export default function MemoryPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Memory</h1>
          <p className="text-neutral">Manage your AI's memory and preferences</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
            <Download className="h-4 w-4" />
            <span>Export Memory</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 text-sm bg-primary text-white rounded-md hover:bg-primary-700">
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </button>
        </div>
      </div>

      {/* Memory Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Total Memories</p>
              <p className="text-2xl font-semibold text-gray-900">2,847</p>
            </div>
            <div className="h-12 w-12 bg-primary-50 rounded-lg flex items-center justify-center">
              <Database className="h-6 w-6 text-primary" />
            </div>
          </div>
          <p className="text-sm text-neutral mt-2">Last updated 5 minutes ago</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Learning Rate</p>
              <p className="text-2xl font-semibold text-gray-900">94%</p>
            </div>
            <div className="h-12 w-12 bg-success-50 rounded-lg flex items-center justify-center">
              <Brain className="h-6 w-6 text-success" />
            </div>
          </div>
          <p className="text-sm text-neutral mt-2">High accuracy score</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Storage Used</p>
              <p className="text-2xl font-semibold text-gray-900">1.2GB</p>
            </div>
            <div className="h-12 w-12 bg-highlight-50 rounded-lg flex items-center justify-center">
              <Database className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-highlight h-2 rounded-full" style={{ width: '24%' }}></div>
            </div>
            <p className="text-sm text-neutral mt-1">24% of 5GB limit</p>
          </div>
        </div>
      </div>

      {/* Memory Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Personal Preferences */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Personal Preferences</h3>
          <div className="space-y-4">
            {[
              { category: 'Communication Style', value: 'Professional, concise', count: 45 },
              { category: 'Meeting Preferences', value: 'Morning slots preferred', count: 23 },
              { category: 'Project Priorities', value: 'User experience focus', count: 67 },
              { category: 'Decision Making', value: 'Data-driven approach', count: 34 },
            ].map((pref, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{pref.category}</p>
                  <p className="text-sm text-neutral">{pref.value}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs bg-primary-100 text-primary px-2 py-1 rounded-full">
                    {pref.count} patterns
                  </span>
                  <button className="text-neutral hover:text-gray-900">
                    <Eye className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Team Context */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Team Context</h3>
          <div className="space-y-4">
            {[
              { category: 'Team Dynamics', value: 'Collaborative, async-first', count: 89 },
              { category: 'Project History', value: 'E-commerce platform focus', count: 156 },
              { category: 'Key Stakeholders', value: 'Product, Engineering, Design', count: 34 },
              { category: 'Success Metrics', value: 'User engagement, performance', count: 78 },
            ].map((context, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{context.category}</p>
                  <p className="text-sm text-neutral">{context.value}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs bg-success-100 text-success px-2 py-1 rounded-full">
                    {context.count} memories
                  </span>
                  <button className="text-neutral hover:text-gray-900">
                    <Eye className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Memory Activity */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Memory Activity</h3>
          <button className="text-sm text-primary hover:text-primary-700">View all</button>
        </div>
        <div className="space-y-3">
          {[
            { type: 'learned', content: 'Preference for morning meetings updated', time: '2 hours ago', source: 'Calendar analysis' },
            { type: 'stored', content: 'New project stakeholder information saved', time: '5 hours ago', source: 'Team conversation' },
            { type: 'updated', content: 'Communication style pattern refined', time: '1 day ago', source: 'Email interactions' },
            { type: 'learned', content: 'Decision-making preference identified', time: '2 days ago', source: 'Meeting notes' },
          ].map((activity, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg">
              <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                activity.type === 'learned' ? 'bg-success-50' :
                activity.type === 'stored' ? 'bg-primary-50' : 'bg-highlight-50'
              }`}>
                <Brain className={`h-4 w-4 ${
                  activity.type === 'learned' ? 'text-success' :
                  activity.type === 'stored' ? 'text-primary' : 'text-highlight'
                }`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900">{activity.content}</p>
                <div className="flex items-center space-x-2 mt-1">
                  <p className="text-xs text-neutral">{activity.time}</p>
                  <span className="text-xs text-neutral">•</span>
                  <p className="text-xs text-neutral">Source: {activity.source}</p>
                </div>
              </div>
              <button className="text-neutral hover:text-gray-900">
                <EyeOff className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Memory Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Memory Controls</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="flex items-center justify-center space-x-2 p-4 border border-gray-300 rounded-lg hover:bg-gray-50">
            <Upload className="h-5 w-5 text-neutral" />
            <span className="text-sm font-medium">Import Memories</span>
          </button>
          <button className="flex items-center justify-center space-x-2 p-4 border border-gray-300 rounded-lg hover:bg-gray-50">
            <Download className="h-5 w-5 text-neutral" />
            <span className="text-sm font-medium">Export Memories</span>
          </button>
          <button className="flex items-center justify-center space-x-2 p-4 border border-red-300 text-red-600 rounded-lg hover:bg-red-50">
            <Trash2 className="h-5 w-5" />
            <span className="text-sm font-medium">Reset Memory</span>
          </button>
        </div>
      </div>
    </div>
  )
}