import asyncio
import os
import subprocess
import tempfile
from typing import Optional
import logging

from .poolside import poolside_service

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for audio transcription using local whisper.cpp CLI STT with API fallback"""

    def __init__(self, user_id: Optional[str] = None):
        self.poolside_service = poolside_service
        self.user_id = user_id
        self.whisper_exe = os.getenv("SPECTRE_WHISPER_EXE")
        self.whisper_model = os.getenv("SPECTRE_WHISPER_MODEL", "base")

    def _resolve_model_path(self) -> Optional[str]:
        """Resolve the whisper.cpp model file path from the exe location and model name"""
        if not self.whisper_exe:
            return None
        model_dir = os.path.dirname(self.whisper_exe)
        candidates = [
            f"ggml-{self.whisper_model}.en.bin",
            f"ggml-{self.whisper_model}.bin",
        ]
        for name in candidates:
            path = os.path.join(model_dir, name)
            if os.path.isfile(path):
                return path
        return None

    def _get_ffmpeg_path(self) -> Optional[str]:
        """Find available ffmpeg binary"""
        # Check common locations for ffmpeg
        possible_paths = [
            "C:/Users/ASUS/.cursor/extensions/kilocode.kilo-code-7.3.46-win32-x64/bin/ffmpeg.exe",
            "C:/Users/ASUS/AppData/Local/Cypress/Cache/13.17.0/Cypress/resources/app/node_modules/@ffmpeg-installer/win32-x64/ffmpeg.exe",
            "ffmpeg",  # In PATH
            "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
            "/usr/bin/ffmpeg",
        ]
        
        for path in possible_paths:
            if os.path.isfile(path):
                return path
        return None

    def _convert_m4a_to_wav(self, audio_content: bytes) -> bytes:
        """Convert M4A audio to WAV format using ffmpeg"""
        ffmpeg_path = self._get_ffmpeg_path()
        if not ffmpeg_path:
            raise Exception("ffmpeg not found, cannot convert M4A to WAV")
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as input_file:
                input_file.write(audio_content)
                input_path = input_file.name
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
                output_path = output_file.name
            
            try:
                result = subprocess.run(
                    [
                        ffmpeg_path,
                        "-i", input_path,
                        "-acodec", "pcm_s16le",
                        "-ar", "16000",
                        "-y",  # Overwrite without asking
                        output_path
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    logger.error(f"ffmpeg conversion failed: {result.stderr}")
                    raise Exception(f"ffmpeg conversion failed: {result.stderr[:200]}")
                
                with open(output_path, "rb") as f:
                    return f.read()
            finally:
                try:
                    os.unlink(input_path)
                    os.unlink(output_path)
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"M4A to WAV conversion failed: {str(e)}")
            raise Exception(f"M4A format conversion failed: {str(e)}")

    def _transcribe_with_local_whisper(self, audio_content: bytes, language: str = "en") -> str:
        """Transcribe audio using the local whisper.cpp CLI (Speech-to-Text)"""
        if not self.whisper_exe or not os.path.isfile(self.whisper_exe):
            raise Exception("Local whisper CLI not configured (SPECTRE_WHISPER_EXE)")

        model_path = self._resolve_model_path()
        if not model_path:
            raise Exception(f"Whisper model not found for '{self.whisper_model}'")

        # Detect file format and convert if needed
        is_wav = audio_content.startswith(b'RIFF') and audio_content[8:12] == b'WAVE'
        is_mp3 = audio_content.startswith(b'ID3') or (len(audio_content) > 2 and audio_content[:2] == b'\xff\xfb')
        is_ogg = audio_content.startswith(b'OggS')
        is_flac = audio_content.startswith(b'fLaC')
        is_m4a = audio_content.startswith(b'\x00\x00\x00\x18')  # MP4/M4A container
        
        # If not a supported format, try to convert
        if not (is_wav or is_mp3 or is_ogg or is_flac):
            if is_m4a:
                logger.info("Detected M4A format, converting to WAV for whisper.cpp")
                try:
                    audio_content = self._convert_m4a_to_wav(audio_content)
                except Exception as e:
                    logger.error(f"M4A conversion failed: {str(e)}")
                    raise Exception("M4A format requires ffmpeg for conversion")
            else:
                logger.warning(f"Unsupported audio format, attempting direct processing")
        
        # Use WAV extension for whisper.cpp (it supports MP3, WAV, OGG, FLAC)
        extension = ".wav" if is_wav else (".mp3" if is_mp3 else (".ogg" if is_ogg else ".flac"))
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            tmp_file.write(audio_content)
            audio_path = tmp_file.name

        with tempfile.TemporaryDirectory() as out_dir:
            output_base = os.path.join(out_dir, "out")
            try:
                result = subprocess.run(
                    [
                        self.whisper_exe,
                        "-m", model_path,
                        "-f", audio_path,
                        "-otxt",
                        "-of", output_base,
                        "-l", language,
                        "-np",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=600,
                )
                transcript = ""
                txt_path = output_base + ".txt"
                if os.path.isfile(txt_path):
                    with open(txt_path, "r", encoding="utf-8") as f:
                        transcript = f.read().strip()

                if result.returncode != 0 and not transcript:
                    logger.error(f"Whisper CLI stderr: {result.stderr}")
                    raise Exception(f"Whisper CLI failed with exit code {result.returncode}")
                
                if not transcript:
                    logger.warning("Whisper CLI returned empty transcript - file may be unsupported format or silent")
                    raise Exception("Whisper transcription returned empty result")

                return transcript
            finally:
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass

    async def transcribe(self, audio_content: bytes, model: str = "poolside/whisper-1") -> str:
        """
        Transcribe audio content using local whisper.cpp CLI STT (primary)
        Falls back to Poolside/OpenAI API if local whisper is unavailable

        Args:
            audio_content: Raw audio bytes
            model: Model to use for API fallback

        Returns:
            Transcribed text
        """
        try:
            logger.info("Attempting local Whisper transcription")
            transcript = await asyncio.to_thread(self._transcribe_with_local_whisper, audio_content)
            logger.info(f"Local Whisper transcription successful: {len(transcript)} characters")
            return transcript

        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {str(e)}")
            logger.warning("Falling back to Poolside/OpenAI API transcription")
            try:
                # For API fallback, try with a proper model name
                # Poolside uses "whisper-1" not "poolside/whisper-1"
                api_model = model.replace("poolside/", "")
                transcript = await self.poolside_service.transcribe_audio(
                    audio_content=audio_content,
                    model=api_model,
                    language="en"
                )
                logger.info(f"API transcription successful: {len(transcript)} characters")
                return transcript
            except Exception as e2:
                logger.error(f"API transcription also failed: {str(e2)}")
                # Don't re-raise, instead raise a combined error
                raise Exception(f"All transcription methods failed. Local: {str(e)}. API: {str(e2)}")

    async def transcribe_from_file(self, file_path: str, model: str = "poolside/whisper-1") -> str:
        """
        Transcribe audio from file path using local whisper.cpp CLI STT (primary)
        Falls back to Poolside/OpenAI API if local whisper is unavailable

        Args:
            file_path: Path to audio file
            model: Model to use for API fallback

        Returns:
            Transcribed text
        """
        try:
            with open(file_path, "rb") as audio_file:
                content = audio_file.read()
            return await self.transcribe(content, model=model)

        except Exception as e:
            logger.error(f"File transcription error: {str(e)}")
            raise