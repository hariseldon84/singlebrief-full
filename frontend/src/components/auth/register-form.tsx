'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth/context'
import { Eye, EyeOff, Mail, Lock, User, Building, AlertCircle } from 'lucide-react'
import Link from 'next/link'

export function RegisterForm() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    organizationName: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const { register } = useAuth()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return false
    }

    if (formData.password.length < 12) {
      setError('Password must be at least 12 characters long')
      return false
    }

    // Check password complexity
    const hasUpper = /[A-Z]/.test(formData.password)
    const hasLower = /[a-z]/.test(formData.password)
    const hasNumber = /\d/.test(formData.password)
    const hasSpecial = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(formData.password)

    if (!hasUpper || !hasLower || !hasNumber || !hasSpecial) {
      setError('Password must contain uppercase, lowercase, numbers, and special characters')
      return false
    }

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!validateForm()) {
      return
    }

    setIsLoading(true)

    try {
      await register(
        formData.email,
        formData.password,
        formData.fullName,
        formData.organizationName || undefined
      )
      // Redirect will happen automatically via useRequireAuth
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="w-full max-w-md space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Create your account</h1>
        <p className="text-neutral">Start your SingleBrief journey today</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-md">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <span className="text-sm text-red-600">{error}</span>
        </div>
      )}

      {/* Registration Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Full Name */}
        <div className="space-y-2">
          <label htmlFor="fullName" className="text-sm font-medium text-gray-900">
            Full name
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <User className="h-5 w-5 text-neutral" />
            </div>
            <input
              id="fullName"
              name="fullName"
              type="text"
              value={formData.fullName}
              onChange={handleChange}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md 
                       placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary 
                       focus:border-primary transition-colors"
              placeholder="John Doe"
              required
            />
          </div>
        </div>

        {/* Email Field */}
        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium text-gray-900">
            Email address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-neutral" />
            </div>
            <input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md 
                       placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary 
                       focus:border-primary transition-colors"
              placeholder="john@company.com"
              required
            />
          </div>
        </div>

        {/* Organization Name (Optional) */}
        <div className="space-y-2">
          <label htmlFor="organizationName" className="text-sm font-medium text-gray-900">
            Organization name <span className="text-neutral text-xs">(optional)</span>
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Building className="h-5 w-5 text-neutral" />
            </div>
            <input
              id="organizationName"
              name="organizationName"
              type="text"
              value={formData.organizationName}
              onChange={handleChange}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md 
                       placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary 
                       focus:border-primary transition-colors"
              placeholder="Acme Corp"
            />
          </div>
          <p className="text-xs text-neutral">
            Create a new organization or leave blank to join an existing one later
          </p>
        </div>

        {/* Password Field */}
        <div className="space-y-2">
          <label htmlFor="password" className="text-sm font-medium text-gray-900">
            Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-neutral" />
            </div>
            <input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleChange}
              className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md 
                       placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary 
                       focus:border-primary transition-colors"
              placeholder="Create a strong password"
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="h-5 w-5 text-neutral hover:text-gray-600" />
              ) : (
                <Eye className="h-5 w-5 text-neutral hover:text-gray-600" />
              )}
            </button>
          </div>
          <p className="text-xs text-neutral">
            Must be 12+ characters with uppercase, lowercase, numbers, and special characters
          </p>
        </div>

        {/* Confirm Password Field */}
        <div className="space-y-2">
          <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-900">
            Confirm password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-neutral" />
            </div>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleChange}
              className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md 
                       placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary 
                       focus:border-primary transition-colors"
              placeholder="Confirm your password"
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              {showConfirmPassword ? (
                <EyeOff className="h-5 w-5 text-neutral hover:text-gray-600" />
              ) : (
                <Eye className="h-5 w-5 text-neutral hover:text-gray-600" />
              )}
            </button>
          </div>
        </div>

        {/* Terms and Privacy */}
        <div className="text-sm text-neutral">
          By creating an account, you agree to our{' '}
          <Link href="/legal/terms" className="text-primary hover:text-primary-700 font-medium">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link href="/legal/privacy" className="text-primary hover:text-primary-700 font-medium">
            Privacy Policy
          </Link>
          .
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center justify-center space-x-2"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Creating account...</span>
            </>
          ) : (
            <span>Create account</span>
          )}
        </button>
      </form>

      {/* OAuth Registration */}
      <div className="space-y-4">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-neutral">Or sign up with</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            className="flex items-center justify-center px-4 py-2 border border-gray-300 
                     rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white 
                     hover:bg-gray-50 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Google
          </button>

          <button
            type="button"
            className="flex items-center justify-center px-4 py-2 border border-gray-300 
                     rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white 
                     hover:bg-gray-50 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="#00BCF2">
              <path d="M24 12c0-6.627-5.373-12-12-12S0 5.373 0 12c0 5.99 4.388 10.954 10.125 11.854V15.47H7.078V12h3.047V9.356c0-3.008 1.792-4.669 4.532-4.669 1.313 0 2.686.234 2.686.234v2.953H15.83c-1.491 0-1.956.925-1.956 1.874V12h3.328l-.532 3.469h-2.796v8.385C19.612 22.954 24 17.99 24 12z"/>
            </svg>
            Microsoft
          </button>
        </div>
      </div>

      {/* Sign In Link */}
      <div className="text-center">
        <span className="text-sm text-neutral">Already have an account? </span>
        <Link
          href="/auth/login"
          className="text-sm text-primary hover:text-primary-700 font-medium transition-colors"
        >
          Sign in
        </Link>
      </div>
    </div>
  )
}