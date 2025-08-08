'use client'

import { Brain } from 'lucide-react'
import Image from 'next/image'
import { useState } from 'react'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  className?: string
}

export function Logo({ size = 'md', showText = true, className = '' }: LogoProps) {
  const [imageError, setImageError] = useState(false)

  const sizes = {
    sm: { width: 24, height: 24, textClass: 'text-sm' },
    md: { width: 32, height: 32, textClass: 'text-xl' },
    lg: { width: 40, height: 40, textClass: 'text-2xl' }
  }

  const currentSize = sizes[size]
  
  // Always use light mode logo (dark logo for light background)
  const logoSrc = '/assets/logo-light.svg'

  const logoAlt = 'SingleBrief Logo'

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className="flex-shrink-0">
        {!imageError ? (
          <Image
            src={logoSrc}
            alt={logoAlt}
            width={currentSize.width}
            height={currentSize.height}
            className="object-contain"
            onError={() => setImageError(true)}
            priority
          />
        ) : (
          // Fallback to icon if images don't exist
          <div className="rounded-md bg-primary flex items-center justify-center" 
               style={{ width: currentSize.width, height: currentSize.height }}>
            <Brain className="text-white" style={{ width: currentSize.width * 0.7, height: currentSize.height * 0.7 }} />
          </div>
        )}
      </div>
      {showText && (
        <span className={`font-bold text-primary ${currentSize.textClass}`}>
          SingleBrief
        </span>
      )}
    </div>
  )
}

// Simple logo without text for smaller spaces
export function LogoIcon({ size = 'md', className = '' }: { size?: 'sm' | 'md' | 'lg', className?: string }) {
  return <Logo size={size} showText={false} className={className} />
}