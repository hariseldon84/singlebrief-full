'use client'

import { useEffect, useState } from 'react'
import { Calendar, Clock } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export function DashboardHeader() {
  const [greeting, setGreeting] = useState('')
  const [mounted, setMounted] = useState(false)
  const currentDate = new Date()

  useEffect(() => {
    setMounted(true)
    setGreeting(getGreeting())
  }, [])

  if (!mounted) {
    return null
  }

  return (
    <div className="space-y-4">
      {/* Greeting and Date */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {greeting}, John
          </h1>
          <p className="mt-1 text-neutral">
            Here's what's happening with your team today
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 flex items-center space-x-4 text-sm text-neutral">
          <div className="flex items-center space-x-1">
            <Calendar className="h-4 w-4" />
            <span>{formatDate(currentDate)}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Clock className="h-4 w-4" />
            <span>Last updated 2 min ago</span>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-md p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral uppercase tracking-wide">Active Tasks</p>
              <p className="text-2xl font-semibold text-gray-900">12</p>
            </div>
            <div className="p-2 bg-primary-50 rounded-md">
              <div className="w-2 h-2 bg-primary rounded-full"></div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-md p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral uppercase tracking-wide">Team Members</p>
              <p className="text-2xl font-semibold text-gray-900">8</p>
            </div>
            <div className="p-2 bg-success-50 rounded-md">
              <div className="w-2 h-2 bg-success rounded-full"></div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-md p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral uppercase tracking-wide">Confidence</p>
              <p className="text-2xl font-semibold text-gray-900">87%</p>
            </div>
            <div className="p-2 bg-highlight-50 rounded-md">
              <div className="w-2 h-2 bg-highlight rounded-full"></div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-md p-4 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-neutral uppercase tracking-wide">Data Sources</p>
              <p className="text-2xl font-semibold text-gray-900">5</p>
            </div>
            <div className="p-2 bg-soft-100 rounded-md">
              <div className="w-2 h-2 bg-soft-500 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}