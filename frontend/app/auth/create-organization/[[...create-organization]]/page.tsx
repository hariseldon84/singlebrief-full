import { CreateOrganization } from '@clerk/nextjs'

export default function Page() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <CreateOrganization 
        appearance={{
          elements: {
            formButtonPrimary: 'bg-primary hover:bg-primary/90 text-primary-foreground',
            card: 'shadow-lg border-0',
          }
        }}
        afterCreateOrganizationUrl="/"
      />
    </div>
  )
}