import asyncio
import os
import tempfile
from typing import Optional
import openai
import logging

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for audio transcription using OpenAI Whisper API"""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def transcribe(self, audio_content: bytes) -> str:
        """
        Transcribe audio content using Whisper API
        
        Args:
            audio_content: Raw audio bytes
            
        Returns:
            Transcribed text
        """
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_content)
                tmp_path = tmp_file.name

            try:
                # Call Whisper API
                with open(tmp_path, "rb") as audio_file:
                    response = await asyncio.to_thread(
                        self.client.audio.transcriptions.create,
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )

                transcript = response.text
                logger.info(f"Transcription successful: {len(transcript)} characters")
                return transcript

            finally:
                # Clean up temporary file
                os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise

    async def transcribe_from_file(self, file_path: str) -> str:
        """
        Transcribe audio from file path
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            with open(file_path, "rb") as audio_file:
                response = await asyncio.to_thread(
                    self.client.audio.transcriptions.create,
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )

            return response.text

        except Exception as e:
            logger.error(f"File transcription error: {str(e)}")
            raise
