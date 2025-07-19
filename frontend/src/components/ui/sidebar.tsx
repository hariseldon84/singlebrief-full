'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  BarChart3, 
  Brain, 
  MessageSquare, 
  Settings, 
  Users, 
  Database,
  Zap,
  Shield,
  FileText,
  Home
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Intelligence', href: '/query', icon: Brain },
  { name: 'Team Status', href: '/team', icon: Users },
  { name: 'Memory', href: '/memory', icon: Database },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Integrations', href: '/integrations', icon: Zap },
  { name: 'Trust Center', href: '/trust', icon: Shield },
  { name: 'Reports', href: '/reports', icon: FileText },
]

const secondaryNavigation = [
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex w-64 flex-col bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="flex h-16 items-center justify-center border-b border-gray-200 px-6">
        <div className="flex items-center space-x-2">
          <div className="h-8 w-8 rounded-md bg-primary flex items-center justify-center">
            <Brain className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold text-primary">SingleBrief</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-6">
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200',
                  isActive
                    ? 'bg-primary-50 text-primary border-r-2 border-primary'
                    : 'text-neutral hover:bg-gray-50 hover:text-gray-900'
                )}
              >
                <item.icon
                  className={cn(
                    'mr-3 h-5 w-5 flex-shrink-0 transition-colors',
                    isActive ? 'text-primary' : 'text-neutral group-hover:text-gray-600'
                  )}
                />
                {item.name}
              </Link>
            )
          })}
        </div>

        {/* Secondary Navigation */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="space-y-1">
            {secondaryNavigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200',
                    isActive
                      ? 'bg-primary-50 text-primary border-r-2 border-primary'
                      : 'text-neutral hover:bg-gray-50 hover:text-gray-900'
                  )}
                >
                  <item.icon
                    className={cn(
                      'mr-3 h-5 w-5 flex-shrink-0 transition-colors',
                      isActive ? 'text-primary' : 'text-neutral group-hover:text-gray-600'
                    )}
                  />
                  {item.name}
                </Link>
              )
            })}
          </div>
        </div>
      </nav>

      {/* User Profile Section */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
            <span className="text-sm font-medium text-primary">JD</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">John Doe</p>
            <p className="text-xs text-neutral truncate">john@company.com</p>
          </div>
        </div>
      </div>
    </div>
  )
}