'use client'

import { useAuth } from '@clerk/nextjs'

export default function DebugPage() {
  const { isLoaded, userId, isSignedIn } = useAuth()
  
  return (
    <div className="min-h-screen bg-yellow-50 flex items-center justify-center">
      <div className="text-center bg-white p-8 rounded-lg shadow">
        <h1 className="text-2xl font-bold text-yellow-900 mb-4">Debug Auth State</h1>
        <div className="space-y-2 text-left">
          <p><strong>isLoaded:</strong> {String(isLoaded)}</p>
          <p><strong>userId:</strong> {userId || 'null'}</p>
          <p><strong>isSignedIn:</strong> {String(isSignedIn)}</p>
        </div>
        <div className="mt-6 space-x-4">
          <a href="/signin" className="bg-blue-600 text-white px-4 py-2 rounded">
            Go to Sign In
          </a>
          <a href="/simple" className="bg-green-600 text-white px-4 py-2 rounded">
            Simple Page
          </a>
        </div>
      </div>
    </div>
  )
}