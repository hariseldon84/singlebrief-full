import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diffInSeconds < 60) {
    return 'Just now'
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes}m ago`
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return `${hours}h ago`
  } else {
    const days = Math.floor(diffInSeconds / 86400)
    return `${days}d ago`
  }
}

export function getConfidenceColor(score: number): string {
  if (score >= 80) return 'text-success'
  if (score >= 60) return 'text-highlight'
  return 'text-red-500'
}

export function getConfidenceBadgeColor(score: number): string {
  if (score >= 80) return 'bg-success-50 text-success-800 border-success-200'
  if (score >= 60) return 'bg-highlight-50 text-highlight-800 border-highlight-200'
  return 'bg-red-50 text-red-800 border-red-200'
}