'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Mail, MailOpen, Link2, Loader2, AlertCircle, User } from 'lucide-react'
import { api } from '@/lib/api'

interface MailMessage {
  id: string
  threadId?: string
  snippet?: string
  payload?: {
    headers?: { name?: string; value?: string }[]
  }
}

interface ParsedMail {
  id: string
  subject: string
  from: string
  date: string
  snippet: string
}

function parseHeaders(msg: MailMessage): ParsedMail {
  const headers = msg.payload?.headers || []
  const get = (name: string) => headers.find((h) => h.name?.toLowerCase() === name)?.value || ''
  return {
    id: msg.id,
    subject: get('subject') || '(no subject)',
    from: get('from') || 'unknown sender',
    date: get('date') || '',
    snippet: msg.snippet || '',
  }
}

function formatSender(from: string): string {
  const match = from.match(/^(.*?)<(.+)>/) || from.match(/^(.+)/)
  return (match?.[1] || from).trim()
}

function relativeDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const diff = Date.now() - d.getTime()
  const day = 86400000
  if (diff < day) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (diff < 7 * day) return d.toLocaleDateString([], { weekday: 'short' })
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

export default function MailTab() {
  const [messages, setMessages] = useState<ParsedMail[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notConnected, setNotConnected] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotConnected(false)
    try {
      const res = await api.listImportantMessages(10)
      setMessages((res.messages || []).map(parseHeaders))
    } catch (err: any) {
      const msg: string = err.message || ''
      if (/not connected|token|401|connect|unavailable/i.test(msg)) setNotConnected(true)
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <Loader2 className="w-10 h-10 mx-auto animate-spin text-muted-foreground" />
          <p className="text-muted-foreground mt-4">Checking your inbox...</p>
        </CardContent>
      </Card>
    )
  }

  if (notConnected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Gmail</CardTitle>
          <CardDescription>Not connected yet</CardDescription>
        </CardHeader>
        <CardContent className="py-10 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-60" />
          <p className="text-muted-foreground mb-4">
            Connect your Google account to surface important unread email highlights.
          </p>
          <Button onClick={() => (window.location.href = api.getGoogleAuthUrl(['gmail']))}>
            <Link2 className="w-4 h-4 mr-2" />
            Connect Gmail
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Important Unread</CardTitle>
        <CardDescription>Filtered highlights from your inbox</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {messages.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-8">No important unread messages.</p>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className="flex items-start gap-4 p-4 border rounded-lg hover:bg-muted/40 transition-colors"
          >
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center shrink-0">
              <User className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <p className="font-medium truncate">{m.subject}</p>
                <span className="text-xs text-muted-foreground shrink-0">{relativeDate(m.date)}</span>
              </div>
              <p className="text-sm text-muted-foreground truncate">{formatSender(m.from)}</p>
              <p className="text-sm text-foreground/80 mt-1 line-clamp-2">{m.snippet}</p>
            </div>
            <MailOpen className="w-4 h-4 text-muted-foreground shrink-0 mt-1" />
          </div>
        ))}
      </CardContent>
    </Card>
  )
}