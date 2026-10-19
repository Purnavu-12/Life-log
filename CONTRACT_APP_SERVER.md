# LifeLog — App & Website Contract (Server / ESP32 / Android / Web)

Authoritative reference for how the ESP32, the LifeLog server, the website and the
Android app fit together.

- **Live server used by the clients:** `https://pouch-lark-series.ngrok-free.dev`
- **WebSocket events:** `wss://pouch-lark-series.ngrok-free.dev/events`
- **ESP32 audio socket:** `ws://<server-lan-ip>:8000/audio` (the ESP32 talks to the
  server directly; the Android app never sends audio to `/audio`)
- **All REST responses are JSON.**

---

## Part 0 — Verified live behaviour

Checked against the running server on 2026-10-19:

| Endpoint | Method | Live response |
|---|---|---|
| `/health` | GET | `{"status":"OK"}` |
| `/status` | GET | `{"connected_clients":0,"connected_devices":1,"recording":true,"active_session":"uuid","queue_size":0}` |
| `/api/memories?limit=3` | GET | **bare array**: `[{"id":1,"vector_id":"uuid","transcript":"…","summary":"…","sentiment":"neutral","tags":[],"topics":[],"tasks":[],"people":[],"dates":[],"action_items":[],"created_at":1792416852.9}]` |
| `/api/search?query=…&threshold=0.3` | POST | `{"results":[]}` — result items are `{"text","metadata","similarity","id"}` |
| `/api/chat` | POST | `{"answer":"…","sources":[…]}` |
| `/api/dashboard/summary` | GET | `{"memories":1,"actions":0,"tags":[],"sentiment":{}}` |
| `/api/dashboard/daily-briefing` | GET | `{"memories":[…],"calendar":[…],"important_emails":[…],"actions":[…]}` (**flat**) |
| `/api/actions` | GET | `[]` (array of action objects) |
| `/auth/google/status` | GET | `{"connected":false,"email":null,"scopes":[]}` |
| `/api/google/messages/important` | GET | `{"messages":[…]}` |
| `/api/google/calendars` | GET | `{"calendars":[…]}` |
| `/events` | WS | pushes `transcript` JSON frames (verified live) |

> **Important:** the memories list is a **bare JSON array** (not `{"memories":[…]}`),
> memory items use **`transcript`** (not `content`), and `id` is a **number**.
> The Android client therefore parses these endpoints leniently and accepts both
> the array form and the wrapped form.

### Google OAuth scope encoding
Scopes are comma-separated in a single query parameter:
`/auth/google?scope=calendar,gmail&mobile=1`
(using `&scope=calendar&scope=gmail` only grants the last scope — do not do this)

`mobile=1` makes the server use `state=mobile` and complete the flow by
redirecting back into the app (`lifelog://oauth?google=connected&email=…`).
The Android app **also polls `/auth/google/status`** when it resumes, so the
connect flow works even if the redirect target differs.

---

## Part 1 — ESP32 firmware → server (`/audio`)

The server's `AudioWebSocket` (server/app/websocket_audio.py) expects binary frames.

### Binary frame layout (40-byte header + payload)

| Offset | Size | Field | Description |
|---|---|---|---|
| 0 | 4B | magic | Must be `LLV1` (ASCII) |
| 4 | 1B | version | Must be `1` |
| 5 | 1B | packet_type | see table below |
| 6 | 2B | reserved | Must be `0x0000` |
| 8 | 16B | device_id | UUID bytes, uniquely identifies the ESP32 |
| 24 | 4B | sequence | unsigned int, incrementing frame counter |
| 28 | 8B | timestamp | micros or `millis()` (unsigned long long) |
| 36 | 4B | payload_length | number of bytes after the header |
| 40 | N | payload | raw data, depends on `packet_type` |

### Packet types

| Type | Hex | Payload | Server behaviour |
|---|---|---|---|
| AUDIO | `0x01` | raw 16-bit PCM mono @16 kHz | appended to WAV recorder, queued for Whisper |
| HEARTBEAT | `0x02` | empty | keep-alive, no-op |
| DEVICE_INFO | `0x03` | empty | logged only |
| START_SESSION | `0x04` | empty | reserved, session state transition |
| END_SESSION | `0x05` | empty | tears down session, writes transcript, broadcasts `recording_finished` |
| ERROR | `0x06` | UTF-8 error string | server closes the socket |

### Firmware checklist (`firmware/src/main.cpp`)

1. `WifiManager::begin()` — connect to SSID/password from `Config.h`
2. `WebSocketClient::begin(SERVER_IP, SERVER_PORT, "/audio")`
3. `MicManager::read(chunk, CHUNK_SIZE)` — 2048 samples (4096 B) 16-bit PCM @16 kHz
4. `PacketBuilder::build(0x01, DEVICE_ID, seq++, millis(), chunk, size)`
5. `wsClient.sendBinary(pkt.data(), pkt.size())`
6. Heartbeat every 5 s → packet type `0x02`, empty payload

### `firmware/include/Config.h`

```c
#define WIFI_SSID "YOUR_SSID"
#define WIFI_PASSWORD "YOUR_PASSWORD"
#define SERVER_IP "192.168.1.1"      // must match the host running the server
#define SERVER_PORT 8000
#define WS_ENDPOINT "/audio"
#define SAMPLE_RATE 16000
#define CHANNELS 1
#define BIT_DEPTH 16
#define CHUNK_SIZE 2048              // 4096 bytes per frame
#define DEVICE_ID "00000000-0000-0000-0000-000000000001"  // valid UUID
```

---

## Part 2 — Server → clients (`/events`)

Every client connected to `wss://<host>/events` receives JSON frames:

```json
{"type":"device_connected","device_id":"uuid","device_name":"xiao-esp32s3-sense","firmware_version":"1.0.0","hardware_revision":"seeed-xiao-esp32s3-sense","protocol_version":1}
{"type":"recording_started","session_id":"uuid","device_id":"uuid","started_at_ms":1720000000000}
{"type":"transcript","session_id":"uuid","device_id":"uuid","sequence":42,"timestamp_ms":12345,"text":"hello world","is_final":true}
{"type":"recording_finished","session_id":"uuid","device_id":"uuid","duration_ms":30000}
```

The Android **Live** tab renders these by `type`:
`device_connected` / `recording_started` / `recording_finished` as status banners,
`transcript` as a chat-style transcript bubble.

---

## Part 3 — REST API (web + Android)

### Health & status
```
GET  /health   -> {"status":"OK"}
GET  /status   -> {"connected_clients":1,"connected_devices":1,"recording":true,"active_session":"uuid","queue_size":0}
```

### Google OAuth
```
GET  /auth/google?scope=calendar,gmail&mobile=1
     -> 307 to accounts.google.com/o/oauth2/v2/auth
        (mobile=1 -> state=mobile -> callback redirects to lifelog://oauth?google=connected&email=…)
GET  /auth/google/callback?code=…&state=mobile|web
     -> stores credentials in SQLite -> redirects to FRONTEND_URL?google=connected&email=…
GET  /auth/google/status      -> {"connected":true,"email":"user@example.com","scopes":["calendar","gmail"]}
POST /auth/google/disconnect  -> {"success":true}
POST /auth/google/connect     -> manual credential connect (access_token, refresh_token, email, scopes)
```
Google Cloud Console → Authorized redirect URI:
`https://pouch-lark-series.ngrok-free.dev/auth/google/callback`

### Upload audio (multipart → transcribe + extract + store)
```
POST /api/upload        (multipart/form-data, field name: file)
-> {
  "success": true,
  "memory_id": "uuid",
  "database_id": 1,
  "transcript": "what was spoken",
  "extracted": {
    "summary": "…", "sentiment": "positive|neutral|negative",
    "tags": [], "topics": [], "tasks": [], "people": [], "dates": [],
    "action_items": []
  },
  "proposed_actions": [{"id":1,"title":"…","description":"…","action_type":"task","priority":"medium","status":"pending","confidence":0.8}],
  "action_count": 1
}
```

### Chat (RAG over memories)
```
POST /api/chat     {"question":"What did I talk about yesterday?"}
-> {"answer":"LLM response grounded in your memories","sources":[{"text":"…","metadata":{…},"similarity":0.95,"id":"uuid"}]}
```

### Search (semantic)
```
POST /api/search?query=…&threshold=0.3
-> {"results":[{"text":"…","metadata":{…},"similarity":0.95,"id":"uuid"}]}
```

### Memories
```
GET    /api/memories?limit=20&offset=0
-> [{"id":1,"vector_id":"uuid","transcript":"…","summary":"…","sentiment":"neutral",
      "tags":[],"topics":[],"tasks":[],"people":[],"dates":[],"action_items":[],"created_at":…}]
GET    /api/memories/{mid} -> single memory object
DELETE /api/memories/{mid} -> {"success":true}
```

### Actions (TODO management)
```
GET  /api/actions -> [{"id":1,"memory_id":1,"title":"…","description":"…","action_type":"task","priority":"medium","status":"pending","confidence":0.8}]
POST /api/actions {"memory_id":1,"title":"…","description":"…","action_type":"task","priority":"high","status":"pending","confidence":0.8}
```

### Dashboard
```
GET /api/dashboard/summary
-> {"memories":5,"actions":3,"tags":[],"sentiment":{}}

GET /api/dashboard/daily-briefing
-> {"memories":[…],"calendar":[…],"important_emails":[…],"actions":[…]}
```

### Google Calendar
```
GET    /api/google/calendars -> {"calendars":[{"id":"primary","summary":"My Calendar"}]}
GET    /api/google/events?calendar_id=primary&time_min=…&time_max=…
->     {"events":[{"id":"evt1","summary":"Meeting","start":{…},"end":{…}}]}
POST   /api/google/events {"summary":"…","start":{…},"end":{…},"description":"…","location":"…","calendar_id":"primary"}
->     {"success":true,"event":{…}}
DELETE /api/google/events/{event_id}?calendar_id=primary -> {"success":true}
GET    /api/google/freebusy?time_min=…&time_max=… -> {"freebusy":{"calendars":{…}}}
```

### Gmail
```
GET  /api/google/messages?query=inbox&max_results=10 -> {"messages":[{"id":"msg1","snippet":"…","payload":{"headers":[…]}}]}
GET  /api/google/messages/important?max_results=10   -> {"messages":[…]}   (is:important is:unread)
GET  /api/google/messages/{message_id}               -> {"message":{…}}
GET  /api/google/profile -> {"profile":{"emailAddress":"…","messagesTotal":…,"threadsTotal":…}}
POST /api/google/index-emails?limit=20 -> {"emails":[…],"count":20}
```

### Privacy
```
POST /api/privacy/revoke-google -> {"success":true}
```

---

## Part 4 — Server environment variables (`.env`)

```
LIFELOG_ENV=production
GOOGLE_REDIRECT_URI=https://pouch-lark-series.ngrok-free.dev/auth/google/callback
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
FRONTEND_URL=https://pouch-lark-series.ngrok-free.dev
OPENROUTER_API_KEY=sk-or-v1-<your-key>
```

`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` live **only on
the server**. They must never be shipped inside the Android app.

---

## Part 5 — Android app contract

### Configuration
- Base URL is baked in at build time: `android/app/build.gradle.kts`
  → `buildConfigField("String", "API_BASE_URL", "\"https://pouch-lark-series.ngrok-free.dev/\"")`
- The app derives the events socket from it: `https://…` → `wss://…/events`
- A hidden developer panel (long-press the LifeLog card in Settings) lets you
  repoint the app at another server without rebuilding. End users never see it.

### Deep link
```
lifelog://oauth?google=connected&email=user@example.com
```
Registered in `AndroidManifest.xml`; handled in `MainActivity.handleDeepLink`.

### Android → server endpoint map

| App feature | Endpoint |
|---|---|
| Memories list | `GET /api/memories?limit&offset` (accepts bare array **or** `{memories:[]}`) |
| Delete memory | `DELETE /api/memories/{id}` |
| Search | `POST /api/search?query&threshold` |
| Chat | `POST /api/chat` `{question}` |
| Upload audio | `POST /api/upload` multipart `file` |
| Google connect | `GET /auth/google?scope=calendar,gmail&mobile=1` (Custom Tab) |
| Google status | `GET /auth/google/status` |
| Google disconnect | `POST /auth/google/disconnect` |
| Calendars | `GET /api/google/calendars` |
| Calendar events | `GET /api/google/events?calendar_id&time_min&time_max` |
| Important emails | `GET /api/google/messages/important?max_results` |
| Gmail profile | `GET /api/google/profile` |
| Daily briefing (Today tab) | `GET /api/dashboard/daily-briefing` |
| Dashboard metrics | `GET /api/dashboard/summary` |
| Actions | `GET /api/actions`, `POST /api/actions` |
| Live transcript | `wss://<host>/events` |
| Server status | `GET /status` |

### App screens
| Tab | Purpose |
|---|---|
| **Today** | daily briefing: memories, calendar, important emails, actions |
| **Memories** | memory cards, search, delete, capture FAB |
| **Chat** | Neural Core chat over memories |
| **Live** | ESP32 live transcript stream + server status |
| **Settings** | Google connect/disconnect, privacy, about, hidden dev panel |

### Robustness rules the app follows
- Lenient JSON: every list endpoint accepts both array and wrapped-object forms.
- `id` accepted as number or string; `transcript` and `content` treated as synonyms.
- Tag/task arrays accepted as JSON arrays **or** as their stringified form
  (the daily-briefing endpoint returns `"tags":"[]"`).
- Network failures surface a readable message, never a crash.
