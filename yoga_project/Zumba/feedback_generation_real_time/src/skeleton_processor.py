# skeleton_processor.py - Video Processing with Skeleton Only (No Feedback)

import cv2
import numpy as np
from ultralytics import YOLO
import os
import subprocess
import shutil
from datetime import datetime


class ZumbaAnalyzer:
    """Simplified analyzer for generating skeleton-only video"""
    
    def __init__(self, model_path: str = "yolo11x-pose.pt"):
        print("🤖 Initialising Zumba Analyzer for skeleton tracking...")
        self.pose_model = YOLO(model_path)
        
        # COCO-17 indices for skeleton drawing
        self.kp = {
            "nose": 0, "left_eye": 1, "right_eye": 2, "left_ear": 3, "right_ear": 4,
            "left_shoulder": 5, "right_shoulder": 6, "left_elbow": 7, "right_elbow": 8,
            "left_wrist": 9, "right_wrist": 10, "left_hip": 11, "right_hip": 12,
            "left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16
        }
        
        print("✅ Ready – skeleton tracking initialized")

    def _draw_skeleton(self, frame, keypoints, conf_threshold=0.5):
        """Draw skeleton on frame (copied from GuidedZumbaAnalyzer)"""
        skeleton_connections = [
            # Head
            (0, 1), (0, 2), (1, 3), (2, 4),  # nose to eyes, eyes to ears
            # Arms
            (5, 6),   # shoulders
            (5, 7), (7, 9),   # left arm
            (6, 8), (8, 10),  # right arm
            # Torso
            (5, 11), (6, 12), (11, 12),  # shoulders to hips
            # Legs
            (11, 13), (13, 15),  # left leg
            (12, 14), (14, 16)   # right leg
        ]
        
        # Draw skeleton connections
        for connection in skeleton_connections:
            kp1_idx, kp2_idx = connection
            
            # Check if both keypoints are valid
            if (keypoints[kp1_idx][2] > conf_threshold and 
                keypoints[kp2_idx][2] > conf_threshold):
                
                # Get coordinates
                x1, y1 = int(keypoints[kp1_idx][0]), int(keypoints[kp1_idx][1])
                x2, y2 = int(keypoints[kp2_idx][0]), int(keypoints[kp2_idx][1])
                
                # Draw line
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw keypoints
        for i, (x, y, conf) in enumerate(keypoints):
            if conf > conf_threshold:
                x, y = int(x), int(y)
                # Different colors for different body parts
                if i < 5:  # Head
                    color = (255, 255, 0)  # Cyan
                elif i < 11:  # Arms
                    color = (255, 0, 255)  # Magenta
                else:  # Legs
                    color = (0, 255, 255)  # Yellow
                
                cv2.circle(frame, (x, y), 4, color, -1)
                cv2.circle(frame, (x, y), 6, (0, 0, 0), 1)  # Black outline

    def track_live(self, cam_id=0):
        """Live skeleton tracking without feedback"""
        cap = cv2.VideoCapture(cam_id)
        if not cap.isOpened():
            print("❌  Cannot open camera")
            return False

        print("\n🎥 Starting real-time skeleton tracking")
        print("   Press ESC to stop\n")
        
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            
            frame = cv2.flip(frame, 1)  # Mirror the frame
            
            # Run pose detection
            results = self.pose_model(frame, verbose=False)
            if results and results[0].keypoints is not None:
                keypoints = results[0].keypoints.data[0].cpu().numpy()
                self._draw_skeleton(frame, keypoints)
            
            cv2.imshow("Skeleton Tracking", frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return True


def process_skeleton_only(input_video: str, output_video: str | None = None, include_audio: bool = True):
    """Process video with skeleton only (supports both video file and real-time camera)"""
    
    # Check if input is camera
    is_camera = input_video.lower() in ['camera', 'cam', '0', '1', '2']
    
    if not is_camera and not os.path.exists(input_video):
        print("❌  Video not found")
        return None
        
    analyzer = ZumbaAnalyzer()
    
    # Handle real-time camera input
    if is_camera:
        print("🎥 Starting real-time skeleton tracking...")
        # Parse camera ID
        cam_id = 0  # Default camera
        if input_video.isdigit():
            cam_id = int(input_video)
        
        # Run live tracking
        result = analyzer.track_live(cam_id)
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
        output_video = f"output/{base}_skeleton_{ts}.mp4"
    
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
    print("    Generating video with skeleton only")
    
    for fnum in range(tot):
        ok, frm = cap.read()
        if not ok: 
            break
            
        res = analyzer.pose_model(frm, verbose=False)
        if res and res[0].keypoints is not None:
            kps = res[0].keypoints.data[0].cpu().numpy()
            analyzer._draw_skeleton(frm, kps)
                
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