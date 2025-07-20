/**
 * Accessibility utilities and helpers
 * WCAG 2.1 AA compliance utilities
 */

// Focus management
export const trapFocus = (element: HTMLElement) => {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  const firstFocusable = focusableElements[0] as HTMLElement
  const lastFocusable = focusableElements[focusableElements.length - 1] as HTMLElement

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          e.preventDefault()
          lastFocusable.focus()
        }
      } else {
        if (document.activeElement === lastFocusable) {
          e.preventDefault()
          firstFocusable.focus()
        }
      }
    }
    
    if (e.key === 'Escape') {
      element.dispatchEvent(new CustomEvent('escape'))
    }
  }

  element.addEventListener('keydown', handleKeyDown)
  
  return () => {
    element.removeEventListener('keydown', handleKeyDown)
  }
}

// Announce to screen readers
export const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcer = document.createElement('div')
  announcer.setAttribute('aria-live', priority)
  announcer.setAttribute('aria-atomic', 'true')
  announcer.className = 'sr-only'
  
  document.body.appendChild(announcer)
  announcer.textContent = message
  
  setTimeout(() => {
    document.body.removeChild(announcer)
  }, 1000)
}

// Check color contrast ratio
export const getContrastRatio = (color1: string, color2: string): number => {
  const getLuminance = (color: string): number => {
    const rgb = color.match(/\d+/g)?.map(Number) || [0, 0, 0]
    const [r, g, b] = rgb.map(c => {
      c = c / 255
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    })
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
  }

  const lum1 = getLuminance(color1)
  const lum2 = getLuminance(color2)
  const brightest = Math.max(lum1, lum2)
  const darkest = Math.min(lum1, lum2)
  
  return (brightest + 0.05) / (darkest + 0.05)
}

// Keyboard navigation helpers
export const createRovingTabIndex = (container: HTMLElement, items: NodeListOf<HTMLElement>) => {
  let currentIndex = 0

  const updateTabIndex = () => {
    items.forEach((item, index) => {
      item.tabIndex = index === currentIndex ? 0 : -1
    })
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        e.preventDefault()
        currentIndex = (currentIndex + 1) % items.length
        updateTabIndex()
        items[currentIndex].focus()
        break
      case 'ArrowUp':
      case 'ArrowLeft':
        e.preventDefault()
        currentIndex = currentIndex === 0 ? items.length - 1 : currentIndex - 1
        updateTabIndex()
        items[currentIndex].focus()
        break
      case 'Home':
        e.preventDefault()
        currentIndex = 0
        updateTabIndex()
        items[currentIndex].focus()
        break
      case 'End':
        e.preventDefault()
        currentIndex = items.length - 1
        updateTabIndex()
        items[currentIndex].focus()
        break
    }
  }

  container.addEventListener('keydown', handleKeyDown)
  updateTabIndex()

  return () => {
    container.removeEventListener('keydown', handleKeyDown)
  }
}

// Skip link component
export const SkipLink = ({ href, children }: { href: string; children: React.ReactNode }) => (
  <a
    href={href}
    className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:rounded-md"
  >
    {children}
  </a>
)

// Screen reader only text
export const ScreenReaderOnly = ({ children }: { children: React.ReactNode }) => (
  <span className="sr-only">{children}</span>
)

// High contrast detection
export const useHighContrast = () => {
  if (typeof window === 'undefined') return false
  
  return window.matchMedia('(prefers-contrast: high)').matches
}

// Reduced motion detection
export const useReducedMotion = () => {
  if (typeof window === 'undefined') return false
  
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

// Focus visible utility
export const focusVisible = 'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2'

// Touch target size (minimum 44px)
export const touchTarget = 'min-h-[44px] min-w-[44px]'

// High contrast mode styles
export const highContrastSupport = 'forced-colors:border-[ButtonBorder] forced-colors:text-[ButtonText]'