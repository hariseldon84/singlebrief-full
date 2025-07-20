import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../src/app/globals.css'
import { Sidebar, MobileSidebar } from '../src/components/ui/sidebar'
import { TopNavbar } from '../src/components/ui/top-navbar'
import { AuthProvider } from '../src/lib/auth/context'
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

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <TopNavbar />
        <div className="flex-1 p-6">
          {children}
        </div>
      </div>
      <MobileSidebar />
    </div>
  )
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
                },
              }}
            />
          </AuthProvider>
        </QueryClientProvider>
      </body>
    </html>
  )
}
