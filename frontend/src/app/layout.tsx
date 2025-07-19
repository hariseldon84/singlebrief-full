import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Sidebar } from '@/components/ui/sidebar'
import { TopNavbar } from '@/components/ui/top-navbar'
import { AuthProvider } from '@/lib/auth/context'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'SingleBrief - AI Intelligence Operative',
  description: 'Answers from everyone. Delivered by one.',
  keywords: ['AI', 'intelligence', 'team management', 'briefing', 'enterprise'],
  authors: [{ name: 'SingleBrief Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#1A2D64',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-gray-50 antialiased">
        <AuthProvider>
          <AppLayout>{children}</AppLayout>
        </AuthProvider>
      </body>
    </html>
  )
}

function AppLayout({ children }: { children: React.ReactNode }) {
  // Check if we're on an auth page
  const isAuthPage = typeof window !== 'undefined' && 
                     (window.location.pathname.startsWith('/auth') || 
                      window.location.pathname.startsWith('/legal'))

  if (isAuthPage) {
    return children
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar - Desktop */}
      <div className="hidden lg:flex lg:flex-shrink-0">
        <Sidebar />
      </div>
      
      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navigation */}
        <TopNavbar />
        
        {/* Page Content */}
        <main className="flex-1 overflow-auto bg-gray-50 p-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}