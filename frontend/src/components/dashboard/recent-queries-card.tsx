'use client'

import { MessageSquare, Clock, TrendingUp } from 'lucide-react'
import { getConfidenceColor } from '@/lib/utils'

const recentQueries = [
  {
    question: "What's the status of the mobile app beta testing?",
    timestamp: "15m ago",
    confidence: 92,
    responseCount: 3
  },
  {
    question: "Are there any blockers for the Q4 launch?",
    timestamp: "2h ago",
    confidence: 78,
    responseCount: 5
  },
  {
    question: "How are the new team members settling in?",
    timestamp: "4h ago",
    confidence: 85,
    responseCount: 2
  },
  {
    question: "What's our current server capacity utilization?",
    timestamp: "6h ago",
    confidence: 95,
    responseCount: 1
  }
]

export function RecentQueriesCard() {
  return (
    <div className="bg-white rounded-lg shadow-soft border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-medium text-gray-900">Recent Queries</h3>
        </div>
        <button className="text-sm text-primary hover:text-primary-700 font-medium transition-colors">
          View All
        </button>
      </div>

      <div className="space-y-4">
        {recentQueries.map((query, index) => (
          <div key={index} className="p-3 rounded-md hover:bg-gray-50 transition-colors cursor-pointer group">
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-900 group-hover:text-primary transition-colors line-clamp-2">
                {query.question}
              </p>
              
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3 text-neutral">
                  <div className="flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>{query.timestamp}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <MessageSquare className="h-3 w-3" />
                    <span>{query.responseCount} responses</span>
                  </div>
                </div>
                
                <span className={`font-medium ${getConfidenceColor(query.confidence)}`}>
                  {query.confidence}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <button className="w-full flex items-center justify-center space-x-2 text-sm text-primary hover:text-primary-700 font-medium transition-colors">
          <TrendingUp className="h-4 w-4" />
          <span>Ask New Question</span>
        </button>
      </div>
    </div>
  )
}