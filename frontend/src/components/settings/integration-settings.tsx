'use client'

import { useState } from 'react'
import { Zap, CheckCircle, XCircle, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function IntegrationSettings() {
  const [integrations] = useState([
    { id: 'slack', name: 'Slack', connected: true, status: 'healthy' },
    { id: 'gmail', name: 'Gmail', connected: true, status: 'healthy' },
    { id: 'github', name: 'GitHub', connected: false, status: 'disconnected' },
    { id: 'notion', name: 'Notion', connected: true, status: 'warning' },
  ])

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Integration Settings</h2>
      
      <div className="space-y-4">
        {integrations.map((integration) => (
          <div key={integration.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                integration.connected ? 'bg-primary-50' : 'bg-gray-100'
              }`}>
                <Zap className={`h-5 w-5 ${
                  integration.connected ? 'text-primary' : 'text-gray-400'
                }`} />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">{integration.name}</h3>
                <div className="flex items-center space-x-2">
                  {integration.status === 'healthy' && (
                    <>
                      <CheckCircle className="h-4 w-4 text-success" />
                      <span className="text-sm text-success">Connected</span>
                    </>
                  )}
                  {integration.status === 'warning' && (
                    <>
                      <XCircle className="h-4 w-4 text-highlight" />
                      <span className="text-sm text-highlight">Needs attention</span>
                    </>
                  )}
                  {integration.status === 'disconnected' && (
                    <>
                      <XCircle className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-500">Disconnected</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {integration.connected && (
                <Button variant="ghost" size="sm" leftIcon={<Settings className="h-4 w-4" />}>
                  Configure
                </Button>
              )}
              <Button 
                variant={integration.connected ? "outline" : "default"} 
                size="sm"
              >
                {integration.connected ? 'Disconnect' : 'Connect'}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}