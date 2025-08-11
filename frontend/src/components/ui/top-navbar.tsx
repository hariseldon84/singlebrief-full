'use client'

import { Search, Bell, User, Menu, Mic } from 'lucide-react'
import { useState } from 'react'
import { useAppStore } from '@/lib/stores/app-store'
import { Button } from './button'
import { NotificationDropdown } from '../dashboard/notification-dropdown'
import { LogoIcon } from './logo'
import { ClerkUserButton } from '../clerk/user-button'
import { ClerkOrganizationSwitcher } from '../clerk/organization-switcher'

export function TopNavbar() {
  const [isSearchFocused, setIsSearchFocused] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const { user, setMobileMenuOpen, notifications, unreadCount } = useAppStore()

  const handleVoiceInput = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setIsListening(!isListening)
      // Voice input implementation would go here
    }
  }

  return (
    <header className="bg-white shadow-soft border-b border-gray-200 z-10 sticky top-0">
      <div className="flex h-16 items-center justify-between px-4 lg:px-6">
        {/* Mobile Menu Button */}
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={() => setMobileMenuOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Search Bar */}
        <div className="flex-1 max-w-2xl mx-4">
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <Search className={`h-5 w-5 transition-colors ${
                isSearchFocused ? 'text-primary' : 'text-neutral'
              }`} />
            </div>
            <input
              type="search"
              placeholder="Ask your team anything..."
              className={`block w-full rounded-md border pl-10 pr-12 py-2 text-sm 
                         transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1
                         text-gray-800 placeholder-gray-500
                         ${isSearchFocused 
                           ? 'border-primary ring-primary ring-opacity-50 bg-primary-50/30' 
                           : 'border-gray-300 hover:border-gray-400 bg-white'
                         }`}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setIsSearchFocused(false)}
            />
            {/* Voice Input Button */}
            <button
              onClick={handleVoiceInput}
              className={`absolute inset-y-0 right-0 flex items-center pr-3 transition-colors ${
                isListening ? 'text-highlight' : 'text-gray-500 hover:text-blue-700'
              }`}
              title="Voice input"
            >
              <Mic className={`h-4 w-4 ${isListening ? 'animate-pulse' : ''}`} />
            </button>
          </div>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center space-x-2 lg:space-x-4">
          {/* Organization Switcher */}
          <ClerkOrganizationSwitcher />

          {/* Notifications */}
          <NotificationDropdown />

          {/* User Profile */}
          <ClerkUserButton />
        </div>
      </div>
    </header>
  )
}