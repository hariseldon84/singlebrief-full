/**
 * Intelligence Query Page
 * Main query interface with advanced features
 */

'use client'

import { useState, useEffect, useRef } from 'react'
import { 
  Send, 
  Mic, 
  Paperclip, 
  History, 
  Star,
  Sparkles,
  Brain,
  Clock,
  Lightbulb,
  Users
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppStore } from '@/lib/stores/app-store'
import { QueryInput } from '@/components/query/query-input'
import { QueryHistory } from '@/components/query/query-history'
import { QuerySuggestions } from '@/components/query/query-suggestions'
import { QueryResponse } from '@/components/query/query-response'
import { cn } from '@/lib/utils'

export default function QueryPage() {
  const [query, setQuery] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [currentResponse, setCurrentResponse] = useState<any>(null)
  const { setCurrentPage, setBreadcrumbs, isQueryLoading, setQueryLoading, addToQueryHistory } = useAppStore()

  // Update navigation context
  useEffect(() => {
    setCurrentPage('Intelligence')
    setBreadcrumbs([
      { name: 'Dashboard', href: '/' },
      { name: 'Intelligence', href: '/query' }
    ])
  }, [setCurrentPage, setBreadcrumbs])

  const handleSubmit = async (queryText: string) => {
    if (!queryText.trim()) return

    setIsProcessing(true)
    setQueryLoading(true)
    
    try {
      // Add to history
      addToQueryHistory(queryText)
      
      // Simulate AI processing
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Mock response
      const mockResponse = {
        id: Date.now().toString(),
        query: queryText,
        response: generateMockResponse(queryText),
        confidence: 0.92,
        sources: [
          { type: 'slack', name: 'Engineering Team', count: 12 },
          { type: 'email', name: 'Recent Emails', count: 8 },
          { type: 'documents', name: 'Project Docs', count: 5 }
        ],
        timestamp: new Date()
      }
      
      setCurrentResponse(mockResponse)
    } catch (error) {
      console.error('Query failed:', error)
    } finally {
      setIsProcessing(false)
      setQueryLoading(false)
      setQuery('')
    }
  }

  const generateMockResponse = (query: string) => {
    const responses = {
      team: "Based on the latest team communications, here's what I found:\n\n• **Project Status**: The Q4 migration is 78% complete with final testing scheduled for next week\n• **Team Sentiment**: Overall positive, with some concerns about the timeline for the mobile app launch\n• **Recent Decisions**: The team decided to prioritize bug fixes over new features for this sprint\n• **Upcoming Meetings**: All-hands meeting scheduled for Friday to discuss 2024 planning",
      
      project: "Here's a comprehensive update on your current projects:\n\n**High Priority:**\n• API redesign - On track, 65% complete\n• User dashboard refresh - Ahead of schedule\n• Security audit - Requires attention, missing 2 critical reviews\n\n**Team Blockers:**\n• Waiting for design approval on the new onboarding flow\n• Database migration scheduled for this weekend\n\n**Key Metrics:**\n• Sprint velocity: 23 points (above target)\n• Bug resolution rate: 89%",
      
      default: "I've analyzed your team's recent activity and communications. Here are the key insights:\n\n• **Recent Activity**: 47 messages in engineering channels, 12 new pull requests, 8 meetings scheduled\n• **Team Focus**: Primary focus on performance optimization and user experience improvements\n• **Decisions Made**: Team agreed to extend the current sprint by 2 days to accommodate testing\n• **Action Items**: 6 open action items from the last standup, 4 assigned to different team members"
    }

    const lowercaseQuery = query.toLowerCase()
    if (lowercaseQuery.includes('team')) return responses.team
    if (lowercaseQuery.includes('project')) return responses.project
    return responses.default
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
      {!currentResponse && (
        <QuerySuggestions onSelectSuggestion={setQuery} />
      )}

      {/* Query Input */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-soft">
        <QueryInput
          query={query}
          setQuery={setQuery}
          onSubmit={handleSubmit}
          isProcessing={isProcessing}
        />
      </div>

      {/* Response */}
      {currentResponse && (
        <QueryResponse 
          response={currentResponse}
          onNewQuery={() => setCurrentResponse(null)}
        />
      )}

      {/* Query History Sidebar */}
      {showHistory && (
        <div className="fixed inset-y-0 right-0 w-80 bg-white border-l border-gray-200 shadow-lg z-50">
          <QueryHistory onClose={() => setShowHistory(false)} />
        </div>
      )}

      {/* History Toggle */}
      <Button
        variant="outline"
        size="sm"
        onClick={() => setShowHistory(!showHistory)}
        className="fixed bottom-6 right-6 shadow-lg"
        leftIcon={<History className="h-4 w-4" />}
      >
        History
      </Button>
    </div>
  )
}