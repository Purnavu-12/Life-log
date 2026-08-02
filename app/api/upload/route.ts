import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const audioFile = formData.get('audio') as File

    if (!audioFile) {
      return NextResponse.json(
        { error: 'No audio file provided' },
        { status: 400 }
      )
    }

    // TODO: Send to Python backend for processing
    // For now, return success
    console.log('Audio file received:', audioFile.name, audioFile.size)

    return NextResponse.json(
      {
        success: true,
        message: 'Audio uploaded successfully',
        filename: audioFile.name,
      },
      { status: 200 }
    )
  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json(
      { error: 'Failed to process upload' },
      { status: 500 }
    )
  }
}
