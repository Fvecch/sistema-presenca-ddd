"""
CAMADA DE DOMÍNIO — Catálogo
=============================
Entidades para Curso e Aluno.

Conceitos DDD:
- Entity: Course e Student têm identidade própria (UUID)
- Aggregate: cada um é simples o suficiente para ser seu próprio agregado
"""

from uuid import UUID, uuid4


# ── Entity: Course ────────────────────────────────────────────────────────────

class Course:
    """Representa um curso/turma cadastrado no sistema."""

    def __init__(self, name: str):
        if not name or not name.strip():
            raise ValueError("O nome do curso não pode ser vazio.")

        self.id   = uuid4()
        self.name = name.strip()

    def to_dict(self) -> dict:
        return {
            "id":   str(self.id),
            "name": self.name,
        }


# ── Entity: Student ───────────────────────────────────────────────────────────

class Student:
    """Representa um aluno vinculado a um curso."""

    def __init__(self, name: str, course_id: UUID):
        if not name or not name.strip():
            raise ValueError("O nome do aluno não pode ser vazio.")

        self.id        = uuid4()
        self.name      = name.strip()
        self.course_id = course_id

    def to_dict(self) -> dict:
        return {
            "id":        str(self.id),
            "name":      self.name,
            "course_id": str(self.course_id),
        }
