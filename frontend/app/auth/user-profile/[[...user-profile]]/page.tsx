'use client'

import { UserProfile } from '@clerk/nextjs'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export default function Page() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back Button */}
      <div className="p-4">
        <Link
          href="/"
          className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
      
      {/* User Profile */}
      <div className="flex items-center justify-center px-4 pb-8">
        <UserProfile 
          appearance={{
            elements: {
              formButtonPrimary: 'bg-primary hover:bg-primary/90 text-primary-foreground',
              card: 'shadow-lg border-0',
            }
          }}
          routing="path"
          path="/auth/user-profile"
        />
      </div>
    </div>
  )
}