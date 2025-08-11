'use client'

import { useOrganization, useOrganizationList, useUser } from '@clerk/nextjs'

export function useClerkOrganization() {
  const { organization, isLoaded: isOrgLoaded } = useOrganization()
  const { userMemberships, setActive, isLoaded: isListLoaded } = useOrganizationList({
    userMemberships: {
      infinite: true,
    }
  })
  const { user } = useUser()

  const switchOrganization = async (orgId: string) => {
    try {
      if (setActive) {
        await setActive({ organization: orgId })
      }
    } catch (error) {
      console.error('Failed to switch organization:', error)
      throw error
    }
  }

  const createOrganization = async (name: string) => {
    // This will redirect to Clerk's create organization flow
    window.location.href = '/auth/create-organization'
  }

  return {
    organization,
    organizationList: userMemberships.data,
    user,
    isLoaded: isOrgLoaded && isListLoaded,
    switchOrganization,
    createOrganization,
    isOwner: (organization as any)?.membership?.role === 'org:admin',
    isMember: (organization as any)?.membership?.role === 'org:member',
  }
}