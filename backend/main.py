from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="LifeLog API",
    description="Backend service for LifeLog - AI-powered memory management",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (will be imported when needed)
from services.transcription import TranscriptionService
from services.extraction import ExtractionService
from services.search import SearchService

transcription_service = TranscriptionService()
extraction_service = ExtractionService()
search_service = SearchService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LifeLog API"}

@app.post("/api/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload audio file for processing
    - Transcribe using Whisper
    - Extract information using LLM
    - Store in vector database
    """
    try:
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        logger.info(f"Processing audio: {file.filename}")

        # Read file content
        contents = await file.read()

        # Step 1: Transcribe
        transcript = await transcription_service.transcribe(contents)
        logger.info(f"Transcribed audio: {len(transcript)} characters")

        # Step 2: Extract structured information
        extracted = await extraction_service.extract(transcript)
        logger.info(f"Extracted information: {extracted}")

        # Step 3: Store in vector database
        memory_id = await search_service.store_memory(
            content=transcript,
            extracted_data=extracted,
            filename=file.filename
        )
        logger.info(f"Stored memory: {memory_id}")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "memory_id": memory_id,
                "transcript": transcript,
                "extracted": extracted,
            }
        )
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_memories(query: str, threshold: float = 0.5):
    """
    Search memories using semantic search
    """
    try:
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        logger.info(f"Searching for: {query}")

        results = await search_service.search(query, threshold)
        logger.info(f"Found {len(results)} results")

        return JSONResponse(
            status_code=200,
            content={"results": results}
        )
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories")
async def get_memories(limit: int = 10, offset: int = 0):
    """
    Get list of memories
    """
    try:
        memories = await search_service.list_memories(limit, offset)
        return JSONResponse(
            status_code=200,
            content={"memories": memories}
        )
    except Exception as e:
        logger.error(f"Error fetching memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: str):
    """
    Delete a memory
    """
    try:
        await search_service.delete_memory(memory_id)
        return JSONResponse(
            status_code=200,
            content={"success": True}
        )
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
