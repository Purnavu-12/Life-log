import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { query, threshold } = await request.json()

    if (!query) {
      return NextResponse.json(
        { error: 'No query provided' },
        { status: 400 }
      )
    }

    // TODO: Call ChromaDB vector search via Python backend
    // Mock results for now
    const mockResults = [
      {
        id: '1',
        date: '2024-08-01',
        similarity: 0.92,
        content: 'Had a meeting with Sarah about the Q3 project roadmap.',
        tags: ['meeting', 'work', 'planning'],
      },
      {
        id: '2',
        date: '2024-07-31',
        similarity: 0.87,
        content: 'Discussed quarterly planning with the team.',
        tags: ['meeting', 'planning', 'team'],
      },
    ]

    const filtered = mockResults.filter((r) => r.similarity >= threshold)

    return NextResponse.json(
      { results: filtered },
      { status: 200 }
    )
  } catch (error) {
    console.error('Search error:', error)
    return NextResponse.json(
      { error: 'Failed to process search' },
      { status: 500 }
    )
  }
}
