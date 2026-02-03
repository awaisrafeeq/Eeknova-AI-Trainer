# feedback_processor.py - Video Processing with Feedback

import cv2, json, time
from collections import deque
from pathlib import Path
import numpy as np
from ultralytics import YOLO
import pyttsx3
import os
import subprocess
import shutil
from datetime import datetime


class FeedbackManager:
    """Manages informative feedback generation with proper pacing"""
    
    def __init__(self):
        # Detailed feedback templates for each body part
        self.feedback_templates = {
            "left_arm_angle": {
                "name": "left elbow",
                "increase": ["Bend your left elbow more - bring your hand closer to shoulder", 
                           "Left arm needs more bend at the elbow",
                           "Tighten your left elbow angle"],
                "decrease": ["Straighten your left arm a bit - extend elbow outward",
                           "Open up your left elbow angle",
                           "Left arm is too bent - extend it slightly"]
            },
            "right_arm_angle": {
                "name": "right elbow",
                "increase": ["Bend your right elbow more - bring hand toward shoulder",
                           "Right arm needs tighter angle at elbow",
                           "Pull your right hand closer by bending elbow"],
                "decrease": ["Extend your right arm - straighten the elbow",
                           "Right elbow too bent - open it up",
                           "Stretch your right arm out more"]
            },
            "left_shoulder_lift": {
                "name": "left shoulder",
                "increase": ["Raise your left arm higher from the shoulder",
                           "Lift left arm up - shoulder level or above",
                           "Left arm needs to come up higher"],
                "decrease": ["Lower your left arm - bring it down",
                           "Drop your left shoulder and arm",
                           "Left arm is too high - relax it down"]
            },
            "right_shoulder_lift": {
                "name": "right shoulder", 
                "increase": ["Lift your right arm up from shoulder",
                           "Right arm should be raised higher",
                           "Bring right arm up to shoulder height"],
                "decrease": ["Lower your right arm down",
                           "Right arm too high - drop it down",
                           "Relax your right shoulder downward"]
            },
            "left_leg_angle": {
                "name": "left knee",
                "increase": ["Bend your left knee more - lower into position",
                           "Left leg needs more bend at knee",
                           "Sink deeper on your left leg"],
                "decrease": ["Straighten your left leg - less knee bend",
                           "Left knee is too bent - stand taller",
                           "Extend your left leg more"]
            },
            "right_leg_angle": {
                "name": "right knee",
                "increase": ["Bend your right knee deeper",
                           "Right leg needs more flex at knee",
                           "Lower down on your right side"],
                "decrease": ["Straighten right leg - reduce knee bend",
                           "Right knee too bent - stand up more",
                           "Less bend in your right knee"]
            },
            "left_hip_flex": {
                "name": "left hip",
                "increase": ["Lean forward slightly from left hip",
                           "Tilt your torso forward on left side",
                           "Bring left hip forward more"],
                "decrease": ["Stand straighter on left side",
                           "Left hip leaning too far - straighten up",
                           "Pull your left hip back to neutral"]
            },
            "right_hip_flex": {
                "name": "right hip",
                "increase": ["Lean into your right hip forward",
                           "Tilt forward from right side",
                           "Push right hip forward slightly"],
                "decrease": ["Straighten up your right side",
                           "Right hip too forward - stand tall",
                           "Bring right hip back to center"]
            }
        }
        
        # Track last feedback to avoid repetition
        self.last_feedback = {}
        self.feedback_variety_index = {}
    
    def generate_feedback(self, joint_name, current_angle, target_angle, tolerance):
        """Generate informative, varied feedback messages"""
        
        if joint_name not in self.feedback_templates:
            # Fallback for joints not in templates
            return f"Adjust your {joint_name.replace('_', ' ')}"
        
        diff = current_angle - target_angle
        template = self.feedback_templates[joint_name]
        
        # Determine direction and severity
        if abs(diff) <= tolerance * 0.5:
            return None  # Very minor - no feedback needed
        
        severity = "minor" if abs(diff) <= tolerance * 1.5 else "major"
        direction = "increase" if diff < 0 else "decrease"
        
        # Get varied feedback
        feedback_options = template[direction]
        
        # Track variety index for this joint
        if joint_name not in self.feedback_variety_index:
            self.feedback_variety_index[joint_name] = 0
        
        # Select feedback with variety
        idx = self.feedback_variety_index[joint_name] % len(feedback_options)
        feedback = feedback_options[idx]
        
        # Add severity indicator for major issues
        if severity == "major":
            feedback = "!!!WARNING " + feedback + f" (off by {abs(diff):.0f}°)"
        
        # Update variety index
        self.feedback_variety_index[joint_name] += 1
        
        return feedback
    
    def generate_enhanced_feedback(self, joint_name, current_angle, target_angle, tolerance, characteristics, signature):
        """Generate enhanced feedback using movement characteristics and signatures"""
        
        if joint_name not in self.feedback_templates:
            return f"Adjust your {joint_name.replace('_', ' ')}"
        
        diff = current_angle - target_angle
        abs_diff = abs(diff)
        template = self.feedback_templates[joint_name]
        
        # Use characteristics for more intelligent feedback
        if characteristics:
            mean_val = characteristics.get('mean', target_angle)
            std_val = characteristics.get('std', tolerance/2)
            min_val = characteristics.get('min', target_angle - tolerance)
            max_val = characteristics.get('max', target_angle + tolerance)
            range_val = characteristics.get('range', tolerance * 2)
        
        # Pattern-based feedback adjustments
        pattern = signature.get('pattern', 'variable') if signature else 'variable'
        
        # Determine severity based on statistical data
        if characteristics and (current_angle < min_val or current_angle > max_val):
            severity = "extreme"
            severity_text = "!!!CRITICAL "
        elif abs_diff > tolerance * 2:
            severity = "major"
            severity_text = "!!!WARNING "
        elif abs_diff > tolerance:
            severity = "moderate"
            severity_text = "!ADJUST "
        else:
            severity = "minor"
            severity_text = ""
        
        # Direction
        direction = "increase" if diff < 0 else "decrease"
        
        # Get feedback options
        feedback_options = template[direction]
        
        # Track variety
        if joint_name not in self.feedback_variety_index:
            self.feedback_variety_index[joint_name] = 0
        
        idx = self.feedback_variety_index[joint_name] % len(feedback_options)
        base_feedback = feedback_options[idx]
        
        # Enhanced feedback with pattern information
        enhanced_feedback = severity_text + base_feedback
        
        # Add specific guidance based on pattern and severity
        if pattern == 'cyclic' and severity in ['major', 'extreme']:
            enhanced_feedback += " - focus on smooth rhythm"
        elif pattern == 'static' and severity in ['major', 'extreme']:
            enhanced_feedback += " - hold position steady"
        
        # Add quantitative feedback for major deviations
        if severity in ['major', 'extreme']:
            if characteristics:
                # Compare to historical range
                if current_angle < min_val:
                    enhanced_feedback += f" (too low by {min_val - current_angle:.0f}°)"
                elif current_angle > max_val:
                    enhanced_feedback += f" (too high by {current_angle - max_val:.0f}°)"
                else:
                    enhanced_feedback += f" (off by {abs_diff:.0f}°)"
            else:
                enhanced_feedback += f" (off by {abs_diff:.0f}°)"
        
        self.feedback_variety_index[joint_name] += 1
        
        return enhanced_feedback


class GuidedZumbaAnalyzer:
    """Enhanced analyzer with better feedback and pacing"""
    
    def __init__(
        self,
        model_path: str = "yolo11x-pose.pt",
        reference_file: str = r"E:\Ai Data House Intern\nalla-maneendra-ai-full-stack-developer\Zumba\feedback_generation_real_time\src\improved_automatic_references.json",
        smooth_window: int = 10,
        feedback_interval: float = 3.0,
        min_feedback_gap: float = 2.0,
    ):
        print("🤖  Initialising Enhanced Guided Zumba Analyzer...")

        self.pose_model = YOLO(model_path)
        
        # Feedback manager
        self.feedback_manager = FeedbackManager()
        
        # Enhanced voice settings for clearer, slower speech
        try:
            self.voice = pyttsx3.init()
            self.voice.setProperty("rate", 120)
            self.voice.setProperty("volume", 0.9)
            voices = self.voice.getProperty('voices')
            if len(voices) > 1:
                self.voice.setProperty('voice', voices[1].id)
            self.voice_enabled = True
        except Exception as e:
            print(f"⚠️  Voice engine not available: {e}")
            self.voice_enabled = False

        # COCO-17 indices
        self.kp = {
            "nose": 0, "left_eye": 1, "right_eye": 2, "left_ear": 3, "right_ear": 4,
            "left_shoulder": 5, "right_shoulder": 6, "left_elbow": 7, "right_elbow": 8,
            "left_wrist": 9, "right_wrist": 10, "left_hip": 11, "right_hip": 12,
            "left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16
        }

        # State tracking
        self.angle_history = deque(maxlen=smooth_window)
        self.feedback_interval = feedback_interval
        self.min_feedback_gap = min_feedback_gap
        self.last_feedback_ts = 0.0
        self.last_voice_ts = 0.0
        
        # Feedback queue for pacing
        self.feedback_queue = deque(maxlen=3)
        self.current_issues = {}
        self.issue_persistence = {}
        
        # Feedback message list for display (max 8 messages)
        self.feedback_message_list = deque(maxlen=8)
        
        # Performance tracking for enhanced mode
        self.performance_metrics = {
            "total_frames": 0,
            "good_frames": 0,
            "improvement_trend": []
        }

        # Load references
        self.reference_angles = {}
        self.angle_tolerances = {}
        self.move_characteristics = {}
        self.move_signatures = {}
        self.load_references(reference_file)

        self.target_move = None
        print("✅  Ready – moves loaded:", list(self.reference_angles.keys()))

    def load_references(self, filename):
        dat = json.loads(Path(filename).read_text())
        self.reference_angles = dat["reference_angles"]
        self.angle_tolerances = dat["angle_tolerances"]
        # Load additional characteristics for enhanced accuracy
        self.move_characteristics = dat.get("move_characteristics", {})
        self.move_signatures = dat.get("move_signatures", {})
        
        # Check if enhanced features are available
        if self.move_characteristics and self.move_signatures:
            total_joints_with_chars = sum(len(chars) for chars in self.move_characteristics.values())
            total_joints_with_sigs = sum(len(sigs) for sigs in self.move_signatures.values())
            print(f"   ✅ Loaded movement characteristics ({total_joints_with_chars} joints) and patterns ({total_joints_with_sigs} joints)")
        else:
            print("   ⚠️  No movement characteristics found - using basic feedback only")

    @staticmethod
    def _angle(a, b, c):
        a, b, c = np.array(a), np.array(b), np.array(c)
        ba, bc = a - b, c - b
        if not (np.linalg.norm(ba) and np.linalg.norm(bc)):
            return None
        cosang = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        return np.degrees(np.arccos(np.clip(cosang, -1.0, 1.0)))

    def _extract_angles(self, kps, conf=0.5):
        kd = {n: (np.array(kps[i][:2]), kps[i][2]) if kps[i][2] > conf else (None, 0)
              for n, i in self.kp.items()}

        def p(n): return kd[n][0]

        triples = {
            "left_arm_angle": ("left_shoulder", "left_elbow", "left_wrist"),
            "right_arm_angle": ("right_shoulder", "right_elbow", "right_wrist"),
            "left_leg_angle": ("left_hip", "left_knee", "left_ankle"),
            "right_leg_angle": ("right_hip", "right_knee", "right_ankle"),
            "left_shoulder_lift": ("left_elbow", "left_shoulder", "left_hip"),
            "right_shoulder_lift": ("right_elbow", "right_shoulder", "right_hip"),
            "left_hip_flex": ("left_shoulder", "left_hip", "left_knee"),
            "right_hip_flex": ("right_shoulder", "right_hip", "right_knee"),
        }
        
        ang = {}
        for name, (a, b, c) in triples.items():
            if all(p(x) is not None for x in (a, b, c)):
                val = self._angle(p(a), p(b), p(c))
                if val is not None:
                    ang[name] = round(val, 2)

        # Temporal smoothing
        self.angle_history.append(ang)
        smoothed = {}
        
        # Get movement signatures if available
        sigs = self.move_signatures.get(self.target_move, {}) if self.target_move else {}
        
        for k in ang:
            hist = [h.get(k, ang[k]) for h in self.angle_history]
            
            # Adjust smoothing based on movement pattern
            pattern = sigs.get(k, {}).get('pattern', 'variable') if k in sigs else 'variable'
            
            if pattern == 'static':
                # More smoothing for static positions
                w = np.linspace(0.2, 1.0, len(hist))
            elif pattern == 'cyclic':
                # Less smoothing for cyclic movements to preserve dynamics
                w = np.linspace(0.5, 1.0, len(hist))
            else:
                # Default smoothing
                w = np.linspace(0.3, 1.0, len(hist))
                
            smoothed[k] = round(np.average(hist, weights=w / w.sum()), 2)
        return smoothed

    def compare(self, user_angles):
        """Enhanced comparison with detailed feedback generation using all characteristics"""
        ref = self.reference_angles[self.target_move]
        tol = self.angle_tolerances[self.target_move]
        chars = self.move_characteristics.get(self.target_move, {})
        sigs = self.move_signatures.get(self.target_move, {})
        
        detailed_feedback = {}
        simple_bad_parts = []
        
        for joint_name, ref_val in ref.items():
            if joint_name not in user_angles:
                continue
            
            user_val = user_angles[joint_name]
            diff = abs(user_val - ref_val)
            
            # Get characteristics for this joint
            joint_chars = chars.get(joint_name, {})
            joint_sig = sigs.get(joint_name, {})
            
            # Enhanced tolerance calculation using characteristics
            if joint_chars:
                # Use statistical data for more intelligent tolerance
                std_dev = joint_chars.get('std', 0)
                min_val = joint_chars.get('min', ref_val - tol[joint_name])
                max_val = joint_chars.get('max', ref_val + tol[joint_name])
                pattern = joint_sig.get('pattern', 'variable')
                
                # Adjust tolerance based on pattern type
                if pattern == 'cyclic':
                    # More lenient for cyclic movements
                    effective_tolerance = max(tol[joint_name], std_dev * 2.5)
                elif pattern == 'static':
                    # Stricter for static positions
                    effective_tolerance = min(tol[joint_name], std_dev * 1.5)
                else:  # variable
                    effective_tolerance = tol[joint_name]
                
                # Check if user is within the historical min/max range
                if user_val < min_val or user_val > max_val:
                    # User is outside historical range - major issue
                    severity = "major"
                elif diff > effective_tolerance:
                    # User is outside tolerance but within historical range
                    severity = "moderate"
                else:
                    # User is within tolerance
                    continue
            else:
                # Fallback to original logic if no characteristics
                effective_tolerance = tol[joint_name]
                if diff <= effective_tolerance:
                    continue
                severity = "major" if diff > effective_tolerance * 2 else "minor"
            
            # Generate enhanced feedback using all available data
            feedback = self.feedback_manager.generate_enhanced_feedback(
                joint_name, 
                user_val,
                ref_val,
                effective_tolerance,
                joint_chars,
                joint_sig
            )
            
            if feedback:
                detailed_feedback[joint_name] = {
                    "message": feedback,
                    "severity": severity,
                    "diff": diff,
                    "pattern": joint_sig.get('pattern', 'unknown')
                }
                
                # Simple part name for display
                simple_bad_parts.append(joint_name.replace("_", " ").title())
                
                # Track persistence
                if joint_name not in self.issue_persistence:
                    self.issue_persistence[joint_name] = 0
                self.issue_persistence[joint_name] += 1
        
        # Reset persistence for joints that are now correct
        # This ensures we properly track when issues are resolved
        for joint_name in list(self.issue_persistence.keys()):
            if joint_name not in detailed_feedback:
                del self.issue_persistence[joint_name]
        
        # Store current issues for intelligent feedback
        self.current_issues = detailed_feedback
        
        # Update performance metrics if enhanced features are available
        if self.move_characteristics.get(self.target_move):
            self.performance_metrics["total_frames"] += 1
            if not detailed_feedback:  # No issues means good frame
                self.performance_metrics["good_frames"] += 1
            
            # Calculate rolling accuracy
            if self.performance_metrics["total_frames"] > 0:
                current_accuracy = (self.performance_metrics["good_frames"] / 
                                  self.performance_metrics["total_frames"]) * 100
                self.performance_metrics["improvement_trend"].append(current_accuracy)
                # Keep only last 100 frames for trend
                if len(self.performance_metrics["improvement_trend"]) > 100:
                    self.performance_metrics["improvement_trend"].pop(0)
        
        return simple_bad_parts

    def _maybe_feedback(self, bad_parts):
        """Enhanced feedback with better pacing and pattern-aware prioritization"""
        now = time.time()
        
        if not bad_parts:
            # Clear issues if everything is good
            self.current_issues = {}
            self.issue_persistence = {}
            return
        
        # Check if enough time has passed for any feedback
        if now - self.last_feedback_ts < self.feedback_interval:
            return
        
        # Prioritize feedback based on severity, persistence, and pattern
        priority_issues = []
        for joint, details in self.current_issues.items():
            persistence = self.issue_persistence.get(joint, 0)
            pattern = details.get('pattern', 'variable')
            
            # Calculate priority score
            severity_score = {"extreme": 4, "major": 3, "moderate": 2, "minor": 1}.get(details["severity"], 1)
            
            # Pattern-based priority adjustment
            if pattern == 'static':
                # Static positions are more critical - boost priority
                pattern_multiplier = 1.5
            elif pattern == 'cyclic':
                # Cyclic movements have more natural variation
                pattern_multiplier = 0.8
            else:
                pattern_multiplier = 1.0
            
            # Combined priority score
            priority = persistence * severity_score * pattern_multiplier
            priority_issues.append((priority, joint, details))
        
        # Sort by priority
        priority_issues.sort(reverse=True, key=lambda x: x[0])
        
        # Select top issue for voice feedback
        if priority_issues and now - self.last_voice_ts >= self.min_feedback_gap:
            top_priority = priority_issues[0]
            joint_name = top_priority[1]
            details = top_priority[2]
            
            msg = details["message"]
            print(f"💬 {msg}")
            
            # Add to feedback list for display
            self._add_feedback_to_list(msg)
            
            if self.voice_enabled:
                # Add a pause before speaking for natural pacing
                self.voice.say(msg)
                self.voice.runAndWait()
            
            self.last_voice_ts = now
            self.last_feedback_ts = now

    def guide_live(self, target_move, cam_id=0):
        """Live guidance with enhanced feedback"""
        if target_move not in self.reference_angles:
            raise KeyError(f"{target_move} not in ground-truth file")
        self.target_move = target_move

        # Check if enhanced features are available
        has_chars = bool(self.move_characteristics.get(target_move))
        has_sigs = bool(self.move_signatures.get(target_move))
        
        print(f"\n🎯 Starting {target_move.replace('_', ' ').title()} practice")
        if has_chars and has_sigs:
            print("   ✨ Enhanced mode: Using movement patterns and characteristics")
            # Show key movement patterns
            move_sigs = self.move_signatures.get(target_move, {})
            patterns = {}
            for joint, sig in move_sigs.items():
                pattern = sig.get('pattern', 'unknown')
                if pattern not in patterns:
                    patterns[pattern] = []
                patterns[pattern].append(joint.replace('_', ' '))
            
            if patterns:
                print("   📋 Movement patterns:")
                for pattern, joints in patterns.items():
                    if pattern == 'cyclic':
                        print(f"      🔄 Cyclic (rhythmic): {', '.join(joints[:3])}")
                    elif pattern == 'static':
                        print(f"      ⏸️  Static (hold steady): {', '.join(joints[:3])}")
                    elif pattern == 'variable':
                        print(f"      〰️  Variable: {', '.join(joints[:3])}")
        print("   Feedback will be paced for better learning")
        print("   Press ESC to stop\n")

        # Reset performance metrics for new session
        self.performance_metrics = {
            "total_frames": 0,
            "good_frames": 0,
            "improvement_trend": []
        }
        self.issue_persistence = {}  # Reset persistence tracking
        self.current_issues = {}      # Reset current issues
        
        cap = cv2.VideoCapture(cam_id)
        if not cap.isOpened():
            print("❌  Cannot open camera")
            return

        frame_count = 0
        
        while True:
            ok, frm = cap.read()
            if not ok: break
            frm = cv2.flip(frm, 1)
            frame_count += 1

            res = self.pose_model(frm, verbose=False)
            if res and res[0].keypoints is not None:
                kps = res[0].keypoints.data[0].cpu().numpy()
                ang = self._extract_angles(kps)
                bad = self.compare(ang)
                
                # Provide feedback at controlled pace
                if frame_count % 30 == 0:
                    self._maybe_feedback(bad)

        # Enhanced overlay display with skeleton
        self._draw_enhanced_overlay(frm, bad, kps)

        cv2.imshow("Guided Zumba Analyzer", frm)
        if cv2.waitKey(1) & 0xFF == 27:
            # Show performance summary if characteristics are available
            if self.move_characteristics.get(self.target_move):
                self._show_performance_summary()
                

            cap.release()
            cv2.destroyAllWindows()
            return True  # Return True to indicate successful completion

    def _draw_skeleton(self, frame, keypoints, conf_threshold=0.5):
        """Draw skeleton on frame"""
        skeleton_connections = [
            # Head
            (0, 1), (0, 2), (1, 3), (2, 4),
            # Arms
            (5, 6),
            (5, 7), (7, 9),
            (6, 8), (8, 10),
            # Torso
            (5, 11), (6, 12), (11, 12),
            # Legs
            (11, 13), (13, 15),
            (12, 14), (14, 16)
        ]
        
        # Draw skeleton connections
        for connection in skeleton_connections:
            kp1_idx, kp2_idx = connection
            
            if (keypoints[kp1_idx][2] > conf_threshold and 
                keypoints[kp2_idx][2] > conf_threshold):
                
                x1, y1 = int(keypoints[kp1_idx][0]), int(keypoints[kp1_idx][1])
                x2, y2 = int(keypoints[kp2_idx][0]), int(keypoints[kp2_idx][1])
                
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw keypoints
        for i, (x, y, conf) in enumerate(keypoints):
            if conf > conf_threshold:
                x, y = int(x), int(y)
                if i < 5:
                    color = (255, 255, 0)
                elif i < 11:
                    color = (255, 0, 255)
                else:
                    color = (0, 255, 255)
                
                cv2.circle(frame, (x, y), 4, color, -1)
                cv2.circle(frame, (x, y), 6, (0, 0, 0), 1)

    '''def _add_feedback_to_list(self, message):
        """Add feedback message to display list with timestamp and pattern indicator"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%M:%S")
        
        # Extract pattern indicator from message if present
        if "🔄" in message:
            pattern_indicator = " [C]"  # Cyclic
        elif "⏸️" in message:
            pattern_indicator = " [S]"  # Static
        else:
            pattern_indicator = ""
        
        # Remove emoji from message for cleaner display
        clean_message = message.replace("🔄", "").replace("⏸️", "").strip()
        
        self.feedback_message_list.append(f"[{timestamp}]{pattern_indicator} {clean_message}")

    def _draw_feedback_list(self, frame):
        """Draw the list of feedback messages on frame"""
        if not self.feedback_message_list:
            return
        
        x_start = frame.shape[1] - 650
        y_start = 140
        line_height = 25
        
        overlay = frame.copy()
        list_height = min(len(self.feedback_message_list), 8) * line_height + 20
        cv2.rectangle(overlay, (x_start - 10, y_start - 10), 
                     (frame.shape[1] - 10, y_start + list_height), 
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        cv2.putText(frame, "FEEDBACK HISTORY [C=Cyclic S=Static]", 
                   (x_start, y_start), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (255, 255, 255), 2)
        
        for i, msg in enumerate(self.feedback_message_list):
            y_pos = y_start + 30 + (i * line_height)
            
            if i == len(self.feedback_message_list) - 1:
                color = (0, 255, 255)
                thickness = 2
            else:
                color = (0, 200, 200)
                thickness = 1
            
            cv2.putText(frame, msg, 
                       (x_start, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, color, thickness)'''
    def _add_feedback_to_list(self, message):
        """Add feedback message to display list with timestamp and pattern indicator, keeping only the last 5 messages"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%M:%S")
        
        # Extract pattern indicator from message if present
        if "🔄" in message:
            pattern_indicator = " [C]"  # Cyclic
        elif "⏸️" in message:
            pattern_indicator = " [S]"  # Static
        else:
            pattern_indicator = ""
        
        # Remove emoji from message for cleaner display
        clean_message = message.replace("🔄", "").replace("⏸️", "").strip()
        
        # Append to feedback_message_list (deque with maxlen=5)
        self.feedback_message_list.append(f"[{timestamp}]{pattern_indicator} {clean_message}")

    def _draw_feedback_list(self, frame):
        """Draw the list of feedback messages on frame with text wrapping"""
        if not self.feedback_message_list:
            return
        
        # Frame dimensions
        frame_width = frame.shape[1]
        x_start = max(10, frame_width - 650)  # Adjust for narrow frames
        y_start = 140
        line_height = 30  # Increased for larger text
        max_width = frame_width - x_start - 20  # Available width for text
        
        # Draw semi-transparent background
        overlay = frame.copy()
        list_height = min(len(self.feedback_message_list), 8) * line_height * 2 + 20  # Account for wrapping
        cv2.rectangle(overlay, (x_start - 10, y_start - 10), 
                    (frame_width - 10, y_start + list_height), 
                    (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Draw header with larger, darker text
        header = "FEEDBACK HISTORY [C=Cyclic S=Static]"
        cv2.putText(frame, header, 
                    (x_start, y_start), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, (0, 0, 50), 2, cv2.LINE_AA)  # Darker color, larger font
        
        # Process each feedback message
        y_pos = y_start + 40
        font_scale = 0.7  # Larger font for feedback
        for i, msg in enumerate(self.feedback_message_list):
            # Select color and thickness
            color = (0, 0, 100) if i == len(self.feedback_message_list) - 1 else (50, 50, 50)  # Darker colors
            thickness = 2 if i == len(self.feedback_message_list) - 1 else 1
            
            # Split long message into words
            words = msg.split()
            current_line = ""
            lines = []
            
            # Measure and wrap text
            for word in words:
                test_line = current_line + word + " "
                (text_width, _), _ = cv2.getTextSize(test_line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                if text_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())
            
            # Draw each line
            for line in lines:
                cv2.putText(frame, line, 
                            (x_start, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                            font_scale, color, thickness, cv2.LINE_AA)
                y_pos += line_height
        
        # Ensure y_pos doesn't exceed frame height
        if y_pos > frame.shape[0] - 20:
            print("Warning: Feedback text exceeds frame height")

    def _draw_enhanced_overlay(self, frame, bad_parts, keypoints=None):
        """Draw more informative overlay with skeleton and feedback list"""
        h, w = frame.shape[:2]
        
        if keypoints is not None:
            self._draw_skeleton(frame, keypoints)
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        cv2.putText(frame, f"{self.target_move.replace('_', ' ').title()}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        # Show real-time accuracy if enhanced features are available
        if (self.move_characteristics.get(self.target_move) and 
            self.performance_metrics["total_frames"] > 0):
            accuracy = (self.performance_metrics["good_frames"] / 
                    self.performance_metrics["total_frames"]) * 100
            acc_color = (0, 255, 0) if accuracy >= 80 else (0, 165, 255) if accuracy >= 60 else (0, 0, 255)
            #cv2.putText(frame, f"Accuracy: {accuracy:.0f}%", 
            #           (w - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, acc_color, 2)
        
        if not bad_parts:
            cv2.putText(frame, " Excellent form! Keep it up!", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, f"Issues: {len(bad_parts)} corrections needed", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            
            if self.current_issues:
                top_issue = max(self.current_issues.items(), 
                            key=lambda x: self.issue_persistence.get(x[0], 0))
                
                msg = top_issue[1]["message"]
                pattern = top_issue[1].get("pattern", "")
                
                # Add pattern hint to display
                if pattern == "cyclic":
                    msg += " 🔄"  # Indicate cyclic movement
                elif pattern == "static":
                    msg += " ⏸️"  # Indicate static hold
                
                font_scale = 0.6
                thickness = 2
                color = (0, 100, 255)
                x_start = 10
                y_start = 90
                line_height = 25
                max_width = w - x_start - 20  # Available width for text
                
                # Split message into words for wrapping
                words = msg.split()
                current_line = ""
                lines = []
                
                # Measure and wrap text
                for word in words:
                    test_line = current_line + word + " "
                    (text_width, _), _ = cv2.getTextSize(test_line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                    if text_width <= max_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    lines.append(current_line.strip())
                
                # Draw each line
                for i, line in enumerate(lines):
                    y_pos = y_start + (i * line_height)
                    cv2.putText(frame, line, 
                                (x_start, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                                font_scale, color, thickness)
        
        self._draw_feedback_list(frame)
    
    def _show_performance_summary(self):
        """Show performance summary compared to historical data"""
        print("\n" + "="*60)
        print("📊 PERFORMANCE SUMMARY")
        print("="*60)
        
        if not self.current_issues:
            print("✨ Excellent! Your form matches the expert reference perfectly!")
        else:
            print(f"🎯 Areas that needed correction:")
            for joint, details in self.current_issues.items():
                pattern = details.get('pattern', 'unknown')
                severity = details['severity']
                print(f"   - {joint.replace('_', ' ').title()}: {severity} ({pattern} movement)")
        
        # Show persistence stats
        if self.issue_persistence:
            print(f"\n📈 Most persistent issues:")
            sorted_issues = sorted(self.issue_persistence.items(), 
                                 key=lambda x: x[1], reverse=True)[:3]
            for joint, count in sorted_issues:
                print(f"   - {joint.replace('_', ' ').title()}: needed {count} corrections")
        
        # Show accuracy trend if available
        if self.performance_metrics["total_frames"] > 0:
            final_accuracy = (self.performance_metrics["good_frames"] / 
                            self.performance_metrics["total_frames"]) * 100
            #print(f"\n🎯 Overall Accuracy: {final_accuracy:.1f}%")
            
            # Show improvement
            if len(self.performance_metrics["improvement_trend"]) > 10:
                early_avg = np.mean(self.performance_metrics["improvement_trend"][:10])
                recent_avg = np.mean(self.performance_metrics["improvement_trend"][-10:])
                improvement = recent_avg - early_avg
                
                if improvement > 5:
                    print(f"📈 Great improvement! +{improvement:.1f}% from start to finish")
                elif improvement > 0:
                    print(f"📊 Slight improvement: +{improvement:.1f}%")
                else:
                    print(f"💪 Keep practicing for better results")
        
        print("="*60)


def process_with_feedback(input_video: str, target_move: str, output_video: str | None = None, include_audio: bool = True):
    """Process video with feedback (supports both video file and real-time camera)"""
    
    # Check if input is camera
    is_camera = input_video.lower() in ['camera', 'cam', '0', '1', '2']
    
    if not is_camera and not os.path.exists(input_video):
        print("❌  Video not found")
        return None
        
    analyzer = GuidedZumbaAnalyzer(
        feedback_interval=3.0,
        min_feedback_gap=2.0
    )
    
    if target_move not in analyzer.reference_angles:
        print(f"❌  Unknown move '{target_move}'")
        return None
    
    # Check if enhanced characteristics are available
    has_characteristics = bool(analyzer.move_characteristics.get(target_move))
    has_signatures = bool(analyzer.move_signatures.get(target_move))
    
    if has_characteristics and has_signatures:
        print("✨ Using enhanced feedback with movement characteristics and patterns")
    else:
        print("📊 Using basic feedback (no movement characteristics available)")
    
    # Handle real-time camera input
    if is_camera:
        print("🎥 Starting real-time camera processing...")
        # Parse camera ID
        cam_id = 0  # Default camera
        if input_video.isdigit():
            cam_id = int(input_video)
        
        # Run live guidance
        result = analyzer.guide_live(target_move, cam_id)
        return "Real-time session completed" if result else None
    
    # Handle video file processing (existing code)
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print("❌  Cannot open input video")
        return None
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if output_video is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.splitext(os.path.basename(input_video))[0]
        output_video = f"output/{base}_{target_move}_{ts}.mp4"
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_video) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    # Try mp4v codec first, fallback to XVID
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video, fourcc, fps, (W, H))
    
    if not out.isOpened():
        print("⚠️  mp4v codec failed, trying XVID...")
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        output_video = output_video.replace(".mp4", ".avi")
        out = cv2.VideoWriter(output_video, fourcc, fps, (W, H))
        
        if not out.isOpened():
            print(f"❌  VideoWriter failure")
            cap.release()
            return None
        
    print(f"🎬  Processing {tot} frames...")
    print(f"    Move: {target_move.replace('_', ' ').title()}")
    print(f"    Feedback interval: every {analyzer.feedback_interval}s")
    
    # Check and display if enhanced features are being used
    if analyzer.move_characteristics.get(target_move) and analyzer.move_signatures.get(target_move):
        print(f"    ✨ Using enhanced feedback with movement patterns")
        
        # Count pattern types
        patterns = {}
        for joint, sig in analyzer.move_signatures[target_move].items():
            pattern = sig.get('pattern', 'unknown')
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        if patterns:
            print(f"    📊 Movement composition: ", end="")
            pattern_strs = []
            for p, count in patterns.items():
                if p == 'cyclic':
                    pattern_strs.append(f"{count} cyclic")
                elif p == 'static':
                    pattern_strs.append(f"{count} static")
                elif p == 'variable':
                    pattern_strs.append(f"{count} variable")
            print(", ".join(pattern_strs))
    
    analyzer.target_move = target_move
    every = max(1, int(fps * analyzer.feedback_interval))
    
    last_bad = []
    
    for fnum in range(tot):
        ok, frm = cap.read()
        if not ok: 
            break
            
        res = analyzer.pose_model(frm, verbose=False)
        if res and res[0].keypoints is not None:
            kps = res[0].keypoints.data[0].cpu().numpy()
            
            ang = analyzer._extract_angles(kps)
            if fnum % every == 0:
                last_bad = analyzer.compare(ang)
                if analyzer.current_issues:
                    top_issue = max(analyzer.current_issues.items(), 
                                  key=lambda x: analyzer.issue_persistence.get(x[0], 0))
                    analyzer._add_feedback_to_list(top_issue[1]["message"])
            analyzer._draw_enhanced_overlay(frm, last_bad, kps)
                
        out.write(frm)
        
        if fnum and fnum % max(1, tot // 20) == 0:
            progress = (100 * fnum / tot)
            if analyzer.performance_metrics["total_frames"] > 0:
                current_acc = (analyzer.performance_metrics["good_frames"] / 
                             analyzer.performance_metrics["total_frames"]) * 100
                print(f"    ▸ Progress: {progress:.0f}% ({fnum}/{tot} frames) ")
            else:
                print(f"    ▸ Progress: {progress:.0f}% ({fnum}/{tot} frames)")
            
    cap.release()
    out.release()
    print("✅  Saved:", output_video)
    
    # Show performance summary if enhanced features were used
    if analyzer.move_characteristics.get(target_move) and analyzer.performance_metrics["total_frames"] > 0:
        analyzer._show_performance_summary()
    
    if include_audio and shutil.which("ffmpeg"):
        final = os.path.splitext(output_video)[0] + "_audio" + os.path.splitext(output_video)[1]
        cmd = [
            "ffmpeg", "-y",
            "-i", output_video, "-i", input_video,
            "-c:v", "copy", "-c:a", "aac",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", final
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            output_video = final
            print("🔊  Audio merged →", output_video)
        else:
            print(f"⚠️  Audio muxing failed: {result.stderr.decode()}")
            
    return output_video