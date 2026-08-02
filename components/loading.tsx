import { Loader2 } from 'lucide-react'

interface LoadingProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

/**
 * Simple loading spinner
 */
export function LoadingSpinner({ size = 'md', className = '' }: Omit<LoadingProps, 'message'>) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  }
  
  return (
    <Loader2 className={`${sizes[size]} animate-spin ${className}`} />
  )
}

/**
 * Full page loading
 */
export function LoadingPage({ message = 'Loading...' }: LoadingProps) {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <LoadingSpinner size="lg" className="text-primary" />
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  )
}

/**
 * Inline loading with message
 */
export function LoadingInline({ message = 'Loading...', size = 'sm', className = '' }: LoadingProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <LoadingSpinner size={size} />
      <span className="text-sm text-muted-foreground">{message}</span>
    </div>
  )
}

/**
 * Loading button content
 */
export function LoadingButtonContent({ message = 'Loading' }: Omit<LoadingProps, 'size' | 'className'>) {
  return (
    <>
      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
      {message}
    </>
  )
}
