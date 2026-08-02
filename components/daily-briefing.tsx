'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Calendar, Mail, Zap, Clock, TrendingUp, TrendingDown, MessageSquare, Loader2, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

interface DailyBriefing {
  date: string
  memories: {
    today_count: number
    recent: Array<{
      id: string
      summary?: string
      tags: string[]
      sentiment?: string
    }>
  }
  actions: {
    pending_count: number
    high_priority: Array<{
      id: string
      title: string
      priority: string
      action_type: string
    }>
  }
  calendar: {
    today_events_count: number
    upcoming: Array<{
      id: string
      summary: string
      start: string
      end: string
      location?: string
    }>
  }
  gmail: {
    important_messages_count: number
    messages: Array<{
      id: string
      subject: string
      from: string
      snippet: string
    }>
  }
  quick_stats: {
    total_memories: number
    total_pending_actions: number
  }
}

function getSentimentColor(sentiment: string): string {
  switch (sentiment?.toLowerCase()) {
    case 'positive': return 'bg-green-100 text-green-800 border-green-200'
    case 'negative': return 'bg-red-100 text-red-800 border-red-200'
    case 'neutral': return 'bg-gray-100 text-gray-800 border-gray-200'
    default: return 'bg-blue-100 text-blue-800 border-blue-200'
  }
}

function getPriorityColor(priority: string): string {
  switch (priority?.toLowerCase()) {
    case 'urgent': return 'bg-red-500'
    case 'high': return 'bg-orange-500'
    case 'medium': return 'bg-yellow-500'
    case 'low': return 'bg-green-500'
    default: return 'bg-gray-500'
  }
}

function formatTime(isoDate: string): string {
  if (!isoDate) return ''
  try {
    const date = new Date(isoDate)
    if (isNaN(date.getTime())) return isoDate
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoDate
  }
}

function formatDate(isoDate: string): string {
  if (!isoDate) return ''
  try {
    const date = new Date(isoDate)
    if (isNaN(date.getTime())) return isoDate
    return date.toLocaleDateString([], { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  } catch {
    return isoDate
  }
}

export default function DailyBriefing() {
  const [briefing, setBriefing] = useState<DailyBriefing | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string>('')

  const loadBriefing = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getDailyBriefing()
      setBriefing(data)
      setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
    } catch (err: any) {
      setError(err.message || 'Failed to load daily briefing')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadBriefing()
  }, [])

  if (loading) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <Loader2 className="w-10 h-10 mx-auto animate-spin text-muted-foreground" />
          <p className="text-muted-foreground mt-4">Loading your daily briefing...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <AlertCircle className="w-10 h-10 mx-auto text-muted-foreground mb-4" />
          <p className="text-muted-foreground">{error}</p>
          <Button onClick={loadBriefing} className="mt-4">Retry</Button>
        </CardContent>
      </Card>
    )
  }

  if (!briefing) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
          <p className="text-muted-foreground">No briefing data available</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Daily Briefing</h2>
          <p className="text-muted-foreground">Your personalized overview for {formatDate(briefing.date)}</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            Last updated: {lastUpdated}
          </span>
          <Button variant="outline" size="sm" onClick={loadBriefing}>
            <Loader2 className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Today's Events</span>
              </div>
              <Badge variant="outline">{briefing.calendar.today_events_count}</Badge>
            </div>
            <div className="text-3xl font-bold">{briefing.calendar.today_events_count}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Pending Actions</span>
              </div>
              <Badge variant="outline">{briefing.actions.pending_count}</Badge>
            </div>
            <div className="text-3xl font-bold">{briefing.actions.pending_count}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Today's Memories</span>
              </div>
              <Badge variant="outline">{briefing.memories.today_count}</Badge>
            </div>
            <div className="text-3xl font-bold">{briefing.memories.today_count}</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Mail className="w-5 h-5 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Important Emails</span>
              </div>
              <Badge variant="outline">{briefing.gmail.important_messages_count}</Badge>
            </div>
            <div className="text-3xl font-bold">{briefing.gmail.important_messages_count}</div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Calendar Events */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Today's Events
            </CardTitle>
            <CardDescription>
              {briefing.calendar.today_events_count > 0 
                ? `You have ${briefing.calendar.today_events_count} events scheduled for today`
                : 'No events scheduled for today'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {briefing.calendar.upcoming.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No events today</p>
            ) : (
              briefing.calendar.upcoming.map((event) => (
                <div key={event.id} className="flex items-center gap-4 p-3 border rounded-lg">
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center shrink-0">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{event.summary}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatTime(event.start)} - {formatTime(event.end)}
                    </p>
                    {event.location && (
                      <p className="text-sm text-muted-foreground truncate">{event.location}</p>
                    )}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* High Priority Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5" />
              High Priority Actions
            </CardTitle>
            <CardDescription>
              {briefing.actions.high_priority.length > 0 
                ? `You have ${briefing.actions.high_priority.length} high priority actions`
                : 'No high priority actions'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {briefing.actions.high_priority.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No high priority actions</p>
            ) : (
              briefing.actions.high_priority.map((action) => (
                <div key={action.id} className="flex items-center gap-4 p-3 border rounded-lg">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" 
                       style={{ backgroundColor: getPriorityColor(action.priority) }}>
                    <Zap className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{action.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {action.action_type.replace('_', ' ')}
                    </p>
                  </div>
                  <Badge className={getPriorityColor(action.priority)}>
                    {action.priority}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Recent Memories */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Recent Memories
            </CardTitle>
            <CardDescription>
              {briefing.memories.recent.length > 0 
                ? `You have ${briefing.memories.recent.length} recent memories`
                : 'No recent memories'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {briefing.memories.recent.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No recent memories</p>
            ) : (
              briefing.memories.recent.map((memory) => (
                <div key={memory.id} className="flex items-center gap-4 p-3 border rounded-lg">
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center shrink-0">
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">
                      {memory.summary || 'No summary available'}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {memory.tags.slice(0, 2).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Badge className={getSentimentColor(memory.sentiment)}>
                    {memory.sentiment || 'neutral'}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Important Messages */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5" />
              Important Messages
            </CardTitle>
            <CardDescription>
              {briefing.gmail.messages.length > 0 
                ? `You have ${briefing.gmail.messages.length} important messages`
                : 'No important messages'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {briefing.gmail.messages.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">No important messages</p>
            ) : (
              briefing.gmail.messages.map((message) => (
                <div key={message.id} className="flex items-start gap-4 p-3 border rounded-lg">
                  <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center shrink-0">
                    <Mail className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{message.subject}</p>
                    <p className="text-sm text-muted-foreground truncate">{message.from}</p>
                    <p className="text-sm text-foreground/80 line-clamp-2 mt-1">{message.snippet}</p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Statistics</CardTitle>
          <CardDescription>
            Overall metrics for your LifeLog account
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{briefing.quick_stats.total_memories}</div>
            <div className="text-sm text-muted-foreground">Total Memories</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{briefing.quick_stats.total_pending_actions}</div>
            <div className="text-sm text-muted-foreground">Pending Actions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{briefing.gmail.important_messages_count}</div>
            <div className="text-sm text-muted-foreground">Important Emails</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{briefing.calendar.today_events_count}</div>
            <div className="text-sm text-muted-foreground">Today's Events</div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}