'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { authAPI, User, AuthTokens, Organization } from './api'

interface AuthState {
  user: User | null
  organization: Organization | null
  tokens: AuthTokens | null
  isLoading: boolean
  isAuthenticated: boolean
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>
  register: (email: string, password: string, fullName: string, organizationName?: string) => Promise<void>
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
  clearAuth: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_STORAGE_KEY = 'sb_tokens'
const USER_STORAGE_KEY = 'sb_user'
const ORG_STORAGE_KEY = 'sb_organization'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    organization: null,
    tokens: null,
    isLoading: true,
    isAuthenticated: false,
  })

  // Clear auth state
  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(USER_STORAGE_KEY)
    localStorage.removeItem(ORG_STORAGE_KEY)
    setState({
      user: null,
      organization: null,
      tokens: null,
      isLoading: false,
      isAuthenticated: false,
    })
  }, [])

  // Set auth state
  const setAuth = useCallback((user: User, tokens: AuthTokens, organization?: Organization) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens))
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
    if (organization) {
      localStorage.setItem(ORG_STORAGE_KEY, JSON.stringify(organization))
    }

    setState({
      user,
      organization: organization || null,
      tokens,
      isLoading: false,
      isAuthenticated: true,
    })
  }, [])

  // Refresh authentication
  const refreshAuth = useCallback(async () => {
    try {
      const tokensStr = localStorage.getItem(TOKEN_STORAGE_KEY)
      if (!tokensStr) {
        clearAuth()
        return
      }

      const tokens: AuthTokens = JSON.parse(tokensStr)
      
      try {
        // Try to get current user to validate token
        const user = await authAPI.getCurrentUser(tokens.access_token)
        
        // Update user in storage and state
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
        setState(prev => ({
          ...prev,
          user,
          isLoading: false,
          isAuthenticated: true,
        }))
      } catch (error) {
        // Token might be expired, try to refresh
        try {
          const newTokens = await authAPI.refreshToken(tokens.refresh_token)
          const user = await authAPI.getCurrentUser(newTokens.access_token)
          
          const orgStr = localStorage.getItem(ORG_STORAGE_KEY)
          const organization = orgStr ? JSON.parse(orgStr) : null
          
          setAuth(user, newTokens, organization)
        } catch (refreshError) {
          // Refresh failed, clear auth
          clearAuth()
        }
      }
    } catch (error) {
      clearAuth()
    }
  }, [clearAuth, setAuth])

  // Login
  const login = useCallback(async (email: string, password: string, rememberMe = false) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }))
      
      const response = await authAPI.login({
        email,
        password,
        remember_me: rememberMe,
      })
      
      setAuth(response.user, response.tokens, response.organization)
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }))
      throw error
    }
  }, [setAuth])

  // Register
  const register = useCallback(async (
    email: string,
    password: string,
    fullName: string,
    organizationName?: string
  ) => {
    try {
      setState(prev => ({ ...prev, isLoading: true }))
      
      const response = await authAPI.register({
        email,
        password,
        full_name: fullName,
        organization_name: organizationName,
      })
      
      setAuth(response.user, response.tokens, response.organization)
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }))
      throw error
    }
  }, [setAuth])

  // Logout
  const logout = useCallback(async () => {
    try {
      if (state.tokens?.access_token) {
        await authAPI.logout(state.tokens.access_token)
      }
    } catch (error) {
      // Even if logout fails on server, clear local state
      console.error('Logout error:', error)
    } finally {
      clearAuth()
    }
  }, [state.tokens?.access_token, clearAuth])

  // Initialize auth on mount
  useEffect(() => {
    const initAuth = async () => {
      const tokensStr = localStorage.getItem(TOKEN_STORAGE_KEY)
      const userStr = localStorage.getItem(USER_STORAGE_KEY)
      const orgStr = localStorage.getItem(ORG_STORAGE_KEY)

      if (tokensStr && userStr) {
        try {
          const tokens: AuthTokens = JSON.parse(tokensStr)
          const user: User = JSON.parse(userStr)
          const organization: Organization | null = orgStr ? JSON.parse(orgStr) : null

          setState({
            user,
            organization,
            tokens,
            isLoading: false,
            isAuthenticated: true,
          })

          // Refresh to validate tokens
          await refreshAuth()
        } catch (error) {
          clearAuth()
        }
      } else {
        setState(prev => ({ ...prev, isLoading: false }))
      }
    }

    initAuth()
  }, [refreshAuth, clearAuth])

  // Set up token refresh interval
  useEffect(() => {
    if (!state.tokens || !state.isAuthenticated) return

    const refreshInterval = setInterval(() => {
      refreshAuth()
    }, 14 * 60 * 1000) // Refresh every 14 minutes (tokens expire in 15)

    return () => clearInterval(refreshInterval)
  }, [state.tokens, state.isAuthenticated, refreshAuth])

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshAuth,
    clearAuth,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function useRequireAuth() {
  const auth = useAuth()
  
  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated) {
      window.location.href = '/auth/login'
    }
  }, [auth.isLoading, auth.isAuthenticated])

  return auth
}