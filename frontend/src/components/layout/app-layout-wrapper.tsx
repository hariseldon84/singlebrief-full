'use client'

import { usePathname } from 'next/navigation'
import { useAuth } from '@clerk/nextjs'
import { Sidebar, MobileSidebar } from '../ui/sidebar'
import { TopNavbar } from '../ui/top-navbar'
import { useEffect } from 'react'

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const { isLoaded, userId } = useAuth()
  
  // Check if current path is an auth page or has special handling
  const isAuthPage = pathname?.startsWith('/auth') || pathname === '/signin' || pathname === '/signup' || pathname === '/working' || pathname === '/simple' || pathname === '/debug' || pathname === '/test' || pathname === '/signout'
  
  // For auth pages, render children without the main app layout
  if (isAuthPage) {
    return <>{children}</>
  }
  
  // For protected pages, show loading while checking auth
  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }
  
  // For non-auth pages, redirect to login if not authenticated (only after loaded)
  // Add extra safety check to prevent redirect loops
  if (!userId && isLoaded && typeof window !== 'undefined') {
    // Only redirect if we're not already being redirected
    if (!window.location.href.includes('/signin')) {
      window.location.href = '/signin'
    }
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Redirecting to sign in...</p>
        </div>
      </div>
    )
  }
  
  // For all other pages, render with the main app layout (only when authenticated)
  return (
    <div className="h-screen flex overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopNavbar />
        <div className="flex-1 p-6 overflow-y-auto">
          {children}
        </div>
      </div>
      <MobileSidebar />
    </div>
  )
}