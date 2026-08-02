'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'

export default function GoogleCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, isAuthenticated } = useAuth()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')

  useEffect(() => {
    const code = searchParams.get('code')
    const error = searchParams.get('error')
    const state = searchParams.get('state')

    const handleCallback = async () => {
      if (error) {
        setStatus('error')
        setMessage(error)
        return
      }

      if (!code) {
        setStatus('error')
        setMessage('No authorization code received from Google')
        return
      }

      try {
        // First, we need to get the tokens from the backend
        // The backend /auth/google/callback endpoint handles the OAuth flow
        // But we need a way to pass the code to the backend and get tokens back
        
        // Since this is a frontend page, we'll exchange the code directly
        // The backend will return the Google user info, then we connect it
        
        // For now, we'll show instructions since the flow needs backend support
        // In production, you would:
        // 1. Exchange code for tokens on backend
        // 2. Get Google user info
        // 3. Connect to current user
        
        // Show loading while we wait for the backend to process
        setStatus('loading')
        setMessage('Connecting to Google...')

        // In a real implementation, you would call:
        // const response = await fetch(`/api/auth/google/callback?code=${code}&state=${state}`)
        // But we need the backend to handle this
        
        // For now, redirect to settings with a message
        setTimeout(() => {
          if (!isAuthenticated) {
            router.push('/auth/login?from=google')
            return
          }
          router.push('/settings?google=connecting')
        }, 2000)

      } catch (err) {
        setStatus('error')
        setMessage(err.message || 'Failed to connect Google account')
      }
    }

    handleCallback()
  }, [searchParams, router, isAuthenticated])

  // If user needs to login first
  useEffect(() => {
    if (!isAuthenticated && status !== 'loading') {
      router.push('/auth/login?from=google')
    }
  }, [isAuthenticated, router, status])

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="w-full max-w-md border-0 shadow-lg">
          <CardHeader className="text-center">
            <CardTitle>Please Sign In First</CardTitle>
            <CardDescription>
              You need to be logged in to connect your Google account
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button onClick={() => router.push('/auth/login?from=google')}>
              Sign In
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-0 shadow-lg">
        <CardHeader className="text-center">
          <CardTitle>Connecting Google Account</CardTitle>
          <CardDescription>
            Please wait while we connect your Google account
          </CardDescription>
        </CardHeader>
        
        <CardContent className="text-center space-y-4">
          {status === 'loading' && (
            <>
              <Loader2 className="w-12 h-12 mx-auto animate-spin text-primary" />
              <p className="text-muted-foreground">{message}</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <CheckCircle className="w-12 h-12 mx-auto text-green-500" />
              <p className="text-foreground">Successfully connected Google account!</p>
              {email && <p className="text-muted-foreground">Connected as: {email}</p>}
              <Button onClick={() => router.push('/settings')} className="mt-4">
                Go to Settings
              </Button>
            </>
          )}
          
          {status === 'error' && (
            <>
              <XCircle className="w-12 h-12 mx-auto text-red-500" />
              <Alert className="bg-red-50 border-red-200 text-red-700">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{message}</AlertDescription>
              </Alert>
              <Button onClick={() => router.push('/settings')} variant="outline" className="mt-4">
                Back to Settings
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
