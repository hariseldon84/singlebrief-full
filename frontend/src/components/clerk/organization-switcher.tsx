'use client'

import { OrganizationSwitcher } from '@clerk/nextjs'

export function ClerkOrganizationSwitcher() {
  return (
    <OrganizationSwitcher
      appearance={{
        elements: {
          organizationSwitcherTrigger: 'px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50',
          organizationSwitcherTriggerIcon: 'text-gray-600',
        }
      }}
      createOrganizationMode="navigation"
      createOrganizationUrl="/auth/create-organization"
      organizationProfileMode="navigation"
      organizationProfileUrl="/auth/organization-profile"
      afterCreateOrganizationUrl="/"
      afterLeaveOrganizationUrl="/auth/organization-selection"
      afterSelectOrganizationUrl="/"
    />
  )
}