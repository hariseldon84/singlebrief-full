'use client'

import { useState } from 'react'
import { Database, Download, Trash2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function DataSettings() {
  const [memoryEnabled, setMemoryEnabled] = useState(true)
  const [autoCleanup, setAutoCleanup] = useState(false)

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Data & Memory</h2>
      
      <div className="space-y-6">
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <Database className="h-5 w-5 text-primary" />
            <div>
              <h3 className="font-medium text-gray-900">AI Memory</h3>
              <p className="text-sm text-gray-600">Allow AI to remember our conversations and preferences</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={memoryEnabled}
              onChange={(e) => setMemoryEnabled(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <RefreshCw className="h-5 w-5 text-primary" />
            <div>
              <h3 className="font-medium text-gray-900">Auto Cleanup</h3>
              <p className="text-sm text-gray-600">Automatically delete old data after 90 days</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={autoCleanup}
              onChange={(e) => setAutoCleanup(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        <div className="border-t pt-6">
          <h3 className="font-medium text-gray-900 mb-3">Data Management</h3>
          <div className="space-y-3">
            <div className="text-sm text-gray-600 mb-4">
              <p>Current data usage: <span className="font-medium">1.2 GB</span> of 5 GB limit</p>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: '24%' }}></div>
              </div>
            </div>
            <Button variant="outline" leftIcon={<Download className="h-4 w-4" />}>
              Export All Data
            </Button>
            <Button variant="outline" leftIcon={<RefreshCw className="h-4 w-4" />}>
              Clear Cache
            </Button>
            <Button variant="outline" className="text-red-600 hover:text-red-700" leftIcon={<Trash2 className="h-4 w-4" />}>
              Reset All Memory
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}