# src/utils/singleton.py - Singleton metaclass for global managers

class Singleton(type):
    """Metaclass that creates a Singleton instance"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def get_instance(cls):
        if cls in cls._instances:
            return cls._instances[cls]
        raise ValueError(f"{cls.__name__} instance has not been created yet.")

# src/utils/timer.py - Timer utilities for educational features

import time

class Timer:
    """Simple timer for tracking elapsed time"""
    
    def __init__(self):
        self.start_time = time.time()
        self.paused_time = 0
        self.is_paused = False
        self.pause_start = None
    
    def reset(self):
        """Reset the timer"""
        self.start_time = time.time()
        self.paused_time = 0
        self.is_paused = False
        self.pause_start = None
    
    def pause(self):
        """Pause the timer"""
        if not self.is_paused:
            self.is_paused = True
            self.pause_start = time.time()
    
    def resume(self):
        """Resume the timer"""
        if self.is_paused and self.pause_start:
            self.paused_time += time.time() - self.pause_start
            self.is_paused = False
            self.pause_start = None
    
    def get_elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.is_paused and self.pause_start:
            return self.pause_start - self.start_time - self.paused_time
        else:
            return time.time() - self.start_time - self.paused_time
    
    def get_elapsed_string(self) -> str:
        """Get elapsed time as a formatted string"""
        elapsed = int(self.get_elapsed())
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes:02d}:{seconds:02d}"


# src/utils/math_helpers.py - Mathematical helper functions

import math
from typing import Tuple

def distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Calculate distance between two points"""
    return math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)

def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation between two values"""
    return start + (end - start) * t

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max"""
    return max(min_val, min(value, max_val))

def ease_in_out(t: float) -> float:
    """Ease in-out interpolation curve"""
    if t < 0.5:
        return 2 * t * t
    else:
        return 1 - pow(-2 * t + 2, 2) / 2

def point_in_rect(point: Tuple[float, float], rect) -> bool:
    """Check if a point is inside a rectangle"""
    return (rect.left <= point[0] <= rect.right and 
            rect.top <= point[1] <= rect.bottom)