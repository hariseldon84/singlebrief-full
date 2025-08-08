import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Sidebar, MobileSidebar } from '../src/components/ui/sidebar'
import { TopNavbar } from '../src/components/ui/top-navbar'
import { Providers } from '../src/lib/providers'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'SingleBrief - AI Intelligence Operative',
  description: 'Answers from everyone. Delivered by one.',
  keywords: ['AI', 'intelligence', 'team management', 'briefing', 'enterprise'],
  authors: [{ name: 'SingleBrief Team' }],
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
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
      <body className="min-h-screen bg-background text-foreground antialiased">
        <Providers>
          <AppLayout>{children}</AppLayout>
        </Providers>
      </body>
    </html>
  )
}