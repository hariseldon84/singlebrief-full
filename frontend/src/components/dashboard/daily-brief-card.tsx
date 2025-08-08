'use client'

import { TrendingUp, AlertTriangle, CheckCircle, ExternalLink, MoreHorizontal } from 'lucide-react'
import { formatRelativeTime, getConfidenceBadgeColor } from '@/lib/utils'

// Mock data - will be replaced with API calls
const briefData = {
  brief_id: "brief_20241125_001",
  generated_at: Date.now() - 10 * 60 * 1000, // 10 minutes ago (timestamp)
  updated_at: Date.now() - 2 * 60 * 1000, // 2 minutes ago (timestamp)
  confidence_score: 87,
  sections: [
    {
      type: "wins",
      items: [
        {
          title: "Mobile App Beta Launch Success",
          description: "Beta testing achieved 4.8/5 user rating with 250+ active testers",
          sources: ["Sarah Chen", "Beta Test Results", "App Store Analytics"],
          confidence: 92
        },
        {
          title: "Q4 Sales Target Achieved",
          description: "Sales team exceeded quarterly target by 15% with $2.3M revenue",
          sources: ["Mike Johnson", "Salesforce", "Financial Reports"],
          confidence: 95
        }
      ]
    },
    {
      type: "risks",
      items: [
        {
          title: "Server Infrastructure Capacity",
          description: "Current servers at 85% capacity, may need scaling before Black Friday",
          sources: ["DevOps Team", "Monitoring Alerts", "AWS CloudWatch"],
          confidence: 78
        },
        {
          title: "Key Developer Burnout Signals",
          description: "2 senior developers showing stress indicators in recent communications",
          sources: ["Slack Analytics", "HR Insights", "Team Surveys"],
          confidence: 71
        }
      ]
    },
    {
      type: "actions",
      items: [
        {
          title: "Schedule Infrastructure Review",
          description: "Book capacity planning session with DevOps by Wednesday",
          sources: ["Infrastructure Team", "Capacity Planning"],
          confidence: 88
        },
        {
          title: "Team Wellness Check-in",
          description: "1:1 meetings with senior developers scheduled for this week",
          sources: ["HR Recommendations", "Team Lead Notes"],
          confidence: 85
        }
      ]
    }
  ]
}

export function DailyBriefCard() {
  return (
    <div className="bg-white rounded-lg shadow-soft border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Daily Intelligence Brief</h2>
            <p className="text-sm text-neutral mt-1">
              Generated {formatRelativeTime(new Date(briefData.generated_at))} • Updated {formatRelativeTime(new Date(briefData.updated_at))}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getConfidenceBadgeColor(briefData.confidence_score)}`}>
              {briefData.confidence_score}% Confidence
            </span>
            <button className="p-2 hover:bg-gray-100 rounded-md transition-colors">
              <MoreHorizontal className="h-4 w-4 text-neutral" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {briefData.sections.map((section) => (
          <div key={section.type}>
            <div className="flex items-center space-x-2 mb-4">
              {section.type === 'wins' && <CheckCircle className="h-5 w-5 text-success" />}
              {section.type === 'risks' && <AlertTriangle className="h-5 w-5 text-highlight" />}
              {section.type === 'actions' && <TrendingUp className="h-5 w-5 text-primary" />}
              <h3 className="text-lg font-medium text-gray-900 capitalize">
                {section.type === 'actions' ? 'Recommended Actions' : section.type}
              </h3>
            </div>
            
            <div className="space-y-4">
              {section.items.map((item, index) => (
                <div key={index} className="border border-gray-100 rounded-md p-4 hover:border-gray-200 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 mb-1">{item.title}</h4>
                      <p className="text-sm text-neutral mb-3">{item.description}</p>
                      
                      {/* Sources */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-neutral">Sources:</span>
                          <div className="flex flex-wrap gap-1">
                            {item.sources.slice(0, 2).map((source, sourceIndex) => (
                              <span key={sourceIndex} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                {source}
                              </span>
                            ))}
                            {item.sources.length > 2 && (
                              <span className="text-xs text-neutral">+{item.sources.length - 2} more</span>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <span className={`text-xs px-2 py-1 rounded border ${getConfidenceBadgeColor(item.confidence)}`}>
                            {item.confidence}%
                          </span>
                          <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                            <ExternalLink className="h-3 w-3 text-neutral" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-neutral">
            Brief ID: {briefData.brief_id}
          </span>
          <button className="text-primary hover:text-primary-700 font-medium transition-colors">
            View Full Report →
          </button>
        </div>
      </div>
    </div>
  )
}