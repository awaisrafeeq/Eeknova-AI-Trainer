# main.py - Main Entry Point for Dance Guidance System (Command-line version)

import os
import sys
import argparse
from src.feedback_processor import process_with_feedback
from src.skeleton_processor import process_skeleton_only


def main():
    parser = argparse.ArgumentParser(description="🎯 Dance Guidance System")

    parser.add_argument('--choice', type=int, required=True, choices=[1, 2, 3],
                        help="1: With Feedback, 2: Skeleton Only, 3: Exit")
    parser.add_argument('--video_path', type=str, required=True, 
                        help="Path to video file OR 'camera' for real-time (or camera index like '0', '1')")
    parser.add_argument('--output_path', type=str, default=None, help="Path to save the output video")
    parser.add_argument('--include_audio', type=lambda x: x.lower() in ['true', '1', 'yes', 'y'], default=True,
                        help="Include audio in output video (default: True)")
    parser.add_argument('--target_move', type=str, default=None,
                        help="Target dance move (required only for choice=1)")

    args = parser.parse_args()

    # Check if using camera or video file
    is_camera = args.video_path.lower() in ['camera', 'cam', '0', '1', '2']
    
    # Check file existence only if not using camera
    if not is_camera and not os.path.exists(args.video_path):
        print(f"❌ Video file not found: {args.video_path}")
        sys.exit(1)

    os.makedirs("output", exist_ok=True)

    if args.choice == 3:
        print("\n👋 Thank you for using the Dance Guidance System! Goodbye!")
        sys.exit(0)

    if args.choice == 1:
        if not args.target_move:
            print("❌ 'target_move' is required for feedback mode (choice=1).")
            print("\nAvailable moves:")
            moves = [
                "twist_step", "hip_roll_", "salsa_step", "lunge_with_punches",
                "jumping_jacks", "squat_with_clap", "cumbia_step", "zumba_freeze_game",
                "reggaeton_stomp", "zumba_turn_(pivot)", "knee_lifts", "step_clap",
                "step_touch", "grape_vine", "mambo_step", "march_in_place",
                "body_rolls", "side_punches", "shimmy", "merengue_march", "heel_taps"
            ]
            for move in moves:
                print(f"  - {move}")
            sys.exit(1)
        
        if is_camera:
            print("\n🎥 Starting real-time processing with feedback...")
        else:
            print("\n✅ Processing video with feedback and guidance...")
        
        result = process_with_feedback(
            input_video=args.video_path,
            target_move=args.target_move,
            output_video=args.output_path,
            include_audio=args.include_audio
        )
    elif args.choice == 2:
        if is_camera:
            print("\n🎥 Starting real-time skeleton tracking...")
        else:
            print("\n✅ Processing video with skeleton only (no feedback)...")
        
        result = process_skeleton_only(
            input_video=args.video_path,
            output_video=args.output_path,
            include_audio=args.include_audio
        )

    if result:
        if is_camera:
            print(f"\n🎉 {result}")
        else:
            print(f"\n🎉 Success! Output saved to: {result}")
    else:
        print("\n❌ Processing failed. Please check the error messages above.")


if __name__ == "__main__":
    main()