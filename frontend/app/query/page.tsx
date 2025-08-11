/**
 * Intelligence Query Page - Team Interrogation Workflow
 */

'use client'

import { useState } from 'react'
import { Brain, Send, Mic, History, Users, ArrowRight, MessageCircle } from 'lucide-react'
import { IntelligenceChat } from '../../src/components/query/intelligence-chat'

type WorkflowStep = 'input' | 'team-selection' | 'communication-analysis' | 'chat-execution'

type TeamMember = {
  id: string
  name: string
  email: string
  avatar?: string
  role: string
  communicationModes: string[]
  status: 'online' | 'offline' | 'busy'
}

type QuestionBreakdown = {
  teamMemberId: string
  questions: string[]
  communicationMode: string
  priority: 'high' | 'medium' | 'low'
}

export default function QueryPage() {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('input')
  const [query, setQuery] = useState('')
  const [selectedTeamMembers, setSelectedTeamMembers] = useState<string[]>([])
  const [questionBreakdowns, setQuestionBreakdowns] = useState<QuestionBreakdown[]>([])
  const [isProcessing, setIsProcessing] = useState(false)

  // Mock team data
  const mockTeamMembers: TeamMember[] = [
    {
      id: '1',
      name: 'Sarah Johnson',
      email: 'sarah@company.com',
      role: 'Product Manager',
      communicationModes: ['Slack', 'Email'],
      status: 'online'
    },
    {
      id: '2', 
      name: 'Mike Chen',
      email: 'mike@company.com',
      role: 'Engineering Lead',
      communicationModes: ['Slack', 'Teams'],
      status: 'busy'
    },
    {
      id: '3',
      name: 'Emily Rodriguez',
      email: 'emily@company.com', 
      role: 'Design Lead',
      communicationModes: ['Slack', 'Email', 'In-person'],
      status: 'online'
    },
    {
      id: '4',
      name: 'Alex Thompson',
      email: 'alex@company.com',
      role: 'Data Analyst',
      communicationModes: ['Email', 'Teams'],
      status: 'offline'
    }
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setCurrentStep('team-selection')
  }

  const handleTeamSelection = () => {
    if (selectedTeamMembers.length === 0) return
    
    setIsProcessing(true)
    // Simulate AI analysis of the query
    setTimeout(() => {
      const breakdowns = selectedTeamMembers.map(memberId => {
        const member = mockTeamMembers.find(m => m.id === memberId)!
        return {
          teamMemberId: memberId,
          questions: [
            `What's your perspective on: ${query}?`,
            `Any blockers or concerns related to this?`,
            `What additional context should I know?`
          ],
          communicationMode: member.communicationModes[0],
          priority: 'high' as const
        }
      })
      setQuestionBreakdowns(breakdowns)
      setIsProcessing(false)
      setCurrentStep('communication-analysis')
    }, 1500)
  }

  const handleStartChat = () => {
    setCurrentStep('chat-execution')
  }

  const toggleTeamMember = (memberId: string) => {
    setSelectedTeamMembers(prev => 
      prev.includes(memberId) 
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    )
  }

  // Step-based rendering
  if (currentStep === 'team-selection') {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Select Team Members</h2>
            <p className="text-gray-600">Choose who to include in this intelligence query</p>
            <div className="mt-3 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800 font-medium">Query: "{query}"</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {mockTeamMembers.map(member => (
              <div
                key={member.id}
                onClick={() => toggleTeamMember(member.id)}
                className={`p-4 border rounded-lg cursor-pointer transition-all ${
                  selectedTeamMembers.includes(member.id)
                    ? 'border-primary bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="font-medium text-gray-600">
                      {member.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium text-gray-900">{member.name}</h3>
                      <span className={`inline-block w-2 h-2 rounded-full ${
                        member.status === 'online' ? 'bg-green-400' :
                        member.status === 'busy' ? 'bg-yellow-400' : 'bg-gray-400'
                      }`} />
                    </div>
                    <p className="text-sm text-gray-600">{member.role}</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {member.communicationModes.map(mode => (
                        <span key={mode} className="px-2 py-1 bg-gray-100 text-xs rounded">
                          {mode}
                        </span>
                      ))}
                    </div>
                  </div>
                  {selectedTeamMembers.includes(member.id) && (
                    <div className="text-primary">✓</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={() => setCurrentStep('input')}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              ← Back to Query
            </button>
            <button
              onClick={handleTeamSelection}
              disabled={selectedTeamMembers.length === 0}
              className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <span>Analyze Communication</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (currentStep === 'communication-analysis') {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Communication Analysis</h2>
            <p className="text-gray-600">AI breakdown of questions and communication modes for each team member</p>
          </div>

          {isProcessing ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600">Analyzing query and preparing questions...</p>
            </div>
          ) : (
            <div className="space-y-4">
              {questionBreakdowns.map(breakdown => {
                const member = mockTeamMembers.find(m => m.id === breakdown.teamMemberId)!
                return (
                  <div key={breakdown.teamMemberId} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                          <span className="text-sm font-medium">{member.name.split(' ').map(n => n[0]).join('')}</span>
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900">{member.name}</h3>
                          <p className="text-sm text-gray-600">{member.role}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs rounded ${
                          breakdown.priority === 'high' ? 'bg-red-100 text-red-800' :
                          breakdown.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {breakdown.priority} priority
                        </span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                          {breakdown.communicationMode}
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-700">AI-Generated Questions:</h4>
                      <ul className="space-y-1">
                        {breakdown.questions.map((question, idx) => (
                          <li key={idx} className="text-sm text-gray-600 pl-4">
                            • {question}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {!isProcessing && questionBreakdowns.length > 0 && (
            <div className="flex items-center justify-between mt-6 pt-6 border-t">
              <button
                onClick={() => setCurrentStep('team-selection')}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                ← Back to Team Selection
              </button>
              <button
                onClick={handleStartChat}
                className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-700 flex items-center space-x-2"
              >
                <MessageCircle className="h-4 w-4" />
                <span>Start AI Chat</span>
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (currentStep === 'chat-execution') {
    // Convert selected team members to chat participants
    const chatParticipants = selectedTeamMembers.map(memberId => {
      const member = mockTeamMembers.find(m => m.id === memberId)!
      return {
        id: member.id,
        name: member.name,
        role: member.role,
        status: member.status
      }
    })

    const handleResponseComplete = (responses: any[]) => {
      console.log('Intelligence responses received:', responses)
      // Here you would typically:
      // 1. Store responses in state
      // 2. Trigger AI synthesis
      // 3. Generate intelligence report
    }

    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Intelligence Chat - Live Conversation</h2>
            <p className="text-gray-600">Real-time intelligence gathering with selected team members</p>
            <div className="mt-3 p-3 bg-green-50 rounded-lg">
              <p className="text-sm text-green-800 font-medium">Query: "{query}"</p>
            </div>
          </div>

          <div className="h-96">
            <IntelligenceChat
              queryId={`query-${Date.now()}`}
              participants={chatParticipants}
              initialQuestion={query}
              onResponseComplete={handleResponseComplete}
            />
          </div>

          <div className="flex items-center justify-between mt-6 pt-6 border-t">
            <button
              onClick={() => setCurrentStep('communication-analysis')}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              ← Back to Analysis
            </button>
            <button
              onClick={() => {
                setCurrentStep('input')
                setQuery('')
                setSelectedTeamMembers([])
                setQuestionBreakdowns([])
              }}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Complete & Generate Report
            </button>
          </div>

          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">What's New in Story 16.1</h4>
            <ul className="text-xs text-blue-800 space-y-1">
              <li>✅ In-app chat interface replaces email-only responses</li>
              <li>✅ Real-time team member communication</li>
              <li>✅ Clerk-native team invitation system</li>
              <li>🔄 Email-to-chat threading (coming in Story 16.6)</li>
            </ul>
          </div>
        </div>
      </div>
    )
  }

  // Default: Input step
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