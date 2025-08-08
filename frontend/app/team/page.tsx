/**
 * Team Status Page
 */

'use client'

import { Users, MessageCircle, Calendar, CheckCircle, TrendingUp, Activity, MessageSquare, Clock } from 'lucide-react'

export default function TeamPage() {
  const teamMembers = [
    { name: 'Sarah Chen', role: 'Frontend Developer', status: 'active', lastSeen: '2 minutes ago' },
    { name: 'Mike Johnson', role: 'Backend Developer', status: 'busy', lastSeen: '15 minutes ago' },
    { name: 'Emma Wilson', role: 'Product Manager', status: 'active', lastSeen: '5 minutes ago' },
    { name: 'Alex Rodriguez', role: 'DevOps Engineer', status: 'offline', lastSeen: '2 hours ago' },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Status</h1>
          <p className="text-neutral">Monitor team activity and insights</p>
        </div>
        <div className="flex items-center space-x-3">
          <select className="rounded-md border border-gray-300 px-3 py-2 text-sm">
            <option>Last 7 days</option>
            <option>Last 30 days</option>
            <option>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Active Members</p>
              <p className="text-2xl font-semibold text-gray-900">24</p>
            </div>
            <div className="h-12 w-12 bg-primary-50 rounded-lg flex items-center justify-center">
              <Users className="h-6 w-6 text-primary" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-success mr-1" />
            <span className="text-success">+12%</span>
            <span className="text-neutral ml-1">from last week</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Messages Today</p>
              <p className="text-2xl font-semibold text-gray-900">156</p>
            </div>
            <div className="h-12 w-12 bg-highlight-50 rounded-lg flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-success mr-1" />
            <span className="text-success">+8%</span>
            <span className="text-neutral ml-1">from yesterday</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Response Rate</p>
              <p className="text-2xl font-semibold text-gray-900">87%</p>
            </div>
            <div className="h-12 w-12 bg-success-50 rounded-lg flex items-center justify-center">
              <Activity className="h-6 w-6 text-success" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-success mr-1" />
            <span className="text-success">+3%</span>
            <span className="text-neutral ml-1">from last week</span>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral">Avg Response Time</p>
              <p className="text-2xl font-semibold text-gray-900">1.2h</p>
            </div>
            <div className="h-12 w-12 bg-soft-50 rounded-lg flex items-center justify-center">
              <Clock className="h-6 w-6 text-highlight" />
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <TrendingUp className="h-4 w-4 text-success mr-1" />
            <span className="text-success">-15m</span>
            <span className="text-neutral ml-1">faster than last week</span>
          </div>
        </div>
      </div>

      {/* Team Activity & Members */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {[
              { user: 'Sarah Chen', action: 'Responded to intelligence query', time: '2 min ago', type: 'response' },
              { user: 'Mike Johnson', action: 'Updated project status', time: '15 min ago', type: 'update' },
              { user: 'Emma Davis', action: 'Shared team metrics', time: '1 hour ago', type: 'share' },
              { user: 'James Wilson', action: 'Provided feedback on brief', time: '2 hours ago', type: 'feedback' },
            ].map((activity, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-medium text-primary">
                    {activity.user.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    <span className="font-medium">{activity.user}</span> {activity.action}
                  </p>
                  <p className="text-xs text-neutral">{activity.time}</p>
                </div>
                <div className={`h-2 w-2 rounded-full ${
                  activity.type === 'response' ? 'bg-success' :
                  activity.type === 'update' ? 'bg-primary' :
                  activity.type === 'share' ? 'bg-highlight' : 'bg-neutral'
                }`} />
              </div>
            ))}
          </div>
        </div>

        {/* Team Members */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Team Members</h3>
          <div className="space-y-3">
            {[
              { name: 'Sarah Chen', role: 'Product Manager', status: 'online', lastSeen: 'Active now' },
              { name: 'Mike Johnson', role: 'Engineering Lead', status: 'online', lastSeen: '5 min ago' },
              { name: 'Emma Davis', role: 'Designer', status: 'away', lastSeen: '1 hour ago' },
              { name: 'James Wilson', role: 'Data Analyst', status: 'offline', lastSeen: '3 hours ago' },
              { name: 'Lisa Rodriguez', role: 'QA Engineer', status: 'online', lastSeen: 'Active now' },
            ].map((member, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div className="h-10 w-10 bg-primary-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-primary">
                        {member.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div className={`absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-white ${
                      member.status === 'online' ? 'bg-success' :
                      member.status === 'away' ? 'bg-highlight' : 'bg-neutral'
                    }`} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{member.name}</p>
                    <p className="text-xs text-neutral">{member.role}</p>
                  </div>
                </div>
                <p className="text-xs text-neutral">{member.lastSeen}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}