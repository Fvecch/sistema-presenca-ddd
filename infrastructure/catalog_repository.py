"""
CAMADA DE INFRAESTRUTURA — Repositório do Catálogo
====================================================
Persiste e recupera Cursos e Alunos no PostgreSQL.
"""

from uuid import UUID

import psycopg2
import psycopg2.extras

from infrastructure.repository import get_connection  # reutiliza a conexão existente
from domain.entities_catalog import Course, Student


def create_catalog_tables():
    """Cria as tabelas courses e students se ainda não existirem."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id   UUID PRIMARY KEY,
                    name TEXT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id        UUID PRIMARY KEY,
                    name      TEXT NOT NULL,
                    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE
                );
            """)
        conn.commit()
    finally:
        conn.close()


# ── Course Repository ─────────────────────────────────────────────────────────

class CourseRepository:

    def save(self, course: Course) -> None:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO courses (id, name) VALUES (%s, %s)",
                    (str(course.id), course.name)
                )
            conn.commit()
        finally:
            conn.close()

    def find_all(self) -> list[Course]:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM courses ORDER BY name")
                rows = cur.fetchall()
            courses = []
            for row in rows:
                c = object.__new__(Course)
                c.id   = UUID(row["id"])
                c.name = row["name"]
                courses.append(c)
            return courses
        finally:
            conn.close()

    def find_by_id(self, course_id: UUID) -> Course | None:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM courses WHERE id = %s", (str(course_id),))
                row = cur.fetchone()
            if row is None:
                return None
            c = object.__new__(Course)
            c.id   = UUID(row["id"])
            c.name = row["name"]
            return c
        finally:
            conn.close()

    def delete(self, course_id: UUID) -> bool:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM courses WHERE id = %s", (str(course_id),))
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()


# ── Student Repository ────────────────────────────────────────────────────────

class StudentRepository:

    def save(self, student: Student) -> None:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO students (id, name, course_id) VALUES (%s, %s, %s)",
                    (str(student.id), student.name, str(student.course_id))
                )
            conn.commit()
        finally:
            conn.close()

    def find_all(self, course_id: UUID | None = None) -> list[Student]:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                if course_id:
                    cur.execute(
                        "SELECT * FROM students WHERE course_id = %s ORDER BY name",
                        (str(course_id),)
                    )
                else:
                    cur.execute("SELECT * FROM students ORDER BY name")
                rows = cur.fetchall()
            students = []
            for row in rows:
                s = object.__new__(Student)
                s.id        = UUID(row["id"])
                s.name      = row["name"]
                s.course_id = UUID(row["course_id"])
                students.append(s)
            return students
        finally:
            conn.close()

    def find_by_id(self, student_id: UUID) -> Student | None:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM students WHERE id = %s", (str(student_id),))
                row = cur.fetchone()
            if row is None:
                return None
            s = object.__new__(Student)
            s.id        = UUID(row["id"])
            s.name      = row["name"]
            s.course_id = UUID(row["course_id"])
            return s
        finally:
            conn.close()

    def delete(self, student_id: UUID) -> bool:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM students WHERE id = %s", (str(student_id),))
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()
