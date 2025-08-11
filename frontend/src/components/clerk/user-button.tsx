'use client'

import { UserButton } from '@clerk/nextjs'

export function ClerkUserButton() {
  return (
    <UserButton
      appearance={{
        elements: {
          avatarBox: 'w-8 h-8',
        }
      }}
      userProfileMode="navigation"
      userProfileUrl="/auth/user-profile"
      afterSignOutUrl="/auth/sign-in"
      showName={false}
    />
  )
}