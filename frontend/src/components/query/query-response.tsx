'use client'

import { useState } from 'react'
import { ThumbsUp, ThumbsDown, Copy, Share2, RefreshCw, Star, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface QueryResponseProps {
  response: {
    id: string
    query: string
    response: string
    confidence: number
    sources: Array<{
      type: string
      name: string
      count: number
    }>
    timestamp: Date
  }
  onNewQuery: () => void
}

export function QueryResponse({ response, onNewQuery }: QueryResponseProps) {
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null)
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(response.response)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text:', err)
    }
  }

  const handleFeedback = (type: 'up' | 'down') => {
    setFeedback(type)
    // Here you would typically send feedback to your backend
  }

  return (
    <div className="space-y-4">
      {/* Query Echo */}
      <div className="bg-gray-50 rounded-lg p-4 border-l-4 border-primary">
        <div className="flex items-center space-x-2 mb-2">
          <MessageSquare className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium text-primary">Your Question</span>
        </div>
        <p className="text-gray-900">{response.query}</p>
      </div>

      {/* Response */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-soft">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-primary">AI</span>
              </div>
              <div>
                <h3 className="font-medium text-gray-900">Intelligence Assistant</h3>
                <p className="text-xs text-gray-500">
                  {response.timestamp.toLocaleTimeString()} • Confidence: {Math.round(response.confidence * 100)}%
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-1">
              <Button variant="ghost" size="icon-sm" onClick={handleCopy}>
                <Copy className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon-sm">
                <Share2 className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon-sm">
                <Star className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Confidence Bar */}
          <div className="mb-4">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>Confidence Level</span>
              <span>{Math.round(response.confidence * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all duration-500"
                style={{ width: `${response.confidence * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Response Content */}
          <div className="prose prose-sm max-w-none">
            <div className="whitespace-pre-line text-gray-900">
              {response.response}
            </div>
          </div>

          {/* Sources */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Sources</h4>
            <div className="flex flex-wrap gap-2">
              {response.sources.map((source, index) => (
                <div
                  key={index}
                  className="inline-flex items-center space-x-1 bg-gray-100 rounded-full px-3 py-1"
                >
                  <span className="text-xs font-medium text-gray-700">{source.name}</span>
                  <span className="text-xs text-gray-500">({source.count})</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Was this helpful?</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleFeedback('up')}
                className={feedback === 'up' ? 'text-success' : ''}
              >
                <ThumbsUp className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleFeedback('down')}
                className={feedback === 'down' ? 'text-red-500' : ''}
              >
                <ThumbsDown className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={onNewQuery}>
                <RefreshCw className="h-4 w-4 mr-2" />
                New Query
              </Button>
              {copied && (
                <span className="text-sm text-success">Copied!</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}