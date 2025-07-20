
import { DashboardHeader } from '../src/components/dashboard/dashboard-header'
import { DailyBriefCard } from '../src/components/dashboard/daily-brief-card'
import { TeamStatusCard } from '../src/components/dashboard/team-status-card'
import { DataSourcesCard } from '../src/components/dashboard/data-sources-card'
import { QuickActionsCard } from '../src/components/dashboard/quick-actions-card'
import { RecentQueriesCard } from '../src/components/dashboard/recent-queries-card'
import { TeamMetricsCard } from '../src/components/dashboard/team-metrics-card'

export default function Dashboard() {
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
