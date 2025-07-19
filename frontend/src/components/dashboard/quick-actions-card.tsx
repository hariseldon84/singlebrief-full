'use client'

import { Brain, MessageSquare, FileText, Settings, Zap, Users } from 'lucide-react'

const quickActions = [
  { 
    name: 'Ask Intelligence', 
    description: 'Query your team knowledge',
    icon: Brain, 
    href: '/query',
    color: 'bg-primary-50 text-primary hover:bg-primary-100'
  },
  { 
    name: 'Team Check-in', 
    description: 'Send status request',
    icon: Users, 
    href: '/team/checkin',
    color: 'bg-success-50 text-success hover:bg-success-100'
  },
  { 
    name: 'Generate Report', 
    description: 'Create custom brief',
    icon: FileText, 
    href: '/reports/new',
    color: 'bg-highlight-50 text-highlight hover:bg-highlight-100'
  },
  { 
    name: 'Quick Message', 
    description: 'Broadcast to team',
    icon: MessageSquare, 
    href: '/messages/new',
    color: 'bg-soft-100 text-soft-700 hover:bg-soft-200'
  },
  { 
    name: 'Automation', 
    description: 'Setup workflows',
    icon: Zap, 
    href: '/automation',
    color: 'bg-purple-50 text-purple-600 hover:bg-purple-100'
  },
  { 
    name: 'Settings', 
    description: 'Configure preferences',
    icon: Settings, 
    href: '/settings',
    color: 'bg-gray-50 text-gray-600 hover:bg-gray-100'
  },
]

export function QuickActionsCard() {
  return (
    <div className="bg-white rounded-lg shadow-soft border border-gray-200 p-6">
      <div className="flex items-center space-x-2 mb-4">
        <Zap className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
      </div>

      <div className="space-y-2">
        {quickActions.map((action, index) => (
          <button
            key={index}
            className="w-full text-left p-3 rounded-md hover:bg-gray-50 transition-all duration-200 group"
          >
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-md transition-colors ${action.color}`}>
                <action.icon className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 group-hover:text-primary transition-colors">
                  {action.name}
                </p>
                <p className="text-xs text-neutral">{action.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}