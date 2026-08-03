'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Calendar, Search, Zap, User, Clock, Mail, FileText, Trash2 } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/lib/api'
import CalendarTab from '@/components/calendar-tab'
import MailTab from '@/components/mail-tab'
import ActionsQueue from '@/components/actions-queue'
import DailyBriefing from '@/components/daily-briefing'

interface Memory {
  id: string
  date: string
  time?: string
  content: string
  summary?: string
  tags: string[]
  tasks?: string[]
  people?: string[]
  sentiment?: string
}

export default function DashboardPage() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMemories = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await api.getMemories(10, 0)
        setMemories(data.memories)
      } catch (err: any) {
        setError(err?.message || 'Failed to fetch memories')
      } finally {
        setLoading(false)
      }
    }

    fetchMemories()
  }, [])

  const filteredMemories = memories.filter(
    (memory) =>
      memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      memory.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (memory.summary && memory.summary.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const handleDeleteMemory = async (id: string) => {
    try {
      await api.deleteMemory(id)
      setMemories((prev) => prev.filter((m) => m.id !== id))
    } catch (err: any) {
      setError(err?.message || 'Failed to delete memory')
    }
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-4xl font-serif font-bold text-foreground">LifeLog</h1>
              <p className="text-muted-foreground">Your memory and life management system</p>
            </div>
            <div className="flex gap-4 items-center">
              <Link href="/upload">
                <Button>+ New Memory</Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="mb-8">
          <div className="relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Daily Briefing */}
        <div className="mb-8">
          <DailyBriefing />
        </div>

        {/* Tabs */}
        <Tabs defaultValue="memories" className="space-y-4">
          <TabsList>
            <TabsTrigger value="memories">
              <Clock className="w-4 h-4 mr-2" />
              Memories
            </TabsTrigger>
            <TabsTrigger value="calendar">
              <Calendar className="w-4 h-4 mr-2" />
              Calendar
            </TabsTrigger>
            <TabsTrigger value="tasks">
              <Zap className="w-4 h-4 mr-2" />
              Tasks
            </TabsTrigger>
            <TabsTrigger value="people">
              <User className="w-4 h-4 mr-2" />
              People
            </TabsTrigger>
            <TabsTrigger value="mail">
              <Mail className="w-4 h-4 mr-2" />
              Mail
            </TabsTrigger>
          </TabsList>

          <TabsContent value="memories" className="space-y-4">
            {loading ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">Loading memories...</p>
              </div>
            ) : filteredMemories.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
                  <p className="text-muted-foreground">No memories found</p>
                  <Link href="/upload">
                    <Button className="mt-4" variant="outline">
                      Create Your First Memory
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ) : (
              filteredMemories.map((memory) => (
                <Card key={memory.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">{memory.date}</CardTitle>
                        <CardDescription>{memory.time || 'N/A'}</CardDescription>
                      </div>
                      <div className="flex gap-2 flex-wrap justify-end">
                        {memory.tags && memory.tags.length > 0 ? (
                          memory.tags.map((tag) => (
                            <Badge key={tag} variant="secondary">
                              {tag}
                            </Badge>
                          ))
                        ) : (
                          <Badge variant="secondary">No tags</Badge>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-muted-foreground hover:text-red-600"
                          onClick={() => handleDeleteMemory(memory.id)}
                          aria-label="Delete memory"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-foreground leading-relaxed">{memory.content}</p>

                    {memory.people && memory.people.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-2">People</p>
                        <div className="flex gap-2 flex-wrap">
                          {memory.people.map((person) => (
                            <Badge key={person} variant="outline">
                              <User className="w-3 h-3 mr-1" />
                              {person}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {memory.tasks && memory.tasks.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-2">Related Tasks</p>
                        <ul className="space-y-1">
                          {memory.tasks.map((task, idx) => (
                            <li key={idx} className="text-sm flex items-center">
                              <span className="w-2 h-2 rounded-full bg-primary mr-2" />
                              {task}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          <TabsContent value="calendar">
            <CalendarTab />
          </TabsContent>

          <TabsContent value="tasks">
            <ActionsQueue />
          </TabsContent>

          <TabsContent value="people">
            <Card>
              <CardContent className="py-12 text-center">
                <User className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
                <p className="text-muted-foreground">People view coming soon</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="mail">
            <MailTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
