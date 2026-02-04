# src/education/progress_tracker.py - Student progress tracking system

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

class StudentProfile:
    """Represents a student's profile and progress"""
    
    def __init__(self, student_id: str, name: str, age: int):
        self.student_id = student_id
        self.name = name
        self.age = age
        self.created_date = datetime.now().isoformat()
        
        # Progress data
        self.modules_progress = {
            'identify_pieces': ModuleProgress(),
            'board_setup': ModuleProgress(),
            'pawn_movement': ModuleProgress(),
            'rook_movement': ModuleProgress(),
            'knight_movement': ModuleProgress(),
            'bishop_movement': ModuleProgress(),
            'queen_movement': ModuleProgress(),
            'king_movement': ModuleProgress(),
            'mini_match': ModuleProgress(),
            'capture_game': ModuleProgress()
        }
        
        # Overall statistics
        self.total_playtime = 0  # seconds
        self.total_sessions = 0
        self.achievements = []
        self.favorite_modules = []
        self.current_skill_level = 'beginner'
        
        # Learning preferences
        self.preferences = {
            'hint_frequency': 'normal',  # low, normal, high
            'session_length': 15,  # minutes
            'difficulty_mode': 'adaptive',  # adaptive, manual
            'audio_enabled': True,
            'celebration_effects': True
        }

class ModuleProgress:
    """Track progress for individual modules"""
    
    def __init__(self):
        self.completed = False
        self.stars_earned = 0  # 0-3 stars
        self.best_score = 0
        self.total_attempts = 0
        self.correct_answers = 0
        self.time_spent = 0  # seconds
        self.last_played = None
        self.mastery_level = 0  # 0-100
        self.sessions = []
        
    def add_session(self, session_data: dict):
        """Add a session record"""
        session = {
            'date': datetime.now().isoformat(),
            'duration': session_data.get('duration', 0),
            'score': session_data.get('score', 0),
            'accuracy': session_data.get('accuracy', 0),
            'attempts': session_data.get('attempts', 0),
            'hints_used': session_data.get('hints_used', 0),
            'difficulty_level': session_data.get('difficulty_level', 1)
        }
        
        self.sessions.append(session)
        self.update_statistics(session_data)
    
    def update_statistics(self, session_data: dict):
        """Update module statistics based on session"""
        self.total_attempts += session_data.get('attempts', 0)
        self.correct_answers += session_data.get('correct', 0)
        self.time_spent += session_data.get('duration', 0)
        self.last_played = datetime.now().isoformat()
        
        # Update best score
        score = session_data.get('score', 0)
        if score > self.best_score:
            self.best_score = score
        
        # Calculate mastery level
        if self.total_attempts > 0:
            accuracy = self.correct_answers / self.total_attempts
            self.mastery_level = min(100, int(accuracy * 100))
        
        # Award stars based on performance
        if session_data.get('accuracy', 0) >= 0.9:
            self.stars_earned = max(self.stars_earned, 3)
        elif session_data.get('accuracy', 0) >= 0.8:
            self.stars_earned = max(self.stars_earned, 2)
        elif session_data.get('accuracy', 0) >= 0.7:
            self.stars_earned = max(self.stars_earned, 1)
        
        # Mark as completed if mastery achieved
        if self.mastery_level >= 80:
            self.completed = True

class ProgressTracker:
    """Main progress tracking system"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir / "profiles"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_profile: Optional[StudentProfile] = None
        self.profiles_cache: Dict[str, StudentProfile] = {}
        
        # Achievement definitions
        self.achievements = {
            'first_correct': {
                'name': 'First Step',
                'description': 'Answer your first question correctly',
                'icon': 'star'
            },
            'perfect_session': {
                'name': 'Perfect Score',
                'description': 'Complete a session with 100% accuracy',
                'icon': 'trophy'
            },
            'piece_master': {
                'name': 'Piece Master',
                'description': 'Master all piece identification',
                'icon': 'crown'
            },
            'quick_learner': {
                'name': 'Quick Learner',
                'description': 'Complete a module in under 5 minutes',
                'icon': 'lightning'
            },
            'persistent': {
                'name': 'Never Give Up',
                'description': 'Try 10 times to get the right answer',
                'icon': 'shield'
            },
            'streak_3': {
                'name': 'On Fire',
                'description': 'Get 3 correct answers in a row',
                'icon': 'fire'
            },
            'all_pieces': {
                'name': 'Know Them All',
                'description': 'Correctly identify all 6 piece types',
                'icon': 'collection'
            }
        }
    
    def create_profile(self, name: str, age: int) -> str:
        """Create a new student profile"""
        # Generate unique ID
        student_id = self._generate_student_id(name)
        
        # Create profile
        profile = StudentProfile(student_id, name, age)
        
        # Save profile
        self.save_profile(profile)
        
        # Set as current
        self.current_profile = profile
        self.profiles_cache[student_id] = profile
        
        return student_id
    
    def load_profile(self, student_id: str) -> Optional[StudentProfile]:
        """Load a student profile"""
        # Check cache first
        if student_id in self.profiles_cache:
            self.current_profile = self.profiles_cache[student_id]
            return self.current_profile
        
        # Load from file
        profile_path = self.data_dir / f"{student_id}.json"
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r') as f:
                data = json.load(f)
            
            # Reconstruct profile
            profile = StudentProfile(
                data['student_id'],
                data['name'],
                data['age']
            )
            
            # Load all data
            profile.__dict__.update(data)
            
            # Cache and set as current
            self.profiles_cache[student_id] = profile
            self.current_profile = profile
            
            return profile
            
        except Exception as e:
            print(f"Error loading profile {student_id}: {e}")
            return None
    
    def save_profile(self, profile: Optional[StudentProfile] = None):
        """Save a student profile"""
        if profile is None:
            profile = self.current_profile
        
        if profile is None:
            return
        
        profile_path = self.data_dir / f"{profile.student_id}.json"
        
        try:
            # Convert profile to dict
            data = self._profile_to_dict(profile)
            
            # Save to file
            with open(profile_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving profile: {e}")
    
    def get_all_profiles(self) -> List[Dict[str, str]]:
        """Get list of all profiles"""
        profiles = []
        
        for profile_file in self.data_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                
                profiles.append({
                    'student_id': data['student_id'],
                    'name': data['name'],
                    'age': data['age'],
                    'last_played': data.get('last_played', 'Never'),
                    'skill_level': data.get('current_skill_level', 'beginner')
                })
            except:
                continue
        
        return profiles
    
    def record_module_session(self, module_name: str, session_data: dict):
        """Record a module session"""
        if self.current_profile is None:
            return
        
        # Update module progress
        if module_name in self.current_profile.modules_progress:
            module = self.current_profile.modules_progress[module_name]
            module.add_session(session_data)
        
        # Update overall stats
        self.current_profile.total_sessions += 1
        self.current_profile.total_playtime += session_data.get('duration', 0)
        
        # Check for achievements
        self._check_achievements(module_name, session_data)
        
        # Update favorite modules
        self._update_favorites()
        
        # Save profile
        self.save_profile()
    
    def _check_achievements(self, module_name: str, session_data: dict):
        """Check if any achievements were earned"""
        profile = self.current_profile
        
        # First correct answer
        if ('first_correct' not in profile.achievements and 
            session_data.get('correct', 0) > 0):
            self._award_achievement('first_correct')
        
        # Perfect session
        if ('perfect_session' not in profile.achievements and
            session_data.get('accuracy', 0) == 1.0):
            self._award_achievement('perfect_session')
        
        # Quick learner
        if ('quick_learner' not in profile.achievements and
            session_data.get('duration', 0) < 300):  # Under 5 minutes
            self._award_achievement('quick_learner')
        
        # Persistent
        if ('persistent' not in profile.achievements and
            session_data.get('attempts', 0) >= 10):
            self._award_achievement('persistent')
        
        # Streak
        if ('streak_3' not in profile.achievements and
            session_data.get('streak', 0) >= 3):
            self._award_achievement('streak_3')
        
        # All pieces identified
        if module_name == 'identify_pieces':
            pieces_identified = session_data.get('pieces_identified', [])
            all_pieces = ['pawn', 'rook', 'knight', 'bishop', 'queen', 'king']
            
            if all(piece in pieces_identified for piece in all_pieces):
                self._award_achievement('all_pieces')
    
    def _award_achievement(self, achievement_id: str):
        """Award an achievement to the current student"""
        if self.current_profile and achievement_id not in self.current_profile.achievements:
            self.current_profile.achievements.append({
                'id': achievement_id,
                'earned_date': datetime.now().isoformat(),
                **self.achievements[achievement_id]
            })
            
            # Emit achievement event
            from src.core.event_manager import EventManager, EventType
            event_manager = EventManager()
            event_manager.emit_achievement(
                self.achievements[achievement_id]['name'],
                self.achievements[achievement_id]
            )
    
    def _update_favorites(self):
        """Update favorite modules based on play frequency"""
        if not self.current_profile:
            return
        
        # Calculate play counts
        play_counts = {}
        
        for module_name, progress in self.current_profile.modules_progress.items():
            if len(progress.sessions) > 0:
                play_counts[module_name] = len(progress.sessions)
        
        # Get top 3 most played
        favorites = sorted(play_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        self.current_profile.favorite_modules = [module for module, _ in favorites]
    
    def get_module_progress(self, module_name: str) -> Optional[ModuleProgress]:
        """Get progress for a specific module"""
        if self.current_profile and module_name in self.current_profile.modules_progress:
            return self.current_profile.modules_progress[module_name]
        return None
    
    def get_overall_progress(self) -> dict:
        """Get overall progress statistics"""
        if not self.current_profile:
            return {}
        
        total_modules = len(self.current_profile.modules_progress)
        completed_modules = sum(1 for m in self.current_profile.modules_progress.values() 
                              if m.completed)
        
        total_stars = sum(m.stars_earned for m in self.current_profile.modules_progress.values())
        max_stars = total_modules * 3
        
        return {
            'modules_completed': completed_modules,
            'total_modules': total_modules,
            'completion_percentage': (completed_modules / total_modules) * 100,
            'total_stars': total_stars,
            'max_stars': max_stars,
            'total_playtime': self.current_profile.total_playtime,
            'total_sessions': self.current_profile.total_sessions,
            'achievements_earned': len(self.current_profile.achievements),
            'current_skill_level': self.current_profile.current_skill_level
        }
    
    def _generate_student_id(self, name: str) -> str:
        """Generate a unique student ID"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{name}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    def _profile_to_dict(self, profile: StudentProfile) -> dict:
        """Convert profile to dictionary for saving"""
        data = profile.__dict__.copy()
        
        # Convert module progress objects
        modules_data = {}
        for name, progress in profile.modules_progress.items():
            modules_data[name] = progress.__dict__
        
        data['modules_progress'] = modules_data
        
        return data