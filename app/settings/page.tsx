'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, CheckCircle, Calendar, Mail, Link2, Unlink2 } from 'lucide-react'
import { LifeLogApi, api } from '@/lib/api'

export default function SettingsPage() {
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

  // Check Google connection status
  useEffect(() => {
    const checkGoogleStatus = async () => {
      try {
        const status = await api.getGoogleStatus()
        setGoogleStatus(status)
      } catch (err: any) {
        setGoogleError(err?.message || 'Failed to check Google status')
      }
    }
    checkGoogleStatus()
  }, [])

  const handleSave = async () => {
    setSaving(true)
    // Simulate save
    setTimeout(() => {
      setSaving(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    }, 1000)
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
      } else {
        setGoogleError(apiRes.message || 'Failed to disconnect')
      }
    } catch (err: any) {
      setGoogleError(err?.message || 'Failed to disconnect Google')
    } finally {
      setConnecting(false)
    }
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-serif font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground">Manage your LifeLog preferences</p>
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
                    <AlertDescription>
                      Connected to Google as {googleStatus.email}
                      {googleStatus.scopes && googleStatus.scopes.length > 0 && (
                        <span className="block text-sm mt-1">
                          Scopes: {googleStatus.scopes.join(', ')}
                        </span>
                      )}
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
                    Your memories are stored securely and encrypted at rest.
                  </p>
                  <Button variant="outline" size="sm">
                    View Privacy Policy
                  </Button>
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
