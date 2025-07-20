import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Sidebar, MobileSidebar } from '@/components/ui/sidebar'
import { TopNavbar } from '@/components/ui/top-navbar'
import { AuthProvider } from '@/lib/auth/context'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
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
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AppLayout>{children}</AppLayout>
            <Toaster 
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#fff',
                  color: '#1A2D64',
                  border: '1px solid #e5e7eb',
                },
              }}
            />
          </AuthProvider>
        </QueryClientProvider>
      </body>
    </html>
  )
}

function AppLayout({ children }: { children: React.ReactNode }) {
  // Check if we're on an auth page (client-side only)
  if (typeof window !== 'undefined') {
    const isAuthPage = window.location.pathname.startsWith('/auth') || 
                       window.location.pathname.startsWith('/legal')
    
    if (isAuthPage) {
      return <div className="min-h-screen">{children}</div>
    }
  }

  return (
    <>
      <div className="flex h-screen overflow-hidden">
        {/* Desktop Sidebar */}
        <div className="hidden lg:flex lg:flex-shrink-0">
          <Sidebar />
        </div>
        
        {/* Main Content Area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Top Navigation */}
          <TopNavbar />
          
          {/* Page Content */}
          <main className="flex-1 overflow-auto bg-gray-50 p-4 lg:p-6">
            <div className="mx-auto max-w-7xl">
              {children}
            </div>
          </main>
        </div>
      </div>
      
      {/* Mobile Sidebar */}
      <MobileSidebar />
    </>
  )
}