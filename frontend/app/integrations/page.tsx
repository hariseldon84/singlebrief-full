/**
 * Integrations Dashboard Page
 * Real-time integration status monitoring and management
 */

'use client'

import { useState, useEffect } from 'react'
import { 
  Plus, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Settings,
  Zap,
  TrendingUp,
  Clock,
  Database
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAppStore } from '@/lib/stores/app-store'
import { IntegrationCard } from '@/components/dashboard/integration-card'
import { IntegrationMetrics } from '@/components/dashboard/integration-metrics'
import { AddIntegrationModal } from '@/components/dashboard/add-integration-modal'

export default function IntegrationsPage() {
  const { integrations, setCurrentPage, setBreadcrumbs } = useAppStore()
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  // Update navigation context
  useEffect(() => {
    setCurrentPage('Integrations')
    setBreadcrumbs([
      { name: 'Dashboard', href: '/' },
      { name: 'Integrations', href: '/integrations' }
    ])
  }, [setCurrentPage, setBreadcrumbs])

  const handleRefresh = async () => {
    setRefreshing(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    setRefreshing(false)
  }

  const connectedIntegrations = integrations.filter(i => i.status === 'connected')
  const unhealthyIntegrations = integrations.filter(i => i.health !== 'healthy')
  const totalDataPoints = integrations.reduce((acc, i) => acc + (i.metrics?.dataPoints || 0), 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage your connected services and data sources
          </p>
        </div>
        <div className="flex space-x-3 mt-4 sm:mt-0">
          <Button
            variant="outline"
            onClick={handleRefresh}
            loading={refreshing}
            leftIcon={<RefreshCw className="h-4 w-4" />}
          >
            Refresh Status
          </Button>
          <Button
            onClick={() => setIsAddModalOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Add Integration
          </Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-primary-100 rounded-lg">
              <Zap className="h-6 w-6 text-primary" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Connected</p>
              <p className="text-2xl font-bold text-gray-900">
                {connectedIntegrations.length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-success-100 rounded-lg">
              <CheckCircle className="h-6 w-6 text-success" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Healthy</p>
              <p className="text-2xl font-bold text-gray-900">
                {integrations.length - unhealthyIntegrations.length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-highlight-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-highlight" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Need Attention</p>
              <p className="text-2xl font-bold text-gray-900">
                {unhealthyIntegrations.length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Database className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Data Points</p>
              <p className="text-2xl font-bold text-gray-900">
                {totalDataPoints.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Integration Metrics */}
      <IntegrationMetrics />

      {/* Integrations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {integrations.map((integration) => (
          <IntegrationCard key={integration.id} integration={integration} />
        ))}
      </div>

      {/* Empty State */}
      {integrations.length === 0 && (
        <div className="text-center py-12">
          <Zap className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No integrations yet
          </h3>
          <p className="text-gray-500 mb-6">
            Connect your first service to start gathering intelligence from your team
          </p>
          <Button
            onClick={() => setIsAddModalOpen(true)}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Add Your First Integration
          </Button>
        </div>
      )}

      {/* Add Integration Modal */}
      <AddIntegrationModal
        open={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
      />
    </div>
  )
}