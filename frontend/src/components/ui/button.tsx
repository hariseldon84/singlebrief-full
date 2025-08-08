/**
 * Enhanced Button component with variants, sizes, and accessibility
 */

import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-white hover:bg-blue-700 focus-visible:ring-primary',
        destructive: 'bg-red-500 text-white hover:bg-red-600 focus-visible:ring-red-500',
        outline: 'border border-gray-300 bg-white text-gray-800 hover:bg-gray-50 hover:border-gray-400 hover:text-blue-700 focus-visible:ring-primary',
        secondary: 'bg-gray-100 text-gray-800 hover:bg-gray-200 hover:text-blue-700 focus-visible:ring-gray-500',
        ghost: 'text-gray-700 hover:bg-gray-100 hover:text-blue-700 focus-visible:ring-gray-500',
        link: 'text-primary underline-offset-4 hover:underline hover:text-blue-700 focus-visible:ring-primary',
        success: 'bg-success text-white hover:bg-green-600 focus-visible:ring-success',
        warning: 'bg-highlight text-white hover:bg-orange-600 focus-visible:ring-highlight'
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 px-3 text-xs',
        lg: 'h-12 px-6 text-base',
        xl: 'h-14 px-8 text-lg',
        icon: 'h-10 w-10',
        'icon-sm': 'h-8 w-8',
        'icon-lg': 'h-12 w-12'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default'
    }
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, leftIcon, rightIcon, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {!loading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        {children}
        {!loading && rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }