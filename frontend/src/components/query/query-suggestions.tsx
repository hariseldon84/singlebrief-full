'use client'

import { Users, TrendingUp, MessageSquare, Calendar, Lightbulb } from 'lucide-react'

interface QuerySuggestionsProps {
  onSelectSuggestion: (suggestion: string) => void
}

export function QuerySuggestions({ onSelectSuggestion }: QuerySuggestionsProps) {
  const suggestions = [
    {
      icon: Users,
      title: "Team Status",
      query: "What's the current status of my team and recent activity?",
      category: "Team"
    },
    {
      icon: TrendingUp,
      title: "Project Updates",
      query: "Give me an update on all current projects and their progress",
      category: "Projects"
    },
    {
      icon: MessageSquare,
      title: "Recent Decisions",
      query: "What important decisions were made in recent team meetings?",
      category: "Decisions"
    },
    {
      icon: Calendar,
      title: "Upcoming Events",
      query: "What meetings and events are coming up this week?",
      category: "Schedule"
    },
    {
      icon: Lightbulb,
      title: "Suggestions",
      query: "What insights or suggestions do you have based on recent activity?",
      category: "Insights"
    }
  ]

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Quick Questions</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSelectSuggestion(suggestion.query)}
            className="text-left p-4 border border-border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-primary transition-all group"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-2 bg-primary-50 rounded-lg group-hover:bg-primary-100">
                <suggestion.icon className="h-4 w-4 text-primary" />
              </div>
              <span className="text-xs text-primary font-medium bg-primary-50 px-2 py-1 rounded-full">
                {suggestion.category}
              </span>
            </div>
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-1">{suggestion.title}</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{suggestion.query}</p>
          </button>
        ))}
      </div>
    </div>
  )
}