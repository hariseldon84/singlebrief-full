/**
 * Notification dropdown component with real-time updates
 */

'use client'

import { Fragment } from 'react'
import { Menu, Transition } from '@headlessui/react'
import { Bell, CheckCheck, X, AlertTriangle, Info, CheckCircle } from 'lucide-react'
import { useAppStore } from '@/lib/stores/app-store'
import { Button } from '../ui/button'
import { cn } from '@/lib/utils'

export function NotificationDropdown() {
  const { notifications, unreadCount, markNotificationRead, clearNotifications } = useAppStore()

  const getNotificationIcon = (type: 'info' | 'success' | 'warning' | 'error') => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-success" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-highlight" />
      case 'error':
        return <X className="h-4 w-4 text-red-500" />
      default:
        return <Info className="h-4 w-4 text-primary" />
    }
  }

  const formatTime = (timestamp: Date) => {
    const now = new Date()
    const diff = now.getTime() - timestamp.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="relative p-2 rounded-md text-neutral hover:bg-gray-100 hover:text-gray-900 transition-colors">
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 bg-highlight text-white text-xs font-medium rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-96 bg-white rounded-md shadow-large border border-gray-200 focus:outline-none z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
            {notifications.length > 0 && (
              <div className="flex space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearNotifications}
                  leftIcon={<CheckCheck className="h-3 w-3" />}
                >
                  Clear all
                </Button>
              </div>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center">
                <Bell className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-sm">No notifications yet</p>
                <p className="text-gray-400 text-xs mt-1">
                  We'll notify you when something important happens
                </p>
              </div>
            ) : (
              <div className="py-2">
                {notifications.map((notification) => (
                  <Menu.Item key={notification.id}>
                    {({ active }) => (
                      <div
                        className={cn(
                          'relative px-4 py-3 cursor-pointer transition-colors',
                          active && 'bg-gray-50',
                          !notification.read && 'bg-primary-50/30'
                        )}
                        onClick={() => markNotificationRead(notification.id)}
                      >
                        <div className="flex items-start space-x-3">
                          <div className="flex-shrink-0 mt-1">
                            {getNotificationIcon(notification.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <p className={cn(
                                'text-sm font-medium truncate',
                                notification.read ? 'text-gray-700' : 'text-gray-900'
                              )}>
                                {notification.title}
                              </p>
                              <p className="text-xs text-gray-400 ml-2 flex-shrink-0">
                                {formatTime(notification.timestamp)}
                              </p>
                            </div>
                            <p className={cn(
                              'text-sm mt-1',
                              notification.read ? 'text-gray-500' : 'text-gray-700'
                            )}>
                              {notification.message}
                            </p>
                            {notification.actionUrl && (
                              <Button
                                variant="link"
                                size="sm"
                                className="p-0 h-auto text-xs mt-2"
                              >
                                View details
                              </Button>
                            )}
                          </div>
                          {!notification.read && (
                            <div className="flex-shrink-0">
                              <div className="h-2 w-2 bg-primary rounded-full"></div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </Menu.Item>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="border-t border-gray-200 p-4">
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-center"
              >
                View all notifications
              </Button>
            </div>
          )}
        </Menu.Items>
      </Transition>
    </Menu>
  )
}