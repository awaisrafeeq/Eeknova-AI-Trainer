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