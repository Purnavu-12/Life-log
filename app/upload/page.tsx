'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Upload, Mic, Loader2, CheckCircle, ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useRouter } from 'next/navigation'
import { useToast } from '@/hooks/use-toast'

export default function UploadPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [isRecording, setIsRecording] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const handleFileSelect = async (file: File) => {
    // Check by MIME type or file extension
    const allowedExtensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.webm']
    const isAudioByType = file.type.startsWith('audio/')
    const isAudioByExtension = allowedExtensions.some(ext => file.name.toLowerCase().endsWith(ext))

    if (isAudioByType || isAudioByExtension) {
      setUploadedFile(file)
      setError(null)
      await uploadAudio(file)
    } else {
      setError('Please select an audio file (MP3, WAV, M4A, AAC, OGG, FLAC, WEBM)')
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
      toast({
        title: "Audio uploaded successfully",
        description: "Your memory is being processed and stored.",
      })
      setTimeout(() => {
        router.push('/dashboard')
      }, 2000)
    } catch (err: any) {
      setError(err?.message || 'Failed to upload audio. Please try again.')
      setIsUploading(false)
      toast({
        title: "Upload failed",
        description: err?.message || 'Failed to upload audio',
        variant: "destructive",
      })
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
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="p-2">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-serif font-bold text-foreground mb-2">LifeLog</h1>
              <p className="text-muted-foreground">Capture your thoughts and memories</p>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Link href="/dashboard">
              <Button variant="outline" size="sm">Dashboard</Button>
            </Link>
            <Link href="/search">
              <Button variant="outline" size="sm">Search</Button>
            </Link>
            <Link href="/settings">
              <Button variant="outline" size="sm">Settings</Button>
            </Link>
          </div>
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
