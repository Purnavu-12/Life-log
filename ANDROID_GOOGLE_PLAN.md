# Plan: Gmail & Calendar in the Android app

## Goal
Bring the website's Google Calendar + Gmail features into the Android app:
- Google sign-in / connect flow
- Show upcoming calendar events
- Show important unread emails
- Disconnect Google
- Keep server as source of truth (app only calls existing backend endpoints)

## Recommended approach (low hassle)
Use the existing backend OAuth flow with a mobile deep link, instead of adding the Google Sign-In SDK.

Why:
- Backend already implements OAuth, token storage, calendar and Gmail endpoints.
- App does not need Google Cloud OAuth client IDs / SHA-1 setup.
- App only needs to open a browser tab and then read status/endpoints.

## Backend changes
1. Add mobile-friendly OAuth completion.
   - Modify `/auth/google` and `/auth/google/callback` to accept an optional `mobile=1` (or `platform=android`) flag.
   - When mobile, redirect final callback to `lifelog://oauth?google=connected&email=...` (or error).
   - Keep existing web redirect behavior unchanged.
2. No new data endpoints needed; reuse:
   - `GET /auth/google/status`
   - `POST /auth/google/disconnect`
   - `GET /api/google/calendars`
   - `GET /api/google/events`
   - `GET /api/google/messages`
   - `GET /api/google/messages/important`
   - `GET /api/google/profile`

## Android manifest
1. Add intent filter for custom scheme:
   - `lifelog://oauth` (or `com.lifelog.app://oauth`)
2. Ensure `MainActivity` handles the incoming intent and updates a "Google connected" state.

## Android API client
Add to `LifeLogService` / `Api`:
- `getGoogleStatus()`
- `disconnectGoogle()`
- `listCalendars()`
- `listEvents(calendarId, timeMin, timeMax)`
- `listMessages(query, maxResults)`
- `listImportantMessages(maxResults)`
- `getGmailProfile()`

## Data models
Add Kotlin serializable models:
- `GoogleStatus(connected, email, scopes)`
- `CalendarInfo(id, summary, primary)`
- `CalendarEvent(id, summary, start, end, location, description)`
- `GmailMessage(id, threadId, subject, from, snippet, date)`
- `GmailProfile(emailAddress, messagesTotal)`

## UI plan
1. Settings screen:
   - Google account card:
     - status (connected email or "Not connected")
     - Connect button opens Custom Tab to `/auth/google?scope=calendar&scope=gmail&mobile=1`
     - Disconnect button
2. New "Insights" or extend Home:
   - "Upcoming events" card list (next 7 days)
   - "Important emails" card list
   - Pull-to-refresh / manual refresh
3. Keep navigation simple:
   - Option A: add a 5th bottom-nav item "Insights"
   - Option B: put both sections on Home below memories
   Recommended: Option B for less navigation clutter, with a "See all" link.

## ViewModel
Add:
- `googleStatus: StateFlow<GoogleStatus?>`
- `upcomingEvents: StateFlow<List<CalendarEvent>>`
- `importantEmails: StateFlow<List<GmailMessage>>`
- `loadGoogleStatus()`
- `loadUpcomingEvents()`
- `loadImportantEmails()`
- `disconnectGoogle()`

## OAuth flow in app
1. User taps "Connect Google".
2. App opens Custom Tab to backend auth URL with `mobile=1`.
3. Backend redirects to Google consent.
4. Google redirects back to backend callback.
5. Backend saves credentials and redirects to `lifelog://oauth?google=connected&email=...`.
6. Android receives deep link, sets connected state, refreshes status.
7. App calls `loadUpcomingEvents()` and `loadImportantEmails()`.

## Edge cases
- Server not reachable: show friendly error and retry.
- User denies scopes: status remains disconnected; show message.
- Token expired: backend refreshes using stored refresh token; if refresh fails, prompt reconnect.
- Phone and laptop must be on same network for local IP server.

## Effort estimate
- Backend mobile redirect: small
- Android API + models: small
- UI: medium
- Deep link handling: small
- Testing: medium

## First implementation step
Start with backend mobile redirect + Android deep link + status check, then add calendar list, then Gmail list.