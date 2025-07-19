'use client'

import { Database, CheckCircle, AlertCircle, Clock } from 'lucide-react'

const dataSources = [
  { name: 'Slack Workspace', status: 'connected', lastSync: '2m ago', health: 'good' },
  { name: 'Google Calendar', status: 'connected', lastSync: '5m ago', health: 'good' },
  { name: 'Gmail', status: 'connected', lastSync: '1m ago', health: 'good' },
  { name: 'GitHub', status: 'syncing', lastSync: '10m ago', health: 'warning' },
  { name: 'Salesforce', status: 'error', lastSync: '30m ago', health: 'error' },
]

export function DataSourcesCard() {
  const connectedSources = dataSources.filter(source => source.status === 'connected').length
  const totalSources = dataSources.length

  return (
    <div className="bg-white rounded-lg shadow-soft border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Database className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-medium text-gray-900">Data Sources</h3>
        </div>
        <span className="text-sm text-neutral">{connectedSources}/{totalSources} active</span>
      </div>

      <div className="space-y-3">
        {dataSources.map((source, index) => (
          <div key={index} className="flex items-center justify-between p-3 rounded-md hover:bg-gray-50 transition-colors">
            <div className="flex items-center space-x-3">
              <div className={`h-2 w-2 rounded-full 
                ${source.health === 'good' ? 'bg-success' : 
                  source.health === 'warning' ? 'bg-highlight' : 'bg-red-500'}`}
              />
              <div>
                <p className="text-sm font-medium text-gray-900">{source.name}</p>
                <p className="text-xs text-neutral">Last sync: {source.lastSync}</p>
              </div>
            </div>
            <div className="flex items-center space-x-1">
              {source.status === 'connected' && <CheckCircle className="h-4 w-4 text-success" />}
              {source.status === 'syncing' && <Clock className="h-4 w-4 text-highlight animate-spin" />}
              {source.status === 'error' && <AlertCircle className="h-4 w-4 text-red-500" />}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <button className="w-full text-sm text-primary hover:text-primary-700 font-medium transition-colors">
          Manage Integrations →
        </button>
      </div>
    </div>
  )
}