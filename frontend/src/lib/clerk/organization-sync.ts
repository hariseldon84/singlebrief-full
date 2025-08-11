'use client'

import { useUser, useOrganization, useAuth } from '@clerk/nextjs'
import { useEffect } from 'react'

// Sync Clerk user/org data with backend
export function useClerkSync() {
  const { user, isLoaded: userLoaded } = useUser()
  const { organization, isLoaded: orgLoaded } = useOrganization()
  const { getToken } = useAuth()

  useEffect(() => {
    if (!userLoaded || !orgLoaded) return

    const syncUserData = async () => {
      if (user) {
        try {
          // Sync user data with backend
          const userData = {
            clerk_user_id: user.id,
            email: user.primaryEmailAddress?.emailAddress,
            full_name: user.fullName,
            avatar_url: user.imageUrl,
            phone: user.primaryPhoneNumber?.phoneNumber,
          }

          // Call backend API to sync user
          await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/clerk/sync-user`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${await getToken()}`,
            },
            body: JSON.stringify(userData),
          })
        } catch (error) {
          console.error('Failed to sync user data:', error)
        }
      }
    }

    const syncOrganizationData = async () => {
      if (organization) {
        try {
          // Sync organization data with backend
          const orgData = {
            clerk_org_id: organization.id,
            name: organization.name,
            slug: organization.slug,
            image_url: organization.imageUrl,
            members_count: organization.membersCount,
            created_at: organization.createdAt,
          }

          // Call backend API to sync organization
          await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/clerk/sync-organization`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${await getToken()}`,
            },
            body: JSON.stringify(orgData),
          })
        } catch (error) {
          console.error('Failed to sync organization data:', error)
        }
      }
    }

    syncUserData()
    syncOrganizationData()
  }, [user, organization, userLoaded, orgLoaded])

  return {
    user,
    organization,
    isLoaded: userLoaded && orgLoaded,
  }
}