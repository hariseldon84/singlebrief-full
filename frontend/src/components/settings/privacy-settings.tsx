'use client'

import { useState } from 'react'
import { Shield, Eye, Lock, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function PrivacySettings() {
  const [dataCollection, setDataCollection] = useState(true)
  const [analytics, setAnalytics] = useState(true)
  const [thirdPartySharing, setThirdPartySharing] = useState(false)

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Privacy & Security</h2>
      
      <div className="space-y-6">
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <Shield className="h-5 w-5 text-primary" />
            <div>
              <h3 className="font-medium text-gray-900">Data Collection</h3>
              <p className="text-sm text-gray-600">Allow collection of usage data to improve service</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={dataCollection}
              onChange={(e) => setDataCollection(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <Eye className="h-5 w-5 text-primary" />
            <div>
              <h3 className="font-medium text-gray-900">Analytics Tracking</h3>
              <p className="text-sm text-gray-600">Help us understand how you use the platform</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={analytics}
              onChange={(e) => setAnalytics(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <Lock className="h-5 w-5 text-primary" />
            <div>
              <h3 className="font-medium text-gray-900">Third-party Sharing</h3>
              <p className="text-sm text-gray-600">Share anonymized data with partners</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={thirdPartySharing}
              onChange={(e) => setThirdPartySharing(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
          </label>
        </div>

        <div className="border-t pt-6">
          <h3 className="font-medium text-gray-900 mb-3">Data Management</h3>
          <div className="space-y-3">
            <Button variant="outline" leftIcon={<Download className="h-4 w-4" />}>
              Export My Data
            </Button>
            <Button variant="outline" className="text-red-600 hover:text-red-700">
              Delete Account
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}