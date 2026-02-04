# src/core/event_manager.py - Global event handling system

import pygame
from typing import Callable, Dict, List
from enum import Enum, auto

class EventType(Enum):
    """Custom event types for the chess education system"""
    ACHIEVEMENT_EARNED = auto()
    LEVEL_COMPLETED = auto()
    HINT_REQUESTED = auto()
    BREAK_REMINDER = auto()
    PROFILE_CHANGED = auto()
    SETTINGS_CHANGED = auto()
    
class EventManager:
    """Manages global event handling and custom events"""
    
    def __init__(self):
        self.listeners: Dict[int, List[Callable]] = {}
        self.custom_listeners: Dict[EventType, List[Callable]] = {}
        
        # Register pygame user events for custom events
        self.custom_event_ids = {}
        for event_type in EventType:
            event_id = pygame.USEREVENT + event_type.value
            self.custom_event_ids[event_type] = event_id
    
    def add_listener(self, event_type: int, callback: Callable):
        """Add a listener for a pygame event type"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def add_custom_listener(self, event_type: EventType, callback: Callable):
        """Add a listener for a custom event type"""
        if event_type not in self.custom_listeners:
            self.custom_listeners[event_type] = []
        self.custom_listeners[event_type].append(callback)
    
    def remove_listener(self, event_type: int, callback: Callable):
        """Remove a listener for a pygame event type"""
        if event_type in self.listeners:
            self.listeners[event_type].remove(callback)
    
    def remove_custom_listener(self, event_type: EventType, callback: Callable):
        """Remove a listener for a custom event type"""
        if event_type in self.custom_listeners:
            self.custom_listeners[event_type].remove(callback)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle a pygame event"""
        # Handle standard pygame events
        if event.type in self.listeners:
            for callback in self.listeners[event.type]:
                callback(event)
        
        # Handle custom events
        for event_type, event_id in self.custom_event_ids.items():
            if event.type == event_id:
                if event_type in self.custom_listeners:
                    for callback in self.custom_listeners[event_type]:
                        callback(event)
    
    def emit_custom_event(self, event_type: EventType, data: dict = None):
        """Emit a custom event"""
        event_id = self.custom_event_ids[event_type]
        event = pygame.event.Event(event_id, data or {})
        pygame.event.post(event)
    
    def emit_achievement(self, achievement_name: str, achievement_data: dict):
        """Emit an achievement earned event"""
        self.emit_custom_event(EventType.ACHIEVEMENT_EARNED, {
            'name': achievement_name,
            'data': achievement_data
        })
    
    def emit_level_completed(self, level_name: str, score: int, stars: int):
        """Emit a level completed event"""
        self.emit_custom_event(EventType.LEVEL_COMPLETED, {
            'level': level_name,
            'score': score,
            'stars': stars
        })
    
    def emit_hint_requested(self, module: str, context: dict):
        """Emit a hint requested event"""
        self.emit_custom_event(EventType.HINT_REQUESTED, {
            'module': module,
            'context': context
        })
    
    def clear_all_listeners(self):
        """Clear all event listeners"""
        self.listeners.clear()
        self.custom_listeners.clear()