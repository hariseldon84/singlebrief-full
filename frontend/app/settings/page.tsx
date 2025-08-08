/**
 * User Settings Page
 * Comprehensive settings interface for user profile, preferences, and privacy controls
 */

'use client'

import { useState, useEffect } from 'react'
import { 
  User, 
  Bell, 
  Shield, 
  Database, 
  Zap,
  Eye,
  Lock,
  Download,
  Trash2,
  ChevronRight
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppStore } from '@/lib/stores/app-store'
import { ProfileSettings } from '@/components/settings/profile-settings'
import { NotificationSettings } from '@/components/settings/notification-settings'
import { PrivacySettings } from '@/components/settings/privacy-settings'
import { IntegrationSettings } from '@/components/settings/integration-settings'
import { DataSettings } from '@/components/settings/data-settings'

const settingsTabs = [
  {
    id: 'profile',
    name: 'Profile',
    icon: User,
    description: 'Manage your account information and profile'
  },
  {
    id: 'notifications',
    name: 'Notifications', 
    icon: Bell,
    description: 'Configure how you receive notifications'
  },
  {
    id: 'privacy',
    name: 'Privacy & Security',
    icon: Shield,
    description: 'Control your privacy and security settings'
  },
  {
    id: 'integrations',
    name: 'Integrations',
    icon: Zap,
    description: 'Manage connected services and permissions'
  },
  {
    id: 'data',
    name: 'Data & Memory',
    icon: Database,
    description: 'Control your data and AI memory'
  }
]

export default function SettingsPage() {
  const [selectedTab, setSelectedTab] = useState(0)
  const { setCurrentPage, setBreadcrumbs } = useAppStore()

  // Update navigation context
  useEffect(() => {
    setCurrentPage('Settings')
    setBreadcrumbs([
      { name: 'Dashboard', href: '/' },
      { name: 'Settings', href: '/settings' }
    ])
  }, [setCurrentPage, setBreadcrumbs])

  const renderTabContent = () => {
    const tabId = settingsTabs[selectedTab]?.id
    
    switch (tabId) {
      case 'profile':
        return <ProfileSettings />
      case 'notifications':
        return <NotificationSettings />
      case 'privacy':
        return <PrivacySettings />
      case 'integrations':
        return <IntegrationSettings />
      case 'data':
        return <DataSettings />
      default:
        return <ProfileSettings />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-600 mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:w-64 flex-shrink-0">
          <nav className="space-y-1">
            {settingsTabs.map((tab, index) => (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(index)}
                className={`w-full flex items-center justify-between px-3 py-3 text-left text-sm font-medium rounded-md transition-all duration-200 ${
                  selectedTab === index
                    ? 'bg-primary-50 text-primary border-r-2 border-primary'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <div className="flex items-center">
                  <tab.icon className={`mr-3 h-5 w-5 ${
                    selectedTab === index ? 'text-primary' : 'text-gray-400'
                  }`} />
                  <div>
                    <div className="font-medium">{tab.name}</div>
                    <div className="text-xs text-gray-500 hidden lg:block">
                      {tab.description}
                    </div>
                  </div>
                </div>
                <ChevronRight className={`h-4 w-4 transition-colors ${
                  selectedTab === index ? 'text-primary' : 'text-gray-400'
                }`} />
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-lg border border-gray-200 shadow-soft">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  )
}