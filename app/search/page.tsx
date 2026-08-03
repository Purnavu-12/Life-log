'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import Link from 'next/link'
import { Search, Zap, ArrowLeft } from 'lucide-react'
import { api } from '@/lib/api'

interface SearchResult {
  id: string
  date: string
  similarity: number
  content: string
  tags: string[]
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [threshold, setThreshold] = useState([0.5])

  const handleSearch = async () => {
    if (!query.trim()) return

    setIsSearching(true)
    try {
      const data = await api.searchMemories(query, threshold[0])
      setResults(data.results)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="sm" className="p-2">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-serif font-bold text-foreground mb-2">Search Memories</h1>
              <p className="text-muted-foreground">Find memories using semantic search</p>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Link href="/dashboard">
              <Button variant="outline" size="sm">Dashboard</Button>
            </Link>
            <Link href="/upload">
              <Button variant="outline" size="sm">Upload</Button>
            </Link>
            <Link href="/settings">
              <Button variant="outline" size="sm">Settings</Button>
            </Link>
          </div>
        </div>

        {/* Search Input */}
        <Card className="mb-8">
          <CardContent className="pt-6 space-y-4">
            <div>
              <Input
                placeholder="What are you looking for? (e.g., 'meetings with Sarah', 'lunch plans', 'project updates')"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="text-lg"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-muted-foreground">
                  Similarity Threshold
                </label>
                <span className="text-sm font-medium">{(threshold[0] * 100).toFixed(0)}%</span>
              </div>
              <Slider
                value={threshold}
                onValueChange={setThreshold}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
            </div>

            <Button
              onClick={handleSearch}
              disabled={!query.trim() || isSearching}
              className="w-full"
            >
              <Search className="w-4 h-4 mr-2" />
              {isSearching ? 'Searching...' : 'Search'}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <div className="space-y-4">
          {results.length === 0 && query && !isSearching ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Zap className="w-12 h-12 mx-auto text-muted-foreground mb-4 opacity-50" />
                <p className="text-muted-foreground">No results found. Try a different query.</p>
              </CardContent>
            </Card>
          ) : (
            results.map((result) => (
              <Card key={result.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base">{result.date}</CardTitle>
                    </div>
                    <Badge variant="secondary">
                      {(result.similarity * 100).toFixed(1)}% match
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-foreground line-clamp-3">{result.content}</p>
                  <div className="flex gap-2 flex-wrap">
                    {result.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
