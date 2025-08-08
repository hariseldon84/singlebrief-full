'use client'

import { useState } from 'react'
import { Palette, Monitor, Moon, Sun } from 'lucide-react'
import { useTheme } from '@/lib/theme/context'

export function AppearanceSettings() {
  const { theme, setTheme } = useTheme()
  const [fontSize, setFontSize] = useState('medium')

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Appearance</h2>
      
      <div className="space-y-6">
        <div>
          <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Theme</h3>
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => setTheme('light')}
              className={`p-4 border rounded-lg flex flex-col items-center space-y-2 ${
                theme === 'light' ? 'border-primary bg-primary-50' : 'border-gray-300 dark:border-gray-600'
              }`}
            >
              <Sun className="h-6 w-6" />
              <span className="text-sm text-gray-900 dark:text-gray-100">Light</span>
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`p-4 border rounded-lg flex flex-col items-center space-y-2 ${
                theme === 'dark' ? 'border-primary bg-primary-50' : 'border-gray-300 dark:border-gray-600'
              }`}
            >
              <Moon className="h-6 w-6" />
              <span className="text-sm text-gray-900 dark:text-gray-100">Dark</span>
            </button>
            <button
              onClick={() => setTheme('system')}
              className={`p-4 border rounded-lg flex flex-col items-center space-y-2 ${
                theme === 'system' ? 'border-primary bg-primary-50' : 'border-gray-300'
              }`}
            >
              <Monitor className="h-6 w-6" />
              <span className="text-sm text-gray-900 dark:text-gray-100">System</span>
            </button>
          </div>
        </div>

        <div>
          <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Font Size</h3>
          <div className="space-y-2">
            <label className="flex items-center space-x-3">
              <input 
                type="radio" 
                name="fontSize" 
                value="small"
                checked={fontSize === 'small'}
                onChange={(e) => setFontSize(e.target.value)}
                className="text-primary"
              />
              <span className="text-sm text-gray-900 dark:text-gray-100">Small</span>
            </label>
            <label className="flex items-center space-x-3">
              <input 
                type="radio" 
                name="fontSize" 
                value="medium"
                checked={fontSize === 'medium'}
                onChange={(e) => setFontSize(e.target.value)}
                className="text-primary"
              />
              <span className="text-base text-gray-900 dark:text-gray-100">Medium</span>
            </label>
            <label className="flex items-center space-x-3">
              <input 
                type="radio" 
                name="fontSize" 
                value="large"
                checked={fontSize === 'large'}
                onChange={(e) => setFontSize(e.target.value)}
                className="text-primary"
              />
              <span className="text-lg text-gray-900 dark:text-gray-100">Large</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}