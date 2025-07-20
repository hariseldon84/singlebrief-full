/**
 * Integration Card Component
 * Displays individual integration status and metrics
 */

'use client'

import { useState } from 'react'
import { 
  Settings, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  MoreVertical,
  RefreshCw,
  Trash2,
  Eye,
  Wifi,
  WifiOff
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Integration } from '@/lib/stores/app-store'
import { cn } from '@/lib/utils'
import { Menu } from '@headlessui/react'

interface IntegrationCardProps {
  integration: Integration
}

const integrationIcons = {
  slack: '💬',
  email: '📧', 
  calendar: '📅',
  github: '⚡',
  jira: '📋',
  documents: '📄'
}

const statusColors = {
  connected: 'text-success',
  disconnected: 'text-red-500',
  error: 'text-red-500',
  syncing: 'text-highlight'
}

const healthColors = {
  healthy: 'text-success bg-success-50',
  warning: 'text-highlight bg-highlight-50',
  critical: 'text-red-500 bg-red-50'
}

export function IntegrationCard({ integration }: IntegrationCardProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = async () => {
    setIsRefreshing(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsRefreshing(false)
  }

  const formatLastSync = (date?: Date) => {
    if (!date) return 'Never'
    
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return date.toLocaleDateString()
  }

  const getStatusIcon = () => {
    switch (integration.status) {
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-success" />
      case 'disconnected':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'syncing':
        return <RefreshCw className="h-4 w-4 text-highlight animate-spin" />
      default:
        return <XCircle className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-soft hover:shadow-medium transition-shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">
              {integrationIcons[integration.type]}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {integration.name}
              </h3>
              <div className="flex items-center space-x-2 mt-1">
                {getStatusIcon()}
                <span className={cn(
                  'text-sm font-medium capitalize',
                  statusColors[integration.status]
                )}>
                  {integration.status}
                </span>
                <span className={cn(
                  'px-2 py-1 text-xs font-medium rounded-full',
                  healthColors[integration.health]
                )}>
                  {integration.health}
                </span>
              </div>
            </div>
          </div>

          {/* Actions Menu */}
          <Menu as="div" className="relative">
            <Menu.Button className="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100">
              <MoreVertical className="h-4 w-4" />
            </Menu.Button>
            <Menu.Items className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 focus:outline-none z-10">
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={handleRefresh}
                    className={cn(
                      'flex items-center w-full px-4 py-2 text-sm text-left',
                      active ? 'bg-gray-50 text-gray-900' : 'text-gray-700'
                    )}
                  >
                    <RefreshCw className="h-4 w-4 mr-3" />
                    Refresh
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={cn(
                      'flex items-center w-full px-4 py-2 text-sm text-left',
                      active ? 'bg-gray-50 text-gray-900' : 'text-gray-700'
                    )}
                  >
                    <Settings className="h-4 w-4 mr-3" />
                    Settings
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={cn(
                      'flex items-center w-full px-4 py-2 text-sm text-left',
                      active ? 'bg-gray-50 text-gray-900' : 'text-gray-700'
                    )}
                  >
                    <Eye className="h-4 w-4 mr-3" />
                    View Details
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    className={cn(
                      'flex items-center w-full px-4 py-2 text-sm text-left text-red-600',
                      active ? 'bg-red-50' : ''
                    )}
                  >
                    <Trash2 className="h-4 w-4 mr-3" />
                    Disconnect
                  </button>
                )}
              </Menu.Item>
            </Menu.Items>
          </Menu>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Metrics */}
        {integration.metrics && (
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {integration.metrics.dataPoints.toLocaleString()}
              </div>
              <div className="text-xs text-gray-500">Data Points</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-semibold text-gray-900">
                {integration.metrics.syncFrequency}
              </div>
              <div className="text-xs text-gray-500">Sync Frequency</div>
            </div>
            <div className="text-center">
              <div className={cn(
                'text-2xl font-bold',
                integration.metrics.errorRate > 5 ? 'text-red-500' : 
                integration.metrics.errorRate > 1 ? 'text-highlight' : 'text-success'
              )}>
                {integration.metrics.errorRate}%
              </div>
              <div className="text-xs text-gray-500">Error Rate</div>
            </div>
          </div>
        )}

        {/* Last Sync */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Last sync:</span>
          <div className="flex items-center space-x-2">
            <Clock className="h-3 w-3 text-gray-400" />
            <span className="text-gray-700">
              {formatLastSync(integration.lastSync)}
            </span>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex space-x-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            loading={isRefreshing}
            className="flex-1"
          >
            {integration.status === 'connected' ? 'Sync Now' : 'Reconnect'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<Settings className="h-3 w-3" />}
          >
            Configure
          </Button>
        </div>
      </div>
    </div>
  )
}