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

import time

import zumba_scoring

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
                'started_at_monotonic': time.monotonic(),
                'settings': settings or {},
                'status': 'active',
                'frames_processed': 0,
                'total_frames': 0,
                'feedback_messages': [],
                'performance_metrics': {
                    'good_frames': 0,
                    'total_frames': 0,
                    'detected_frames': 0,
                    'comparable_frames': 0,
                    'active_frames': 0,
                    'feedback_count': 0
                },
                'last_angles': None
            }

            # Post-session analytics accumulators (per-move, body-part, beat sync).
            zumba_scoring.init_session_scoring(session_data, settings)

            self.sessions[session_id] = session_data
            self.analyzers[session_id] = analyzer

            return session_data
            
        except Exception as e:
            raise Exception(f"Failed to create Zumba session: {str(e)}")
    
    def process_frame(
        self,
        session_id: str,
        frame_data: str,
        target_move: str = None,
        target_move_name: str = None,
        timeline_ms: float = None,
    ) -> Dict[str, Any]:
        """Process a frame for Zumba pose analysis.

        For timeline-driven sessions the frontend sends the move the timeline
        currently expects (target_move) with each frame. We switch the session's
        comparison target in place — without creating a new session — so metrics
        accumulate across the whole song. If no target_move is supplied we keep
        the session's initial target (single-move backward compatibility).
        """
        if not ZUMBA_AVAILABLE:
            raise Exception("Zumba functionality not available")

        if session_id not in self.sessions:
            raise Exception("Session not found")

        # Apply an incoming per-frame target move if it is valid and changed.
        if target_move and session_id in self.analyzers:
            session = self.sessions[session_id]
            if target_move != session.get('target_move'):
                analyzer = self.analyzers[session_id]
                if target_move in analyzer.reference_angles:
                    session['target_move'] = target_move
                    analyzer.target_move = target_move
                    # Reset motion baseline so cyclic motion isn't compared across moves.
                    session['last_angles'] = None
            
        if session_id not in self.analyzers:
            return {
                'session_id': session_id,
                'pose_detected': False,
                'message': 'Session ended - frame processing stopped',
                'timestamp': datetime.now().isoformat(),
                'performance_metrics': {
                    'total_frames': 0,
                    'good_frames': 0,
                    'detected_frames': 0,
                    'comparable_frames': 0,
                    'active_frames': 0,
                    'feedback_count': 0
                }
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
                    comparable_frames = session['performance_metrics'].get('comparable_frames', 0)
                    accuracy = 0
                    if comparable_frames > 0:
                        accuracy = (session['performance_metrics']['good_frames'] / comparable_frames) * 100
                    
                    return {
                        'session_id': session_id,
                        'pose_detected': False,
                        'message': 'No valid keypoints detected',
                        'accuracy': accuracy,
                        'timestamp': datetime.now().isoformat(),
                        'performance_metrics': session['performance_metrics']
                    }
                
                # Calculate angles using the correct method name
                angles = analyzer._extract_angles(keypoints)
                
                # Compare with reference and get feedback
                target_move = session['target_move']
                ref = analyzer.reference_angles.get(target_move, {})
                comparable_angles = [name for name in angles.keys() if name in ref]
                has_enough_angles = len(comparable_angles) >= 4

                session['frames_processed'] += 1
                session['performance_metrics']['total_frames'] += 1

                if not has_enough_angles:
                    accuracy = 0
                    if session['performance_metrics']['comparable_frames'] > 0:
                        accuracy = (session['performance_metrics']['good_frames'] /
                                   session['performance_metrics']['comparable_frames']) * 100

                    return {
                        'session_id': session_id,
                        'pose_detected': False,
                        'target_move': target_move,
                        'angles': angles,
                        'feedback_messages': ['Move fully into the camera view so your arms and legs are visible.'],
                        'corrections': [],
                        'accuracy': accuracy,
                        'timestamp': datetime.now().isoformat(),
                        'performance_metrics': session['performance_metrics']
                    }

                bad_parts = analyzer.compare(angles)
                
                feedback_messages = []
                corrections = []
                
                if hasattr(analyzer, 'current_issues') and analyzer.current_issues:
                    for joint_name, issue_data in analyzer.current_issues.items():
                        feedback_messages.append(issue_data['message'])
                        corrections.append(f"{joint_name.replace('_', ' ').title()}: {issue_data['message']}")
                
                session['performance_metrics']['detected_frames'] += 1
                session['performance_metrics']['comparable_frames'] += 1

                move_signatures = analyzer.move_signatures.get(target_move, {})
                cyclic_angle_names = [
                    name for name, signature in move_signatures.items()
                    if signature.get('pattern') == 'cyclic' and name in angles
                ]
                last_angles = session.get('last_angles')
                motion_score = 0.0
                is_active_movement = True

                if cyclic_angle_names:
                    if last_angles:
                        deltas = [
                            abs(angles[name] - last_angles[name])
                            for name in cyclic_angle_names
                            if name in last_angles
                        ]
                        motion_score = float(np.mean(deltas)) if deltas else 0.0
                    else:
                        is_active_movement = False

                    # Zumba cyclic moves must show actual motion, not only a static body match.
                    if motion_score < 2.0:
                        is_active_movement = False

                session['last_angles'] = dict(angles)

                if is_active_movement:
                    session['performance_metrics']['active_frames'] += 1
                else:
                    feedback_messages.append('Keep moving with the selected dance step.')
                
                if is_active_movement and not bad_parts:  # Good form
                    session['performance_metrics']['good_frames'] += 1

                accuracy = None
                if session['performance_metrics']['comparable_frames'] > 0:
                    accuracy = (session['performance_metrics']['good_frames'] /
                               session['performance_metrics']['comparable_frames']) * 100

                # Post-session analytics: graded pose accuracy + body-part scores
                # for this frame, plus motion sample for beat-sync detection.
                frame_score = zumba_scoring.score_frame(
                    angles,
                    ref,
                    analyzer.angle_tolerances.get(target_move, {}),
                    target_move,
                )
                zumba_scoring.record_frame(
                    session,
                    target_move,
                    target_move_name,
                    frame_score,
                    motion_score,
                    is_active_movement,
                    timeline_ms,
                )
                
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
                    'motion_score': motion_score,
                    'active_movement': is_active_movement,
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
                comparable_frames = session['performance_metrics'].get('comparable_frames', 0)
                accuracy = 0
                if comparable_frames > 0:
                    accuracy = (session['performance_metrics']['good_frames'] / comparable_frames) * 100
                
                return {
                    'session_id': session_id,
                    'pose_detected': False,
                    'message': 'No pose detected in frame',
                    'accuracy': accuracy,
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
        comparable_frames = metrics.get('comparable_frames', metrics['total_frames'])
        if comparable_frames > 0:
            accuracy = (metrics['good_frames'] / comparable_frames) * 100

        started = session.get('started_at_monotonic')
        duration_seconds = round(time.monotonic() - started, 1) if started else 0

        # Full post-session score object (Overall, Beat Sync, body parts, ...).
        try:
            scores = zumba_scoring.build_scores(session, duration_seconds)
        except Exception as exc:  # scoring must never block session end
            print(f"Warning: Zumba scoring failed for {session_id}: {exc}")
            scores = None

        return {
            'session_id': session_id,
            'target_move': session['target_move'],
            'duration_seconds': duration_seconds,
            'frames_processed': metrics['total_frames'],
            'average_accuracy': accuracy,
            'feedback_count': metrics['feedback_count'],
            'created_at': session['created_at'],
            'status': session['status'],
            'song_title': (session.get('scoring') or {}).get('song_title') or '',
            'mode': (session.get('scoring') or {}).get('mode') or '',
            'username': (session.get('scoring') or {}).get('username') or '',
            'scores': scores,
        }
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a Zumba session and return summary"""
        # Reuse the frozen summary if the session was already ended.
        existing = self.sessions.get(session_id, {}).get('final_summary')
        if existing:
            return existing

        summary = self.get_session_summary(session_id)
        summary['status'] = 'completed'

        if session_id in self.sessions:
            self.sessions[session_id]['status'] = 'completed'
            self.sessions[session_id]['final_summary'] = summary
        
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
