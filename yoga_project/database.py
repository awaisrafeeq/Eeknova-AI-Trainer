# database.py - SQLite Database Module with SQLAlchemy
# Replaces in-memory user storage with persistent SQLite database

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging
import re

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "sqlite:///./yoga_users.db"

# Create engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ===================== Models =====================

class User(Base):
    """User authentication model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class UserProfile(Base):
    """User profile model with fitness information"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100))
    full_name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    height = Column(Float, nullable=True)  # in cm
    weight = Column(Float, nullable=True)  # in kg
    fitness_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    preferences = Column(Text, default="{}")  # JSON string for flexible preferences
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class YogaStreak(Base):
    """Yoga streak tracking model"""
    __tablename__ = "yoga_streaks"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    current_streak = Column(Integer, default=0)  # Current consecutive days
    longest_streak = Column(Integer, default=0)  # Longest streak ever achieved
    last_practice_date = Column(DateTime, nullable=True)  # Last date user practiced yoga
    total_sessions = Column(Integer, default=0)  # Total yoga sessions completed
    total_minutes = Column(Integer, default=0)  # Total minutes of yoga practice
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class YogaSession(Base):
    """Individual yoga session records"""
    __tablename__ = "yoga_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    session_date = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Integer, nullable=False)
    pose_name = Column(String(100), nullable=False)
    average_accuracy = Column(Float, nullable=False)
    calories_burned = Column(Integer, default=0)
    corrections_given = Column(Integer, default=0)
    frames_processed = Column(Integer, default=0)
    completed = Column(Boolean, default=True)  # Whether session was completed successfully
    created_at = Column(DateTime, default=datetime.utcnow)


class YogaInstruction(Base):
    """Yoga pose instructions stored in DB"""
    __tablename__ = "yoga_instructions"

    id = Column(Integer, primary_key=True, index=True)
    pose_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    entry = Column(Text, default="[]")
    release = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChessProgress(Base):
    """Chess progress tracking model"""
    __tablename__ = "chess_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    module_id = Column(String(50), nullable=False)  # chess module ID
    completed_exercises = Column(Integer, default=0)
    total_exercises = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    best_accuracy = Column(Float, default=0.0)
    total_time_minutes = Column(Integer, default=0)
    last_played_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModuleProgress(Base):
    """General module progress tracking"""
    __tablename__ = "module_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    module_id = Column(String(50), nullable=False)
    progress_percentage = Column(Float, default=0.0)
    completed_lessons = Column(Integer, default=0)
    total_lessons = Column(Integer, default=0)
    last_accessed_date = Column(DateTime, nullable=True)
    completion_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ===================== Database Initialization =====================

def init_db():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def count_yoga_instructions() -> int:
    db = SessionLocal()
    try:
        return db.query(YogaInstruction).count()
    finally:
        db.close()


# ===================== User CRUD Operations =====================

def create_user(username: str, email: str, hashed_password: str) -> Optional[Dict[str, Any]]:
    """Create a new user and their profile"""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            logger.warning(f"User already exists: {username}")
            return None
        
        # Create user
        new_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        db.add(new_user)
        
        # Create default profile with AI settings
        default_preferences = {
            "angle_tolerance": 10.0,
            "confidence_threshold": 0.5,
            "mirror_mode": True
        }
        new_profile = UserProfile(
            username=username,
            email=email,
            fitness_level="beginner",
            preferences=json.dumps(default_preferences)
        )
        db.add(new_profile)
        
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Created new user: {username}")
        
        return {
            "username": new_user.username,
            "email": new_user.email,
            "hashed_password": new_user.hashed_password,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise
    finally:
        db.close()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        return {
            "username": user.username,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_active": user.is_active
        }
        
    finally:
        db.close()


def get_user_profile(username: str) -> Optional[Dict[str, Any]]:
    """Get user profile by username"""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.username == username).first()
        
        if not profile:
            return None
        
        # Parse preferences JSON
        try:
            preferences = json.loads(profile.preferences) if profile.preferences else {}
        except:
            preferences = {}
        
        return {
            "username": profile.username,
            "email": profile.email,
            "full_name": profile.full_name,
            "age": profile.age,
            "height": profile.height,
            "weight": profile.weight,
            "fitness_level": profile.fitness_level,
            "preferences": preferences
        }
        
    finally:
        db.close()


def update_user_profile(username: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user profile"""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.username == username).first()
        
        if not profile:
            logger.warning(f"Profile not found for user: {username}")
            return None
        
        # Update fields
        if "email" in profile_data:
            profile.email = profile_data["email"]
        if "full_name" in profile_data:
            profile.full_name = profile_data["full_name"]
        if "age" in profile_data:
            profile.age = profile_data["age"]
        if "height" in profile_data:
            profile.height = profile_data["height"]
        if "weight" in profile_data:
            profile.weight = profile_data["weight"]
        if "fitness_level" in profile_data:
            profile.fitness_level = profile_data["fitness_level"]
        if "preferences" in profile_data:
            profile.preferences = json.dumps(profile_data["preferences"])
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Updated profile for user: {username}")
        
        return get_user_profile(username)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile: {e}")
        raise
    finally:
        db.close()


def user_exists(username: str) -> bool:
    """Check if username already exists"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        return user is not None
    finally:
        db.close()


def email_exists(email: str) -> bool:
    """Check if email already exists"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        return user is not None
    finally:
        db.close()


# ===================== Yoga Streak Operations =====================

def _normalize_pose_id(name: str) -> str:
    cleaned = re.sub(r"\([^)]*\)", "", name or "")
    cleaned = cleaned.replace("–", "-").replace("—", "-").replace("-", " ")
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower().replace(" ", "_")


def _pose_id_aliases() -> Dict[str, str]:
    return {
        "cat_and_camel_pose": "cat_cow_pose",
        "child_pose": "childs_pose",
        "warrior_pose": "warrior_ii",
        "warrior_1": "warrior_i",
        "seated_forward": "seated_forward_bend",
        "triangle": "triangle_pose",
    }


def yoga_instruction_exists(pose_id: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(YogaInstruction).filter(YogaInstruction.pose_id == pose_id).first() is not None
    finally:
        db.close()


def resolve_pose_id_db(pose_name: str) -> Optional[str]:
    if not pose_name:
        return None
    candidate = _normalize_pose_id(pose_name)
    if yoga_instruction_exists(candidate):
        return candidate
    alias = _pose_id_aliases().get(candidate)
    if alias and yoga_instruction_exists(alias):
        return alias
    return None


def list_yoga_instructions() -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        records = db.query(YogaInstruction).order_by(YogaInstruction.name.asc()).all()
        return [
            {
                "pose_id": rec.pose_id,
                "name": rec.name,
                "entry": json.loads(rec.entry or "[]"),
                "release": json.loads(rec.release or "[]"),
            }
            for rec in records
        ]
    finally:
        db.close()


def get_yoga_instruction(pose_id: str) -> Optional[Dict[str, Any]]:
    db = SessionLocal()
    try:
        rec = db.query(YogaInstruction).filter(YogaInstruction.pose_id == pose_id).first()
        if not rec:
            return None
        return {
            "pose_id": rec.pose_id,
            "name": rec.name,
            "entry": json.loads(rec.entry or "[]"),
            "release": json.loads(rec.release or "[]"),
        }
    finally:
        db.close()


def upsert_yoga_instruction(pose_id: str, name: str, entry: List[str], release: List[str]) -> None:
    db = SessionLocal()
    try:
        rec = db.query(YogaInstruction).filter(YogaInstruction.pose_id == pose_id).first()
        if not rec:
            rec = YogaInstruction(pose_id=pose_id, name=name)
            db.add(rec)
        rec.name = name
        rec.entry = json.dumps(entry or [])
        rec.release = json.dumps(release or [])
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error upserting yoga instruction: {e}")
        raise
    finally:
        db.close()

def get_yoga_streak(username: str) -> Optional[Dict[str, Any]]:
    """Get yoga streak data for user"""
    db = SessionLocal()
    try:
        streak = db.query(YogaStreak).filter(YogaStreak.username == username).first()
        
        if not streak:
            # Create new streak record
            new_streak = YogaStreak(
                username=username,
                current_streak=0,
                longest_streak=0,
                total_sessions=0,
                total_minutes=0
            )
            db.add(new_streak)
            db.commit()
            db.refresh(new_streak)
            streak = new_streak
        
        return {
            "username": streak.username,
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "last_practice_date": streak.last_practice_date.isoformat() if streak.last_practice_date else None,
            "total_sessions": streak.total_sessions,
            "total_minutes": streak.total_minutes
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error getting yoga streak: {e}")
        return None
    finally:
        db.close()


def update_yoga_streak(username: str, session_duration_seconds: int, session_minutes: int) -> Optional[Dict[str, Any]]:
    """Update yoga streak after a completed session"""
    print(f"[DEBUG] update_yoga_streak called for {username}, duration={session_duration_seconds}s")
    db = SessionLocal()
    try:
        streak = db.query(YogaStreak).filter(YogaStreak.username == username).first()
        
        if not streak:
            # Create new streak record
            streak = YogaStreak(
                username=username,
                current_streak=0,
                longest_streak=0,
                total_sessions=0,
                total_minutes=0
            )
            db.add(streak)
        
        today = datetime.utcnow().date()
        yesterday = today.replace(day=today.day - 1) if today.day > 1 else today.replace(month=today.month - 1, day=31)
        
        # Check if streak should be updated
        if streak.last_practice_date:
            last_practice = streak.last_practice_date.date()
            
            if last_practice == today:
                # Already practiced today, no streak change
                pass
            elif last_practice == yesterday:
                # Consecutive day, increment streak
                streak.current_streak += 1
            else:
                # Missed days, reset streak
                streak.current_streak = 1
        else:
            # First practice
            streak.current_streak = 1
        
        # Update other stats
        streak.total_sessions += 1
        streak.total_minutes += session_minutes
        streak.last_practice_date = datetime.utcnow()
        
        # Update longest streak if needed
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        
        db.commit()
        db.refresh(streak)
        
        return get_yoga_streak(username)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating yoga streak: {e}")
        return None
    finally:
        db.close()


def create_yoga_session(username: str, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new yoga session record"""
    db = SessionLocal()
    try:
        session = YogaSession(
            username=username,
            duration_seconds=session_data.get("duration_seconds", 0),
            pose_name=session_data.get("pose_name", "Unknown"),
            average_accuracy=session_data.get("average_accuracy", 0.0),
            calories_burned=session_data.get("calories_burned", 0),
            corrections_given=session_data.get("corrections_given", 0),
            frames_processed=session_data.get("frames_processed", 0),
            completed=session_data.get("completed", True)
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Update streak if session was completed
        if session.completed:
            update_yoga_streak(username, session.duration_seconds, session.duration_seconds // 60)
        
        return {
            "id": session.id,
            "username": session.username,
            "session_date": session.session_date.isoformat(),
            "duration_seconds": session.duration_seconds,
            "pose_name": session.pose_name,
            "average_accuracy": session.average_accuracy,
            "calories_burned": session.calories_burned,
            "completed": session.completed
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating yoga session: {e}")
        return None
    finally:
        db.close()


# ===================== Chess Progress Operations =====================

def get_chess_progress(username: str, module_id: str = None) -> Optional[Dict[str, Any]]:
    """Get chess progress for user"""
    db = SessionLocal()
    try:
        if module_id:
            progress = db.query(ChessProgress).filter(
                ChessProgress.username == username,
                ChessProgress.module_id == module_id
            ).first()
        else:
            progress = db.query(ChessProgress).filter(ChessProgress.username == username).all()
            return [{
                "module_id": p.module_id,
                "completed_exercises": p.completed_exercises,
                "total_exercises": p.total_exercises,
                "correct_answers": p.correct_answers,
                "best_accuracy": p.best_accuracy,
                "total_time_minutes": p.total_time_minutes,
                "last_played_date": p.last_played_date.isoformat() if p.last_played_date else None
            } for p in progress]
        
        if not progress:
            return None
        
        return {
            "username": progress.username,
            "module_id": progress.module_id,
            "completed_exercises": progress.completed_exercises,
            "total_exercises": progress.total_exercises,
            "correct_answers": progress.correct_answers,
            "best_accuracy": progress.best_accuracy,
            "total_time_minutes": progress.total_time_minutes,
            "last_played_date": progress.last_played_date.isoformat() if progress.last_played_date else None
        }
        
    finally:
        db.close()


def update_chess_progress(username: str, module_id: str, progress_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update chess progress for user"""
    db = SessionLocal()
    try:
        progress = db.query(ChessProgress).filter(
            ChessProgress.username == username,
            ChessProgress.module_id == module_id
        ).first()
        
        if not progress:
            # Create new progress record
            progress = ChessProgress(
                username=username,
                module_id=module_id
            )
            db.add(progress)
        
        # Update fields
        if "completed_exercises" in progress_data:
            progress.completed_exercises = progress_data["completed_exercises"]
        if "total_exercises" in progress_data:
            progress.total_exercises = progress_data["total_exercises"]
        if "correct_answers" in progress_data:
            progress.correct_answers = progress_data["correct_answers"]
        if "best_accuracy" in progress_data:
            progress.best_accuracy = max(progress.best_accuracy, progress_data["best_accuracy"])
        if "total_time_minutes" in progress_data:
            progress.total_time_minutes += progress_data["total_time_minutes"]
        
        progress.last_played_date = datetime.utcnow()
        
        db.commit()
        db.refresh(progress)
        
        return get_chess_progress(username, module_id)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating chess progress: {e}")
        return None
    finally:
        db.close()


# ===================== Module Progress Operations =====================

def get_module_progress(username: str, module_id: str) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
    """Get module progress for user"""
    db = SessionLocal()
    try:
        if module_id:
            # Get specific module progress
            progress = db.query(ModuleProgress).filter(
                ModuleProgress.username == username,
                ModuleProgress.module_id == module_id
            ).first()
            
            if not progress:
                return None
            
            return {
                "username": progress.username,
                "module_id": progress.module_id,
                "progress_percentage": progress.progress_percentage,
                "completed_lessons": progress.completed_lessons,
                "total_lessons": progress.total_lessons,
                "is_completed": progress.is_completed,
                "completion_date": progress.completion_date.isoformat() if progress.completion_date else None,
                "last_accessed_date": progress.last_accessed_date.isoformat() if progress.last_accessed_date else None
            }
        else:
            # Get all modules progress for user
            progress_list = db.query(ModuleProgress).filter(
                ModuleProgress.username == username
            ).all()
            
            if not progress_list:
                return []
            
            return [{
                "username": p.username,
                "module_id": p.module_id,
                "progress_percentage": p.progress_percentage,
                "completed_lessons": p.completed_lessons,
                "total_lessons": p.total_lessons,
                "is_completed": p.is_completed,
                "completion_date": p.completion_date.isoformat() if p.completion_date else None,
                "last_accessed_date": p.last_accessed_date.isoformat() if p.last_accessed_date else None
            } for p in progress_list]
        
    finally:
        db.close()


def update_module_progress(username: str, module_id: str, progress_percentage: float, 
                          completed_lessons: int = None, total_lessons: int = None) -> Optional[Dict[str, Any]]:
    """Update module progress for user"""
    db = SessionLocal()
    try:
        progress = db.query(ModuleProgress).filter(
            ModuleProgress.username == username,
            ModuleProgress.module_id == module_id
        ).first()
        
        if not progress:
            # Create new progress record
            progress = ModuleProgress(
                username=username,
                module_id=module_id,
                progress_percentage=progress_percentage,  # Set initial progress
                total_lessons=total_lessons or 0
            )
            db.add(progress)
        else:
            # Update fields - allow progress to increase
            old_progress = progress.progress_percentage
            if progress.progress_percentage is not None:
                # Allow progress to increase, not just take max
                progress.progress_percentage = progress_percentage
            else:
                progress.progress_percentage = progress_percentage
        
        progress.last_accessed_date = datetime.utcnow()
        
        if completed_lessons is not None:
            progress.completed_lessons = completed_lessons
        if total_lessons is not None:
            progress.total_lessons = total_lessons
        
        # Mark as completed if 100% progress
        if progress.progress_percentage >= 100.0:
            progress.is_completed = True
            progress.completion_date = datetime.utcnow()
        
        db.commit()
        db.refresh(progress)
        
        return get_module_progress(username, module_id)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating module progress: {e}")
        return None
    finally:
        db.close()
