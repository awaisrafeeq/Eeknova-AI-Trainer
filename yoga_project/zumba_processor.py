import cv2
import numpy as np
import base64
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import sys
import os
from pathlib import Path

zumba_path = Path(__file__).parent.parent / "Zumba" / "feedback_generation_real_time" / "src"
sys.path.append(str(zumba_path))

try:
    from feedback_processor import GuidedZumbaAnalyzer, FeedbackManager
    ZUMBA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Zumba module not available: {e}")
    ZUMBA_AVAILABLE = False

class ZumbaSessionManager:
    """Manages Zumba analysis sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.analyzers: Dict[str, GuidedZumbaAnalyzer] = {}
        
    def create_session(self, session_id: str, target_move: str, settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new Zumba analysis session"""
        if not ZUMBA_AVAILABLE:
            raise Exception("Zumba functionality not available")
            
        try:
            analyzer = GuidedZumbaAnalyzer(
                feedback_interval=settings.get('feedback_interval', 3.0) if settings else 3.0,
                min_feedback_gap=settings.get('min_feedback_gap', 2.0) if settings else 2.0
            )
            
            # Initialize target_move to prevent AttributeError
            analyzer.target_move = target_move
            
            # Load reference data
            references_path = zumba_path / "improved_automatic_references.json"
            if references_path.exists():
                analyzer.load_references(str(references_path))
            else:
                raise Exception(f"Reference data not found at {references_path}")
            
            if target_move not in analyzer.reference_angles:
                available_moves = list(analyzer.reference_angles.keys())
                raise Exception(f"Unknown move '{target_move}'. Available moves: {available_moves}")
            
            session_data = {
                'session_id': session_id,
                'target_move': target_move,
                'created_at': datetime.now().isoformat(),
                'settings': settings or {},
                'status': 'active',
                'frames_processed': 0,
                'total_frames': 0,
                'feedback_messages': [],
                'performance_metrics': {
                    'good_frames': 0,
                    'total_frames': 0,
                    'feedback_count': 0
                }
            }
            
            self.sessions[session_id] = session_data
            self.analyzers[session_id] = analyzer
            
            return session_data
            
        except Exception as e:
            raise Exception(f"Failed to create Zumba session: {str(e)}")
    
    def process_frame(self, session_id: str, frame_data: str) -> Dict[str, Any]:
        """Process a frame for Zumba pose analysis"""
        if not ZUMBA_AVAILABLE:
            raise Exception("Zumba functionality not available")
            
        if session_id not in self.sessions:
            raise Exception("Session not found")
            
        if session_id not in self.analyzers:
            return {
                'session_id': session_id,
                'pose_detected': False,
                'message': 'Session ended - frame processing stopped',
                'timestamp': datetime.now().isoformat(),
                'performance_metrics': {'total_frames': 0, 'good_frames': 0, 'feedback_count': 0}
            }
        
        try:
            frame_bytes = base64.b64decode(frame_data.split(',')[1])
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                raise Exception("Failed to decode frame")
            
            # OPTIMIZATION: Ultra-small frame size for integrated GPU
            height, width = frame.shape[:2]
            if width > 160:
                scale = 160 / width
                frame = cv2.resize(frame, (160, int(height * scale)))
            
            analyzer = self.analyzers[session_id]
            session = self.sessions[session_id]
            
            results = analyzer.pose_model(frame, verbose=False)
            
            if results and len(results) > 0 and results[0].keypoints is not None and results[0].keypoints.data is not None and len(results[0].keypoints.data) > 0:
                keypoints = results[0].keypoints.data[0].cpu().numpy()
                
                if len(keypoints) == 0:
                    session['frames_processed'] += 1
                    session['performance_metrics']['total_frames'] += 1
                    
                    return {
                        'session_id': session_id,
                        'pose_detected': False,
                        'message': 'No valid keypoints detected',
                        'timestamp': datetime.now().isoformat(),
                        'performance_metrics': session['performance_metrics']
                    }
                
                # Calculate angles using the correct method name
                angles = analyzer._extract_angles(keypoints)
                
                # Compare with reference and get feedback
                target_move = session['target_move']
                
                bad_parts = analyzer.compare(angles)
                
                feedback_messages = []
                corrections = []
                
                if hasattr(analyzer, 'current_issues') and analyzer.current_issues:
                    for joint_name, issue_data in analyzer.current_issues.items():
                        feedback_messages.append(issue_data['message'])
                        corrections.append(f"{joint_name.replace('_', ' ').title()}: {issue_data['message']}")
                
                session['frames_processed'] += 1
                session['performance_metrics']['total_frames'] += 1
                
                if not bad_parts:  # Good form
                    session['performance_metrics']['good_frames'] += 1
                
                accuracy = None
                if session['performance_metrics']['total_frames'] > 0:
                    accuracy = (session['performance_metrics']['good_frames'] / 
                               session['performance_metrics']['total_frames']) * 100
                
                # Add new feedback to session
                session['feedback_messages'].extend(feedback_messages)
                session['performance_metrics']['feedback_count'] += len(feedback_messages)
                
                # ==========================================
                # TESTING ONLY - REMOVE FOR PRODUCTION
                # ==========================================
                # TEMPORARILY DISABLED FOR LAG TESTING
                # Enable skeleton drawing for visualization
                # analyzer._draw_skeleton(frame, keypoints)   # important for skeleton visualization
                
                # TEMPORARILY DISABLED FOR LAG TESTING  
                # Enable processed frame return to show skeleton overlay
                # _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                # processed_frame = base64.b64encode(buffer).decode('utf-8')
                
                return {
                    'session_id': session_id,
                    'pose_detected': True,
                    'target_move': target_move,
                    'angles': angles,
                    'feedback_messages': feedback_messages,
                    'corrections': corrections,
                    'accuracy': accuracy,
                    # 'processed_frame': f"data:image/jpeg;base64,{processed_frame}", # TESTING: Remove this line for production
                    'timestamp': datetime.now().isoformat(),
                    'performance_metrics': session['performance_metrics']
                }
                
                # ==========================================
                # PRODUCTION VERSION (uncomment for production)
                # ==========================================
                # return {
                #     'session_id': session_id,
                #     'pose_detected': True,
                #     'target_move': target_move,
                #     'angles': angles,
                #     'feedback_messages': feedback_messages,
                #     'corrections': corrections,
                #     'accuracy': accuracy,
                #     # 'processed_frame': f"data:image/jpeg;base64,{processed_frame}", # PRODUCTION: Keep commented
                #     'timestamp': datetime.now().isoformat(),
                #     'performance_metrics': session['performance_metrics']
                # }
            else:
                session['frames_processed'] += 1
                session['performance_metrics']['total_frames'] += 1
                
                return {
                    'session_id': session_id,
                    'pose_detected': False,
                    'message': 'No pose detected in frame',
                    'timestamp': datetime.now().isoformat(),
                    'performance_metrics': session['performance_metrics']
                }
                
        except Exception as e:
            raise Exception(f"Frame processing failed: {str(e)}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary and performance metrics"""
        if session_id not in self.sessions:
            raise Exception("Session not found")
        
        session = self.sessions[session_id]
        metrics = session['performance_metrics']
        
        # Calculate final accuracy
        accuracy = 0
        if metrics['total_frames'] > 0:
            accuracy = (metrics['good_frames'] / metrics['total_frames']) * 100
        
        return {
            'session_id': session_id,
            'target_move': session['target_move'],
            'duration_seconds': 0,  # TODO: Calculate actual duration
            'frames_processed': metrics['total_frames'],
            'average_accuracy': accuracy,
            'feedback_count': metrics['feedback_count'],
            'created_at': session['created_at'],
            'status': session['status']
        }
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a Zumba session and return summary"""
        summary = self.get_session_summary(session_id)
        
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = 'completed'
        
        import threading
        def cleanup_analyzer():
            import time
            time.sleep(1.0) 
            if session_id in self.analyzers:
                del self.analyzers[session_id]
        
        cleanup_thread = threading.Thread(target=cleanup_analyzer)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        return summary
    
    def get_available_moves(self) -> List[str]:
        if not ZUMBA_AVAILABLE:
            return []
        
        try:
            temp_analyzer = GuidedZumbaAnalyzer()
            references_path = zumba_path / "improved_automatic_references.json"
            
            if references_path.exists():
                temp_analyzer.load_references(str(references_path))
                return list(temp_analyzer.reference_angles.keys())
            else:
                return []
        except:
            return []

zumba_session_manager = ZumbaSessionManager()
