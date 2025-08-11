import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { ClerkProvider } from '@clerk/nextjs'
import { Providers } from '@/lib/providers'
import { AppLayoutWrapper } from '@/components/layout/app-layout-wrapper'

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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider>
      <html lang="en" className={inter.variable}>
        <body className="min-h-screen bg-background text-foreground antialiased">
          <Providers>
            <AppLayoutWrapper>{children}</AppLayoutWrapper>
          </Providers>
        </body>
      </html>
    </ClerkProvider>
  )
}