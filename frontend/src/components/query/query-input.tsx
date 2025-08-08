/**
 * Advanced Query Input Component
 * Features: Voice input, autocomplete, attachments, suggestions
 */

'use client'

import { useState, useRef, useCallback } from 'react'
import { 
  Send, 
  Mic, 
  Paperclip, 
  Smile, 
  AtSign,
  Hash,
  Sparkles,
  ArrowUp
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface QueryInputProps {
  query: string
  setQuery: (query: string) => void
  onSubmit: (query: string) => void
  isProcessing: boolean
}

export function QueryInput({ query, setQuery, onSubmit, isProcessing }: QueryInputProps) {
  const [isListening, setIsListening] = useState(false)
  const [isFocused, setIsFocused] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const quickSuggestions = [
    "What's the status of our current sprint?",
    "Who's working on the mobile app?",
    "Any blockers from yesterday's standup?",
    "Show me recent team decisions",
    "What meetings do I have today?",
    "How is the team feeling about the deadline?"
  ]

  const handleSubmit = useCallback(() => {
    if (query.trim() && !isProcessing) {
      onSubmit(query.trim())
    }
  }, [query, isProcessing, onSubmit])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleVoiceInput = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setIsListening(!isListening)
      
      if (!isListening) {
        const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
        const recognition = new SpeechRecognition()
        
        recognition.continuous = false
        recognition.interimResults = false
        recognition.lang = 'en-US'
        
        recognition.onstart = () => {
          setIsListening(true)
        }
        
        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript
          setQuery(query + ' ' + transcript)
          setIsListening(false)
        }
        
        recognition.onerror = () => {
          setIsListening(false)
        }
        
        recognition.onend = () => {
          setIsListening(false)
        }
        
        recognition.start()
      }
    }
  }

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  const insertSuggestion = (suggestion: string) => {
    setQuery(suggestion)
    setShowSuggestions(false)
    textareaRef.current?.focus()
  }

  return (
    <div className="relative">
      {/* Suggestions Dropdown */}
      {showSuggestions && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          <div className="p-2 border-b border-gray-200">
            <div className="flex items-center text-sm text-gray-600">
              <Sparkles className="h-4 w-4 mr-2" />
              Quick suggestions
            </div>
          </div>
          <div className="max-h-48 overflow-y-auto">
            {quickSuggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => insertSuggestion(suggestion)}
                className="w-full text-left px-3 py-2 text-sm text-gray-800 hover:bg-gray-100 hover:text-blue-700 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Input Area */}
      <div className={cn(
        'border rounded-lg transition-all duration-200',
        isFocused 
          ? 'border-primary ring-2 ring-primary ring-opacity-20' 
          : 'border-gray-300 hover:border-gray-400'
      )}>
        {/* Toolbar */}
        <div className="flex items-center justify-between p-3 border-b border-border">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setShowSuggestions(!showSuggestions)}
              className={cn(
                'transition-colors',
                showSuggestions ? 'text-primary bg-primary/10' : 'text-muted-foreground hover:text-foreground'
              )}
              title="Quick suggestions"
            >
              <Sparkles className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-muted-foreground hover:text-foreground"
              title="Attach file"
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-muted-foreground hover:text-foreground"
              title="Mention team member"
            >
              <AtSign className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={handleVoiceInput}
              className={cn(
                'transition-colors',
                isListening ? 'text-highlight animate-pulse' : 'text-muted-foreground hover:text-foreground'
              )}
              title="Voice input"
            >
              <Mic className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Text Input */}
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              adjustTextareaHeight()
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Ask me anything about your team, projects, or recent activity..."
            className="w-full p-4 resize-none border-none focus:outline-none text-foreground placeholder:text-muted-foreground bg-transparent"
            rows={1}
            style={{ minHeight: '60px' }}
          />
          
          {/* Submit Button */}
          <div className="absolute bottom-3 right-3">
            <Button
              onClick={handleSubmit}
              disabled={!query.trim() || isProcessing}
              loading={isProcessing}
              size="icon-sm"
              className="rounded-full"
            >
              {isProcessing ? null : <ArrowUp className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 bg-muted text-xs text-muted-foreground">
          <div className="flex items-center space-x-4">
            <span>Press Enter to send, Shift+Enter for new line</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>{query.length}/2000</span>
            {isListening && (
              <div className="flex items-center space-x-1 text-highlight">
                <div className="w-1 h-1 bg-highlight rounded-full animate-pulse"></div>
                <span>Listening...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}