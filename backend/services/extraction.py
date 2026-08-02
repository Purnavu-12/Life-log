import asyncio
import os
import json
from typing import Dict, List, Any
import openai
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ExtractionService:
    """Service for extracting structured information from transcripts"""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def extract(self, transcript: str) -> Dict[str, Any]:
        """
        Extract structured information from transcript
        
        Args:
            transcript: Text transcript to analyze
            
        Returns:
            Dictionary with extracted information
        """
        try:
            prompt = f"""Analyze the following transcript and extract structured information.
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

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured information from text transcripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )

            # Parse response
            extracted_text = response.choices[0].message.content
            
            # Try to extract JSON
            try:
                extracted_data = json.loads(extracted_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured format
                extracted_data = {
                    "summary": extracted_text,
                    "tasks": [],
                    "people": [],
                    "dates": [],
                    "topics": [],
                    "tags": [],
                    "sentiment": "neutral",
                    "action_items": []
                }

            logger.info(f"Extraction successful: {extracted_data}")
            return extracted_data

        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            raise

    def _parse_extracted_data(self, data: str) -> Dict[str, Any]:
        """
        Parse extracted data JSON
        """
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
