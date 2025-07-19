'use client'

import { Users, Clock, MessageSquare } from 'lucide-react'

const teamMembers = [
  { name: 'Sarah Chen', role: 'Product Manager', status: 'active', lastSeen: '2m ago', avatar: 'SC' },
  { name: 'Mike Johnson', role: 'Sales Lead', status: 'active', lastSeen: '5m ago', avatar: 'MJ' },
  { name: 'Alex Rodriguez', role: 'Developer', status: 'busy', lastSeen: '15m ago', avatar: 'AR' },
  { name: 'Emily Davis', role: 'Designer', status: 'away', lastSeen: '1h ago', avatar: 'ED' },
]

export function TeamStatusCard() {
  return (
    <div className="bg-white rounded-lg shadow-soft border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Users className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-medium text-gray-900">Team Status</h3>
        </div>
        <span className="text-sm text-neutral">4 members</span>
      </div>

      <div className="space-y-3">
        {teamMembers.map((member, index) => (
          <div key={index} className="flex items-center justify-between p-3 rounded-md hover:bg-gray-50 transition-colors">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-xs font-medium text-primary">{member.avatar}</span>
                </div>
                <div className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white
                  ${member.status === 'active' ? 'bg-success' : 
                    member.status === 'busy' ? 'bg-highlight' : 'bg-gray-400'}`}
                />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">{member.name}</p>
                <p className="text-xs text-neutral">{member.role}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-xs text-neutral">
              <Clock className="h-3 w-3" />
              <span>{member.lastSeen}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <button className="w-full flex items-center justify-center space-x-2 text-sm text-primary hover:text-primary-700 font-medium transition-colors">
          <MessageSquare className="h-4 w-4" />
          <span>Send Team Message</span>
        </button>
      </div>
    </div>
  )
}