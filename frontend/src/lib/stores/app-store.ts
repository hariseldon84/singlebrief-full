/**
 * Application state management using Zustand
 * Handles UI state, navigation, theme, and global app state
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export interface User {
  id: string
  name: string
  email: string
  role: string
  organization: string
  avatar?: string
}

export interface Integration {
  id: string
  name: string
  type: 'slack' | 'email' | 'calendar' | 'github' | 'jira' | 'documents'
  status: 'connected' | 'disconnected' | 'error' | 'syncing'
  lastSync?: Date
  health: 'healthy' | 'warning' | 'critical'
  metrics?: {
    dataPoints: number
    syncFrequency: string
    errorRate: number
  }
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
  actionUrl?: string
}

export interface AppState {
  // UI State
  sidebarCollapsed: boolean
  mobileMenuOpen: boolean
  theme: 'light' | 'dark' | 'system'
  loading: boolean
  
  // User & Auth
  user: User | null
  isAuthenticated: boolean
  
  // Navigation
  currentPage: string
  breadcrumbs: Array<{ name: string; href: string }>
  
  // Integrations
  integrations: Integration[]
  
  // Notifications
  notifications: Notification[]
  unreadCount: number
  
  // Query State
  isQueryLoading: boolean
  lastQuery: string
  queryHistory: string[]
  
  // Actions
  setSidebarCollapsed: (collapsed: boolean) => void
  setMobileMenuOpen: (open: boolean) => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  setLoading: (loading: boolean) => void
  setUser: (user: User | null) => void
  setAuthenticated: (authenticated: boolean) => void
  setCurrentPage: (page: string) => void
  setBreadcrumbs: (breadcrumbs: Array<{ name: string; href: string }>) => void
  updateIntegration: (id: string, updates: Partial<Integration>) => void
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void
  markNotificationRead: (id: string) => void
  clearNotifications: () => void
  setQueryLoading: (loading: boolean) => void
  addToQueryHistory: (query: string) => void
}

export const useAppStore = create<AppState>()(
  subscribeWithSelector((set, get) => ({
    // Initial UI State
    sidebarCollapsed: false,
    mobileMenuOpen: false,
    theme: 'light',
    loading: false,
    
    // Initial User State
    user: null,
    isAuthenticated: false,
    
    // Initial Navigation
    currentPage: 'Dashboard',
    breadcrumbs: [{ name: 'Dashboard', href: '/' }],
    
    // Initial Integrations
    integrations: [
      {
        id: 'slack-1',
        name: 'Slack Workspace',
        type: 'slack',
        status: 'connected',
        health: 'healthy',
        lastSync: new Date(),
        metrics: {
          dataPoints: 1247,
          syncFrequency: 'Real-time',
          errorRate: 0.2
        }
      },
      {
        id: 'email-1',
        name: 'Gmail Integration',
        type: 'email',
        status: 'connected',
        health: 'warning',
        lastSync: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        metrics: {
          dataPoints: 892,
          syncFrequency: 'Hourly',
          errorRate: 2.1
        }
      },
      {
        id: 'calendar-1',
        name: 'Google Calendar',
        type: 'calendar',
        status: 'disconnected',
        health: 'critical',
        metrics: {
          dataPoints: 0,
          syncFrequency: 'N/A',
          errorRate: 100
        }
      }
    ],
    
    // Initial Notifications
    notifications: [
      {
        id: '1',
        type: 'warning',
        title: 'Email Integration Issue',
        message: 'Gmail sync is experiencing delays. Last successful sync was 2 hours ago.',
        timestamp: new Date(Date.now() - 30 * 60 * 1000),
        read: false
      },
      {
        id: '2',
        type: 'success',
        title: 'Daily Brief Ready',
        message: 'Your daily intelligence brief has been generated with insights from 5 sources.',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        read: false
      }
    ],
    unreadCount: 2,
    
    // Initial Query State
    isQueryLoading: false,
    lastQuery: '',
    queryHistory: [],
    
    // UI Actions
    setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    setMobileMenuOpen: (open) => set({ mobileMenuOpen: open }),
    setTheme: (theme) => set({ theme }),
    setLoading: (loading) => set({ loading }),
    
    // User Actions
    setUser: (user) => set({ user }),
    setAuthenticated: (authenticated) => set({ isAuthenticated: authenticated }),
    
    // Navigation Actions
    setCurrentPage: (page) => set({ currentPage: page }),
    setBreadcrumbs: (breadcrumbs) => set({ breadcrumbs }),
    
    // Integration Actions
    updateIntegration: (id, updates) => set((state) => ({
      integrations: state.integrations.map(integration =>
        integration.id === id ? { ...integration, ...updates } : integration
      )
    })),
    
    // Notification Actions
    addNotification: (notification) => set((state) => {
      const newNotification: Notification = {
        ...notification,
        id: Date.now().toString(),
        timestamp: new Date(),
        read: false
      }
      return {
        notifications: [newNotification, ...state.notifications],
        unreadCount: state.unreadCount + 1
      }
    }),
    
    markNotificationRead: (id) => set((state) => ({
      notifications: state.notifications.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      ),
      unreadCount: Math.max(0, state.unreadCount - 1)
    })),
    
    clearNotifications: () => set({
      notifications: [],
      unreadCount: 0
    }),
    
    // Query Actions
    setQueryLoading: (loading) => set({ isQueryLoading: loading }),
    addToQueryHistory: (query) => set((state) => ({
      lastQuery: query,
      queryHistory: [query, ...state.queryHistory.filter(q => q !== query)].slice(0, 10)
    }))
  }))
)

// Subscribe to theme changes and apply to document
useAppStore.subscribe(
  (state) => state.theme,
  (theme) => {
    if (typeof window !== 'undefined') {
      const root = document.documentElement
      if (theme === 'dark') {
        root.classList.add('dark')
      } else if (theme === 'light') {
        root.classList.remove('dark')
      } else {
        // System theme
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        if (mediaQuery.matches) {
          root.classList.add('dark')
        } else {
          root.classList.remove('dark')
        }
      }
    }
  }
)