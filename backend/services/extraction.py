import asyncio
import os
import json
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .poolside import poolside_service
from models.action import ProposedActionCreate, ActionType, ActionPriority
from database import create_proposed_action

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting structured information from transcripts using Poolside Laguna AI (primary) with OpenAI fallback"""

    def __init__(self, user_id: Optional[str] = None):
        self.poolside_service = poolside_service
        self.user_id = user_id

    async def extract(self, transcript: str, model: str = "poolside/laguna-s-2.1") -> Dict[str, Any]:
        """
        Extract structured information from transcript using Poolside Laguna AI (primary) with OpenAI fallback

        Args:
            transcript: Text transcript to analyze
            model: Model to use (poolside/laguna-s-2.1 for Poolside, gpt-4 for OpenAI)

        Returns:
            Dictionary with extracted information
        """
        try:
            # Use Poolside service which handles fallback automatically
            extracted_data = await self.poolside_service.extract_information(
                transcript=transcript,
                model=model
            )

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

    async def generate_proposed_actions(
        self, 
        transcript: str, 
        extracted_data: Dict[str, Any],
        memory_id: str
    ) -> List[ProposedActionCreate]:
        """
        Generate proposed actions based on extracted data and transcript
        """
        actions = []
        
        # Extract action items that might need user approval
        action_items = extracted_data.get("action_items", [])
        tasks = extracted_data.get("tasks", [])
        people = extracted_data.get("people", [])
        dates = extracted_data.get("dates", [])
        topics = extracted_data.get("topics", [])
        
        # Generate actions for action_items
        for i, action_item in enumerate(action_items):
            action_type = self._determine_action_type(action_item, extracted_data)
            
            action = ProposedActionCreate(
                title=f"Action {i+1}: {action_item}",
                description=self._generate_action_description(action_item, extracted_data),
                action_type=action_type,
                priority=self._determine_priority(action_item, extracted_data),
                status="pending",
                confidence=0.8,  # Default confidence for AI-generated actions
                memory_id=memory_id,
                related_entities=self._extract_related_entities(action_item, people, topics, dates),
                recipients=people[:3] if action_type == ActionType.SEND_EMAIL else []  # Limit to 3 recipients
            )
            actions.append(action)
            
        # Generate actions for tasks that might need to be scheduled
        for i, task in enumerate(tasks):
            # Skip if already created as action_item
            if not any(task in str(item) for item in action_items):
                action = ProposedActionCreate(
                    title=f"Task: {task}",
                    description=f"Task extracted from conversation: {task}",
                    action_type=ActionType.CREATE_TASK,
                    priority=ActionPriority.MEDIUM,
                    status="pending",
                    confidence=0.7,
                    memory_id=memory_id,
                    related_entities=self._extract_related_entities(task, people, topics, dates),
                    recipients=[]
                )
                actions.append(action)
        
        # Generate calendar sync actions if dates are found
        if dates and self.user_id:
            calendar_action = ProposedActionCreate(
                title="Sync calendar events",
                description=f"Sync events for dates: {', '.join(dates[:3])}",
                action_type=ActionType.SYNC_CALENDAR,
                priority=ActionPriority.LOW,
                status="pending",
                confidence=0.6,
                memory_id=memory_id,
                related_entities=dates[:5],  # Limit to 5 dates
                recipients=[]
            )
            actions.append(calendar_action)
        
        return actions
    
    def _determine_action_type(self, action_item: str, extracted_data: Dict[str, Any]) -> ActionType:
        """Determine the type of action based on the action item text"""
        action_item_lower = action_item.lower()
        
        if any(word in action_item_lower for word in ["email", "send", "message", "contact", "write"]):
            return ActionType.SEND_EMAIL
        elif any(word in action_item_lower for word in ["event", "meeting", "appointment", "schedule", "calendar"]):
            return ActionType.CREATE_EVENT
        elif any(word in action_item_lower for word in ["remind", "reminder", "alert", "notify"]):
            return ActionType.SET_REMINDER
        elif any(word in action_item_lower for word in ["task", "todo", "do", "complete", "finish"]):
            return ActionType.CREATE_TASK
        else:
            return ActionType.ADD_NOTE
    
    def _determine_priority(self, action_item: str, extracted_data: Dict[str, Any]) -> ActionPriority:
        """Determine priority based on action item and context"""
        action_item_lower = action_item.lower()
        
        if any(word in action_item_lower for word in ["urgent", "immediate", "asap", "emergency"]):
            return ActionPriority.URGENT
        elif any(word in action_item_lower for word in ["important", "priority", "critical", "must"]):
            return ActionPriority.HIGH
        elif any(word in action_item_lower for word in ["soon", "today", "tomorrow", "week"]):
            return ActionPriority.MEDIUM
        else:
            return ActionPriority.LOW
    
    def _generate_action_description(self, action_item: str, extracted_data: Dict[str, Any]) -> str:
        """Generate a description for the proposed action"""
        summary = extracted_data.get("summary", "")
        people = extracted_data.get("people", [])
        dates = extracted_data.get("dates", [])
        
        description_parts = [f"Generated from conversation: {action_item}"]
        
        if people:
            description_parts.append(f"Involves: {', '.join(people[:3])}")
        if dates:
            description_parts.append(f"Related dates: {', '.join(dates[:3])}")
        if summary:
            description_parts.append(f"Context: {summary[:100]}...")
        
        return " | ".join(description_parts)
    
    def _extract_related_entities(
        self, 
        action_item: str, 
        people: List[str], 
        topics: List[str], 
        dates: List[str]
    ) -> List[str]:
        """Extract relevant entities related to an action"""
        entities = []
        
        # Add people mentioned in action item
        action_item_lower = action_item.lower()
        for person in people:
            if person.lower() in action_item_lower:
                entities.append(f"person:{person}")
        
        # Add dates mentioned in action item
        for date in dates:
            if date.lower() in action_item_lower:
                entities.append(f"date:{date}")
        
        # Add topics
        entities.extend([f"topic:{topic}" for topic in topics[:2]])
        
        # If no specific entities found, add general ones
        if not entities:
            entities = [f"person:{person}" for person in people[:2]] + [f"date:{date}" for date in dates[:2]]
        
        return entities[:5]  # Limit to 5 entities

    async def extract_and_create_actions(
        self, 
        transcript: str, 
        memory_id: str
    ) -> tuple[Dict[str, Any], List[ProposedActionCreate]]:
        """
        Extract information and generate proposed actions
        Returns both extracted data and generated actions
        """
        # Extract information first
        extracted_data = await self.extract(transcript)
        
        # Generate proposed actions
        actions = await self.generate_proposed_actions(
            transcript=transcript,
            extracted_data=extracted_data,
            memory_id=memory_id
        )
        
        return extracted_data, actions

    async def extract_and_save_actions(
        self, 
        transcript: str, 
        memory_id: str
    ) -> tuple[Dict[str, Any], List[ProposedActionCreate]]:
        """
        Extract information, generate proposed actions, and save them to database
        Returns extracted data and saved actions
        """
        if not self.user_id:
            raise ValueError("user_id is required for saving actions")
        
        # Extract and generate actions
        extracted_data, actions = await self.extract_and_create_actions(
            transcript=transcript,
            memory_id=memory_id
        )
        
        # Save actions to database
        saved_actions = []
        for action in actions:
            try:
                saved_action = create_proposed_action(action, self.user_id)
                saved_actions.append(saved_action)
                logger.info(f"Saved proposed action: {saved_action.id}")
            except Exception as e:
                logger.error(f"Error saving proposed action: {str(e)}")
        
        return extracted_data, saved_actions