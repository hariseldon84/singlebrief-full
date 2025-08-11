'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Clock, CheckCircle } from 'lucide-react'

type Message = {
  id: string
  content: string
  sender: 'system' | 'user' | 'team_member'
  senderName?: string
  senderRole?: string
  timestamp: Date
  status: 'sending' | 'sent' | 'delivered' | 'read'
}

type ChatParticipant = {
  id: string
  name: string
  role: string
  status: 'online' | 'offline' | 'busy'
}

interface IntelligenceChatProps {
  queryId: string
  participants: ChatParticipant[]
  initialQuestion: string
  onResponseComplete: (responses: any[]) => void
}

export function IntelligenceChat({ 
  queryId, 
  participants, 
  initialQuestion,
  onResponseComplete 
}: IntelligenceChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Initialize chat with system question
  useEffect(() => {
    const systemMessage: Message = {
      id: 'system-1',
      content: initialQuestion,
      sender: 'system',
      senderName: 'Intelligence Assistant',
      timestamp: new Date(),
      status: 'delivered'
    }
    setMessages([systemMessage])
  }, [initialQuestion])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const newMessage: Message = {
      id: `user-${Date.now()}`,
      content: inputValue.trim(),
      sender: 'user',
      senderName: 'You',
      timestamp: new Date(),
      status: 'sending'
    }

    setMessages(prev => [...prev, newMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Simulate API call to send message to team members
      // In real implementation, this would:
      // 1. Send message to selected team members via real-time chat
      // 2. Notify team members of new intelligence query
      // 3. Handle real-time responses from team members
      
      // Update message status
      setMessages(prev => 
        prev.map(msg => 
          msg.id === newMessage.id 
            ? { ...msg, status: 'delivered' }
            : msg
        )
      )

      // Simulate team member responses (replace with real WebSocket integration)
      setTimeout(() => {
        const mockResponses = participants.map((participant, index) => ({
          id: `team-${participant.id}-${Date.now()}`,
          content: `Hi! Based on your question about "${initialQuestion.substring(0, 50)}...", here's my perspective from the ${participant.role} standpoint...`,
          sender: 'team_member' as const,
          senderName: participant.name,
          senderRole: participant.role,
          timestamp: new Date(Date.now() + index * 1000),
          status: 'delivered' as const
        }))

        setMessages(prev => [...prev, ...mockResponses])
        
        // Notify parent component of responses
        onResponseComplete(mockResponses)
      }, 2000)

    } catch (error) {
      console.error('Failed to send message:', error)
      // Update message status to failed
      setMessages(prev => 
        prev.map(msg => 
          msg.id === newMessage.id 
            ? { ...msg, status: 'sent' }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const getMessageIcon = (message: Message) => {
    switch (message.sender) {
      case 'system':
        return <Bot className="h-5 w-5 text-blue-600" />
      case 'team_member':
        return (
          <div className="h-6 w-6 rounded-full bg-green-100 flex items-center justify-center">
            <span className="text-xs font-medium text-green-700">
              {message.senderName?.split(' ').map(n => n[0]).join('')}
            </span>
          </div>
        )
      default:
        return <User className="h-5 w-5 text-gray-600" />
    }
  }

  const getMessageStyles = (message: Message) => {
    switch (message.sender) {
      case 'system':
        return 'bg-blue-50 border-blue-200 text-blue-900'
      case 'team_member':
        return 'bg-green-50 border-green-200 text-green-900'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-900'
    }
  }

  return (
    <div className="flex flex-col h-full max-h-96 bg-white border border-gray-200 rounded-lg">
      {/* Chat Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h3 className="font-medium text-gray-900">Intelligence Chat</h3>
          <p className="text-sm text-gray-600">{participants.length} participants</p>
        </div>
        <div className="flex items-center space-x-2">
          {participants.map(participant => (
            <div key={participant.id} className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${
                participant.status === 'online' ? 'bg-green-400' :
                participant.status === 'busy' ? 'bg-yellow-400' : 'bg-gray-400'
              }`} />
              <span className="text-xs text-gray-600">{participant.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className="flex items-start space-x-3">
            {getMessageIcon(message)}
            <div className="flex-1">
              <div className={`border rounded-lg p-3 ${getMessageStyles(message)}`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">
                    {message.senderName}
                    {message.senderRole && (
                      <span className="text-xs text-gray-500 ml-1">({message.senderRole})</span>
                    )}
                  </span>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-3 w-3 text-gray-400" />
                    <span className="text-xs text-gray-500">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.status === 'delivered' && (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    )}
                  </div>
                </div>
                <p className="text-sm">{message.content}</p>
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a follow-up question or provide additional context..."
              className="w-full min-h-[40px] max-h-24 p-2 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-primary focus:border-transparent"
              rows={1}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="p-2 bg-primary text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}