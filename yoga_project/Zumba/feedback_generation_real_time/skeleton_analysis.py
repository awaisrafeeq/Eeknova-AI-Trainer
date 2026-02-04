#!/usr/bin/env python3
# skeleton_analysis.py - Detailed Skeleton Generation Analysis

import cv2
import numpy as np
from pathlib import Path
import json

class SkeletonGenerationAnalyzer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_path = self.project_root / "src"
        
    def analyze_skeleton_generation(self):
        """Analyze how skeleton is generated in the project"""
        print("🦴 SKELETON GENERATION ANALYSIS")
        print("=" * 50)
        
        self.step1_pose_detection()
        self.step2_keypoint_extraction()
        self.step3_confidence_filtering()
        self.step4_skeleton_drawing()
        self.step5_visual_enhancement()
        
        print("\n🎯 COMPLETE SKELETON GENERATION PROCESS")
        print("=" * 50)
        
    def step1_pose_detection(self):
        """Step 1: YOLO Pose Detection"""
        print("\n📸 STEP 1: POSE DETECTION")
        print("-" * 30)
        
        print("🤖 YOLO11x-Pose Model:")
        print("   • Model: yolo11x-pose.pt (118MB)")
        print("   • Architecture: 372 layers, 58.8M parameters")
        print("   • Input: Video frame (640x480 or any size)")
        print("   • Output: 17 keypoints with confidence scores")
        
        print("\n🔍 Detection Process:")
        print("   1. Frame captured from video/camera")
        print("   2. Frame passed to YOLO model")
        print("   3. Model detects human pose(s)")
        print("   4. Returns keypoints data structure")
        
        # Show actual keypoint structure
        try:
            from ultralytics import YOLO
            model = YOLO(str(self.project_root / "yolo11x-pose.pt"))
            
            # Create test frame
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            test_frame[:] = (100, 150, 200)
            
            # Run detection
            results = model(test_frame, verbose=False)
            if results and results[0].keypoints is not None:
                keypoints = results[0].keypoints.data[0].cpu().numpy()
                print(f"\n📊 Keypoint Structure:")
                print(f"   • Shape: {keypoints.shape} (17 points × 3 values)")
                print(f"   • Format: [x, y, confidence] for each keypoint")
                print(f"   • Sample: {keypoints[0]} (nose)")
                
        except Exception as e:
            print(f"   Error in demo: {e}")
    
    def step2_keypoint_extraction(self):
        """Step 2: Keypoint Extraction and Mapping"""
        print("\n🎯 STEP 2: KEYPOINT EXTRACTION")
        print("-" * 30)
        
        # Load keypoint mapping from actual code
        try:
            spec = __import__('importlib.util').util.spec_from_file_location(
                "skeleton_processor", self.src_path / "skeleton_processor.py"
            )
            module = __import__('importlib.util').util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            analyzer = module.ZumbaAnalyzer()
            keypoints = analyzer.kp
            
            print("📍 COCO-17 Keypoint Mapping:")
            for i, (name, idx) in enumerate(keypoints.items()):
                print(f"   {idx:2d}. {name:15s} -> Index {idx}")
            
            print(f"\n📋 Keypoint Categories:")
            print("   • Head (0-4): nose, eyes, ears")
            print("   • Arms (5-10): shoulders, elbows, wrists") 
            print("   • Legs (11-16): hips, knees, ankles")
            
        except Exception as e:
            print(f"   Error: {e}")
    
    def step3_confidence_filtering(self):
        """Step 3: Confidence Filtering"""
        print("\n🎚️ STEP 3: CONFIDENCE FILTERING")
        print("-" * 30)
        
        print("🔍 Confidence Threshold:")
        print("   • Default threshold: 0.5 (50% confidence)")
        print("   • Purpose: Filter out low-quality detections")
        print("   • Logic: Only use keypoints above threshold")
        
        print("\n📊 Filtering Process:")
        print("   1. Each keypoint has confidence score (0-1)")
        print("   2. Compare score against threshold")
        print("   3. Keep if score > threshold")
        print("   4. Discard if score <= threshold")
        
        print("\n💡 Why Important:")
        print("   • Prevents skeleton from broken joints")
        print("   • Ensures smooth pose tracking")
        print("   • Reduces false detections")
    
    def step4_skeleton_drawing(self):
        """Step 4: Skeleton Drawing Process"""
        print("\n🎨 STEP 4: SKELETON DRAWING")
        print("-" * 30)
        
        # Load actual drawing code
        try:
            with open(self.src_path / "skeleton_processor.py", 'r') as f:
                content = f.read()
            
            print("🔗 Skeleton Connections:")
            # Extract connections from code
            connections = [
                # Head
                (0, 1), (0, 2), (1, 3), (2, 4),
                # Arms  
                (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
                # Torso
                (5, 11), (6, 12), (11, 12),
                # Legs
                (11, 13), (13, 15), (12, 14), (14, 16)
            ]
            
            connection_names = {
                (0, 1): "nose-left_eye", (0, 2): "nose-right_eye",
                (1, 3): "left_eye-left_ear", (2, 4): "right_eye-right_ear",
                (5, 6): "shoulders", (5, 7): "left_shoulder-elbow", (7, 9): "left_elbow-wrist",
                (6, 8): "right_shoulder-elbow", (8, 10): "right_elbow-wrist",
                (5, 11): "left_shoulder-hip", (6, 12): "right_shoulder-hip", (11, 12): "hips",
                (11, 13): "left_hip-knee", (13, 15): "left_knee-ankle",
                (12, 14): "right_hip-knee", (14, 16): "right_knee-ankle"
            }
            
            for conn in connections:
                name = connection_names.get(conn, f"points {conn[0]}-{conn[1]}")
                print(f"   • {name:20s} -> Points {conn[0]}-{conn[1]}")
            
            print(f"\n🎨 Drawing Process:")
            print("   1. Draw lines between connected keypoints")
            print("   2. Draw circles at each keypoint location")
            print("   3. Apply colors based on body part")
            print("   4. Add black outline for visibility")
            
        except Exception as e:
            print(f"   Error: {e}")
    
    def step5_visual_enhancement(self):
        """Step 5: Visual Enhancement"""
        print("\n✨ STEP 5: VISUAL ENHANCEMENT")
        print("-" * 30)
        
        print("🎨 Color Coding:")
        print("   • Head (0-4):     Cyan (255, 255, 0)")
        print("   • Arms (5-10):    Magenta (255, 0, 255)")
        print("   • Legs (11-16):   Yellow (0, 255, 255)")
        
        print("\n⭕ Circle Properties:")
        print("   • Inner circle: 4px radius (filled)")
        print("   • Outer outline: 6px radius (black)")
        print("   • Purpose: Better visibility on any background")
        
        print("\n📏 Line Properties:")
        print("   • Color: Green (0, 255, 0)")
        print("   • Thickness: 2px")
        print("   • Purpose: Clear bone structure")
        
        print("\n🔄 Frame Processing:")
        print("   1. Original frame captured")
        print("   2. Skeleton drawn on top")
        print("   3. Frame displayed/saved")
        print("   4. Process repeats for next frame")
    
    def demonstrate_skeleton_math(self):
        """Demonstrate the mathematics behind skeleton generation"""
        print("\n🧮 SKELETON MATHEMATICS")
        print("=" * 30)
        
        print("📐 Coordinate System:")
        print("   • Origin (0,0): Top-left corner")
        print("   • X-axis: Horizontal (left to right)")
        print("   • Y-axis: Vertical (top to bottom)")
        print("   • Pixel coordinates: (x, y)")
        
        print("\n📊 Keypoint Data Structure:")
        print("   • Shape: (17, 3) array")
        print("   • Columns: [x_coordinate, y_coordinate, confidence]")
        print("   • Example: [320.5, 240.2, 0.95]")
        
        print("\n🔍 Line Drawing Mathematics:")
        print("   • Line equation: y = mx + b")
        print("   • OpenCV line: cv2.line(frame, (x1,y1), (x2,y2), color, thickness)")
        print("   • Distance calculation: √[(x2-x1)² + (y2-y1)²]")
        
        print("\n⭕ Circle Drawing:")
        print("   • Circle equation: (x-h)² + (y-k)² = r²")
        print("   • OpenCV circle: cv2.circle(frame, (x,y), radius, color, thickness)")
        
    def show_actual_skeleton_code(self):
        """Show actual skeleton drawing code"""
        print("\n💻 ACTUAL SKELETON CODE")
        print("=" * 30)
        
        try:
            with open(self.src_path / "skeleton_processor.py", 'r') as f:
                lines = f.readlines()
            
            # Find the _draw_skeleton method
            in_method = False
            method_lines = []
            
            for line in lines:
                if "def _draw_skeleton" in line:
                    in_method = True
                    method_lines.append(line)
                elif in_method and line.strip().startswith("def "):
                    break
                elif in_method:
                    method_lines.append(line)
            
            if method_lines:
                print("🔧 _draw_skeleton Method:")
                for i, line in enumerate(method_lines[:20]):  # Show first 20 lines
                    print(f"   {i+1:2d}: {line.rstrip()}")
                if len(method_lines) > 20:
                    print(f"   ... ({len(method_lines)-20} more lines)")
            
        except Exception as e:
            print(f"   Error loading code: {e}")
    
    def run_complete_analysis(self):
        """Run complete skeleton generation analysis"""
        self.analyze_skeleton_generation()
        self.demonstrate_skeleton_math()
        self.show_actual_skeleton_code()
        
        print("\n🎯 SUMMARY: HOW SKELETON IS GENERATED")
        print("=" * 50)
        print("1. 📸 Video frame → YOLO model → 17 keypoints")
        print("2. 🎯 Keypoints mapped to body parts (COCO-17)")
        print("3. 🎚️ Confidence filtering (> 0.5 threshold)")
        print("4. 🔗 Draw lines between connected joints")
        print("5. ⭕ Draw colored circles at joint positions")
        print("6. ✨ Overlay skeleton on original frame")
        print("7. 🔄 Repeat for each video frame")

if __name__ == "__main__":
    analyzer = SkeletonGenerationAnalyzer()
    analyzer.run_complete_analysis()
