'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, CheckCircle } from 'lucide-react'

export default function SettingsPage() {
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [autoCreate, setAutoCreate] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    // Simulate save
    setTimeout(() => {
      setSaving(false)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    }, 1000)
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
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <h3 className="font-semibold">Google Calendar</h3>
                    <p className="text-sm text-muted-foreground">Sync with your calendar</p>
                  </div>
                  <Button size="sm" variant="outline">
                    Connect
                  </Button>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <h3 className="font-semibold">Gmail</h3>
                    <p className="text-sm text-muted-foreground">Index your emails</p>
                  </div>
                  <Button size="sm" variant="outline">
                    Connect
                  </Button>
                </div>

                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <h3 className="font-semibold">Slack</h3>
                    <p className="text-sm text-muted-foreground">Connect your workspace</p>
                  </div>
                  <Button size="sm" variant="outline">
                    Connect
                  </Button>
                </div>
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
