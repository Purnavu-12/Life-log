'use client'

import { NeuralCore } from "@/components/chat/neural-core"
import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowRight, Mic, Search, Brain, Calendar } from "lucide-react"

export default function Home() {
  const [showChat, setShowChat] = useState(false)

  if (showChat) {
    return <NeuralCore />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-accent/5">
      {/* Navigation */}
      <nav className="border-b bg-background/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-6 h-6 text-primary" />
            <span className="font-serif font-bold text-lg">LifeLog</span>
          </div>
          <div className="flex gap-2">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">Dashboard</Button>
            </Link>
            <Button onClick={() => setShowChat(true)} size="sm">
              Neural Core
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 py-16 md:py-24">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div className="space-y-3">
              <h1 className="text-5xl md:text-6xl font-serif font-bold text-foreground">
                Your Life, Captured
              </h1>
              <p className="text-xl text-muted-foreground">
                Transform fleeting thoughts into structured memories. Record audio, extract insights, and stay connected to what matters.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/upload" className="flex-1">
                <Button size="lg" className="w-full">
                  <Mic className="w-4 h-4 mr-2" />
                  Start Recording
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
              <Link href="/dashboard" className="flex-1">
                <Button size="lg" variant="outline" className="w-full">
                  View Dashboard
                </Button>
              </Link>
            </div>
          </div>

          {/* Feature Cards */}
          <div className="grid gap-4">
            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">Record & Transcribe</CardTitle>
                    <CardDescription>Capture audio and get instant transcriptions</CardDescription>
                  </div>
                  <Mic className="w-5 h-5 text-primary" />
                </div>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                Record your thoughts directly or upload audio files for automatic transcription.
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">Semantic Search</CardTitle>
                    <CardDescription>Find memories by meaning, not just keywords</CardDescription>
                  </div>
                  <Search className="w-5 h-5 text-primary" />
                </div>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                Search using natural language to find related memories and insights.
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">Calendar Integration</CardTitle>
                    <CardDescription>Sync with your calendar and tasks</CardDescription>
                  </div>
                  <Calendar className="w-5 h-5 text-primary" />
                </div>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                Automatically create calendar events and tasks from your memories.
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-card/50 border-t">
        <div className="max-w-7xl mx-auto px-4 py-16">
          <h2 className="text-3xl font-serif font-bold text-foreground mb-12 text-center">
            How It Works
          </h2>

          <div className="grid md:grid-cols-4 gap-8">
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <Mic className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground">Record</h3>
              <p className="text-sm text-muted-foreground">
                Record your thoughts, meetings, or conversations
              </p>
            </div>

            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <Brain className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground">Extract</h3>
              <p className="text-sm text-muted-foreground">
                AI extracts tasks, dates, and key information
              </p>
            </div>

            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <Search className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground">Search</h3>
              <p className="text-sm text-muted-foreground">
                Find memories with semantic search
              </p>
            </div>

            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <Calendar className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground">Action</h3>
              <p className="text-sm text-muted-foreground">
                Create events and tasks automatically
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <Card className="border-0 bg-gradient-to-r from-primary/10 to-accent/10">
          <CardContent className="py-12 text-center space-y-6">
            <h2 className="text-3xl font-serif font-bold text-foreground">
              Ready to capture your life?
            </h2>
            <p className="text-lg text-muted-foreground max-w-md mx-auto">
              Start recording your first memory and see how LifeLog transforms your daily routine.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/upload">
                <Button size="lg">
                  <Mic className="w-4 h-4 mr-2" />
                  Start Recording
                </Button>
              </Link>
              <Button onClick={() => setShowChat(true)} size="lg" variant="outline">
                <Brain className="w-4 h-4 mr-2" />
                Ask Neural Core
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
