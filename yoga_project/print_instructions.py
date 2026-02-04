#!/usr/bin/env python3
from yoga_instructions import load_instructions, get_pose_display_name

def main():
    instructions = load_instructions()
    print("=== Pose Instructions ===\n")
    for pid, data in instructions.items():
        name = get_pose_display_name(pid) or pid.replace('_', ' ').title()
        print(f"{name} ({pid})")
        print("  Entry:")
        for i, line in enumerate(data.get('entry', []), 1):
            print(f"    {i}. {line}")
        print("  Exit:")
        for i, line in enumerate(data.get('release', []), 1):
            print(f"    {i}. {line}")
        print()

if __name__ == "__main__":
    main()
