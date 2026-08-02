# LifeLog: Poolside AI & Google OAuth Setup Guide

This guide provides step-by-step instructions for setting up Poolside AI models and Google OAuth (Calendar + Gmail) integration with LifeLog.

## 🎯 Overview

LifeLog now supports:
- **Primary AI Provider**: Poolside Laguna models (`poolside/laguna-s-2.1` for extraction, `poolside/whisper-1` for transcription)
- **Fallback AI Provider**: OpenAI models (GPT-4 for extraction, Whisper-1 for transcription)
- **Google Services**: Calendar and Gmail integration via OAuth 2.0

## 🔧 Part 1: Poolside AI Setup

### Step 1: Get Poolside API Key
1. Go to [Poolside AI Inference](https://inference.poolside.ai)
2. Sign up or log in to your account
3. Navigate to your account settings or API keys section
4. Generate a new API key
5. Copy the API key

### Step 2: Configure Environment Variables

Edit your `.env` file in the `backend` directory:

```bash
# Poolside AI Configuration (Primary)
POOLSIDE_API_KEY=your-poolside-api-key-here
POOLSIDE_BASE_URL=https://inference.poolside.ai/v1

# OpenAI Configuration (Fallback - optional)
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 3: Install Dependencies

The required dependencies are already in `requirements.txt`. Install them:

```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Test Poolside Integration

Start your backend server:

```bash
cd backend
python main.py
```

Then test the Poolside health endpoint:

```bash
# Test general health (includes Poolside status)
curl http://localhost:8000/health

# Test Poolside-specific health
curl http://localhost:8000/api/poolside/health
```

You should see output like:
```json
{
  "poolside_available": true,
  "openai_available": true,
  "poolside_error": null,
  "openai_error": null
}
```

## 🔧 Part 2: Google OAuth Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (e.g., "LifeLog-Integration")
3. Wait for the project to be created

### Step 2: Enable Required APIs
1. Navigate to **APIs & Services** > **Library**
2. Enable these APIs:
   - **Google Calendar API**
   - **Gmail API**
3. Search for each API and click **Enable**

### Step 3: Create OAuth 2.0 Credentials
1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Configure the OAuth consent screen if prompted:
   - Application type: **External** (for development) or **Internal** (for GSuite)
   - Application name: "LifeLog"
   - User support email: your email
   - Developer contact email: your email
   - Add scopes (optional at this stage)
4. Click **Save and Continue** through the consent screen setup
5. Back in **Credentials**, click **Create Credentials** > **OAuth client ID**
6. Select **Web application** as the application type
7. Add authorized redirect URIs:
   - `http://localhost:8000/auth/google/callback`
   - `http://localhost:3000/auth/google/callback` (if your frontend runs on 3000)
8. Click **Create**

### Step 4: Get Client Credentials
After creating the OAuth client:
1. Copy the **Client ID** and **Client Secret**
2. Add these to your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

### Step 5: Configure Frontend URL
Also in your `.env` file:

```bash
# Frontend Configuration
FRONTEND_URL=http://localhost:3000
```

### Step 6: Add Required Scopes to OAuth Consent Screen
1. Go back to **APIs & Services** > **OAuth consent screen**
2. Click **Edit App**
3. Navigate to **Scopes**
4. Add these scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
5. Click **Save and Continue**

### Step 7: Test Google OAuth Flow

Start your backend server:

```bash
cd backend
python main.py
```

#### Test Calendar Integration:

1. **Get authorization URL**:
```bash
# For Calendar only
curl "http://localhost:8000/auth/google?scope=calendar"

# For Gmail only  
curl "http://localhost:8000/auth/google?scope=gmail"

# For both (default)
curl "http://localhost:8000/auth/google"
```

2. **Visit the URL** in your browser - this will redirect you to Google's consent screen
3. **Login** with your Google account and **allow** the requested permissions
4. **Copy the authorization code** from the redirect URL (after `code=` parameter)
5. **Exchange code for token** (in development, you'll need to handle this in the frontend)

#### API Endpoints for Testing:

```bash
# Check Google connection status (requires authentication)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/auth/google/status

# List calendars
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/api/google/calendars

# List calendar events
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" "http://localhost:8000/api/google/events"

# List Gmail messages
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" "http://localhost:8000/api/google/messages"

# Get Gmail profile
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/api/google/profile
```

## 🔄 Part 3: Using Poolside + Google Together

### Upload Audio with Google Context

When you upload audio files, LifeLog will:
1. Use Poolside (or OpenAI fallback) to transcribe the audio
2. Use Poolside (or OpenAI fallback) to extract structured information
3. Store the results in your personal vector database

The extracted information can include:
- Tasks and action items that can be added to Google Calendar
- People and events mentioned that can be cross-referenced with your emails
- Topics and tags for better organization

## 🚀 Part 4: Production Deployment

### Environment Configuration
For production, update your environment variables:

```bash
# Production URLs
FRONTEND_URL=https://your-frontend-domain.com
GOOGLE_REDIRECT_URI=https://your-backend-domain.com/auth/google/callback

# Poolside (recommended for production)
POOLSIDE_API_KEY=your-production-poolside-key

# OpenAI (fallback)
OPENAI_API_KEY=your-production-openai-key
```

### Google OAuth for Production
1. In Google Cloud Console, add your production domain to **Authorized JavaScript origins**
2. Add your production callback URL to **Authorized redirect URIs**
3. Publish your OAuth consent screen (requires verification for external users)
4. For external users, you may need to submit your app for Google verification

### Security Considerations
- Never commit `.env` files to version control
- Use HTTPS in production
- Consider using a secrets manager for API keys
- Implement rate limiting (already configured in the API)

## 🐛 Troubleshooting

### Poolside Issues

**Issue**: `Poolside API error: 401 Unauthorized`
- **Solution**: Check your `POOLSIDE_API_KEY` is correct

**Issue**: `Poolside API error: 404 Not Found`
- **Solution**: Verify `POOLSIDE_BASE_URL` is set to `https://inference.poolside.ai/v1`

**Issue**: Poolside models not available
- **Solution**: Ensure your Poolside account has access to the required models

### Google OAuth Issues

**Issue**: `Google OAuth not configured`
- **Solution**: Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set

**Issue**: `redirect_uri_mismatch` error
- **Solution**: Ensure the redirect URI in your Google Cloud Console matches exactly with `GOOGLE_REDIRECT_URI`

**Issue**: `Error 403: Access Denied` after authentication
- **Solution**: Verify that the OAuth consent screen includes all required scopes

**Issue**: Token expiration
- **Solution**: The system automatically refreshes tokens. If refresh fails, reconnect your Google account

## 📋 API Reference

### Poolside AI Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/poolside/health` | Check Poolside service health |
| GET | `/health` | General health check (includes Poolside status) |

### Google OAuth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/google` | Redirect to Google OAuth consent |
| GET | `/auth/google/callback` | OAuth callback handler |
| POST | `/auth/google/connect` | Connect Google credentials |
| GET | `/auth/google/status` | Check connection status |
| POST | `/auth/google/disconnect` | Disconnect Google |

### Google Calendar Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/google/calendars` | List calendars |
| GET | `/api/google/events` | List events |
| POST | `/api/google/events` | Create event |
| DELETE | `/api/google/events/{event_id}` | Delete event |

### Google Gmail Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/google/messages` | List messages |
| GET | `/api/google/messages/{message_id}` | Get message |
| GET | `/api/google/profile` | Get Gmail profile |
| POST | `/api/google/index-emails` | Index emails for search |

## 🔄 Fallback Behavior

The system is designed with automatic fallback:

1. **Transcription**: Tries Poolside first → Falls back to OpenAI → Throws error if both fail
2. **Extraction**: Tries Poolside first → Falls back to OpenAI → Throws error if both fail
3. **Google OAuth**: Uses refresh tokens automatically when access tokens expire

## 📊 Model Comparison

### Transcription Models

| Model | Provider | Speed | Accuracy | Cost |
|-------|----------|-------|----------|------|
| `poolside/whisper-1` | Poolside | ⚡ Fast | ⭐⭐⭐⭐ | 💰 Low |
| `whisper-1` | OpenAI | ⚡⚡ Medium | ⭐⭐⭐⭐ | 💰💰 Medium |

### Extraction Models

| Model | Provider | Capabilities | Cost |
|-------|----------|--------------|------|
| `poolside/laguna-s-2.1` | Poolside | ⭐⭐⭐⭐ High | 💰 Low |
| `gpt-4` | OpenAI | ⭐⭐⭐⭐⭐ Very High | 💰💰💰 High |

**Recommendation**: Use Poolside for both transcription and extraction for optimal cost-performance ratio.

## 🎉 Success Checklist

- [ ] Poolside API key configured
- [ ] Google OAuth credentials configured
- [ ] Required Google APIs enabled
- [ ] Redirect URIs configured in Google Cloud Console
- [ ] Required scopes added to OAuth consent screen
- [ ] Backend server starts without errors
- [ ] Health check shows Poolside and Google as available
- [ ] Google OAuth flow completes successfully
- [ ] Audio upload and processing works
- [ ] Calendar and Gmail data accessible via API

## 📖 Additional Resources

- [Poolside AI Documentation](https://inference.poolside.ai)
- [Google Calendar API Docs](https://developers.google.com/calendar/api)
- [Gmail API Docs](https://developers.google.com/gmail/api)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)

---

**Support**: For issues, check the logs first and ensure all environment variables are correctly set. The system provides detailed error messages to help diagnose problems.