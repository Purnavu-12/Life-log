"""
Poolside AI Service for LifeLog
Handles transcription and extraction using Poolside Laguna models
with OpenAI fallback support

Uses the OpenAI SDK pointed at the Poolside inference API.
"""

import os
import asyncio
import json
import tempfile
import logging
from typing import Optional, Dict, Any

from openai import OpenAI

logger = logging.getLogger(__name__)


class PoolsideService:
    """Service for Poolside AI API operations"""

    def __init__(self):
        self.poolside_api_key = os.getenv("POOLSIDE_API_KEY")
        self.poolside_base_url = os.getenv("POOLSIDE_BASE_URL", "https://inference.poolside.ai/v1")

        # Poolside client (OpenAI SDK pointed at Poolside)
        self.poolside_client = None
        if self.poolside_api_key:
            self.poolside_client = OpenAI(
                api_key=self.poolside_api_key,
                base_url=self.poolside_base_url
            )

        # Fallback to OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

        logger.info(f"Poolside service initialized. Poolside API available: {bool(self.poolside_api_key)}")
        logger.info(f"OpenAI fallback available: {bool(self.openai_api_key)}")

    async def transcribe_audio(
        self,
        audio_content: bytes,
        model: str = "poolside/whisper-1",
        language: str = "en"
    ) -> str:
        """
        Transcribe audio using Poolside Whisper model
        Falls back to OpenAI Whisper if Poolside is not available

        Args:
            audio_content: Raw audio bytes
            model: Model to use (poolside/whisper-1 or whisper-1)
            language: Language for transcription

        Returns:
            Transcribed text
        """
        # Try Poolside Whisper via the OpenAI-compatible audio API first.
        if self.poolside_client:
            try:
                return await self._transcribe_with_poolside(audio_content, model, language)
            except Exception as e:
                logger.warning(f"Poolside transcription failed, falling back to OpenAI: {e}")

        if self.openai_client:
            return await self._transcribe_with_openai(audio_content, language)
        else:
            raise Exception("No audio transcription service available (Poolside and OpenAI not configured)")

    @staticmethod
    def _ext_for_audio(audio_content: bytes) -> str:
        """Detect audio container by magic bytes and return the correct file extension."""
        if audio_content.startswith(b"RIFF") and audio_content[8:12] == b"WAVE":
            return ".wav"
        if audio_content[:2] == b"\xff\xfb" or audio_content.startswith(b"ID3"):
            return ".mp3"
        if audio_content.startswith(b"OggS"):
            return ".ogg"
        if audio_content.startswith(b"fLaC"):
            return ".flac"
        if audio_content.startswith(b"\x00\x00\x00") and b"ftyp" in audio_content[:12]:
            return ".m4a"
        # Fallback (ffprobe/most Whisper APIs accept mp3)
        return ".mp3"

    async def _transcribe_with_poolside(
        self,
        audio_content: bytes,
        model: str = "poolside/whisper-1",
        language: str = "en"
    ) -> str:
        """Transcribe audio using Poolside via the OpenAI SDK"""
        # Create in-memory file with the CORRECT extension for the container, so the
        # multipart upload filetype matches the actual bytes (poolside's audio API
        # rejects a mismatched extension like naming WAV bytes as .mp3).
        import io
        audio_file_obj = io.BytesIO(audio_content)
        audio_file_obj.name = "audio" + self._ext_for_audio(audio_content)

        try:
            def _transcribe():
                audio_file_obj.seek(0)  # Rewind to beginning
                # Poolside exposes Whisper as "whisper-1" over its OpenAI-compatible API.
                poolside_model = "whisper-1" if model.startswith("poolside/") else model
                return self.poolside_client.audio.transcriptions.create(
                    model=poolside_model,
                    file=(audio_file_obj.name, audio_file_obj, f"audio/{audio_file_obj.name.rsplit('.',1)[1] or 'mpeg'}"),
                    language=language
                )

            response = await asyncio.to_thread(_transcribe)
            transcript = response.text
            logger.info(f"Poolside transcription successful: {len(transcript)} characters")
            return transcript

        except Exception as e:
            logger.error(f"Poolside transcription error: {str(e)}")
            # Retry once with the fallback model name
            if "whisper-1" not in str(e):
                try:
                    def _transcribe_fallback():
                        audio_file_obj.seek(0)
                        return self.poolside_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=(audio_file_obj.name, audio_file_obj, f"audio/{audio_file_obj.name.rsplit('.',1)[1] or 'mpeg'}"),
                            language=language
                        )

                    response = await asyncio.to_thread(_transcribe_fallback)
                    transcript = response.text
                    logger.info(f"Poolside fallback transcription successful: {len(transcript)} characters")
                    return transcript
                except Exception:
                    pass
            raise
        finally:
            try:
                audio_file_obj.close()
            except Exception:
                pass

    async def _transcribe_with_openai(self, audio_content: bytes, language: str = "en") -> str:
        """Transcribe audio using OpenAI Whisper API"""
        if not self.openai_client:
            raise Exception("OpenAI API key not configured")

        # Use BytesIO with the correct extension for the container.
        import io
        audio_file_obj = io.BytesIO(audio_content)
        audio_file_obj.name = "audio" + self._ext_for_audio(audio_content)

        try:
            def _transcribe():
                audio_file_obj.seek(0)
                return self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file_obj,
                    language=language
                )

            response = await asyncio.to_thread(_transcribe)
            transcript = response.text
            logger.info(f"OpenAI transcription successful: {len(transcript)} characters")
            return transcript

        finally:
            try:
                audio_file_obj.close()
            except Exception:
                pass

    async def extract_information(
        self,
        transcript: str,
        model: str = "poolside/laguna-s-2.1",
        extraction_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured information from transcript using Poolside Laguna model
        Falls back to OpenAI GPT-4 if Poolside is not available

        Args:
            transcript: Text to analyze
            model: Model to use (poolside/laguna-s-2.1 or gpt-4)
            extraction_prompt: Custom prompt for extraction

        Returns:
            Dictionary with extracted information
        """
        try:
            # Try Poolside first
            if self.poolside_client:
                return await self._extract_with_poolside(transcript, model, extraction_prompt)
            else:
                logger.warning("Poolside API key not configured, falling back to OpenAI")
                return await self._extract_with_openai(transcript, extraction_prompt)

        except Exception as e:
            logger.error(f"Poolside extraction failed: {str(e)}")
            if self.openai_client:
                logger.info("Falling back to OpenAI for extraction")
                return await self._extract_with_openai(transcript, extraction_prompt)
            else:
                logger.error("Both Poolside and OpenAI are unavailable")
                raise

    async def _extract_with_poolside(
        self,
        transcript: str,
        model: str = "poolside/laguna-s-2.1",
        extraction_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract information using Poolside via the OpenAI SDK (streaming)"""
        if extraction_prompt is None:
            extraction_prompt = self._get_default_extraction_prompt(transcript)

        messages = [
            {
                "role": "system",
                "content": "You are an expert at extracting structured information from text transcripts."
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ]

        def _extract():
            response = self.poolside_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
                stream=True,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}}
            )

            parts = []
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    parts.append(chunk.choices[0].delta.content)
            return "".join(parts)

        extracted_text = await asyncio.to_thread(_extract)
        return self._parse_extracted_data(extracted_text)

    async def _extract_with_openai(self, transcript: str, extraction_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Extract information using OpenAI API"""
        if not self.openai_client:
            raise Exception("OpenAI API key not configured")

        if extraction_prompt is None:
            extraction_prompt = self._get_default_extraction_prompt(transcript)

        messages = [
            {
                "role": "system",
                "content": "You are an expert at extracting structured information from text transcripts."
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ]

        def _extract():
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content

        try:
            extracted_text = await asyncio.to_thread(_extract)
            return self._parse_extracted_data(extracted_text)
        except Exception as e:
            logger.error(f"OpenAI extraction error: {str(e)}")
            raise

    def _get_default_extraction_prompt(self, transcript: str) -> str:
        """Get default extraction prompt"""
        return f"""Analyze the following transcript and extract structured information.
Return a JSON object with the following fields:
- summary: Brief summary of the content
- tasks: List of actionable tasks mentioned
- people: List of people mentioned
- dates: List of dates or time references mentioned
- topics: Main topics discussed
- tags: Relevant tags for categorization
- sentiment: Overall sentiment (positive, neutral, negative)
- action_items: Specific items that need action

Transcript:
{transcript}

Return only valid JSON."""

    def _parse_extracted_data(self, data: str) -> Dict[str, Any]:
        """Parse extracted data JSON"""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON response")
            return {
                "summary": data,
                "tasks": [],
                "people": [],
                "dates": [],
                "topics": [],
                "tags": [],
                "sentiment": "neutral",
                "action_items": []
            }

    async def generate_answer(
        self,
        question: str,
        context: str,
        model: str = "poolside/laguna-s-2.1"
    ) -> str:
        """
        Generate a grounded conversational answer using Poolside (OpenAI fallback).
        Returns an empty string if all providers are unavailable.
        """
        system_prompt = (
            "You are Neural Core, the AI assistant for LifeLog, a memory management app. "
            "Answer the user's question using ONLY the provided memory context. "
            "Be concise, accurate, and cite facts from the context. If the context does not "
            "contain enough information to answer, say so honestly instead of guessing."
        )
        user_prompt = f"""Relevant memories / context:
--- START CONTEXT ---
{context}
--- END CONTEXT ---

Question: {question}

Answer based only on the context above:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Try Poolside first
        if self.poolside_client:
            try:
                def _generate():
                    response = self.poolside_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=500,
                        stream=True,
                        extra_body={"chat_template_kwargs": {"enable_thinking": False}}
                    )
                    parts = []
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content is not None:
                            parts.append(chunk.choices[0].delta.content)
                    return "".join(parts).strip()
                return await asyncio.to_thread(_generate)
            except Exception as e:
                logger.error(f"Poolside chat generation failed: {str(e)}")
                # fall through to OpenAI

        # OpenAI fallback
        if self.openai_client:
            try:
                def _generate_openai():
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=messages,
                        temperature=0.3,
                        max_tokens=500,
                    )
                    return response.choices[0].message.content.strip()
                return await asyncio.to_thread(_generate_openai)
            except Exception as e:
                logger.error(f"OpenAI chat generation failed: {str(e)}")

        return ""

    async def health_check(self) -> Dict[str, Any]:
        """Check Poolside API health"""
        result = {
            "poolside_available": False,
            "openai_available": False,
            "poolside_error": None,
            "openai_error": None
        }

        # Check Poolside
        if self.poolside_client:
            try:
                def _list_models():
                    return self.poolside_client.models.list()
                await asyncio.to_thread(_list_models)
                result["poolside_available"] = True
            except Exception as e:
                result["poolside_error"] = str(e)
        else:
            result["poolside_error"] = "API key not configured"

        # Check OpenAI
        if self.openai_client:
            try:
                def _list_models():
                    return self.openai_client.models.list()
                await asyncio.to_thread(_list_models)
                result["openai_available"] = True
            except Exception as e:
                result["openai_error"] = str(e)
        else:
            result["openai_error"] = "API key not configured"

        return result


# Singleton instance
poolside_service = PoolsideService()
