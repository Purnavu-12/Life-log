'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import Link from 'next/link'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, CheckCircle, Calendar, Mail, Link2, Unlink2, Download, Trash2, ArrowLeft } from 'lucide-react'
import { LifeLogApi, api } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

export default function SettingsPage() {
  const router = useRouter()
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [autoCreate, setAutoCreate] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [googleStatus, setGoogleStatus] = useState<{
    connected: boolean
    email?: string
    scopes?: string[]
  } | null>(null)
  const [connecting, setConnecting] = useState(false)
  const [googleError, setGoogleError] = useState<string | null>(null)
  const [loadingSettings, setLoadingSettings] = useState(true)
  const [privacyAction, setPrivacyAction] = useState<string | null>(null)
  const [privacyMessage, setPrivacyMessage] = useState<string | null>(null)
  const { toast } = useToast()

  // Load settings + Google connection status
  useEffect(() => {
    const load = async () => {
      try {
        const settings = await api.getSettings()
        setEmailNotifications(settings.email_notifications)
        setAutoCreate(settings.auto_create_events)
      } catch (err: any) {
        console.warn('Could not load settings', err)
      } finally {
        setLoadingSettings(false)
      }

      try {
        const status = await api.getGoogleStatus()
        setGoogleStatus(status)
      } catch (err: any) {
        setGoogleError(err?.message || 'Failed to check Google status')
      }

      // Check URL params for OAuth redirect result
      const params = new URLSearchParams(window.location.search)
      const googleParam = params.get('google')
      if (googleParam === 'connected') {
        const email = params.get('email') || ''
        setGoogleStatus({ connected: true, email, scopes: [] })
        setGoogleError(null)
        // Clear the query param from the URL
        window.history.replaceState({}, document.title, '/settings')
      } else if (googleParam === 'error') {
        const msg = params.get('message') || 'Google OAuth failed'
        setGoogleError(msg)
        setGoogleStatus({ connected: false })
        // Clear the query param from the URL
        window.history.replaceState({}, document.title, '/settings')
      }
    }
    load()
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.updateSettings({ email_notifications: emailNotifications, auto_create_events: autoCreate })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
      toast({
        title: "Settings saved",
        description: "Your preferences have been updated.",
      })
    } catch (err: any) {
      setGoogleError(err?.message || 'Failed to save settings')
      toast({
        title: "Save failed",
        description: err?.message || 'Failed to save settings',
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  const handleConnectGoogle = async () => {
    try {
      setConnecting(true)
      setGoogleError(null)

      // Open Google OAuth in new window
      const scopes = ['calendar', 'gmail']
      const authUrl = api.getGoogleAuthUrl(scopes)
      window.location.href = authUrl
    } catch (err: any) {
      setGoogleError(err?.message || 'Failed to connect Google')
      setConnecting(false)
      toast({
        title: "Google connect failed",
        description: err?.message || 'Failed to connect Google',
        variant: "destructive",
      })
    }
  }

  const handleDisconnectGoogle = async () => {
    try {
      setConnecting(true)
      setGoogleError(null)

      // Use the API client method
      const apiRes = await api.disconnectGoogle()

      if (apiRes.success) {
        // Refresh status
        const status = await api.getGoogleStatus()
        setGoogleStatus(status)
        toast({
          title: "Google disconnected",
          description: "Your Google Calendar and Gmail integrations have been disconnected.",
        })
      } else {
        setGoogleError(apiRes.message || 'Failed to disconnect')
        toast({
          title: "Disconnect failed",
          description: apiRes.message || 'Failed to disconnect Google',
          variant: "destructive",
        })
      }
    } catch (err: any) {
      setGoogleError(err?.message || 'Failed to disconnect Google')
      toast({
        title: "Disconnect failed",
        description: err?.message || 'Failed to disconnect Google',
        variant: "destructive",
      })
    } finally {
      setConnecting(false)
    }
  }

  const handleExportData = async () => {
    setPrivacyAction('exporting')
    setPrivacyMessage(null)
    try {
      const data = await api.exportUserData()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `lifelog-export-${new Date().toISOString().slice(0, 10)}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      setPrivacyMessage('Your data has been exported as a JSON file.')
      toast({
        title: "Data exported",
        description: "Your data has been downloaded as a JSON file.",
      })
    } catch (err: any) {
      setPrivacyMessage(`Export failed: ${err?.message || 'unknown error'}`)
      toast({
        title: "Export failed",
        description: err?.message || 'Unknown error',
        variant: "destructive",
      })
    } finally {
      setPrivacyAction(null)
    }
  }

  const handleClearData = async () => {
    if (!window.confirm('This will permanently delete ALL your memories, actions, audit logs, and Google credentials. This cannot be undone. Continue?')) {
      return
    }
    setPrivacyAction('clearing')
    setPrivacyMessage(null)
    try {
      const res = await api.clearUserData()
      setPrivacyMessage(res.message || 'All user data has been cleared.')
      const status = await api.getGoogleStatus()
      setGoogleStatus(status)
    } catch (err: any) {
      setPrivacyMessage(`Clear failed: ${err?.message || 'unknown error'}`)
    } finally {
      setPrivacyAction(null)
    }
  }

  const handleRevokeGoogle = async () => {
    setPrivacyAction('revoking')
    setPrivacyMessage(null)
    try {
      const res = await api.revokeGoogleAccess()
      setPrivacyMessage(res.message || 'Google access revoked.')
      const status = await api.getGoogleStatus()
      setGoogleStatus(status)
    } catch (err: any) {
      setPrivacyMessage(`Revoke failed: ${err?.message || 'unknown error'}`)
    } finally {
      setPrivacyAction(null)
    }
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm" className="p-2">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <h1 className="text-3xl font-serif font-bold text-foreground">Settings</h1>
          </div>
          <div className="flex gap-2">
            <Link href="/">
              <Button variant="ghost" size="sm">
                ← Back to Home
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="outline" size="sm">
                → Dashboard
              </Button>
            </Link>
          </div>
        </div>

        {saved && (
          <Alert className="mb-4 bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-700">Settings saved successfully</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="general" className="space-y-6">
          <TabsList>
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="integrations">Integrations</TabsTrigger>
            <TabsTrigger value="privacy">Privacy</TabsTrigger>
          </TabsList>

          {/* General Settings */}
          <TabsContent value="general" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Preferences</CardTitle>
                <CardDescription>Customize your LifeLog experience</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-base font-semibold">Email Notifications</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Receive daily summaries of your memories
                    </p>
                  </div>
                  <Switch
                    checked={emailNotifications}
                    onCheckedChange={setEmailNotifications}
                  />
                </div>

                <div className="flex items-center justify-between pt-4 border-t">
                  <div>
                    <Label className="text-base font-semibold">Auto-Create Events</Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      Automatically create calendar events from meetings
                    </p>
                  </div>
                  <Switch
                    checked={autoCreate}
                    onCheckedChange={setAutoCreate}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Integrations */}
          <TabsContent value="integrations" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Connected Services</CardTitle>
                <CardDescription>Manage your integrations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {googleError && (
                  <Alert className="bg-red-50 border-red-200 text-red-700 mb-4">
                    <AlertDescription>{googleError}</AlertDescription>
                  </Alert>
                )}

                {/* Google Calendar */}
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    <Calendar className="w-8 h-8 text-blue-500" />
                    <div>
                      <h3 className="font-semibold">Google Calendar</h3>
                      <p className="text-sm text-muted-foreground">Sync with your calendar</p>
                    </div>
                  </div>
                  {googleStatus?.connected ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleDisconnectGoogle}
                      disabled={connecting}
                    >
                      {connecting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Unlink2 className="w-4 h-4 mr-2" />
                          Disconnect
                        </>
                      )}
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={handleConnectGoogle}
                      disabled={connecting}
                    >
                      {connecting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Link2 className="w-4 h-4 mr-2" />
                          Connect
                        </>
                      )}
                    </Button>
                  )}
                </div>

                {/* Gmail */}
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    <Mail className="w-8 h-8 text-red-500" />
                    <div>
                      <h3 className="font-semibold">Gmail</h3>
                      <p className="text-sm text-muted-foreground">Index your emails</p>
                    </div>
                  </div>
                  {googleStatus?.connected ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleDisconnectGoogle}
                      disabled={connecting}
                    >
                      {connecting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Unlink2 className="w-4 h-4 mr-2" />
                          Disconnect
                        </>
                      )}
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={handleConnectGoogle}
                      disabled={connecting}
                    >
                      {connecting ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Link2 className="w-4 h-4 mr-2" />
                          Connect
                        </>
                      )}
                    </Button>
                  )}
                </div>

                {/* Slack */}
                <div className="flex items-center justify-between p-4 border rounded-lg opacity-50">
                  <div className="flex items-center gap-4">
                    <div className="w-8 h-8 bg-gray-200 rounded flex items-center justify-center">
                      <span className="text-sm font-bold">S</span>
                    </div>
                    <div>
                      <h3 className="font-semibold">Slack</h3>
                      <p className="text-sm text-muted-foreground">Connect your workspace</p>
                    </div>
                  </div>
                  <Button size="sm" variant="outline" disabled>
                    Coming Soon
                  </Button>
                </div>

                {/* Connection Info */}
                {googleStatus?.connected && (
                  <Alert className="bg-green-50 border-green-200 text-green-700">
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription className="flex flex-col gap-2">
                      <span>
                        Connected to Google as {googleStatus.email}
                        {googleStatus.scopes && googleStatus.scopes.length > 0 && (
                          <span className="block text-sm mt-1">
                            Scopes: {googleStatus.scopes.join(', ')}
                          </span>
                        )}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        className="self-start border-green-300 text-green-800 hover:bg-green-100"
                        onClick={() => router.push('/dashboard')}
                      >
                        Go to Dashboard
                      </Button>
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Privacy */}
          <TabsContent value="privacy" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Privacy & Security</CardTitle>
                <CardDescription>Control how your data is handled</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-semibold mb-2">Data Retention</h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    Your memories are stored securely and encrypted at rest. You can export or clear your data at any time.
                  </p>
                  {privacyMessage && (
                    <p className="text-sm text-green-700 mb-4">{privacyMessage}</p>
                  )}
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Button variant="outline" size="sm" onClick={handleExportData} disabled={!!privacyAction}>
                      {privacyAction === 'exporting' ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                      Export My Data
                    </Button>
                    {googleStatus?.connected && (
                      <Button variant="outline" size="sm" onClick={handleRevokeGoogle} disabled={!!privacyAction}>
                        {privacyAction === 'revoking' ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Unlink2 className="w-4 h-4 mr-2" />}
                        Revoke Google Access
                      </Button>
                    )}
                    <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700 hover:border-red-300" onClick={handleClearData} disabled={!!privacyAction}>
                      {privacyAction === 'clearing' ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}
                      Clear All Data
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Save Button */}
        <div className="mt-8 flex justify-end gap-4">
          <Button variant="outline">Cancel</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
