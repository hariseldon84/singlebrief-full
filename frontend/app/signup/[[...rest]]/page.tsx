'use client'

import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <SignUp 
        appearance={{
          elements: {
            formButtonPrimary: 'bg-indigo-600 hover:bg-indigo-700 text-white',
            card: 'shadow-lg border-0',
            headerTitle: 'text-2xl font-bold text-gray-900',
            headerSubtitle: 'text-gray-600',
          }
        }}
        afterSignUpUrl="/"
        signInUrl="/signin"
        redirectUrl="/"
      />
    </div>
  )
}