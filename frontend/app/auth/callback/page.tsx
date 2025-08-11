'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth/context'
import { authAPI } from '@/lib/auth/api'
import { AlertCircle } from 'lucide-react'

export default function AuthCallback() {
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const searchParams = useSearchParams()
  const router = useRouter()
  const { login } = useAuth()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code')
        const state = searchParams.get('state')
        const error = searchParams.get('error')

        if (error) {
          throw new Error(`OAuth error: ${error}`)
        }

        if (!code || !state) {
          throw new Error('Missing required OAuth parameters (code or state)')
        }

        // Determine provider from session storage (set during OAuth initiation)
        const provider = sessionStorage.getItem('oauth_provider') as 'google' | 'microsoft'
        
        if (!provider) {
          throw new Error('OAuth provider not found in session. Please try signing in again.')
        }

        // Clear the session storage
        sessionStorage.removeItem('oauth_provider')

        const redirectUri = `${window.location.origin}/auth/callback`
        const response = await authAPI.oauthCallback(provider, code, state, redirectUri)

        // Set auth state
        const { login: contextLogin } = useAuth()
        // We need to manually set the auth state since we got the response directly
        localStorage.setItem('sb_tokens', JSON.stringify(response.tokens))
        localStorage.setItem('sb_user', JSON.stringify(response.user))
        if (response.organization) {
          localStorage.setItem('sb_organization', JSON.stringify(response.organization))
        }

        // Redirect to dashboard
        router.push('/')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication failed')
        setIsLoading(false)
      }
    }

    handleCallback()
  }, [searchParams, router])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
          <p className="mt-4 text-gray-600">Completing sign-in...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-full max-w-md">
          <div className="bg-white shadow-md rounded-lg p-6">
            <div className="flex items-center space-x-2 mb-4">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <h1 className="text-xl font-semibold text-gray-900">Authentication Error</h1>
            </div>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={() => router.push('/auth/login')}
              className="w-full btn-primary"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    )
  }

  return null
}