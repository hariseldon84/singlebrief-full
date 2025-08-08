/**
 * Intelligence Query Page - Simplified Version
 */

'use client'

import { useState } from 'react'
import { Brain, Send, Mic, History } from 'lucide-react'

export default function QueryPage() {
  const [query, setQuery] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [response, setResponse] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsProcessing(true)
    
    // Simulate AI processing
    setTimeout(() => {
      const mockResponse = `Based on your query "${query}", here's what I found:\n\n• Project status updates from the team\n• Recent communications analysis\n• Key decisions and action items\n• Upcoming deadlines and priorities\n\nThis is a demo response. The actual AI intelligence system will provide real insights from your team's data.`
      setResponse(mockResponse)
      setIsProcessing(false)
      setQuery('')
    }, 2000)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
          <Brain className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Intelligence Assistant
        </h1>
        <p className="text-gray-600">
          Ask me anything about your team, projects, or recent activity
        </p>
      </div>

      {/* Quick Suggestions */}
      {!response && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {[
            "What's the current status of our main project?",
            "How is the team feeling about the upcoming deadline?",
            "What decisions were made in yesterday's meetings?",
            "What are the biggest blockers right now?"
          ].map((suggestion, index) => (
            <button
              key={index}
              onClick={() => setQuery(suggestion)}
              className="p-4 text-left bg-white border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
            >
              <div className="text-sm text-gray-700">{suggestion}</div>
            </button>
          ))}
        </div>
      )}

      {/* Query Input */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <form onSubmit={handleSubmit} className="p-4">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask your team anything..."
                className="w-full min-h-[60px] p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-primary focus:border-transparent"
                rows={3}
              />
            </div>
            <div className="flex flex-col space-y-2">
              <button
                type="button"
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md"
                title="Voice input"
              >
                <Mic className="h-5 w-5" />
              </button>
              <button
                type="submit"
                disabled={!query.trim() || isProcessing}
                className="p-2 bg-primary text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Send query"
              >
                {isProcessing ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Processing indicator */}
      {isProcessing && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
            <div>
              <p className="text-sm font-medium text-blue-900">Processing your query...</p>
              <p className="text-xs text-blue-700">Analyzing team data and communications</p>
            </div>
          </div>
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Brain className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-gray-900">Intelligence Report</h3>
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                92% Confidence
              </span>
            </div>
            <div className="prose prose-sm max-w-none">
              <div className="whitespace-pre-line text-gray-700">{response}</div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm text-gray-500">
                <div className="flex items-center space-x-4">
                  <span>Sources: Slack (12), Email (8), Docs (5)</span>
                </div>
                <button
                  onClick={() => setResponse(null)}
                  className="text-primary hover:text-primary-700"
                >
                  Ask another question →
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* History Toggle */}
      <button
        onClick={() => alert('Query history feature coming soon!')}
        className="fixed bottom-6 right-6 bg-white border border-gray-200 shadow-lg rounded-lg p-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <History className="h-4 w-4" />
          <span className="text-sm">History</span>
        </div>
      </button>
    </div>
  )
}