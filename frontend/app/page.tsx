'use client'

import { useAuth, RedirectToSignIn } from '@clerk/nextjs'
import { DashboardHeader } from '@/components/dashboard/dashboard-header'
import { DailyBriefCard } from '@/components/dashboard/daily-brief-card'
import { TeamStatusCard } from '@/components/dashboard/team-status-card'
import { DataSourcesCard } from '@/components/dashboard/data-sources-card'
import { QuickActionsCard } from '@/components/dashboard/quick-actions-card'
import { RecentQueriesCard } from '@/components/dashboard/recent-queries-card'
import { TeamMetricsCard } from '@/components/dashboard/team-metrics-card'

export default function Dashboard() {
  const { isLoaded, userId } = useAuth()
  
  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading authentication...</p>
        </div>
      </div>
    )
  }
  
  if (!userId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to SingleBrief</h2>
          <p className="text-gray-600 mb-6">Please sign in to continue</p>
          <a 
            href="/signin"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Sign In
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <DashboardHeader />
      
      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column - Main Content */}
        <div className="lg:col-span-8 space-y-6">
          {/* Daily Brief - Primary Focus */}
          <DailyBriefCard />
          
          {/* Secondary Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <TeamStatusCard />
            <DataSourcesCard />
          </div>
          
          {/* Team Performance Metrics */}
          <TeamMetricsCard />
        </div>
        
        {/* Right Column - Sidebar Content */}
        <div className="lg:col-span-4 space-y-6">
          <QuickActionsCard />
          <RecentQueriesCard />
        </div>
      </div>
    </div>
  )
}