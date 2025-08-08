import { FileText, Download, Plus, Calendar, Filter, Search, Eye, Share2, Clock } from 'lucide-react'

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-neutral">Generated reports and analytics</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search reports..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm w-64"
            />
          </div>
          <button className="flex items-center space-x-2 px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
            <Filter className="h-4 w-4" />
            <span>Filter</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 text-sm bg-primary text-white rounded-md hover:bg-primary-700">
            <Plus className="h-4 w-4" />
            <span>New Report</span>
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Total Reports</p>
              <p className="text-2xl font-semibold text-gray-900">47</p>
            </div>
            <div className="h-12 w-12 bg-primary-50 rounded-lg flex items-center justify-center">
              <FileText className="h-6 w-6 text-primary" />
            </div>
          </div>
          <p className="text-sm text-neutral mt-2">Generated this month</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Scheduled Reports</p>
              <p className="text-2xl font-semibold text-gray-900">12</p>
            </div>
            <div className="h-12 w-12 bg-highlight-50 rounded-lg flex items-center justify-center">
              <Calendar className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <p className="text-sm text-neutral mt-2">Automated generation</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Downloads</p>
              <p className="text-2xl font-semibold text-gray-900">234</p>
            </div>
            <div className="h-12 w-12 bg-success-50 rounded-lg flex items-center justify-center">
              <Download className="h-6 w-6 text-success" />
            </div>
          </div>
          <p className="text-sm text-neutral mt-2">Last 30 days</p>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Shared Reports</p>
              <p className="text-2xl font-semibold text-gray-900">18</p>
            </div>
            <div className="h-12 w-12 bg-soft-50 rounded-lg flex items-center justify-center">
              <Share2 className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <p className="text-sm text-neutral mt-2">Team collaboration</p>
        </div>
      </div>

      {/* Report Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Briefs */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Briefs</h3>
          <div className="space-y-3">
            {[
              { title: 'Executive Daily Brief', date: 'Today, 9:00 AM', status: 'generated' },
              { title: 'Team Status Update', date: 'Today, 8:30 AM', status: 'generated' },
              { title: 'Project Progress Summary', date: 'Yesterday, 9:00 AM', status: 'generated' },
              { title: 'Weekly Team Metrics', date: 'Monday, 9:00 AM', status: 'scheduled' },
            ].map((brief, index) => (
              <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{brief.title}</p>
                  <p className="text-xs text-neutral">{brief.date}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    brief.status === 'generated' ? 'bg-success-100 text-success' : 'bg-highlight-100 text-highlight'
                  }`}>
                    {brief.status}
                  </span>
                  <button className="text-neutral hover:text-gray-900">
                    <Eye className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Analytics Reports */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Analytics Reports</h3>
          <div className="space-y-3">
            {[
              { title: 'Performance Dashboard', date: 'Dec 15, 2023', status: 'ready' },
              { title: 'User Engagement Analysis', date: 'Dec 14, 2023', status: 'ready' },
              { title: 'Query Response Metrics', date: 'Dec 13, 2023', status: 'ready' },
              { title: 'Monthly Usage Report', date: 'Dec 1, 2023', status: 'archived' },
            ].map((report, index) => (
              <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{report.title}</p>
                  <p className="text-xs text-neutral">{report.date}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    report.status === 'ready' ? 'bg-primary-100 text-primary' : 'bg-neutral-100 text-neutral'
                  }`}>
                    {report.status}
                  </span>
                  <button className="text-neutral hover:text-gray-900">
                    <Download className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Custom Reports */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Custom Reports</h3>
          <div className="space-y-3">
            {[
              { title: 'Q4 Team Performance', date: 'Dec 10, 2023', status: 'generating' },
              { title: 'Security Audit Report', date: 'Dec 8, 2023', status: 'ready' },
              { title: 'Integration Health Check', date: 'Dec 5, 2023', status: 'ready' },
              { title: 'Data Quality Assessment', date: 'Dec 1, 2023', status: 'ready' },
            ].map((report, index) => (
              <div key={index} className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{report.title}</p>
                  <p className="text-xs text-neutral">{report.date}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    report.status === 'generating' ? 'bg-highlight-100 text-highlight' : 'bg-success-100 text-success'
                  }`}>
                    {report.status}
                  </span>
                  {report.status === 'generating' ? (
                    <Clock className="h-4 w-4 text-neutral animate-spin" />
                  ) : (
                    <button className="text-neutral hover:text-gray-900">
                      <Download className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Reports Table */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Reports</h3>
          <div className="flex items-center space-x-2">
            <select className="text-sm border border-gray-300 rounded px-3 py-1">
              <option>All Types</option>
              <option>Daily Briefs</option>
              <option>Analytics</option>
              <option>Custom</option>
            </select>
            <select className="text-sm border border-gray-300 rounded px-3 py-1">
              <option>Last 30 days</option>
              <option>Last 7 days</option>
              <option>Last 90 days</option>
            </select>
          </div>
        </div>
        
        <div className="overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Report Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Generated
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {[
                { name: 'Executive Daily Brief', type: 'Daily Brief', date: '2 hours ago', size: '2.4 MB', status: 'Ready' },
                { name: 'Team Performance Analytics', type: 'Analytics', date: '5 hours ago', size: '1.8 MB', status: 'Ready' },
                { name: 'Security Compliance Report', type: 'Custom', date: '1 day ago', size: '3.2 MB', status: 'Ready' },
                { name: 'Weekly Team Summary', type: 'Daily Brief', date: '2 days ago', size: '1.5 MB', status: 'Archived' },
                { name: 'Query Response Analysis', type: 'Analytics', date: '3 days ago', size: '2.1 MB', status: 'Ready' },
              ].map((report, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{report.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-neutral">{report.type}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-neutral">{report.date}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-neutral">{report.size}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      report.status === 'Ready' ? 'bg-success-100 text-success' : 'bg-neutral-100 text-neutral'
                    }`}>
                      {report.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button className="text-primary hover:text-primary-700">
                        <Eye className="h-4 w-4" />
                      </button>
                      <button className="text-neutral hover:text-gray-900">
                        <Download className="h-4 w-4" />
                      </button>
                      <button className="text-neutral hover:text-gray-900">
                        <Share2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}