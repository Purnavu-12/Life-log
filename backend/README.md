# LifeLog Backend API

FastAPI backend service for LifeLog - AI-powered memory and life management system.

## Features

- **Audio Transcription**: Convert audio to text using OpenAI Whisper API
- **Information Extraction**: Extract tasks, dates, people, and topics from transcripts using GPT-4
- **Semantic Search**: Vector-based search using ChromaDB for finding relevant memories
- **Memory Management**: Store, retrieve, update, and delete memories
- **Integration Ready**: Designed for Google Calendar and Gmail integration

## Setup

### Prerequisites

- Python 3.8+
- pip or conda
- OpenAI API key (for Whisper and GPT-4)

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Running the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs` (Swagger UI)

## API Endpoints

### Health Check
- `GET /health` - Check API health status

### Memory Management
- `POST /api/upload` - Upload audio file for processing
  - Transcribes audio
  - Extracts structured information
  - Stores in vector database
  - Returns memory ID and extracted data

- `GET /api/memories` - List all memories with pagination
  - Query params: `limit` (default: 10), `offset` (default: 0)

- `DELETE /api/memories/{memory_id}` - Delete a memory

### Search
- `POST /api/search` - Semantic search for memories
  - Body: `{ "query": "search term", "threshold": 0.5 }`
  - Returns: List of matching memories with similarity scores

## Services

### TranscriptionService
Handles audio transcription using OpenAI Whisper API.
- Supports multiple audio formats
- Converts audio bytes to text

### ExtractionService
Extracts structured information from transcripts using GPT-4.
- Identifies tasks, dates, people
- Extracts main topics and tags
- Analyzes sentiment
- Returns structured JSON

### SearchService
Manages vector storage and semantic search using ChromaDB.
- Stores memories with embeddings
- Performs similarity searches
- Handles memory CRUD operations
- Supports metadata filtering

## Architecture

```
backend/
├── main.py                 # FastAPI app and routes
├── services/              # Core services
│   ├── transcription.py   # Audio to text
│   ├── extraction.py      # Information extraction
│   └── search.py          # Vector search
├── data/                  # ChromaDB storage (created at runtime)
├── requirements.txt       # Python dependencies
└── .env.example          # Configuration template
```

## Configuration

Key environment variables:

- `OPENAI_API_KEY` - Required for Whisper and GPT-4 APIs
- `CHROMADB_PATH` - Where to store vector database (default: ./data/chromadb)
- `FRONTEND_URL` - Frontend URL for CORS (default: http://localhost:3000)

## Performance Notes

- First transcription request may take longer as it downloads the Whisper model
- ChromaDB uses local persistent storage by default
- Consider implementing caching for frequently accessed memories
- Large audio files should be chunked for optimal processing

## Future Enhancements

- [ ] Google Calendar integration
- [ ] Gmail integration
- [ ] MCP server implementation
- [ ] Poolside Laguna integration
- [ ] Advanced query parsing
- [ ] Multi-language support
- [ ] Real-time transcription streaming
- [ ] User authentication
- [ ] Database migration system

## Development

For local development with hot reload:

```bash
pip install uvicorn[standard]
uvicorn main:app --reload
```

## Troubleshooting

### OpenAI API Errors
- Verify your API key in `.env`
- Check your OpenAI account quota and billing

### ChromaDB Errors
- Ensure write permissions to the data directory
- Check disk space availability
- Try clearing the data directory if corrupted

### Port Already in Use
- Change PORT in .env or use: `python main.py --port 8001`

## License

MIT
