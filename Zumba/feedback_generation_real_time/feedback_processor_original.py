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
            #feedback = "!!!WARNING " + feedback + f" (off by {abs(diff):.0f}°)"
            feedback = "!!!WARNING : " + feedback 
        # Update variety index
        self.feedback_variety_index[joint_name] += 1
        
        return feedback


class GuidedZumbaAnalyzer:
    """Enhanced analyzer with better feedback and pacing"""
    
    def __init__(
        self,
        model_path: str = r"E:\Ai Data House Intern\nalla-maneendra-ai-full-stack-developer\Zumba\feedback_generation_real_time\yolo11x-pose.pt",
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

        # Load references
        self.reference_angles = {}
        self.angle_tolerances = {}
        self.load_references(reference_file)

        self.target_move = None
        print("✅  Ready – moves loaded:", list(self.reference_angles.keys()))

    def load_references(self, filename):
        dat = json.loads(Path(filename).read_text())
        self.reference_angles = dat["reference_angles"]
        self.angle_tolerances = dat["angle_tolerances"]

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
        for k in ang:
            hist = [h.get(k, ang[k]) for h in self.angle_history]
            w = np.linspace(0.3, 1.0, len(hist))
            smoothed[k] = round(np.average(hist, weights=w / w.sum()), 2)
        return smoothed

    def compare(self, user_angles):
        """Enhanced comparison with detailed feedback generation"""
        ref = self.reference_angles[self.target_move]
        tol = self.angle_tolerances[self.target_move]
        
        detailed_feedback = {}
        simple_bad_parts = []
        
        for joint_name, ref_val in ref.items():
            if joint_name not in user_angles:
                continue
                
            diff = abs(user_angles[joint_name] - ref_val)
            
            if diff > tol[joint_name]:
                # Generate detailed feedback
                feedback = self.feedback_manager.generate_feedback(
                    joint_name, 
                    user_angles[joint_name],
                    ref_val,
                    tol[joint_name]
                )
                
                if feedback:
                    detailed_feedback[joint_name] = {
                        "message": feedback,
                        "severity": "major" if diff > tol[joint_name] * 2 else "minor",
                        "diff": diff
                    }
                    
                    # Simple part name for display
                    simple_bad_parts.append(joint_name.replace("_", " ").title())
                    
                    # Track persistence
                    if joint_name not in self.issue_persistence:
                        self.issue_persistence[joint_name] = 0
                    self.issue_persistence[joint_name] += 1
            else:
                # Reset persistence if fixed
                if joint_name in self.issue_persistence:
                    self.issue_persistence[joint_name] = 0
        
        # Store current issues for intelligent feedback
        self.current_issues = detailed_feedback
        
        return simple_bad_parts

    def _maybe_feedback(self, bad_parts):
        """Enhanced feedback with better pacing and information"""
        now = time.time()
        
        if not bad_parts:
            # Clear issues if everything is good
            self.current_issues = {}
            self.issue_persistence = {}
            return
        
        # Check if enough time has passed for any feedback
        if now - self.last_feedback_ts < self.feedback_interval:
            return
        
        # Prioritize feedback based on severity and persistence
        priority_issues = []
        for joint, details in self.current_issues.items():
            persistence = self.issue_persistence.get(joint, 0)
            # Higher priority for persistent and severe issues
            priority = persistence * (2 if details["severity"] == "major" else 1)
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

        cap = cv2.VideoCapture(cam_id)
        if not cap.isOpened():
            print("❌  Cannot open camera")
            return

        print(f"\n🎯 Starting {target_move.replace('_', ' ').title()} practice")
        print("   Feedback will be paced for better learning")
        print("   Press ESC to stop\n")

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
                break

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

    def _add_feedback_to_list(self, message):
        """Add feedback message to display list with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%M:%S")
        self.feedback_message_list.append(f"[{timestamp}] {message}")

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
        
        cv2.putText(frame, "FEEDBACK HISTORY", 
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
                       0.5, color, thickness)

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
                if len(msg) > 60:
                    msg = msg[:57] + "..."
                
                cv2.putText(frame, msg, 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
        
        self._draw_feedback_list(frame)


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
            print(f"    ▸ Progress: {progress:.0f}% ({fnum}/{tot} frames)")
            
    cap.release()
    out.release()
    print("✅  Saved:", output_video)
    
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