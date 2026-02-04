# chess_api.py - FastAPI backend for Chess Learning System

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from src.education.lesson_core import (
    MODULES,
    LessonSessionManager,
    get_module_by_id,
)


app = FastAPI(title="Chess Learning API", version="1.0.0")

# CORS configuration (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Pydantic models ----

class ModuleListItem(BaseModel):
    id: str
    name: str
    description: str
    icon: str


class SessionCreateRequest(BaseModel):
    module_id: str


class ExerciseResponse(BaseModel):
    session_id: str
    module_id: str
    board_fen: str
    highlights: List[str]
    selected_square: Optional[str]
    instructions: str
    feedback_message: Optional[str]
    is_correct: Optional[bool]
    progress_current: int
    progress_total: int
    hint_available: bool
    module_completed: bool


class ActionRequest(BaseModel):
    type: str
    payload: Dict[str, Any] = {}


class SessionSummary(BaseModel):
    session_id: str
    module_id: str
    completed: bool


# ---- Session manager ----

session_manager = LessonSessionManager()


# ---- Routes ----

@app.get("/api/chess/modules", response_model=List[ModuleListItem])
async def list_modules():
    """List all available chess learning modules."""
    return [
        ModuleListItem(
            id=m.id,
            name=m.name,
            description=m.description,
            icon=m.icon,
        )
        for m in MODULES
    ]


@app.post("/api/chess/session", response_model=ExerciseResponse)
async def create_session(request: SessionCreateRequest):
    """Start a new lesson session for a given module."""
    module = get_module_by_id(request.module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    session = session_manager.create_session(request.module_id)
    exercise = session.get_exercise_state()

    return ExerciseResponse(
        session_id=session.session_id,
        module_id=exercise.module_id,
        board_fen=exercise.board_fen,
        highlights=exercise.highlights,
        selected_square=exercise.selected_square,
        instructions=exercise.instructions,
        feedback_message=exercise.feedback_message,
        is_correct=exercise.is_correct,
        progress_current=exercise.progress_current,
        progress_total=exercise.progress_total,
        hint_available=exercise.hint_available,
        module_completed=exercise.module_completed,
    )


@app.get("/api/chess/session/{session_id}", response_model=ExerciseResponse)
async def get_session_state(session_id: str):
    """Get the current exercise state for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    exercise = session.get_exercise_state()
    return ExerciseResponse(
        session_id=session.session_id,
        module_id=exercise.module_id,
        board_fen=exercise.board_fen,
        highlights=exercise.highlights,
        selected_square=exercise.selected_square,
        instructions=exercise.instructions,
        feedback_message=exercise.feedback_message,
        is_correct=exercise.is_correct,
        progress_current=exercise.progress_current,
        progress_total=exercise.progress_total,
        hint_available=exercise.hint_available,
        module_completed=exercise.module_completed,
    )


@app.post("/api/chess/session/{session_id}/action", response_model=ExerciseResponse)
async def apply_action(session_id: str, request: ActionRequest):
    """Apply a user action (select_square, hint, skip, next, back) and return updated state."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    exercise = session.apply_action(request.type, request.payload)

    return ExerciseResponse(
        session_id=session.session_id,
        module_id=exercise.module_id,
        board_fen=exercise.board_fen,
        highlights=exercise.highlights,
        selected_square=exercise.selected_square,
        instructions=exercise.instructions,
        feedback_message=exercise.feedback_message,
        is_correct=exercise.is_correct,
        progress_current=exercise.progress_current,
        progress_total=exercise.progress_total,
        hint_available=exercise.hint_available,
        module_completed=exercise.module_completed,
    )


@app.post("/api/chess/session/{session_id}/complete", response_model=SessionSummary)
async def complete_session(session_id: str):
    """Mark a session as completed and return a simple summary."""
    state = session_manager.complete_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionSummary(
        session_id=state.session_id,
        module_id=state.module_id,
        completed=state.completed,
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "chess_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
