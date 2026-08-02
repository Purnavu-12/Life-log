'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Check, X, Clock, Calendar, Mail, User, Zap, Loader2, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

interface ProposedAction {
  id: string
  title: string
  description?: string
  action_type: string
  priority: string
  status: string
  confidence: number
  memory_id?: string
  related_entities?: string[]
  scheduled_time?: string
  created_at: string
}

interface ActionCounts {
  pending: number
  approved: number
  rejected: number
  completed: number
}

function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'urgent': return 'bg-red-500'
    case 'high': return 'bg-orange-500'
    case 'medium': return 'bg-yellow-500'
    case 'low': return 'bg-green-500'
    default: return 'bg-gray-500'
  }
}

function getActionIcon(actionType: string) {
  switch (actionType) {
    case 'create_event': return <Calendar className="w-4 h-4" />
    case 'send_email': return <Mail className="w-4 h-4" />
    case 'create_task': return <Zap className="w-4 h-4" />
    case 'set_reminder': return <Clock className="w-4 h-4" />
    case 'add_note': return <User className="w-4 h-4" />
    case 'sync_calendar': return <Calendar className="w-4 h-4" />
    default: return <Zap className="w-4 h-4" />
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'approved': return 'bg-green-100 text-green-800 border-green-200'
    case 'rejected': return 'bg-red-100 text-red-800 border-red-200'
    case 'completed': return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    default: return 'bg-gray-100 text-gray-800 border-gray-200'
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
      day: 'numeric',
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } catch {
    return isoDate
  }
}

function PriorityIndicator({ priority }: { priority: string }) {
  return (
    <div className="flex items-center">
      <div className={cn("w-2 h-2 rounded-full mr-2", getPriorityColor(priority))} />
      <span className="text-xs text-muted-foreground capitalize">{priority}</span>
    </div>
  )
}

export default function ActionsQueue() {
  const [actions, setActions] = useState<ProposedAction[]>([])
  const [counts, setCounts] = useState<ActionCounts>({ pending: 0, approved: 0, rejected: 0, completed: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedStatus, setSelectedStatus] = useState('pending')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [actionsRes, countsRes] = await Promise.all([
        api.getActions(selectedStatus, undefined, undefined, 20, 0),
        api.getActionCounts()
      ])
      
      setActions(actionsRes.actions || [])
      setCounts(countsRes.counts || { pending: 0, approved: 0, rejected: 0, completed: 0 })
    } catch (err: any) {
      setError(err.message || 'Failed to load actions')
    } finally {
      setLoading(false)
    }
  }, [selectedStatus])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleStatusChange = (status: string) => {
    setSelectedStatus(status)
  }

  const handleApprove = async (action: ProposedAction) => {
    try {
      await api.approveAction(action.id)
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to approve action')
    }
  }

  const handleReject = async (action: ProposedAction) => {
    try {
      await api.rejectAction(action.id, 'User rejected')
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to reject action')
    }
  }

  const handleComplete = async (action: ProposedAction) => {
    try {
      await api.completeAction(action.id)
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to complete action')
    }
  }

  const handleDelete = async (action: ProposedAction) => {
    try {
      await api.deleteAction(action.id)
      await loadData()
    } catch (err: any) {
      setError(err.message || 'Failed to delete action')
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-16 text-center">
          <Loader2 className="w-10 h-10 mx-auto animate-spin text-muted-foreground" />
          <p className="text-muted-foreground mt-4">Loading actions...</p>
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
          <Button onClick={loadData} className="mt-4">Retry</Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Status Tabs */}
      <Tabs value={selectedStatus} onValueChange={handleStatusChange} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="pending">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Pending
              {counts.pending > 0 && (
                <Badge variant="default" className="ml-1">{counts.pending}</Badge>
              )}
            </div>
          </TabsTrigger>
          <TabsTrigger value="approved">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              Approved
              {counts.approved > 0 && (
                <Badge variant="default" className="ml-1">{counts.approved}</Badge>
              )}
            </div>
          </TabsTrigger>
          <TabsTrigger value="rejected">
            <div className="flex items-center gap-2">
              <X className="w-4 h-4" />
              Rejected
              {counts.rejected > 0 && (
                <Badge variant="default" className="ml-1">{counts.rejected}</Badge>
              )}
            </div>
          </TabsTrigger>
          <TabsTrigger value="completed">
            <div className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              Completed
              {counts.completed > 0 && (
                <Badge variant="default" className="ml-1">{counts.completed}</Badge>
              )}
            </div>
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Actions List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              {getActionIcon(selectedStatus || 'pending')}
              {selectedStatus.charAt(0).toUpperCase() + selectedStatus.slice(1)} Actions
            </span>
            <Badge variant="outline" className="text-sm">
              {actions.length} total
            </Badge>
          </CardTitle>
          <CardDescription>
            {selectedStatus === 'pending' 
              ? 'Actions that need your approval or review'
              : `Actions with ${selectedStatus} status`}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-3">
          {actions.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
              <p className="text-muted-foreground">
                {selectedStatus === 'pending' 
                  ? 'No pending actions to review'
                  : `No ${selectedStatus} actions found`}
              </p>
              {selectedStatus === 'pending' && (
                <p className="text-sm text-muted-foreground mt-2">
                  Upload audio memories to generate actions
                </p>
              )}
            </div>
          ) : (
            actions.map((action) => (
              <div 
                key={action.id} 
                className="flex items-start gap-4 p-4 border rounded-lg hover:bg-muted/40 transition-colors"
              >
                <div className="flex flex-col items-center shrink-0">
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                    {getActionIcon(action.action_type)}
                  </div>
                  <PriorityIndicator priority={action.priority} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <h3 className="font-medium truncate">{action.title}</h3>
                    <Badge className={getStatusColor(action.status)}>
                      {action.status}
                    </Badge>
                  </div>
                  
                  {action.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                      {action.description}
                    </p>
                  )}
                  
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>Created: {formatDate(action.created_at)}</span>
                    {action.scheduled_time && (
                      <span>Scheduled: {formatDate(action.scheduled_time)}</span>
                    )}
                    <span>Confidence: {Math.round(action.confidence * 100)}%</span>
                    {action.memory_id && (
                      <Badge variant="outline" className="text-xs">
                        Memory: {action.memory_id.slice(0, 8)}...
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Action buttons based on status */}
                <div className="flex flex-col gap-2 shrink-0">
                  {action.status === 'pending' && (
                    <>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="h-8 px-3" 
                        onClick={() => handleApprove(action)}
                        title="Approve"
                      >
                        <Check className="w-3 h-3" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="h-8 px-3" 
                        onClick={() => handleReject(action)}
                        title="Reject"
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </>
                  )}
                  
                  {action.status === 'approved' && (
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="h-8 px-3" 
                      onClick={() => handleComplete(action)}
                      title="Mark as completed"
                    >
                      <Check className="w-3 h-3" /> Complete
                    </Button>
                  )}
                  
                  {(action.status === 'rejected' || action.status === 'completed') && (
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="h-8 px-3" 
                      onClick={() => handleDelete(action)}
                      title="Delete"
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}