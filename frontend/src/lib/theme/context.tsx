'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'

export type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  resolvedTheme: 'light' | 'dark'
}

interface ThemeContextType extends ThemeState {
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

const THEME_STORAGE_KEY = 'sb_theme'

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getStoredTheme(): Theme {
  if (typeof window === 'undefined') return 'system'
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY)
    if (stored && ['light', 'dark', 'system'].includes(stored)) {
      return stored as Theme
    }
  } catch (error) {
    console.error('Error reading theme from localStorage:', error)
  }
  return 'system'
}

function resolveTheme(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') {
    return getSystemTheme()
  }
  return theme
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<ThemeState>(() => {
    const theme = getStoredTheme()
    return {
      theme,
      resolvedTheme: resolveTheme(theme)
    }
  })

  const setTheme = useCallback((newTheme: Theme) => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, newTheme)
    } catch (error) {
      console.error('Error saving theme to localStorage:', error)
    }
    
    setState({
      theme: newTheme,
      resolvedTheme: resolveTheme(newTheme)
    })
  }, [])

  const toggleTheme = useCallback(() => {
    const newTheme = state.resolvedTheme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
  }, [state.resolvedTheme, setTheme])

  // Update resolved theme when system theme changes
  useEffect(() => {
    if (state.theme !== 'system') return

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => {
      setState(prev => ({
        ...prev,
        resolvedTheme: resolveTheme(prev.theme)
      }))
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [state.theme])

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement
    
    // Remove existing theme classes
    root.classList.remove('light', 'dark')
    
    // Add current theme class
    root.classList.add(state.resolvedTheme)
    
    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute(
        'content', 
        state.resolvedTheme === 'dark' ? '#0f172a' : '#ffffff'
      )
    }
  }, [state.resolvedTheme])

  const value: ThemeContextType = {
    ...state,
    setTheme,
    toggleTheme,
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}