'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Upload, Mic, Loader2, CheckCircle } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useRouter } from 'next/navigation'

export default function UploadPage() {
  const router = useRouter()
  const [isRecording, setIsRecording] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const handleFileSelect = async (file: File) => {
    if (file.type.startsWith('audio/')) {
      setUploadedFile(file)
      setError(null)
      await uploadAudio(file)
    } else {
      setError('Please select an audio file (MP3, WAV, M4A, etc.)')
    }
  }

  const uploadAudio = async (file: File) => {
    setIsUploading(true)
    try {
      // Use the API client
      const response = await api.uploadAudio(file)
      
      if (!response.success) {
        throw new Error(response.error || 'Upload failed')
      }

      setUploadComplete(true)
      setTimeout(() => {
        router.push('/dashboard')
      }, 2000)
    } catch (err) {
      setError(err.message || 'Failed to upload audio. Please try again.')
      setIsUploading(false)
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' })
        await uploadAudio(audioFile)
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      setError('Could not access microphone. Please check permissions.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
      setIsUploading(true)
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8">
          <h1 className="text-3xl font-serif font-bold text-foreground mb-2">LifeLog</h1>
          <p className="text-muted-foreground">Capture your thoughts and memories</p>
        </div>

        <Card className="border-0 shadow-lg">
          <CardHeader>
            <CardTitle>Upload Audio</CardTitle>
            <CardDescription>Record or upload audio to extract memories</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {uploadComplete && (
              <Alert className="bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-700">
                  Audio uploaded successfully! Redirecting to dashboard...
                </AlertDescription>
              </Alert>
            )}

            {error && (
              <Alert className="bg-red-50 border-red-200">
                <AlertDescription className="text-red-700">{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-3">
              {/* Record Button */}
              <Button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isUploading && !isRecording}
                className="w-full"
                variant={isRecording ? 'destructive' : 'default'}
              >
                {isRecording ? (
                  <>
                    <Mic className="w-4 h-4 mr-2 animate-pulse" />
                    Stop Recording
                  </>
                ) : isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4 mr-2" />
                    Record Audio
                  </>
                )}
              </Button>

              {/* Upload Button */}
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading || isRecording}
                className="w-full"
                variant="outline"
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload Audio File
              </Button>

              <input
                ref={fileInputRef}
                type="file"
                accept="audio/*"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                className="hidden"
              />

              {uploadedFile && (
                <p className="text-sm text-muted-foreground text-center">
                  File: {uploadedFile.name}
                </p>
              )}
            </div>

            <div className="pt-4 border-t">
              <Link href="/dashboard">
                <Button variant="ghost" className="w-full">
                  Go to Dashboard
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
