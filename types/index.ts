// User types
export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  is_active: boolean
  created_at: string
  last_login?: string
}

// Memory types
export interface Memory {
  id: string
  user_id: string
  content: string
  summary?: string
  sentiment?: 'positive' | 'negative' | 'neutral'
  tags: string[]
  topics?: string[]
  tasks?: string[]
  people?: string[]
  dates?: string[]
  action_items?: string[]
  filename?: string
  source?: 'audio' | 'text' | 'email' | 'calendar'
  timestamp: string
  duration?: number
  word_count?: number
}

// API Response types
export interface ApiResponse<T = any> {
  success?: boolean
  error?: string
  detail?: string
  data?: T
}

export interface UploadResponse {
  success: boolean
  memory_id?: string
  database_id?: string
  transcript?: string
  extracted?: ExtractedData
  error?: string
}

export interface ExtractedData {
  summary?: string
  tasks?: string[]
  people?: string[]
  dates?: string[]
  topics?: string[]
  tags?: string[]
  sentiment?: string
  action_items?: string[]
}

// Search types
export interface SearchResult {
  id: string
  date: string
  similarity: number
  content: string
  tags: string[]
  summary?: string
  sentiment?: string
}

// Authentication types
export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user?: User
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  username: string
  password: string
  full_name?: string
}

// Google OAuth types
export interface GoogleAuthStatus {
  connected: boolean
  email?: string
  scopes?: string[]
}

export interface GoogleOAuthCallbackParams {
  code: string
  state?: string
  error?: string
}

// Settings types
export interface UserSettings {
  theme?: 'light' | 'dark' | 'system'
  email_notifications?: boolean
  auto_create_events?: boolean
  google_calendar_enabled?: boolean
  gmail_enabled?: boolean
}

// Calendar types
export interface CalendarEvent {
  id: string
  summary: string
  description?: string
  start: { dateTime?: string; date?: string }
  end: { dateTime?: string; date?: string }
  location?: string
  attendees?: any[]
}

// Gmail types
export interface GmailMessage {
  id: string
  threadId: string
  subject: string
  from: string
  to: string
  date: string
  snippet: string
  body?: string
  labels?: string[]
}
