import re
from pathlib import Path
from typing import Dict, List, Optional

INSTRUCTION_PATH = Path(__file__).resolve().parents[1] / "BEGINNER_Yoga_Static_Messages.docx.md"

_instructions_cache: Optional[Dict[str, Dict[str, List[str]]]] = None
_pose_name_cache: Optional[Dict[str, str]] = None


def _slugify(name: str) -> str:
    cleaned = re.sub(r"\([^)]*\)", "", name)
    cleaned = cleaned.replace("–", "-").replace("—", "-")
    cleaned = cleaned.replace("-", " ")
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.lower().replace(" ", "_")


def _extract_pose_title(raw_title: str) -> str:
    title = raw_title.strip().strip("*")
    title = title.replace("–", "-").replace("—", "-")
    title = re.sub(r"^[^A-Za-z]+", "", title)
    if " - " in title:
        title = title.split(" - ")[0].strip()
    return title


def _clean_instruction_line(line: str) -> str:
    cleaned = line.strip().strip("\"").strip("\u201c\u201d").strip("\"")
    return cleaned


def _parse_markdown(text: str) -> Dict[str, Dict[str, List[str]]]:
    pose_instructions: Dict[str, Dict[str, List[str]]] = {}
    pose_names: Dict[str, str] = {}
    current_pose_id: Optional[str] = None
    current_section = "entry"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized_header = re.sub(r"[*]", "", line).strip()
        header_upper = normalized_header.upper()
        if "INSTRUCTOR MESSAGES" in header_upper and "POSE" in header_upper and "IDLE" in header_upper:
            idle_index = header_upper.find("IDLE")
            pose_index = header_upper.find("POSE")
            if pose_index < idle_index:
                current_section = "release"
            else:
                current_section = "entry"
            continue
        if line.startswith("---"):
            continue
        if line.startswith("**") and line.endswith("**"):
            if "INSTRUCTOR MESSAGES" in header_upper:
                continue
            title = _extract_pose_title(line)
            if not title:
                continue
            pose_id = _slugify(title)
            pose_names[pose_id] = title
            pose_instructions.setdefault(pose_id, {"entry": [], "release": []})
            current_pose_id = pose_id
            continue
        if line.startswith("*(") and line.endswith(")*"):
            continue
        if not current_pose_id:
            continue
        cleaned = _clean_instruction_line(line)
        if cleaned:
            pose_instructions[current_pose_id][current_section].append(cleaned)

    global _pose_name_cache
    _pose_name_cache = pose_names
    return pose_instructions


def load_instructions() -> Dict[str, Dict[str, List[str]]]:
    global _instructions_cache
    if _instructions_cache is not None:
        return _instructions_cache
    if not INSTRUCTION_PATH.exists():
        _instructions_cache = {}
        return _instructions_cache
    text = INSTRUCTION_PATH.read_text(encoding="utf-8")
    _instructions_cache = _parse_markdown(text)
    return _instructions_cache


def get_pose_instructions(pose_id: str) -> Optional[Dict[str, List[str]]]:
    instructions = load_instructions()
    return instructions.get(pose_id)


def get_pose_display_name(pose_id: str) -> Optional[str]:
    load_instructions()
    if _pose_name_cache is None:
        return None
    return _pose_name_cache.get(pose_id)


def resolve_pose_id(pose_name: str) -> Optional[str]:
    if not pose_name:
        return None
    instructions = load_instructions()
    candidate = _slugify(pose_name)
    if candidate in instructions:
        return candidate
    aliases = {
        "cat_and_camel_pose": "cat_cow_pose",
        "child_pose": "childs_pose",
        "warrior_pose": "warrior_ii",
        "warrior_1": "warrior_i",
        "seated_forward": "seated_forward_bend",
        "triangle": "triangle_pose",
    }
    aliased = aliases.get(candidate)
    if aliased and aliased in instructions:
        return aliased
    return None


def get_all_poses() -> List[Dict[str, object]]:
    instructions = load_instructions()
    poses = []
    for pose_id, content in instructions.items():
        poses.append({
            "pose_id": pose_id,
            "name": get_pose_display_name(pose_id) or pose_id.replace("_", " ").title(),
            "entry": content.get("entry", []),
            "release": content.get("release", [])
        })
    return poses
