"""
Project management endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import json
from app.db.database import get_db_cursor

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    initial_spec: Optional[Dict[str, Any]] = None


@router.get("/list")
def list_projects():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        projects = []
        for r in rows:
            p = dict(r)
            try:
                p["spec"] = json.loads(p.get("spec_json") or "{}")
            except Exception:
                p["spec"] = {}
            projects.append(p)
        return projects


@router.post("/create")
def create_project(req: ProjectCreateRequest):
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    spec_json = json.dumps(req.initial_spec or {})

    with get_db_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO projects (id, name, description, status, spec_json)
            VALUES (?, ?, ?, 'planning', ?)
            """,
            (project_id, req.name, req.description, spec_json)
        )

    return {
        "id": project_id,
        "name": req.name,
        "description": req.description,
        "status": "planning",
        "spec": req.initial_spec or {}
    }


@router.get("/{project_id}")
def get_project(project_id: str):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        p = dict(row)
        try:
            p["spec"] = json.loads(p.get("spec_json") or "{}")
        except Exception:
            p["spec"] = {}
        return p


@router.post("/{project_id}/approve")
def approve_project_spec(project_id: str):
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        cursor.execute(
            "UPDATE projects SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,)
        )
    return {"status": "approved", "project_id": project_id, "new_state": "active"}
