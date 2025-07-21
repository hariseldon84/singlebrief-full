'use client'

import { TrendingUp, Clock, CheckCircle, AlertTriangle } from 'lucide-react'

export function IntegrationMetrics() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Integration Performance</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="text-center">
          <div className="h-16 w-16 bg-success-50 rounded-full flex items-center justify-center mx-auto mb-3">
            <TrendingUp className="h-8 w-8 text-success" />
          </div>
          <h4 className="text-lg font-semibold text-gray-900">Data Sync Rate</h4>
          <p className="text-sm text-neutral mt-1">98.5% successful sync operations</p>
        </div>
        
        <div className="text-center">
          <div className="h-16 w-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-3">
            <Clock className="h-8 w-8 text-primary" />
          </div>
          <h4 className="text-lg font-semibold text-gray-900">Avg Response Time</h4>
          <p className="text-sm text-neutral mt-1">1.2s average API response time</p>
        </div>
        
        <div className="text-center">
          <div className="h-16 w-16 bg-highlight-50 rounded-full flex items-center justify-center mx-auto mb-3">
            <CheckCircle className="h-8 w-8 text-highlight" />
          </div>
          <h4 className="text-lg font-semibold text-gray-900">Uptime</h4>
          <p className="text-sm text-neutral mt-1">99.9% uptime across all services</p>
        </div>
        
        <div className="text-center">
          <div className="h-16 w-16 bg-neutral-50 rounded-full flex items-center justify-center mx-auto mb-3">
            <AlertTriangle className="h-8 w-8 text-neutral" />
          </div>
          <h4 className="text-lg font-semibold text-gray-900">Error Rate</h4>
          <p className="text-sm text-neutral mt-1">0.1% error rate this month</p>
        </div>
      </div>
    </div>
  )
}