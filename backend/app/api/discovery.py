"""
Project discovery endpoints.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Any
from app.services.discovery import DiscoveryService

router = APIRouter(prefix="/api/discovery", tags=["Discovery"])
service = DiscoveryService()


class StartDiscoveryRequest(BaseModel):
    title: str
    initial_prompt: str
    project_id: Optional[str] = None


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    question_text: str
    answer_type: str
    answer_value: Any
    is_confirmed: bool = True


@router.post("/start")
def start_discovery(req: StartDiscoveryRequest):
    return service.start_session(req.title, req.initial_prompt, req.project_id)


@router.post("/answer")
def submit_answer(req: AnswerRequest):
    return service.submit_answer(
        session_id=req.session_id,
        question_id=req.question_id,
        question_text=req.question_text,
        answer_type=req.answer_type,
        answer_value=req.answer_value,
        is_confirmed=req.is_confirmed
    )


@router.get("/spec/{session_id}")
def get_spec(session_id: str):
    return service.generate_specification(session_id)
