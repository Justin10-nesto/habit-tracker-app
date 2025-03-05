"""Event System - Defines the core event system and event types for the habit tracker

Implements the Observer pattern for handling various habit-related events.
"""
from enum import Enum
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime

class EventTypes(Enum):
    """Enumeration of all possible event types in the system"""
    HABIT_COMPLETED = "habit_completed"
    STREAK_UPDATED = "streak_updated"
    HABIT_CREATED = "habit_created"
    HABIT_UPDATED = "habit_updated"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    MILESTONE_REACHED = "milestone_reached"

@dataclass
class Event:
    """Represents an event in the system"""
    type: EventTypes
    data: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class EventSystem:
    """Core event system that handles event dispatching and subscription"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the event system"""
        self._subscribers: Dict[EventTypes, List[Callable]] = {}
        for event_type in EventTypes:
            self._subscribers[event_type] = []
    
    def subscribe(self, event_type: EventTypes, callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type
        
        Args:
            event_type: The type of event to subscribe to
            callback: The function to call when the event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventTypes, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from an event type
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The function to remove from the subscribers
        """
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
    
    def dispatch(self, event: Event) -> None:
        """Dispatch an event to all subscribers
        
        Args:
            event: The event to dispatch
        """
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                callback(event)
    
    def dispatch_event(self, event_type: EventTypes, data: Dict[str, Any]) -> None:
        """Convenience method to dispatch an event with just type and data
        
        Args:
            event_type: The type of event to dispatch
            data: The data associated with the event
        """
        event = Event(type=event_type, data=data)
        self.dispatch(event)