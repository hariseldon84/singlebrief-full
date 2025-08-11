/**
 * Authentication API client
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface User {
  id: string
  email: string
  full_name: string
  avatar_url?: string
  role: 'admin' | 'manager' | 'team_member'
  is_active: boolean
  is_verified: boolean
  is_2fa_enabled: boolean
  last_login?: string
  created_at: string
  organization_id?: string
}

export interface Organization {
  id: string
  name: string
  slug: string
  domain?: string
  is_active: boolean
  privacy_policy_version: string
  data_retention_days: number
  created_at: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AuthResponse {
  user: User
  tokens: AuthTokens
  organization?: Organization
}

export interface RegisterData {
  email: string
  password: string
  full_name: string
  organization_name?: string
}

export interface LoginData {
  email: string
  password: string
  remember_me?: boolean
}

class AuthAPI {
  private baseUrl = `${API_BASE_URL}/api/v1/auth`

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }

    return response.json()
  }

  async login(data: LoginData): Promise<AuthResponse> {
    // Development bypass for testing
    if (process.env.NODE_ENV === 'development' && data.email === 'demo@singlebrief.com' && data.password === 'demo') {
      return {
        user: {
          id: 'demo-user-id',
          email: 'demo@singlebrief.com',
          full_name: 'Demo User',
          role: 'admin' as const,
          is_active: true,
          is_verified: true,
          is_2fa_enabled: false,
          created_at: new Date().toISOString(),
          organization_id: 'demo-org-id'
        },
        tokens: {
          access_token: 'demo-access-token',
          refresh_token: 'demo-refresh-token',
          token_type: 'Bearer',
          expires_in: 3600
        },
        organization: {
          id: 'demo-org-id',
          name: 'Demo Organization',
          slug: 'demo-org',
          is_active: true,
          privacy_policy_version: '1.0',
          data_retention_days: 90,
          created_at: new Date().toISOString()
        }
      }
    }
    
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    return response.json()
  }

  async logout(token: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error('Logout failed')
    }
  }

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await fetch(`${this.baseUrl}/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) {
      throw new Error('Token refresh failed')
    }

    return response.json()
  }

  async getCurrentUser(token: string): Promise<User> {
    const response = await fetch(`${this.baseUrl}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error('Failed to get user')
    }

    return response.json()
  }

  async verifyEmail(token: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/verify-email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Email verification failed')
    }
  }

  async resendVerification(email: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/resend-verification`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to resend verification')
    }
  }

  async getOAuthUrl(provider: 'google' | 'microsoft', redirectUri: string): Promise<{ auth_url: string; state: string }> {
    const response = await fetch(`${this.baseUrl}/oauth/${provider}/url?redirect_uri=${encodeURIComponent(redirectUri)}`)

    if (!response.ok) {
      throw new Error('Failed to get OAuth URL')
    }

    return response.json()
  }

  async oauthCallback(
    provider: 'google' | 'microsoft',
    code: string,
    state: string,
    redirectUri: string
  ): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/oauth/${provider}/callback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider,
        code,
        state,
        redirect_uri: redirectUri,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'OAuth authentication failed')
    }

    return response.json()
  }
}

export const authAPI = new AuthAPI()