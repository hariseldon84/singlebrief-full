import { OrganizationProfile } from '@clerk/nextjs'

export default function Page() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <OrganizationProfile 
        appearance={{
          elements: {
            formButtonPrimary: 'bg-primary hover:bg-primary/90 text-primary-foreground',
            card: 'shadow-lg border-0',
          }
        }}
        afterLeaveOrganizationUrl="/auth/organization-selection"
      />
    </div>
  )
}