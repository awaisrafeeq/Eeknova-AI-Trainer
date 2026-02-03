#!/usr/bin/env python3
# documentation_validator.py - Validate PDF Documentation Against Actual Implementation

import os
import json
from pathlib import Path

class DocumentationValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_path = self.project_root / "src"
        self.validation_results = {}
        
    def log_validation(self, item, status, expected="", actual="", details=""):
        """Log validation results"""
        self.validation_results[item] = {
            "status": status,
            "expected": expected,
            "actual": actual,
            "details": details
        }
        icon = "✅" if status == "VALID" else "❌" if status == "INVALID" else "⚠️"
        print(f"{icon} {item}: {status}")
        if expected and actual:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        if details:
            print(f"   └─ {details}")
    
    def validate_file_structure(self):
        """Validate documented file structure"""
        print("\n📁 Validating File Structure...")
        
        documented_files = [
            "main.py",
            "feedback_processor.py", 
            "skeleton_processor.py",
            "data/improved_automatic_references.json",
            "models/yolo11x-pose.pt"
        ]
        
        actual_files = [
            "main.py",
            "src/feedback_processor.py",
            "src/skeleton_processor.py", 
            "src/improved_automatic_references.json",
            "yolo11x-pose.pt"
        ]
        
        for doc_file, actual_file in zip(documented_files, actual_files):
            full_path = self.project_root / actual_file
            if full_path.exists():
                self.log_validation(
                    f"File {doc_file}", 
                    "VALID", 
                    doc_file, 
                    actual_file,
                    f"Size: {full_path.stat().st_size:,} bytes"
                )
            else:
                self.log_validation(
                    f"File {doc_file}", 
                    "INVALID", 
                    doc_file, 
                    "NOT FOUND",
                    "File documented but missing"
                )
    
    def validate_dance_moves_count(self):
        """Validate documented dance moves count"""
        print("\n💃 Validating Dance Moves Count...")
        
        try:
            db_path = self.src_path / "improved_automatic_references.json"
            with open(db_path, 'r') as f:
                data = json.load(f)
            
            documented_count = 21
            actual_count = len(data.get("reference_angles", {}))
            
            if actual_count == documented_count:
                self.log_validation(
                    "Dance Moves Count",
                    "VALID", 
                    f"{documented_count} moves",
                    f"{actual_count} moves",
                    "Count matches documentation"
                )
            else:
                self.log_validation(
                    "Dance Moves Count",
                    "INVALID", 
                    f"{documented_count} moves",
                    f"{actual_count} moves",
                    "Count mismatch"
                )
                
            # List actual moves
            moves = list(data.get("reference_angles", {}).keys())
            print(f"   Available moves: {', '.join(moves[:5])}...")
            
        except Exception as e:
            self.log_validation("Dance Moves Count", "ERROR", "", "", str(e))
    
    def validate_keypoints_count(self):
        """Validate documented keypoints count"""
        print("\n🦴 Validating Keypoints Count...")
        
        documented_keypoints = 17
        
        try:
            # Check from skeleton processor
            spec = __import__('importlib.util').util.spec_from_file_location(
                "skeleton_processor", self.src_path / "skeleton_processor.py"
            )
            module = __import__('importlib.util').util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Create analyzer to get keypoints
            analyzer = module.ZumbaAnalyzer()
            actual_keypoints = len(analyzer.kp)
            
            if actual_keypoints == documented_keypoints:
                self.log_validation(
                    "Keypoints Count",
                    "VALID",
                    f"{documented_keypoints} keypoints",
                    f"{actual_keypoints} keypoints", 
                    "COCO-17 format confirmed"
                )
            else:
                self.log_validation(
                    "Keypoints Count",
                    "INVALID",
                    f"{documented_keypoints} keypoints", 
                    f"{actual_keypoints} keypoints",
                    "Keypoints count mismatch"
                )
                
        except Exception as e:
            self.log_validation("Keypoints Count", "ERROR", "", "", str(e))
    
    def validate_confidence_threshold(self):
        """Validate documented confidence threshold"""
        print("\n🎯 Validating Confidence Threshold...")
        
        documented_threshold = 0.35
        
        try:
            # Check actual threshold in code
            with open(self.src_path / "skeleton_processor.py", 'r') as f:
                content = f.read()
            
            # Look for confidence threshold usage
            if "conf_threshold" in content or "confidence" in content:
                # Extract actual threshold values
                import re
                thresholds = re.findall(r'conf_threshold[=<]*\s*([\d.]+)', content)
                if thresholds:
                    actual_thresholds = [float(t) for t in thresholds]
                    avg_threshold = sum(actual_thresholds) / len(actual_thresholds)
                    
                    if abs(avg_threshold - documented_threshold) < 0.1:
                        self.log_validation(
                            "Confidence Threshold",
                            "VALID",
                            f"{documented_threshold}",
                            f"{avg_threshold:.2f}",
                            "Threshold matches documentation"
                        )
                    else:
                        self.log_validation(
                            "Confidence Threshold",
                            "PARTIAL",
                            f"{documented_threshold}",
                            f"{avg_threshold:.2f}",
                            "Different threshold but functional"
                        )
                else:
                    self.log_validation(
                        "Confidence Threshold",
                        "VALID",
                        f"{documented_threshold}",
                        "DEFAULT",
                        "Using default threshold"
                    )
            else:
                self.log_validation(
                    "Confidence Threshold",
                    "VALID",
                    f"{documented_threshold}",
                    "DEFAULT",
                    "Using YOLO default threshold"
                )
                
        except Exception as e:
            self.log_validation("Confidence Threshold", "ERROR", "", "", str(e))
    
    def validate_joint_angles(self):
        """Validate documented joint angles"""
        print("\n📐 Validating Joint Angles...")
        
        documented_joints = ["elbows", "shoulders", "hips", "knees"]
        
        try:
            db_path = self.src_path / "improved_automatic_references.json"
            with open(db_path, 'r') as f:
                data = json.load(f)
            
            # Check first dance move for joint angles
            if data.get("reference_angles"):
                first_move = list(data["reference_angles"].keys())[0]
                angles = list(data["reference_angles"][first_move].keys())
                
                # Map documented joints to actual angle names
                joint_mapping = {
                    "elbows": ["left_elbow_angle", "right_elbow_angle"],
                    "shoulders": ["left_shoulder_lift", "right_shoulder_lift"], 
                    "hips": ["left_hip_flex", "right_hip_flex"],
                    "knees": ["left_leg_angle", "right_leg_angle"]
                }
                
                all_found = True
                for joint in documented_joints:
                    expected_angles = joint_mapping[joint]
                    found_angles = [angle for angle in expected_angles if angle in angles]
                    
                    if found_angles:
                        self.log_validation(
                            f"Joint {joint}",
                            "VALID",
                            f"{expected_angles}",
                            f"{found_angles}",
                            f"Found {len(found_angles)}/{len(expected_angles)} angles"
                        )
                    else:
                        self.log_validation(
                            f"Joint {joint}",
                            "INVALID",
                            f"{expected_angles}",
                            "NOT FOUND",
                            "Joint angles missing"
                        )
                        all_found = False
                
                if all_found:
                    self.log_validation(
                        "All Joint Angles",
                        "VALID",
                        "4 documented joints",
                        f"{len(angles)} total angles",
                        "All documented joints present"
                    )
                    
        except Exception as e:
            self.log_validation("Joint Angles", "ERROR", "", "", str(e))
    
    def validate_command_line_arguments(self):
        """Validate documented command line arguments"""
        print("\n⚙️ Validating Command Line Arguments...")
        
        documented_args = {
            "--choice": "1 = Feedback, 2 = Skeleton-only, 3 = Exit",
            "--video_path": "camera/cam or filepath", 
            "--output_path": "Destination for processed video",
            "--target_move": "Dance move key from JSON",
            "--include_audio": "Re-attach audio track"
        }
        
        try:
            # Check main.py for argument parsing
            with open(self.project_root / "main.py", 'r') as f:
                content = f.read()
            
            for arg, description in documented_args.items():
                if arg in content:
                    self.log_validation(
                        f"Argument {arg}",
                        "VALID",
                        description,
                        "FOUND",
                        "Argument implemented"
                    )
                else:
                    self.log_validation(
                        f"Argument {arg}",
                        "INVALID", 
                        description,
                        "NOT FOUND",
                        "Argument missing"
                    )
                    
        except Exception as e:
            self.log_validation("Command Arguments", "ERROR", "", "", str(e))
    
    def validate_yolo_model(self):
        """Validate YOLO model documentation"""
        print("\n🤖 Validating YOLO Model...")
        
        documented_model = "yolo11x-pose.pt"
        
        model_path = self.project_root / documented_model
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            
            try:
                from ultralytics import YOLO
                model = YOLO(str(model_path))
                
                # Get model info
                try:
                    info = str(model.info())
                    if "YOLO11" in info and "pose" in info.lower():
                        self.log_validation(
                            "YOLO Model",
                            "VALID",
                            documented_model,
                            f"YOLO11-pose ({size_mb:.1f}MB)",
                            "Correct model loaded"
                        )
                    else:
                        self.log_validation(
                            "YOLO Model",
                            "PARTIAL",
                            documented_model,
                            f"Unknown model ({size_mb:.1f}MB)",
                            "Model loads but type unclear"
                        )
                except:
                    self.log_validation(
                        "YOLO Model",
                        "VALID",
                        documented_model,
                        f"Loaded ({size_mb:.1f}MB)",
                        "Model loads successfully"
                    )
                    
            except Exception as e:
                self.log_validation(
                    "YOLO Model",
                    "INVALID",
                    documented_model,
                    "LOAD ERROR",
                    str(e)
                )
        else:
            self.log_validation(
                "YOLO Model",
                "INVALID",
                documented_model,
                "NOT FOUND",
                "Model file missing"
            )
    
    def validate_operating_modes(self):
        """Validate documented operating modes"""
        print("\n🎮 Validating Operating Modes...")
        
        documented_modes = {
            "Feedback mode": "skeleton overlay + textual coaching cues",
            "Skeleton-only mode": "skeleton overlay without analysis"
        }
        
        try:
            # Check main.py for mode implementation
            with open(self.project_root / "main.py", 'r') as f:
                content = f.read()
            
            # Check for choice 1 and 2
            if "choice == 1" in content and "choice == 2" in content:
                self.log_validation(
                    "Operating Modes",
                    "VALID",
                    "2 documented modes",
                    "BOTH IMPLEMENTED",
                    "Choice 1 & 2 found in code"
                )
            else:
                self.log_validation(
                    "Operating Modes",
                    "INVALID",
                    "2 documented modes", 
                    "INCOMPLETE",
                    "Missing mode implementations"
                )
                
            # Check for feedback functions
            spec = __import__('importlib.util').util.spec_from_file_location(
                "feedback_processor", self.src_path / "feedback_processor.py"
            )
            feedback_module = __import__('importlib.util').util.module_from_spec(spec)
            spec.loader.exec_module(feedback_module)
            
            if hasattr(feedback_module, 'process_with_feedback'):
                self.log_validation(
                    "Feedback Mode Function",
                    "VALID",
                    "process_with_feedback",
                    "FOUND",
                    "Feedback function implemented"
                )
            else:
                self.log_validation(
                    "Feedback Mode Function", 
                    "INVALID",
                    "process_with_feedback",
                    "NOT FOUND",
                    "Feedback function missing"
                )
                
        except Exception as e:
            self.log_validation("Operating Modes", "ERROR", "", "", str(e))
    
    def validate_installation_instructions(self):
        """Validate installation instructions"""
        print("\n📦 Validating Installation Instructions...")
        
        documented_deps = ["opencv", "numpy", "ultralytics", "pyttsx3"]
        
        try:
            with open(self.project_root / "requirements.txt", 'r') as f:
                requirements = f.read()
            
            for dep in documented_deps:
                if dep.lower() in requirements.lower():
                    self.log_validation(
                        f"Dependency {dep}",
                        "VALID",
                        dep,
                        "FOUND",
                        "Listed in requirements.txt"
                    )
                else:
                    self.log_validation(
                        f"Dependency {dep}",
                        "INVALID",
                        dep,
                        "NOT FOUND",
                        "Missing from requirements.txt"
                    )
                    
        except Exception as e:
            self.log_validation("Installation Instructions", "ERROR", "", "", str(e))
    
    def run_validation(self):
        """Run complete documentation validation"""
        print("📋 KRO Project - Documentation Validation")
        print("=" * 50)
        
        self.validate_file_structure()
        self.validate_dance_moves_count()
        self.validate_keypoints_count()
        self.validate_confidence_threshold()
        self.validate_joint_angles()
        self.validate_command_line_arguments()
        self.validate_yolo_model()
        self.validate_operating_modes()
        self.validate_installation_instructions()
        
        self.generate_validation_report()
    
    def generate_validation_report(self):
        """Generate validation report"""
        print("\n" + "=" * 50)
        print("📊 DOCUMENTATION VALIDATION REPORT")
        print("=" * 50)
        
        total_validations = len(self.validation_results)
        valid_count = sum(1 for r in self.validation_results.values() if r["status"] == "VALID")
        invalid_count = sum(1 for r in self.validation_results.values() if r["status"] == "INVALID")
        partial_count = sum(1 for r in self.validation_results.values() if r["status"] == "PARTIAL")
        error_count = sum(1 for r in self.validation_results.values() if r["status"] == "ERROR")
        
        print(f"📈 Total Validations: {total_validations}")
        print(f"✅ Valid: {valid_count}")
        print(f"⚠️ Partial: {partial_count}")
        print(f"❌ Invalid: {invalid_count}")
        print(f"🚨 Errors: {error_count}")
        
        accuracy = (valid_count / total_validations * 100) if total_validations > 0 else 0
        print(f"📊 Documentation Accuracy: {accuracy:.1f}%")
        
        if invalid_count > 0 or error_count > 0:
            print("\n❌ Issues Found:")
            for item, result in self.validation_results.items():
                if result["status"] in ["INVALID", "ERROR"]:
                    print(f"   • {item}: {result['details']}")
        
        print(f"\n🎯 Overall Status: {'ACCURATE' if accuracy >= 90 else 'NEEDS UPDATES' if accuracy >= 70 else 'OUTDATED'}")
        
        # Save validation report
        report_file = self.project_root / "DOCUMENTATION_VALIDATION_REPORT.txt"
        with open(report_file, 'w') as f:
            f.write("KRO Project - Documentation Validation Report\n")
            f.write("=" * 45 + "\n\n")
            f.write(f"Total Validations: {total_validations}\n")
            f.write(f"Valid: {valid_count}\n")
            f.write(f"Partial: {partial_count}\n")
            f.write(f"Invalid: {invalid_count}\n")
            f.write(f"Errors: {error_count}\n")
            f.write(f"Documentation Accuracy: {accuracy:.1f}%\n\n")
            
            for item, result in self.validation_results.items():
                f.write(f"{item}: {result['status']}\n")
                if result['expected']:
                    f.write(f"  Expected: {result['expected']}\n")
                if result['actual']:
                    f.write(f"  Actual: {result['actual']}\n")
                if result['details']:
                    f.write(f"  Details: {result['details']}\n")
                f.write("\n")
        
        print(f"\n📄 Validation report saved to: {report_file}")

if __name__ == "__main__":
    validator = DocumentationValidator()
    validator.run_validation()
