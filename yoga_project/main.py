from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import cv2
import numpy as np
import base64
import pickle
import os
import uuid
from datetime import datetime, timedelta
import asyncio
import json
import logging
from io import BytesIO
from PIL import Image
import uvicorn
from jose import JWTError, jwt
import bcrypt
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Import database functions
from database import (
    init_db, get_yoga_streak, update_yoga_streak, create_yoga_session,
    get_chess_progress, update_chess_progress,
    get_module_progress, update_module_progress,
    get_user_profile
)

# Import your existing yoga pose analysis functions
from Yoga_pose_estimation_YOLO import (
    calculate_pose_angles,
    compare_with_ground_truth,
    provide_correction_feedback,
    find_pose_in_references,
    load_reference_angles,
    YOLO,
    ANGLES_TO_CALCULATE,
    SKELETON,
    POSE_PALETTE
)
# Import Zumba processor
from zumba_processor import zumba_session_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Yoga Pose Analysis API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models and data
yolo_model = None
classifier_model = None
pose_classes = []
angle_features = []
reference_angles = {}
active_sessions = {}
active_connections: Dict[str, WebSocket] = {}

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized successfully")

# Complete Chess Engine imports - Full pygame functionality
from chess_engine import chess_engine, lesson_engine
from chess_api import (
    CHESS_MODULES, chess_session_manager,
    ChessModuleInfo, ChessExerciseResponse, ChessActionRequest,
    ChessSessionCreateRequest, ChessSessionSummary,
    exercise_state_to_response, board_position_to_model, get_module_by_id
)



# JWT and authentication
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour session instead of 30 minutes

# Import database functions
from database import init_db, create_user, get_user_by_username, get_user_profile, update_user_profile

# Initialize database on startup
init_db()

# Security
security = HTTPBearer()

# Configuration
MODEL_PATH = "pose correction.pkl"
REFERENCES_PATH = "angles_final.pkl"
YOLO_MODEL_PATH = "yolo11x-pose.pt"

# Pydantic models
class SessionStartRequest(BaseModel):
    pose_name: Optional[str] = None
    tolerance: float = 10.0

class SessionResponse(BaseModel):
    session_id: str
    settings: Dict[str, Any]

class PoseInfo(BaseModel):
    name: str
    display_name: str
    description: str

class ModelStatus(BaseModel):
    yolo_ready: bool
    classifier_ready: bool
    reference_angles_loaded: bool
    available_poses: int
    reference_poses: int
    timestamp: str

class SettingsUpdate(BaseModel):
    angle_tolerance: Optional[float] = 10.0
    confidence_threshold: Optional[float] = 0.5
    mirror_mode: Optional[bool] = True

class PoseFrameData(BaseModel):
    data: str
    session_id: str
    timestamp: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    fitness_level: Optional[str] = None

class UserProfile(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    fitness_level: Optional[str] = "beginner"
    preferences: Optional[Dict[str, Any]] = {}




class PoseAnalysisSession:
    def __init__(self, session_id: str, pose_name: Optional[str] = None, tolerance: float = 10.0):
        self.session_id = session_id
        self.pose_name = pose_name
        self.tolerance = tolerance
        self.start_time = datetime.now()
        self.frame_count = 0
        self.total_accuracy = 0
        self.accuracy_count = 0
        self.corrections_given = 0
        self.is_active = True
        
    def add_accuracy_measurement(self, accuracy: float):
        if accuracy is not None:
            self.total_accuracy += accuracy
            self.accuracy_count += 1
    
    def get_average_accuracy(self) -> float:
        if self.accuracy_count > 0:
            return self.total_accuracy / self.accuracy_count
        return 0
    
    def get_summary(self) -> Dict[str, Any]:
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            'session_id': self.session_id,
            'duration_seconds': int(duration),
            'frames_processed': self.frame_count,
            'average_accuracy': self.get_average_accuracy(),
            'corrections_given': self.corrections_given,
            'pose_name': self.pose_name
        }

# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        # Truncate password to 72 bytes (bcrypt limit)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            truncated_password = plain_password[:72]
        else:
            truncated_password = plain_password
        
        return bcrypt.checkpw(truncated_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    try:
        # Truncate password to 72 bytes (bcrypt limit)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            truncated_password = password[:72]
            logger.warning(f"Password truncated from {len(password_bytes)} to 72 bytes")
        else:
            truncated_password = password
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(truncated_password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise HTTPException(status_code=500, detail="Password hashing failed")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(username: str):
    return get_user_by_username(username)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def load_models():
    """Load YOLO model, classifier, and reference angles"""
    global yolo_model, classifier_model, pose_classes, angle_features, reference_angles
    
    try:
        # Load YOLO model
        if os.path.exists(YOLO_MODEL_PATH):
            yolo_model = YOLO(YOLO_MODEL_PATH)
            logger.info("YOLO model loaded successfully")
        else:
            logger.error(f"YOLO model not found at {YOLO_MODEL_PATH}")
            return False
        
        # Load classifier model
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                model_data = pickle.load(f)
            classifier_model = model_data.get('model')
            pose_classes = model_data.get('classes', [])
            angle_features = model_data.get('features', [])
            logger.info(f"Classifier model loaded with {len(pose_classes)} poses")
        else:
            logger.warning(f"Classifier model not found at {MODEL_PATH}")
        
        # Load reference angles
        if os.path.exists(REFERENCES_PATH):
            reference_angles = load_reference_angles(REFERENCES_PATH)
            logger.info(f"Reference angles loaded for {len(reference_angles)} poses")
        else:
            logger.warning(f"Reference angles not found at {REFERENCES_PATH}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        return False

async def process_frame(frame_data: str, session_id: str) -> Dict[str, Any]:
    """Process a single frame for pose analysis"""
    global yolo_model, classifier_model, reference_angles
    
    logger.info(f"Starting frame processing for session {session_id}")  # Add this line

    
    try:
        # Decode base64 image
        logger.info("Decoding base64 image")  # Add this line

        image_data = base64.b64decode(frame_data.split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {'error': 'Failed to decode image'}
        
        # Get session info
        session = active_sessions.get(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        session.frame_count += 1
        
        # Process with YOLO
        results = yolo_model(frame, verbose=False)
        
        # Check if pose detected
        if len(results) == 0 or not hasattr(results[0], 'keypoints') or len(results[0].keypoints) == 0:
            return {
                'pose_detected': False,
                'message': 'No person detected'
            }
        
        # Extract keypoints
        keypoints = results[0].keypoints.data.cpu().numpy()
        
        if keypoints.shape[0] == 0 or keypoints.shape[1] != 17 or keypoints.shape[2] != 3:
            return {
                'pose_detected': False,
                'message': 'Invalid pose keypoints'
            }
        
        # Calculate pose angles
        pose_angles = calculate_pose_angles(keypoints)
        
        if not pose_angles or not pose_angles[0]:
            return {
                'pose_detected': True,
                'message': 'Pose detected but angles not calculable',
                'keypoints': keypoints[0].tolist()
            }
        
        # Classify pose if classifier available and not in fixed mode
        detected_pose = session.pose_name
        pose_confidence = 0
        current_pose_name = session.pose_name
        can_compare = False
        gt_angles = {}
        
        if not session.pose_name and classifier_model:
            # Auto-classify pose
            valid_angles = sum(1 for angle_name in angle_features
                             if angle_name in pose_angles[0] and pose_angles[0][angle_name] is not None)
            
            if valid_angles >= 4:
                feature_vector = []
                for angle_name in angle_features:
                    angle_value = pose_angles[0].get(angle_name)
                    feature_vector.append(angle_value if angle_value is not None else 0)
                
                feature_vector = np.array(feature_vector).reshape(1, -1)
                
                prediction = classifier_model.predict(feature_vector)[0]
                probabilities = classifier_model.predict_proba(feature_vector)[0]
                confidence = probabilities[prediction]
                
                if confidence >= 0.4:
                    predicted_class = pose_classes[prediction]
                    detected_pose = ' '.join(word.capitalize() for word in predicted_class.replace('_', ' ').split())
                    pose_confidence = confidence
                    
                    # Find matching reference angles
                    matched_name, ref_angles, found_match = find_pose_in_references(
                        predicted_class, reference_angles
                    )
                    
                    if found_match:
                        current_pose_name = matched_name
                        can_compare = True
                        gt_angles = ref_angles
        else:
            # Fixed pose mode
            if session.pose_name:
                matched_name, ref_angles, found_match = find_pose_in_references(
                    session.pose_name, reference_angles
                )
                
                if found_match:
                    current_pose_name = matched_name
                    can_compare = True
                    gt_angles = ref_angles
        
        # Compare with reference if available
        comparison_results = None
        accuracy = None
        corrections = []
        angle_status = {}
        
        if can_compare and gt_angles:
            comparison_results = compare_with_ground_truth(
                pose_angles[0], gt_angles, session.tolerance
            )
            
            corrections = provide_correction_feedback(comparison_results, session.tolerance)
            session.corrections_given += len(corrections)
            
            # Calculate accuracy
            correct_count = sum(1 for res in comparison_results.values()
                              if res["within_tolerance"] and res["ground_truth"] is not None)
            total_count = sum(1 for res in comparison_results.values()
                            if res["calculated"] is not None and res["ground_truth"] is not None)
            
            if total_count > 0:
                accuracy = (correct_count / total_count) * 100
                session.add_accuracy_measurement(accuracy)
            
            # Create angle status
            for angle_name, result in comparison_results.items():
                angle_status[angle_name] = {
                    'within_tolerance': result['within_tolerance'],
                    'difference': result['difference']
                }
        
        # return {
        #     'pose_detected': True,
        #     'pose_name': detected_pose,
        #     'confidence': float(pose_confidence) if pose_confidence else 0,
        #     'accuracy': accuracy,
        #     'correct_angles': sum(1 for res in comparison_results.values() 
        #                         if res["within_tolerance"]) if comparison_results else 0,
        #     'total_angles': len([res for res in comparison_results.values() 
        #                        if res["calculated"] is not None]) if comparison_results else 0,
        #     'keypoints': keypoints[0].tolist(),
        #     'angles': pose_angles[0],
        #     'corrections': corrections[:3],  # Limit to top 3 corrections
        #     'angle_status': angle_status,
        #     'session_stats': {
        #         'frames_processed': session.frame_count,
        #         'average_accuracy': session.get_average_accuracy()
        #     }
        # }

     
        return {
            'pose_detected': True,
            'pose_name': detected_pose,
            'confidence': float(pose_confidence) if pose_confidence else 0.0,
            'accuracy': float(accuracy) if accuracy else None,
            'correct_angles': int(sum(1 for res in comparison_results.values() 
                                    if res["within_tolerance"]) if comparison_results else 0),
            'total_angles': int(len([res for res in comparison_results.values() 
                                if res["calculated"] is not None]) if comparison_results else 0),
            'keypoints': [[float(x), float(y), float(conf)] for x, y, conf in keypoints[0].tolist()],
            'angles': {k: float(v) if v is not None else None for k, v in pose_angles[0].items()},
            'corrections': corrections[:3],
            'angle_status': {k: {
                'within_tolerance': bool(v['within_tolerance']),
                'difference': float(v['difference']) if v['difference'] is not None else None
            } for k, v in angle_status.items()},
            'session_stats': {
                'frames_processed': int(session.frame_count),
                'average_accuracy': float(session.get_average_accuracy())
            }
        }        
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return {'error': f'Processing failed: {str(e)}'}

# Authentication endpoints
@app.post("/api/auth/register", response_model=Token)
async def register_user(user: UserCreate):
    """Register a new user"""
    try:
        if get_user(user.username):
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
        
        hashed_password = get_password_hash(user.password)
        
        # Create user in database
        new_user = create_user(user.username, user.email, hashed_password)
        if not new_user:
            raise HTTPException(
                status_code=400,
                detail="Username or email already registered"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Login user and return JWT token"""
    try:
        user = authenticate_user(user_credentials.username, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me", response_model=UserProfile)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    try:
        profile = get_user_profile(current_user["username"])
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/auth/profile")
async def update_user_profile_endpoint(profile_update: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    try:
        username = current_user["username"]
        updated_profile = update_user_profile(username, profile_update.dict())
        if not updated_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {"message": "Profile updated successfully", "profile": updated_profile}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoints

def normalize_pose_name(pose_name: str) -> str:
    """Normalize pose name to match reference angles format"""
    if not pose_name:
        return None
    
    # Convert "Mountain Pose" -> "mountain_pose" -> find best match
    normalized = pose_name.lower().replace(' ', '_').replace('-', '_')
    
    # Also create display format for matching
    display_format = ' '.join(word.capitalize() for word in pose_name.replace('_', ' ').replace('-', ' ').split())
    
    # Check if we have a direct match in reference_angles
    if reference_angles:
        # Try direct match with normalized
        for ref_name in reference_angles.keys():
            ref_normalized = ref_name.lower().replace(' ', '_').replace('-', '_')
            if normalized == ref_normalized or display_format == ref_name:
                return ref_name
        
        # Partial match
        for ref_name in reference_angles.keys():
            ref_normalized = ref_name.lower().replace(' ', '_').replace('-', '_')
            if normalized in ref_normalized or ref_normalized in normalized:
                return ref_name
    
    # Return display format as fallback
    return display_format

@app.post("/api/session/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    """Initialize pose analysis session (no auth required for testing)"""
    try:
        session_id = str(uuid.uuid4())
        
        # Normalize pose name to match reference angles
        normalized_pose = normalize_pose_name(request.pose_name) if request.pose_name else None
        
        session = PoseAnalysisSession(session_id, normalized_pose, request.tolerance)
        active_sessions[session_id] = session
        
        logger.info(f"Started session {session_id} with pose: {normalized_pose} (original: {request.pose_name})")
        
        return SessionResponse(
            session_id=session_id,
            settings={
                'pose_name': normalized_pose,
                'tolerance': request.tolerance,
                'timestamp': datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PoseUpdateRequest(BaseModel):
    pose_name: str
    tolerance: Optional[float] = 10.0

@app.put("/api/session/{session_id}/pose")
async def update_session_pose(session_id: str, request: PoseUpdateRequest):
    """Update the target pose for an active session"""
    try:
        session = active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Normalize pose name
        normalized_pose = normalize_pose_name(request.pose_name)
        
        session.pose_name = normalized_pose
        session.tolerance = request.tolerance
        
        logger.info(f"Updated session {session_id} pose to: {normalized_pose}")
        
        return {
            'session_id': session_id,
            'pose_name': normalized_pose,
            'tolerance': request.tolerance,
            'message': 'Pose updated successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session pose: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/stop/{session_id}")
async def stop_session(session_id: str):
    """End session and get summary"""
    try:
        session = active_sessions.get(session_id)
        if not session:
            # Handle missing session gracefully (e.g. after server restart)
            logger.warning(f"Stop session called for unknown session_id: {session_id}")
            return {
                'session_id': session_id,
                'duration_seconds': 0,
                'frames_processed': 0,
                'average_accuracy': 0,
                'corrections_given': 0,
                'pose_name': "Unknown (Server Restarted)"
            }
        
        session.is_active = False
        summary = session.get_summary()
        
        # Remove from active sessions
        del active_sessions[session_id]
        
        logger.info(f"Stopped session {session_id}")
        
        return summary
    
    except Exception as e:
        logger.error(f"Error stopping session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/poses/available", response_model=List[PoseInfo])
async def get_available_poses():
    """Get list of supported poses"""
    try:
        poses = []
        
        # Add poses from classifier
        for pose_class in pose_classes:
            display_name = ' '.join(word.capitalize() for word in pose_class.replace('_', ' ').split())
            poses.append(PoseInfo(
                name=pose_class,
                display_name=display_name,
                description=f'{display_name} yoga pose'
            ))
        
        # Add poses from reference angles that might not be in classifier
        for ref_pose in reference_angles.keys():
            if ref_pose not in [p.display_name for p in poses]:
                poses.append(PoseInfo(
                    name=ref_pose.lower().replace(' ', '_'),
                    display_name=ref_pose,
                    description=f'{ref_pose} yoga pose'
                ))
        
        return poses
        
    except Exception as e:
        logger.error(f"Error getting available poses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chess/modules", response_model=List[ChessModuleInfo])
async def get_chess_modules():
    """Get list of chess learning modules"""
    try:
        return [
            ChessModuleInfo(
                id=m["id"],
                name=m["name"],
                description=m["description"],
                icon=m["icon"],
                total_exercises=m["total_exercises"],
                unlocked=m["unlocked"]
            )
            for m in CHESS_MODULES
        ]
    except Exception as e:
        logger.error(f"Error getting chess modules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/model/status", response_model=ModelStatus)
async def get_model_status():
    """Check if models are loaded and ready"""
    try:
        return ModelStatus(
            yolo_ready=yolo_model is not None,
            classifier_ready=classifier_model is not None,
            reference_angles_loaded=len(reference_angles) > 0,
            available_poses=len(pose_classes),
            reference_poses=len(reference_angles),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-frame")
async def analyze_frame_endpoint(request: PoseFrameData):
    """Analyze a single frame for pose"""
    try:
        result = await process_frame(request.data, request.session_id)
        if isinstance(result, dict) and result.get('error') == 'Session not found':
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chess/session", response_model=ChessExerciseResponse)
async def create_chess_session(request: ChessSessionCreateRequest):
    """Start a new chess lesson session with full pygame functionality"""
    try:
        session_id = chess_session_manager.create_session(request.module_id)
        session = chess_session_manager.get_session(session_id)
        exercise = session["current_exercise_state"]
        
        return exercise_state_to_response(exercise, session_id)
    except Exception as e:
        logger.error(f"Error creating chess session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chess/session/{session_id}", response_model=ChessExerciseResponse)
async def get_chess_session_state(session_id: str):
    """Get the current exercise state for a chess session"""
    try:
        session = chess_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        exercise = session["current_exercise_state"]
        return exercise_state_to_response(exercise, session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chess session state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chess/session/{session_id}/action", response_model=ChessExerciseResponse)
async def apply_chess_action(session_id: str, request: ChessActionRequest):
    """Apply a user action to a chess lesson session and return updated state"""
    try:
        exercise = chess_session_manager.apply_action(session_id, request.type, request.payload)
        return exercise_state_to_response(exercise, session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying chess action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chess/session/{session_id}/complete", response_model=ChessSessionSummary)
async def complete_chess_session(session_id: str):
    """Mark a chess lesson session as completed and return a summary"""
    try:
        summary = chess_session_manager.complete_session(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Session not found")

        return ChessSessionSummary(**summary)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing chess session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== ZUMBA API ENDPOINTS =====================

class ZumbaSessionStartRequest(BaseModel):
    target_move: str
    settings: Optional[Dict[str, Any]] = {}

class ZumbaSessionResponse(BaseModel):
    session_id: str
    target_move: str
    settings: Dict[str, Any]
    created_at: str
    status: str

class ZumbaFrameData(BaseModel):
    session_id: str
    frame_data: str  # Base64 encoded image

class ZumbaAnalysisResult(BaseModel):
    session_id: str
    pose_detected: bool
    target_move: Optional[str] = None
    angles: Optional[Dict[str, float]] = None
    feedback_messages: List[str] = []
    corrections: List[str] = []
    accuracy: Optional[float] = None
    processed_frame: Optional[str] = None
    timestamp: str
    performance_metrics: Dict[str, Any] = {}
    message: Optional[str] = None

class ZumbaSessionSummary(BaseModel):
    session_id: str
    target_move: str
    duration_seconds: int
    frames_processed: int
    average_accuracy: float
    feedback_count: int
    created_at: str
    status: str

@app.get("/api/zumba/moves", response_model=List[str])
async def get_zumba_moves():
    """Get list of available Zumba moves"""
    try:
        moves = zumba_session_manager.get_available_moves()
        return moves
    except Exception as e:
        logger.error(f"Error getting Zumba moves: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zumba/session", response_model=ZumbaSessionResponse)
async def create_zumba_session(request: ZumbaSessionStartRequest):
    """Start a new Zumba analysis session"""
    try:
        session_id = str(uuid.uuid4())
        session_data = zumba_session_manager.create_session(
            session_id=session_id,
            target_move=request.target_move,
            settings=request.settings
        )
        
        logger.info(f"Created Zumba session: {session_id} for move: {request.target_move}")
        return ZumbaSessionResponse(**session_data)
        
    except Exception as e:
        logger.error(f"Error creating Zumba session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zumba/analyze-frame", response_model=ZumbaAnalysisResult)
async def analyze_zumba_frame(request: ZumbaFrameData):
    """Analyze a single frame for Zumba pose detection"""
    try:
        result = zumba_session_manager.process_frame(
            session_id=request.session_id,
            frame_data=request.frame_data
        )
        
        return ZumbaAnalysisResult(**result)
        
    except Exception as e:
        logger.error(f"Error analyzing Zumba frame: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/zumba/session/{session_id}/summary", response_model=ZumbaSessionSummary)
async def get_zumba_session_summary(session_id: str):
    """Get Zumba session summary"""
    try:
        summary = zumba_session_manager.get_session_summary(session_id)
        return ZumbaSessionSummary(**summary)
        
    except Exception as e:
        logger.error(f"Error getting Zumba session summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/zumba/session/{session_id}/end", response_model=ZumbaSessionSummary)
async def end_zumba_session(session_id: str):
    """End a Zumba session and return summary"""
    try:
        summary = zumba_session_manager.end_session(session_id)
        logger.info(f"Ended Zumba session: {session_id}")
        return ZumbaSessionSummary(**summary)
        
    except Exception as e:
        logger.error(f"Error ending Zumba session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== SETTINGS ENDPOINTS =====================

@app.put("/api/settings")
async def update_settings(settings: SettingsUpdate):
    """Update analysis settings"""
    try:
        updated_settings = {
            'angle_tolerance': settings.angle_tolerance,
            'confidence_threshold': settings.confidence_threshold,
            'mirror_mode': settings.mirror_mode,
            'updated_at': datetime.now().isoformat()
        }
        
        return {'updated_settings': updated_settings}
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws/pose-analysis")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time pose analysis"""
    await websocket.accept()
    client_id = str(uuid.uuid4())
    active_connections[client_id] = websocket
    
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            'type': 'connected',
            'client_id': client_id,
            'message': 'Connected to pose analysis server'
        })
        
        while True:
            # Receive data from client
            data = await websocket.receive_json()
            
            message_type = data.get('type', 'unknown')
            
            if message_type == 'pose_frame':
                # Process pose frame
                frame_data = data.get('data')
                session_id = data.get('session_id')
                session_type = data.get('session_type', 'yoga')  # 'yoga' or 'zumba'
                
                logger.info(f"Received frame for {session_type} session {session_id}")
                
                if not frame_data or not session_id:
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'Missing frame data or session_id'
                    })
                    continue
                
                if session_type == 'zumba':
                    # Handle Zumba frame processing
                    try:
                        result = zumba_session_manager.process_frame(
                            session_id=session_id,
                            frame_data=frame_data
                        )
                        result['type'] = 'zumba_analysis'
                        result['timestamp'] = datetime.now().isoformat()
                        
                        # Send result back to client
                        await websocket.send_json(result)
                        
                    except Exception as e:
                        logger.error(f"Zumba frame processing error for session {session_id}: {e}")
                        try:
                            await websocket.send_json({
                                'type': 'error', 
                                'message': f'Zumba processing failed: {str(e)}'
                            })
                        except Exception as send_error:
                            logger.error(f"Failed to send Zumba error message: {send_error}")
                            break
                else:
                    # Handle existing Yoga frame processing
                    session = active_sessions.get(session_id)
                    if not session or not session.is_active:
                        await websocket.send_json({
                            'type': 'error',
                            'message': 'Invalid or inactive session'
                        })
                        continue
                    
                    # Process the frame with timeout and error handling
                    try:
                        result = await asyncio.wait_for(
                            process_frame(frame_data, session_id), 
                            timeout=10.0  # 10 second timeout
                        )
                        result['type'] = 'pose_analysis'
                        result['timestamp'] = datetime.now().isoformat()
                        
                        # Send result back to client
                        await websocket.send_json(result)
                        
                    except asyncio.TimeoutError:
                        logger.error(f"Frame processing timeout for session {session_id}")
                        try:
                            await websocket.send_json({
                                'type': 'error',
                                'message': 'Frame processing timeout - try reducing image quality'
                            })
                        except Exception as send_error:
                            logger.error(f"Failed to send timeout message: {send_error}")
                            # Connection likely closed, break the loop
                            break
                    except Exception as e:
                        logger.error(f"Frame processing error for session {session_id}: {e}")
                        try:
                            await websocket.send_json({
                                'type': 'error', 
                                'message': f'Processing failed: {str(e)}'
                            })
                        except Exception as send_error:
                            logger.error(f"Failed to send error message: {send_error}")
                            # Connection likely closed, break the loop
                            break
                
            elif message_type == 'start_analysis':
                # Start analysis session
                pose_name = data.get('pose_name')
                tolerance = data.get('tolerance', 10.0)
                
                session_id = str(uuid.uuid4())
                session = PoseAnalysisSession(session_id, pose_name, tolerance)
                active_sessions[session_id] = session
                
                await websocket.send_json({
                    'type': 'analysis_started',
                    'session_id': session_id,
                    'pose_name': pose_name,
                    'tolerance': tolerance
                })
                
            elif message_type == 'stop_analysis':
                # Stop analysis session
                session_id = data.get('session_id')
                
                if session_id in active_sessions:
                    session = active_sessions[session_id]
                    session.is_active = False
                    summary = session.get_summary()
                    del active_sessions[session_id]
                    
                    # Add session summary to the response
                    response = {
                        'type': 'analysis_stopped',
                        'summary': summary,
                        **summary
                    }
                    
                    await websocket.send_json(response)
                else:
                    await websocket.send_json({
                        'type': 'error',
                        'message': 'Session not found'
                    })
            
            elif message_type == 'ping':
                # Handle heartbeat ping
                await websocket.send_json({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'message': f'Server error: {str(e)}'
            })
        except Exception as send_error:
            logger.error(f"Failed to send error message in exception handler: {send_error}")
            # Connection already closed, no need to send
    finally:
        # Clean up
        if client_id in active_connections:
            del active_connections[client_id]

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(active_sessions),
        'active_connections': len(active_connections)
    }

# ===================== Streak & Progress API Endpoints =====================

@app.get("/api/yoga/streak/{username}")
async def get_yoga_streak_endpoint(username: str):
    """Get yoga streak data for user"""
    try:
        streak_data = get_yoga_streak(username)
        if streak_data:
            return {"success": True, "data": streak_data}
        else:
            return {"success": False, "message": "Failed to get streak data"}
    except Exception as e:
        logger.error(f"Error getting yoga streak: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/yoga/session")
async def create_yoga_session_endpoint(session_data: Dict[str, Any]):
    """Create a new yoga session record"""
    try:
        username = session_data.get("username")
        if not username:
            return {"success": False, "message": "Username is required"}
        
        session = create_yoga_session(username, session_data)
        if session:
            return {"success": True, "data": session}
        else:
            return {"success": False, "message": "Failed to create session"}
    except Exception as e:
        logger.error(f"Error creating yoga session: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/chess/progress/{username}")
async def get_chess_progress_endpoint(username: str, module_id: str = None):
    """Get chess progress for user"""
    try:
        progress_data = get_chess_progress(username, module_id)
        if progress_data:
            return {"success": True, "data": progress_data}
        else:
            return {"success": False, "message": "No progress data found"}
    except Exception as e:
        logger.error(f"Error getting chess progress: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/chess/progress/{username}")
async def update_chess_progress_endpoint(username: str, module_id: str, progress_data: Dict[str, Any]):
    """Update chess progress for user"""
    try:
        progress = update_chess_progress(username, module_id, progress_data)
        if progress:
            return {"success": True, "data": progress}
        else:
            return {"success": False, "message": "Failed to update progress"}
    except Exception as e:
        logger.error(f"Error updating chess progress: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/module/progress/{username}")
async def get_module_progress_endpoint(username: str, module_id: str = None):
    """Get module progress for user"""
    try:
        progress_data = get_module_progress(username, module_id)
        if progress_data:
            return {"success": True, "data": progress_data}
        else:
            return {"success": False, "message": "No progress data found"}
    except Exception as e:
        logger.error(f"Error getting module progress: {e}")
        return {"success": False, "message": str(e)}

@app.post("/api/module/progress/{username}")
async def update_module_progress_endpoint(username: str, module_id: str, progress_percentage: float, 
                                        completed_lessons: int = None, total_lessons: int = None):
    """Update module progress for user"""
    try:
        progress = update_module_progress(username, module_id, progress_percentage, completed_lessons, total_lessons)
        if progress:
            return {"success": True, "data": progress}
        else:
            return {"success": False, "message": "Failed to update progress"}
    except Exception as e:
        logger.error(f"Error updating module progress: {e}")
        return {"success": False, "message": str(e)}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize models when the server starts"""
    logger.info("Initializing yoga pose analysis server...")
    success = await load_models()
    if success:
        logger.info("Server initialization complete")
    else:
        logger.error("Server initialization failed - some features may not work")

if __name__ == '__main__':
    # Run the server
    print("Starting yoga pose analysis server with FastAPI...")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
