"""Post-session Zumba scoring engine.

Implements the AITrainer Zumba Post-Session Stats Guide:

    Overall = PoseAccuracy*45% + BeatSync*25% + Completion*15%
              + Energy*10% + Consistency*5%

Frame-level signals are recorded during the session by ``zumba_processor`` and
aggregated here into per-move, body-part, and session-level scores. All
tunable numbers live in ``zumba_scoring_config.json`` so product can adjust
them without a code change.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_PATH = (
    Path(__file__).parent.parent
    / "Zumba"
    / "feedback_generation_real_time"
    / "src"
    / "zumba_scoring_config.json"
)

_config_cache: Optional[Dict[str, Any]] = None

BODY_PARTS = ("arms", "legs", "core", "balance")

# Simple encouraging tips per weakest body part (used for the one-line tip).
PART_TIPS = {
    "arms": "Punch and reach with full intent - keep your arm lines strong.",
    "legs": "Plant your steps firmly and match the footwork pattern.",
    "core": "Move your shoulders and hips together in one smooth wave.",
    "balance": "Keep your weight centered - avoid swaying off your base.",
}


def load_config() -> Dict[str, Any]:
    global _config_cache
    if _config_cache is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            _config_cache = json.load(fh)
    return _config_cache


def init_session_scoring(session: Dict[str, Any], settings: Optional[Dict[str, Any]]) -> None:
    """Attach scoring accumulators to a freshly created session."""
    settings = settings or {}
    session["scoring"] = {
        "per_move": {},           # move_key -> accumulators
        "motion_series": [],      # (timeline_ms, motion_score) for beat sync
        "part_totals": {p: [0.0, 0] for p in BODY_PARTS},  # part -> [sum, count]
        "mode": settings.get("mode") or "Moderate",
        "song_title": settings.get("song_title") or "",
        "username": settings.get("username") or "",
        "weight_kg": settings.get("weight_kg"),
        "key_beats_ms": list(settings.get("key_beats_ms") or []),
        "key_beat_moves": list(settings.get("key_beat_moves") or []),
    }


def score_frame(
    angles: Dict[str, float],
    reference: Dict[str, float],
    tolerances: Dict[str, float],
    move_key: str,
) -> Optional[Dict[str, Any]]:
    """Graded pose accuracy for one frame (PDF section 3.1).

    Joint Error    = |user_angle - reference_angle|
    Joint Accuracy = 1 - min(Joint Error / Allowed Error, 1)
    Frame Accuracy = body-part weighted average of joint accuracies

    Returns {"frame_accuracy": 0..1, "parts": {part: 0..1}} or None when too
    few joints are comparable.
    """
    config = load_config()
    pose_cfg = config["pose_accuracy"]
    multiplier = float(pose_cfg["allowed_error_multiplier"])
    min_allowed = float(pose_cfg["min_allowed_error_deg"])
    part_joints = config["body_part_joints"]
    move_weights = config["move_body_part_weights"].get(
        move_key, config["move_body_part_weights"]["default"]
    )

    def joint_accuracy(joint: str) -> Optional[float]:
        if joint not in angles or joint not in reference:
            return None
        allowed = max(float(tolerances.get(joint, min_allowed)) * multiplier, min_allowed)
        error = abs(float(angles[joint]) - float(reference[joint]))
        return 1.0 - min(error / allowed, 1.0)

    part_scores: Dict[str, float] = {}
    part_counts: Dict[str, int] = {}
    comparable = 0
    for part in BODY_PARTS:
        joint_accs: List[float] = []
        for joint in part_joints.get(part, []):
            acc = joint_accuracy(joint)
            if acc is None:
                continue
            joint_accs.append(acc)
        if joint_accs:
            part_scores[part] = sum(joint_accs) / len(joint_accs)
            part_counts[part] = len(joint_accs)
            comparable += len(joint_accs)

    # Balance = left/right symmetry: how evenly both sides match the reference.
    # (The live extractor has no dedicated alignment angles, so this is the
    # honest measurable proxy for stability.)
    sym_scores: List[float] = []
    for left, right in config.get("balance_symmetry_pairs", []):
        acc_l = joint_accuracy(left)
        acc_r = joint_accuracy(right)
        if acc_l is None or acc_r is None:
            continue
        sym_scores.append(1.0 - min(abs(acc_l - acc_r), 1.0))
    if sym_scores:
        part_scores["balance"] = sum(sym_scores) / len(sym_scores)
        part_counts["balance"] = len(sym_scores)

    if comparable < 4:
        return None

    # Weighted frame accuracy over the parts that had data (weights renormalized).
    total_weight = sum(float(move_weights.get(p, 0)) for p in part_scores)
    if total_weight <= 0:
        frame_accuracy = sum(part_scores.values()) / len(part_scores)
    else:
        frame_accuracy = sum(
            part_scores[p] * float(move_weights.get(p, 0)) for p in part_scores
        ) / total_weight

    return {"frame_accuracy": frame_accuracy, "parts": part_scores}


def record_frame(
    session: Dict[str, Any],
    move_key: str,
    move_name: Optional[str],
    frame_score: Optional[Dict[str, Any]],
    motion_score: float,
    is_active: bool,
    timeline_ms: Optional[float],
) -> None:
    """Accumulate one analysed frame into the session's scoring state."""
    scoring = session.get("scoring")
    if scoring is None:
        return

    pm = scoring["per_move"].setdefault(move_key, {
        "name": move_name or move_key,
        "frames": 0,
        "accuracy_sum": 0.0,
        "accuracy_frames": 0,
        "active_frames": 0,
        "energy_sum": 0.0,
        "energy_frames": 0,
        "parts": {p: [0.0, 0] for p in BODY_PARTS},
    })
    if move_name:
        pm["name"] = move_name
    pm["frames"] += 1
    if is_active:
        pm["active_frames"] += 1
    if motion_score is not None and motion_score > 0:
        pm["energy_sum"] += float(motion_score)
        pm["energy_frames"] += 1

    if frame_score is not None:
        pm["accuracy_sum"] += frame_score["frame_accuracy"]
        pm["accuracy_frames"] += 1
        for part, value in frame_score["parts"].items():
            pm["parts"][part][0] += value
            pm["parts"][part][1] += 1
            scoring["part_totals"][part][0] += value
            scoring["part_totals"][part][1] += 1

    if timeline_ms is not None:
        series = scoring["motion_series"]
        series.append((float(timeline_ms), float(motion_score or 0.0)))
        # Bound memory for very long sessions (~1h at 3fps).
        if len(series) > 12000:
            del series[: len(series) - 12000]


def _beat_sync(scoring: Dict[str, Any]) -> Dict[str, Any]:
    """Beat Sync (PDF section 3.2): movement peaks vs expected beat times."""
    config = load_config()["beat_sync"]
    match_window = float(config["match_window_ms"])
    search_window = float(config["peak_search_window_ms"])
    min_peak = float(config["min_peak_motion"])
    bands = config["bands_ms"]

    beats: List[float] = scoring.get("key_beats_ms") or []
    beat_moves: List[str] = scoring.get("key_beat_moves") or []
    series = scoring.get("motion_series") or []

    result = {
        "matched": 0,
        "total": len(beats),
        "avg_delay_ms": None,
        "bands": {"excellent": 0, "good": 0, "average": 0, "off": 0},
        "per_move": {},  # move_key -> [matched, total]
    }
    if not beats or not series:
        result["total"] = len(beats)
        return result

    delays: List[float] = []
    for i, beat in enumerate(beats):
        move_key = beat_moves[i] if i < len(beat_moves) else None
        if move_key is not None:
            result["per_move"].setdefault(move_key, [0, 0])[1] += 1

        # A beat is matched when the user shows real movement inside the match
        # window around it. Use the strongest sample within the window; the
        # wider search window only rescues beats with sparse samples (~3 fps).
        window = [(t, m) for (t, m) in series if abs(t - beat) <= match_window]
        if not window:
            window = [(t, m) for (t, m) in series if abs(t - beat) <= search_window]
        if not window:
            result["bands"]["off"] += 1
            continue
        peak_t, peak_m = max(window, key=lambda tm: tm[1])
        if peak_m < min_peak:
            result["bands"]["off"] += 1
            continue
        delay = abs(peak_t - beat)
        if delay <= float(bands["excellent"]):
            result["bands"]["excellent"] += 1
        elif delay <= float(bands["good"]):
            result["bands"]["good"] += 1
        elif delay <= float(bands["average"]):
            result["bands"]["average"] += 1
        else:
            result["bands"]["off"] += 1
        if delay <= match_window:
            result["matched"] += 1
            delays.append(delay)
            if move_key is not None:
                result["per_move"][move_key][0] += 1

    if delays:
        result["avg_delay_ms"] = round(sum(delays) / len(delays))
    return result


def build_scores(session: Dict[str, Any], duration_seconds: float) -> Optional[Dict[str, Any]]:
    """Aggregate all recorded frames into the final post-session score object."""
    scoring = session.get("scoring")
    if not scoring:
        return None
    config = load_config()
    metrics = session.get("performance_metrics", {})
    min_frames = int(config.get("min_frames_per_move", 5))

    # ---- Per-move table -----------------------------------------------------
    beat = _beat_sync(scoring)
    moves_out: List[Dict[str, Any]] = []
    eligible_acc: List[float] = []
    for key, pm in scoring["per_move"].items():
        accuracy = (
            (pm["accuracy_sum"] / pm["accuracy_frames"]) * 100
            if pm["accuracy_frames"] > 0 else None
        )
        rhythm = None
        if key in beat["per_move"] and beat["per_move"][key][1] > 0:
            rhythm = (beat["per_move"][key][0] / beat["per_move"][key][1]) * 100
        energy = (
            pm["energy_sum"] / pm["energy_frames"] if pm["energy_frames"] > 0 else 0.0
        )
        completion = (pm["active_frames"] / pm["frames"]) * 100 if pm["frames"] > 0 else 0.0
        parts = {
            p: round((s / c) * 100) if c > 0 else None
            for p, (s, c) in pm["parts"].items()
        }
        moves_out.append({
            "key": key,
            "name": pm["name"],
            "frames": pm["frames"],
            "accuracy": round(accuracy) if accuracy is not None else None,
            "rhythm": round(rhythm) if rhythm is not None else None,
            "energy": round(energy, 2),
            "completion": round(completion),
            "body_parts": parts,
        })
        if accuracy is not None and pm["accuracy_frames"] >= min_frames:
            eligible_acc.append(accuracy)

    # ---- Session Pose Accuracy = average of all move accuracies (PDF 3.1) ---
    pose_accuracy = sum(eligible_acc) / len(eligible_acc) if eligible_acc else 0.0

    # ---- Beat Sync Score = matched beats / total key beats (PDF 3.2) --------
    beat_sync = (beat["matched"] / beat["total"]) * 100 if beat["total"] > 0 else 0.0

    # ---- Completion = valid active frames / expected active frames (PDF 3.3)
    total_frames = metrics.get("total_frames", 0)
    completion = (
        (metrics.get("active_frames", 0) / total_frames) * 100 if total_frames > 0 else 0.0
    )

    # ---- Energy Score = user energy / expected energy, capped (PDF 3.4) -----
    mode = scoring.get("mode") or "Moderate"
    target_energy = float(config["energy_targets"].get(mode, 7.0))
    energy_values = [m for (_, m) in scoring.get("motion_series", []) if m > 0]
    user_energy = sum(energy_values) / len(energy_values) if energy_values else 0.0
    energy_score = min(user_energy / target_energy, 1.0) * 100 if target_energy > 0 else 0.0

    # ---- Consistency = 100 - stdev of move accuracies (PDF 3.5) -------------
    if len(eligible_acc) >= 2:
        mean_acc = sum(eligible_acc) / len(eligible_acc)
        stdev = math.sqrt(sum((a - mean_acc) ** 2 for a in eligible_acc) / len(eligible_acc))
        consistency = max(0.0, 100.0 - stdev)
    else:
        consistency = 100.0 if eligible_acc else 0.0

    # ---- Overall Score (PDF section 2) --------------------------------------
    w = config["overall_weights"]
    overall = (
        pose_accuracy * float(w["pose_accuracy"])
        + beat_sync * float(w["beat_sync"])
        + completion * float(w["completion"])
        + energy_score * float(w["energy"])
        + consistency * float(w["consistency"])
    )

    # ---- Body part scores (PDF section 4); Rhythm = beat sync ---------------
    body_parts = {
        p: round((s / c) * 100) if c > 0 else None
        for p, (s, c) in scoring["part_totals"].items()
    }
    body_parts["rhythm"] = round(beat_sync)

    # ---- Best move / Needs practice (PDF section 1) --------------------------
    ranked = [m for m in moves_out if m["accuracy"] is not None and m["frames"] >= min_frames]
    ranked.sort(key=lambda m: m["accuracy"], reverse=True)
    best_move = ranked[0] if ranked else None
    needs_practice = ranked[-1] if len(ranked) >= 2 else None

    # ---- Calories (PDF section 6): MET x 3.5 x weight / 200 x minutes -------
    met = float(config["met_values"].get(mode, 6.0))
    minutes = max(duration_seconds, 0) / 60.0
    weight = scoring.get("weight_kg")
    if weight:
        calories: Dict[str, Any] = {
            "value": round(met * 3.5 * float(weight) / 200.0 * minutes)
        }
    else:
        lo, hi = config.get("default_weight_range_kg", [55, 85])
        calories = {
            "range": [
                round(met * 3.5 * float(lo) / 200.0 * minutes),
                round(met * 3.5 * float(hi) / 200.0 * minutes),
            ]
        }

    # ---- Active time ----------------------------------------------------------
    active_ratio = (metrics.get("active_frames", 0) / total_frames) if total_frames > 0 else 0.0
    active_time_seconds = round(duration_seconds * active_ratio)

    # ---- One encouraging improvement tip -------------------------------------
    scored_parts = {p: v for p, v in body_parts.items() if p in BODY_PARTS and v is not None}
    weakest_part = min(scored_parts, key=scored_parts.get) if scored_parts else None
    if needs_practice and weakest_part:
        tip = (
            f"Focus on your {weakest_part} during {needs_practice['name']}: "
            f"{PART_TIPS[weakest_part]} Try one more round to improve it."
        )
    elif weakest_part:
        tip = f"{PART_TIPS[weakest_part]} Keep it up!"
    else:
        tip = "Great effort! Dance one more round to unlock detailed feedback."

    return {
        "overall": round(overall),
        "pose_accuracy": round(pose_accuracy),
        "beat_sync": round(beat_sync),
        "completion": round(completion),
        "energy": round(energy_score),
        "consistency": round(consistency),
        "beat_sync_detail": {
            "matched": beat["matched"],
            "total": beat["total"],
            "avg_delay_ms": beat["avg_delay_ms"],
            "bands": beat["bands"],
        },
        "body_parts": body_parts,
        "calories": calories,
        "met": met,
        "active_time_seconds": active_time_seconds,
        "best_move": (
            {"key": best_move["key"], "name": best_move["name"], "accuracy": best_move["accuracy"]}
            if best_move else None
        ),
        "needs_practice": (
            {
                "key": needs_practice["key"],
                "name": needs_practice["name"],
                "accuracy": needs_practice["accuracy"],
            }
            if needs_practice else None
        ),
        "moves": sorted(moves_out, key=lambda m: (m["accuracy"] is None, -(m["accuracy"] or 0))),
        "tip": tip,
        "mode": mode,
        "song_title": scoring.get("song_title") or "",
    }
