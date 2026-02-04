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