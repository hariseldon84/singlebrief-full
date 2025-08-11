'use client'

import { useUser, useOrganization } from '@clerk/nextjs'
import { Button } from '@/components/ui/button'
import { Crown, CreditCard } from 'lucide-react'

interface UpgradeButtonProps {
  variant?: 'default' | 'outline' | 'ghost'
  size?: 'default' | 'sm' | 'lg' | 'xl'
  children?: React.ReactNode
}

export function UpgradeButton({ variant = 'default', size = 'default', children }: UpgradeButtonProps) {
  const { user } = useUser()
  const { organization } = useOrganization()

  const handleUpgrade = () => {
    if (organization) {
      // Organization billing - redirect to Clerk's billing portal
      window.location.href = `/auth/organization-profile/billing`
    } else {
      // Personal billing - redirect to user profile billing
      window.location.href = `/auth/user-profile/billing`
    }
  }

  return (
    <Button
      onClick={handleUpgrade}
      variant={variant}
      size={size}
      className="flex items-center space-x-2"
    >
      <Crown className="h-4 w-4" />
      <span>{children || 'Upgrade Plan'}</span>
    </Button>
  )
}

// Subscription status component
export function SubscriptionStatus() {
  const { user } = useUser()
  const { organization } = useOrganization()

  // Check subscription status from Clerk metadata
  const orgMetadata = organization?.publicMetadata as any
  const userMetadata = user?.publicMetadata as any
  
  const isSubscribed = orgMetadata?.subscriptionStatus === 'active' || 
                      userMetadata?.subscriptionStatus === 'active'
  
  const plan = (orgMetadata?.plan || userMetadata?.plan || 'free') as string

  if (isSubscribed) {
    return (
      <div className="flex items-center space-x-2 text-green-600">
        <Crown className="h-4 w-4" />
        <span className="text-sm font-medium capitalize">{plan} Plan</span>
      </div>
    )
  }

  return (
    <div className="flex items-center space-x-2 text-gray-500">
      <CreditCard className="h-4 w-4" />
      <span className="text-sm">Free Plan</span>
    </div>
  )
}