'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
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
  Home,
  X,
  ChevronLeft,
  User,
  LogOut,
  HelpCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/lib/stores/app-store'
import { Button } from './button'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home, description: 'Overview and daily brief' },
  { name: 'Intelligence', href: '/query', icon: Brain, description: 'Ask your AI assistant' },
  { name: 'Team Status', href: '/team', icon: Users, description: 'Team insights and activity' },
  { name: 'Memory', href: '/memory', icon: Database, description: 'AI memory and preferences' },
  { name: 'Analytics', href: '/analytics', icon: BarChart3, description: 'Performance metrics' },
  { name: 'Integrations', href: '/integrations', icon: Zap, description: 'Connected services' },
  { name: 'Trust Center', href: '/trust', icon: Shield, description: 'Security and compliance' },
  { name: 'Reports', href: '/reports', icon: FileText, description: 'Generated reports' },
]

const secondaryNavigation = [
  { name: 'Settings', href: '/settings', icon: Settings, description: 'Account and preferences' },
  { name: 'Help & Support', href: '/help', icon: HelpCircle, description: 'Get help and support' },
]

function SidebarContent({ mobile = false }: { mobile?: boolean }) {
  const pathname = usePathname()
  const { user, sidebarCollapsed, setSidebarCollapsed, setMobileMenuOpen } = useAppStore()

  const handleLinkClick = () => {
    if (mobile) {
      setMobileMenuOpen(false)
    }
  }

  return (
    <div className="flex h-full flex-col bg-white border-r border-gray-200">
      {/* Header */}
      <div className="flex h-16 items-center justify-between border-b border-gray-200 px-4">
        <div className="flex items-center space-x-2">
          <div className="h-8 w-8 rounded-md bg-primary flex items-center justify-center">
            <Brain className="h-5 w-5 text-white" />
          </div>
          {(!sidebarCollapsed || mobile) && (
            <span className="text-xl font-bold text-primary">SingleBrief</span>
          )}
        </div>
        
        {mobile ? (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setMobileMenuOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            <ChevronLeft className={cn(
              "h-4 w-4 transition-transform",
              sidebarCollapsed && "rotate-180"
            )} />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-6">
        {/* Primary Navigation */}
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={handleLinkClick}
                className={cn(
                  'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200 relative',
                  isActive
                    ? 'bg-primary-50 text-primary border-r-2 border-primary'
                    : 'text-neutral hover:bg-gray-50 hover:text-gray-900'
                )}
                title={sidebarCollapsed && !mobile ? item.description : undefined}
              >
                <item.icon
                  className={cn(
                    'h-5 w-5 flex-shrink-0 transition-colors',
                    sidebarCollapsed && !mobile ? 'mr-0' : 'mr-3',
                    isActive ? 'text-primary' : 'text-neutral group-hover:text-gray-600'
                  )}
                />
                {(!sidebarCollapsed || mobile) && (
                  <span className="truncate">{item.name}</span>
                )}
                {isActive && (
                  <div className="absolute -right-3 top-1/2 transform -translate-y-1/2 w-1 h-6 bg-primary rounded-l" />
                )}
              </Link>
            )
          })}
        </div>

        {/* Secondary Navigation */}
        <div className="pt-4 border-t border-gray-200">
          <div className="space-y-1">
            {secondaryNavigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={handleLinkClick}
                  className={cn(
                    'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-all duration-200',
                    isActive
                      ? 'bg-primary-50 text-primary border-r-2 border-primary'
                      : 'text-neutral hover:bg-gray-50 hover:text-gray-900'
                  )}
                  title={sidebarCollapsed && !mobile ? item.description : undefined}
                >
                  <item.icon
                    className={cn(
                      'h-5 w-5 flex-shrink-0 transition-colors',
                      sidebarCollapsed && !mobile ? 'mr-0' : 'mr-3',
                      isActive ? 'text-primary' : 'text-neutral group-hover:text-gray-600'
                    )}
                  />
                  {(!sidebarCollapsed || mobile) && (
                    <span className="truncate">{item.name}</span>
                  )}
                </Link>
              )
            })}
          </div>
        </div>
      </nav>

      {/* User Profile Section */}
      <div className="border-t border-gray-200 p-4">
        {(!sidebarCollapsed || mobile) ? (
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                {user?.avatar ? (
                  <img src={user.avatar} alt={user.name} className="h-8 w-8 rounded-full" />
                ) : (
                  <span className="text-sm font-medium text-primary">
                    {user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
                  </span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.name || 'User'}
                </p>
                <p className="text-xs text-neutral truncate">
                  {user?.email || 'user@company.com'}
                </p>
              </div>
            </div>
            <div className="flex space-x-1">
              <Button
                variant="ghost"
                size="sm"
                className="flex-1 justify-start h-8"
                leftIcon={<User className="h-3 w-3" />}
              >
                Profile
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="flex-1 justify-start h-8"
                leftIcon={<LogOut className="h-3 w-3" />}
              >
                Sign out
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col space-y-2">
            <Button
              variant="ghost"
              size="icon-sm"
              title="Profile"
            >
              <User className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

export function Sidebar() {
  const { sidebarCollapsed } = useAppStore()

  return (
    <div className={cn(
      "flex flex-col transition-all duration-300",
      sidebarCollapsed ? "w-16" : "w-64"
    )}>
      <SidebarContent />
    </div>
  )
}

export function MobileSidebar() {
  const { mobileMenuOpen, setMobileMenuOpen } = useAppStore()

  return (
    <Transition.Root show={mobileMenuOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50 lg:hidden" onClose={setMobileMenuOpen}>
        <Transition.Child
          as={Fragment}
          enter="transition-opacity ease-linear duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="transition-opacity ease-linear duration-300"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-900/80" />
        </Transition.Child>

        <div className="fixed inset-0 flex">
          <Transition.Child
            as={Fragment}
            enter="transition ease-in-out duration-300 transform"
            enterFrom="-translate-x-full"
            enterTo="translate-x-0"
            leave="transition ease-in-out duration-300 transform"
            leaveFrom="translate-x-0"
            leaveTo="-translate-x-full"
          >
            <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
              <SidebarContent mobile />
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  )
}