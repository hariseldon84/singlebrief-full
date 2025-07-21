'use client'

import { X, Clock, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface QueryHistoryProps {
  onClose: () => void
}

export function QueryHistory({ onClose }: QueryHistoryProps) {
  const queryHistory = [
    { id: 1, query: "What's the status of the Q4 migration project?", timestamp: "2 hours ago" },
    { id: 2, query: "How is the team feeling about the mobile app launch?", timestamp: "5 hours ago" },
    { id: 3, query: "What decisions were made in yesterday's standup?", timestamp: "1 day ago" },
    { id: 4, query: "Show me recent engineering team activity", timestamp: "2 days ago" },
    { id: 5, query: "What are the current project blockers?", timestamp: "3 days ago" },
  ]

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Query History</h3>
        <Button variant="ghost" size="icon-sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {queryHistory.map((item) => (
          <div
            key={item.id}
            className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
          >
            <div className="flex items-start space-x-2">
              <MessageSquare className="h-4 w-4 text-primary mt-1 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900 line-clamp-2">{item.query}</p>
                <div className="flex items-center space-x-1 mt-1">
                  <Clock className="h-3 w-3 text-gray-400" />
                  <span className="text-xs text-gray-500">{item.timestamp}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <Button variant="outline" size="sm" className="w-full">
          View All History
        </Button>
      </div>
    </div>
  )
}