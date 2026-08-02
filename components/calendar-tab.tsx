'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Calendar, Clock, MapPin, Link2, Loader2, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

interface CalEvent {
  id: string
  summary?: string
  description?: string
  location?: string
  start?: { dateTime?: string; date?: string }
  end?: { dateTime?: string; date?: string }
  htmlLink?: string
}

interface BusySlot {
  time?: string
  end?: string
}

interface FreeBusyPayload {
  freebusy?: {
    calendars?: {
      primary?: { busy?: BusySlot[] }
    }
  }
}

function formatTime(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function isBusySlot(startISO?: string, busy: BusySlot[] = []): boolean {
  if (!startISO) return false
  const start = new Date(startISO).getTime()
  return busy.some((b) => {
    const bs = new Date(b?.time || '').getTime()
    const be = new Date(b?.end || '').getTime()
    return !isNaN(bs) && !isNaN(be) && start >= bs && start < be
  })
}

function getBusyHours(slots: BusySlot[]): string | null {
  if (slots.length === 0) return null
  const hours = slots.reduce((acc, s) => {
    if (s.time && s.end) {
      acc += (new Date(s.end).getTime() - new Date(s.time).getTime()) / 3600000
    }
    return acc
  }, 0)
  return `${Math.round(hours)}h busy over the next day`
}

export default function CalendarTab() {
  const [events, setEvents] = useState<CalEvent[]>([])
  const [busySlots, setBusySlots] = useState<BusySlot[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notConnected, setNotConnected] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNotConnected(false)
    try {
      const [evtRes, busyRes] = await Promise.allSettled([
        api.listEvents('primary'),
        api.getFreeBusy(),
      ])

      if (evtRes.status === 'fulfilled') {
        setEvents(evtRes.value.events || [])
      } else {
        const msg: string = evtRes.reason?.message || ''
        if (/not connected|token|401|connect|unavailable/i.test(msg)) setNotConnected(true)
        setError(msg)
      }

      if (busyRes.status === 'fulfilled') {
        const payload = busyRes.value as FreeBusyPayload
        setBusySlots(payload?.freebusy?.calendars?.primary?.busy || [])
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load calendar')
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
          <p className="text-muted-foreground mt-4">Loading your calendar...</p>
        </CardContent>
      </Card>
    )
  }

  if (notConnected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Google Calendar</CardTitle>
          <CardDescription>Not connected yet</CardDescription>
        </CardHeader>
        <CardContent className="py-10 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-60" />
          <p className="text-muted-foreground mb-4">
            Connect your Google account to view your schedule, check free/busy slots, and create events.
          </p>
          <Button onClick={() => (window.location.href = api.getGoogleAuthUrl(['calendar']))}>
            <Link2 className="w-4 h-4 mr-2" />
            Connect Google Calendar
          </Button>
        </CardContent>
      </Card>
    )
  }

  const busyLabel = getBusyHours(busySlots)

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Upcoming Events</CardTitle>
            <CardDescription>Next 30 days from your primary calendar</CardDescription>
          </div>
          {busyLabel && <Badge variant="outline">{busyLabel}</Badge>}
        </CardHeader>
        <CardContent className="space-y-2">
          {events.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">No upcoming events.</p>
          )}
          {events.map((ev) => {
            const isBusy = isBusySlot(ev.start?.dateTime, busySlots)
            const start = ev.start?.dateTime || ev.start?.date || ''
            const date = start ? new Date(start) : null
            return (
              <div
                key={ev.id}
                className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/40 transition-colors"
              >
                <div className="flex flex-col items-center justify-center w-16 shrink-0">
                  <span className="text-xl font-serif font-bold">{Number.isNaN(date.getDate()) ? '–' : date.getDate()}</span>
                  <span className="text-xs text-muted-foreground uppercase tracking-wider">
                    {Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString([], { month: 'short' })}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{ev.summary || 'Untitled event'}</p>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatTime(ev.start?.dateTime) || 'All day'}
                    {ev.end?.dateTime ? ` – ${formatTime(ev.end.dateTime)}` : ''}
                  </p>
                  {ev.location && (
                    <p className="text-sm text-muted-foreground flex items-center gap-1 mt-0.5">
                      <MapPin className="w-3 h-3" />
                      {ev.location}
                    </p>
                  )}
                </div>
                {isBusy && (
                  <Badge variant="secondary" className="shrink-0">
                    Busy
                  </Badge>
                )}
              </div>
            )
          })}
        </CardContent>
      </Card>
    </div>
  )
}