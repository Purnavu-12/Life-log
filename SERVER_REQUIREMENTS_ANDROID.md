# LifeLog Server Requirements — Calendar, Gmail, AI & Chat (for the Android app)

This document lists everything the **backend server** must provide for the Android
app to match the website: Google Calendar, Gmail, AI summarisation / important
extraction from transcripts, and AI chat.

The app is a thin client. It never stores Google tokens and never calls Google
directly. All Google + AI work stays on the server.

---

## 1. Deployment & base URL

- Current deployed base: `https://lifelog-backend-242284331646.us-central1.run.app/`
- Android `API_BASE_URL` is set to that value in `android/app/build.gradle.kts`.
- The events WebSocket is derived automatically:
  - `https://host/` → `wss://host/events`
- Must be reachable over the internet; HTTPS/WSS required in production.

### Required environment variables
| Variable | Purpose |
|---|---|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (server-side only) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret (server-side only) |
| `GOOGLE_REDIRECT_URI` | e.g. `https://.../auth/google/callback` |
| `FRONTEND_URL` | Web frontend URL (used for web OAuth redirect) |
| `OPENAI_API_KEY` | Whisper + LLM fallback |
| `POOLSIDE_API_KEY` / Poolside config | Primary LLM |
| Vector DB / Chroma path | Memory embeddings for search + chat grounding |
| SQL DB config | Memories, actions, Google credentials, settings |

> Google client ID / secret / redirect URI live **only on the server**.
> Never ship them in the Android app.

---

## 2. Google OAuth (Calendar + Gmail sign-in)

### Endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/auth/google?scope=calendar&scope=gmail&mobile=1` | Start OAuth. `mobile=1` makes the callback redirect to `lifelog://oauth?...` instead of the web URL. |
| GET | `/auth/google/callback?code=...&state=...` | Google redirect target. Exchanges code, stores tokens, then redirects to `lifelog://oauth?google=connected&email=...` for mobile. |
| POST | `/auth/google/connect` | Optional: connect credentials manually (access_token/refresh_token/email/scopes). |
| GET | `/auth/google/status` | Returns `{ connected, email, scopes }`. |
| POST | `/auth/google/disconnect` | Removes stored Google credentials. |
| POST | `/api/privacy/revoke-google` | Revokes Google access + deletes credentials. |

### Scopes
- Calendar: `https://www.googleapis.com/auth/calendar`, `.../calendar.events`
- Gmail: `https://www.googleapis.com/auth/gmail.readonly`
- OIDC: `openid`, `email`, `profile`

### Token handling
- Store `access_token`, `refresh_token`, `expires_at`, `scopes`, `email`, `google_user_id`.
- Auto-refresh access token server-side; return `401` only if refresh fails.

---

## 3. Google Calendar endpoints

| Method | Path | Query / body | Returns |
|---|---|---|---|
| GET | `/api/google/calendars` | — | `{ calendars: [...] }` |
| GET | `/api/google/events` | `calendar_id`, `time_min`, `time_max` | `{ events: [...] }` |
| POST | `/api/google/events` | `summary, start, end, description?, location?, calendar_id?` | `{ success, event }` |
| DELETE | `/api/google/events/{event_id}` | `calendar_id` | `{ success }` |
| GET | `/api/google/freebusy` | `time_min`, `time_max` | `{ freebusy }` |

Event object (Google shape):
```json
{
  "id": "...",
  "summary": "Team meeting",
  "start": { "dateTime": "2026-10-20T09:00:00Z" },
  "end":   { "dateTime": "2026-10-20T10:00:00Z" },
  "location": "Room 2",
  "description": "..."
}
```

Android uses: `listCalendars`, `listEvents(calendarId, timeMin, timeMax)`.
Home screen shows the next 7 days.

---

## 4. Gmail endpoints

| Method | Path | Query | Returns |
|---|---|---|---|
| GET | `/api/google/messages` | `query?`, `max_results` | `{ messages: [...] }` |
| GET | `/api/google/messages/important` | `max_results` | `{ messages: [...] }` (important + unread) |
| GET | `/api/google/messages/{message_id}` | — | `{ message }` |
| GET | `/api/google/profile` | — | `{ profile }` |
| POST | `/api/google/index-emails` | `limit` | `{ emails, count }` (index into vector DB for search) |

Message object (Google Gmail shape): `id`, `threadId`, `snippet`, `payload.headers[]`.
Android extracts `Subject` and `From` from headers.

Android uses: `googleImportantMessages(maxResults = 10)`.
Home screen shows the latest important emails.

---

## 5. AI pipeline for transcripts (summaries + important info)

### Endpoint
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/upload` | multipart `file` (audio) | see below |

### Server steps
1. **Transcribe** audio with Whisper (local `whisper.cpp` / OpenAI / Poolside).
2. **Extract** structured info with one LLM pass.
3. **Store** transcript + embeddings in the vector DB.
4. **Generate proposed actions** (task/event candidates) with the LLM.
5. **Save** the memory row in SQL.

### Response shape
```json
{
  "success": true,
  "memory_id": "vector-id",
  "database_id": 123,
  "transcript": "full text ...",
  "extracted": {
    "summary": "short summary",
    "sentiment": "positive",
    "tags": ["..."],
    "topics": ["..."],
    "tasks": ["..."],
    "people": ["..."],
    "dates": ["..."],
    "action_items": ["..."]
  },
  "proposed_actions": [
    { "id": 1, "title": "...", "description": "...", "action_type": "task",
      "priority": "high", "status": "pending", "confidence": 0.8 }
  ],
  "action_count": 1
}
```

Android now shows transcript + summary after upload. To match the website
fully, the app should also surface `extracted.tags/tasks/people` and
`proposed_actions`.

### Related read endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/memories?limit&offset` | list memories |
| GET | `/api/memories/{id}` | one memory |
| DELETE | `/api/memories/{id}` | delete memory |
| POST | `/api/search?query&threshold` | semantic search |
| GET | `/api/dashboard/summary` | metrics, tags, sentiment |
| GET | `/api/dashboard/daily-briefing` | today: memories, actions, calendar, important mail |

`/api/dashboard/daily-briefing` is the best single source for a mobile
"Today" screen — it already merges memories + calendar + important emails.

---

## 6. AI chat (Neural Core)

### Endpoint
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/chat` | `{ "question": "..." }` | `{ "answer": "...", "sources": [ ... ] }` |

### Server behaviour
1. Enrich the question with keywords.
2. Semantic search memories (threshold ~0.3).
3. Build grounding context from top 5 memories.
4. Call LLM (Poolside primary, OpenAI fallback).
5. Fallback to top matching memory if no LLM / no answer.

This is exactly what the website's chat page uses (`api.chat(question)`).

Android currently has **no chat screen** — this is the missing parity item.

---

## 7. Real-time events (ESP32 pipeline)

| Protocol | Path | Purpose |
|---|---|---|
| WSS | `/events` | Server pushes transcript JSON as the ESP32 audio is processed |
| WS  | `/audio` | Only if the app itself acts as the audio device (ESP32 does this today) |

The Android app connects to `wss://<host>/events` on launch and shows live
transcripts in the **Live** tab.

---

## 8. Android ↔ server mapping (current)

| Android feature | Server endpoint |
|---|---|
| Google connect | `/auth/google?...&mobile=1` (Custom Tab) + `lifelog://oauth` deep link |
| Google status | `/auth/google/status` |
| Disconnect | `/auth/google/disconnect` |
| Upcoming events | `/api/google/events` |
| Important emails | `/api/google/messages/important` |
| Upload audio | `/api/upload` |
| Memories | `/api/memories` |
| Search | `/api/search` |
| Live transcript | `wss://<host>/events` |

---

## 9. Missing pieces to reach website parity

1. **AI chat screen in Android** → `POST /api/chat` (highest priority).
2. **Daily briefing / Today screen** → `GET /api/dashboard/daily-briefing`.
3. **Proposed actions UI** → `/api/actions*` endpoints (approve/reject/complete).
4. **Create calendar event from app** → `POST /api/google/events`.
5. **Email search** → `/api/google/messages?query=` + `/api/google/index-emails`.
6. **Dashboard metrics** → `/api/dashboard/summary`.

---

## 10. Server readiness checklist

- [ ] `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` set.
- [ ] Google OAuth consent screen includes Calendar + Gmail readonly scopes and test users.
- [ ] `LIFELOG_...` backend env for LLM + Whisper configured.
- [ ] Vector DB writable and persisted.
- [ ] SQL DB migrated (memories, actions, google credentials, settings).
- [ ] `/events` WebSocket reachable at the deployed WSS URL.
- [ ] CORS allows the web frontend.
- [ ] HTTPS on Cloud Run (default).
