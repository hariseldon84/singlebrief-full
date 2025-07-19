'use client'

import { Search, Bell, User, Menu } from 'lucide-react'
import { useState } from 'react'

export function TopNavbar() {
  const [isSearchFocused, setIsSearchFocused] = useState(false)

  return (
    <header className="bg-white shadow-soft border-b border-gray-200 z-10">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Mobile Menu Button */}
        <button className="lg:hidden p-2 rounded-md text-neutral hover:bg-gray-100">
          <Menu className="h-5 w-5" />
        </button>

        {/* Search Bar */}
        <div className="flex-1 max-w-2xl">
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <Search className={`h-5 w-5 transition-colors ${
                isSearchFocused ? 'text-primary' : 'text-neutral'
              }`} />
            </div>
            <input
              type="search"
              placeholder="Ask your team anything..."
              className={`block w-full rounded-md border pl-10 pr-4 py-2 text-sm 
                         transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1
                         ${isSearchFocused 
                           ? 'border-primary ring-primary ring-opacity-50 bg-primary-50/30' 
                           : 'border-gray-300 hover:border-gray-400 bg-white'
                         }`}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setIsSearchFocused(false)}
            />
          </div>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center space-x-4 ml-6">
          {/* Notifications */}
          <button className="relative p-2 rounded-md text-neutral hover:bg-gray-100 hover:text-gray-900 transition-colors">
            <Bell className="h-5 w-5" />
            {/* Notification Badge */}
            <span className="absolute top-1 right-1 h-2 w-2 bg-highlight rounded-full"></span>
          </button>

          {/* User Profile */}
          <div className="relative">
            <button className="flex items-center space-x-3 p-2 rounded-md hover:bg-gray-100 transition-colors">
              <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                <User className="h-4 w-4 text-primary" />
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-gray-900">John Doe</p>
                <p className="text-xs text-neutral">Team Lead</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}