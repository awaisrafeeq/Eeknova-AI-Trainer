# quick_fix.py - Quick fix to create missing module files

import os
from pathlib import Path

def create_missing_files():
    """Create any missing Python module files"""
    
    base_dir = Path(__file__).parent
    
    # Create missing __init__.py files
    init_files = [
        "src/__init__.py",
        "src/core/__init__.py", 
        "src/states/__init__.py",
        "src/ui/__init__.py",
        "src/utils/__init__.py",
        "src/education/__init__.py",
        "src/modules/__init__.py",
        "src/chess/__init__.py",
        "src/audio/__init__.py",
    ]
    
    for init_file in init_files:
        file_path = base_dir / init_file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_text('# Package init file\n')
            print(f"Created: {init_file}")
    
    # Fix the main src/__init__.py to avoid circular imports
    src_init = base_dir / "src/__init__.py"
    src_init.write_text('''# src/__init__.py
"""Chess Learning System - Educational chess game for children"""

__version__ = "1.0.0"
__author__ = "Chess Learning Team"

# Note: Do not import modules here to avoid circular imports
''')
    print("Fixed: src/__init__.py")
    
    # Ensure math_helpers.py exists
    math_helpers = base_dir / "src/utils/math_helpers.py"
    if not math_helpers.exists():
        math_helpers.write_text('''# src/utils/math_helpers.py - Mathematical helper functions

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
''')
        print("Created: src/utils/math_helpers.py")
    
    # Ensure singleton.py exists
    singleton = base_dir / "src/utils/singleton.py"
    if not singleton.exists():
        singleton.write_text('''# src/utils/singleton.py - Singleton metaclass for global managers

class Singleton(type):
    """Metaclass that creates a Singleton instance"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
''')
        print("Created: src/utils/singleton.py")
    
    # Ensure timer.py exists
    timer = base_dir / "src/utils/timer.py"
    if not timer.exists():
        timer.write_text('''# src/utils/timer.py - Timer utilities for educational features

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
''')
        print("Created: src/utils/timer.py")
    
    print("\nAll missing files created!")
    print("You can now run: python main.py")

if __name__ == "__main__":
    create_missing_files()