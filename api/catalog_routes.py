"""
CAMADA DE API — Cursos e Alunos
================================
Endpoints:
- POST   /api/courses                    → Criar curso
- GET    /api/courses                    → Listar cursos
- DELETE /api/courses/{id}               → Deletar curso

- POST   /api/students                   → Criar aluno
- GET    /api/students?course_id={uuid}  → Listar alunos (todos ou por curso)
- DELETE /api/students/{id}              → Deletar aluno
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from domain.entities_catalog import Course, Student
from infrastructure.catalog_repository import CourseRepository, StudentRepository

router = APIRouter()

course_repo  = CourseRepository()
student_repo = StudentRepository()


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateCourseRequest(BaseModel):
    name: str


class CreateStudentRequest(BaseModel):
    name:      str
    course_id: UUID


# ── Courses ───────────────────────────────────────────────────────────────────

@router.post("/api/courses", status_code=201)
def create_course(request: CreateCourseRequest):
    """Cadastra um novo curso."""
    try:
        course = Course(name=request.name)
        course_repo.save(course)
        return {"message": "Curso criado com sucesso!", "course": course.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/api/courses")
def list_courses():
    """Lista todos os cursos cadastrados."""
    courses = course_repo.find_all()
    return {"total": len(courses), "courses": [c.to_dict() for c in courses]}


@router.delete("/api/courses/{course_id}", status_code=200)
def delete_course(course_id: UUID):
    """Deleta um curso e todos os alunos vinculados a ele."""
    deleted = course_repo.delete(course_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Curso não encontrado.")
    return {"message": "Curso deletado com sucesso!"}


# ── Students ──────────────────────────────────────────────────────────────────

@router.post("/api/students", status_code=201)
def create_student(request: CreateStudentRequest):
    """Cadastra um novo aluno em um curso."""
    # Verifica se o curso existe
    course = course_repo.find_by_id(request.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Curso não encontrado.")
    try:
        student = Student(name=request.name, course_id=request.course_id)
        student_repo.save(student)
        return {"message": "Aluno criado com sucesso!", "student": student.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/api/students")
def list_students(course_id: Optional[UUID] = Query(default=None)):
    """Lista todos os alunos. Filtra por course_id se informado."""
    students = student_repo.find_all(course_id=course_id)
    return {"total": len(students), "students": [s.to_dict() for s in students]}


@router.delete("/api/students/{student_id}", status_code=200)
def delete_student(student_id: UUID):
    """Deleta um aluno."""
    deleted = student_repo.delete(student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
    return {"message": "Aluno deletado com sucesso!"}
