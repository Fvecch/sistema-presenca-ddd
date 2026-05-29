"""
CAMADA DE INFRAESTRUTURA — Repositório
=======================================
Responsável por SALVAR e BUSCAR dados no banco PostgreSQL.

Conceito DDD usado:
- Repository: abstrai o acesso ao banco de dados. O domínio não sabe
  se os dados estão num PostgreSQL, num arquivo, ou em memória.

Usamos psycopg2 para conectar ao PostgreSQL.
A string de conexão vem da variável de ambiente DATABASE_URL
(boa prática de segurança — nunca coloca senha no código!).
"""

import os
from datetime import date
from uuid import UUID

import psycopg2
import psycopg2.extras

from domain.entities import AttendanceRecord, AttendanceStatus, ClassLog


def get_connection():
    """Cria e retorna uma conexão com o banco PostgreSQL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "Variável de ambiente DATABASE_URL não definida. "
            "Exemplo: export DATABASE_URL='postgresql://user:senha@host/db'"
        )
    return psycopg2.connect(database_url)


def create_tables():
    """Cria as tabelas no banco se ainda não existirem."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS class_logs (
                    id          UUID PRIMARY KEY,
                    course_id   UUID NOT NULL,
                    class_date  DATE NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance_records (
                    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    class_log_id UUID NOT NULL REFERENCES class_logs(id) ON DELETE CASCADE,
                    student_id  UUID NOT NULL,
                    status      INTEGER NOT NULL
                );
            """)
        conn.commit()
    finally:
        conn.close()


class ClassLogRepository:

    def save(self, class_log: ClassLog) -> None:
        """Salva um novo ClassLog (e seus registros de presença) no banco."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO class_logs (id, course_id, class_date) VALUES (%s, %s, %s)",
                    (str(class_log.id), str(class_log.course_id), class_log.class_date)
                )
                for record in class_log.records:
                    cur.execute(
                        """INSERT INTO attendance_records (class_log_id, student_id, status)
                           VALUES (%s, %s, %s)""",
                        (str(class_log.id), str(record.student_id), int(record.status))
                    )
            conn.commit()
        finally:
            conn.close()

    def find_by_id(self, class_log_id: UUID) -> ClassLog | None:
        """Busca um ClassLog pelo ID. Retorna None se não encontrar."""
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM class_logs WHERE id = %s", (str(class_log_id),))
                row = cur.fetchone()
                if row is None:
                    return None
                cur.execute(
                    "SELECT * FROM attendance_records WHERE class_log_id = %s",
                    (str(class_log_id),)
                )
                record_rows = cur.fetchall()

            attendance_list = {
                UUID(r["student_id"]): AttendanceStatus(r["status"])
                for r in record_rows
            }
            class_log = object.__new__(ClassLog)
            class_log.id         = UUID(row["id"])
            class_log.course_id  = UUID(row["course_id"])
            class_log.class_date = row["class_date"]
            class_log.records    = [
                AttendanceRecord(sid, status)
                for sid, status in attendance_list.items()
            ]
            return class_log
        finally:
            conn.close()

    def find_all(self) -> list:
        """Retorna todos os ClassLogs do banco."""
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("SELECT * FROM class_logs ORDER BY class_date DESC")
                rows = cur.fetchall()

            result = []
            for row in rows:
                cur_conn = get_connection()
                try:
                    with cur_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as c:
                        c.execute(
                            "SELECT * FROM attendance_records WHERE class_log_id = %s",
                            (str(row["id"]),)
                        )
                        record_rows = c.fetchall()
                finally:
                    cur_conn.close()

                attendance_list = {
                    UUID(r["student_id"]): AttendanceStatus(r["status"])
                    for r in record_rows
                }
                class_log = object.__new__(ClassLog)
                class_log.id         = UUID(row["id"])
                class_log.course_id  = UUID(row["course_id"])
                class_log.class_date = row["class_date"]
                class_log.records    = [
                    AttendanceRecord(sid, status)
                    for sid, status in attendance_list.items()
                ]
                result.append(class_log)
            return result
        finally:
            conn.close()

    def update(self, class_log: ClassLog) -> None:
        """Atualiza os registros de presença de um ClassLog existente."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                for record in class_log.records:
                    cur.execute(
                        """UPDATE attendance_records
                           SET status = %s
                           WHERE class_log_id = %s AND student_id = %s""",
                        (int(record.status), str(class_log.id), str(record.student_id))
                    )
            conn.commit()
        finally:
            conn.close()

    def update_class_log(self, class_log_id: UUID, course_id: UUID, class_date) -> bool:
        """Atualiza course_id e class_date de um ClassLog. Retorna True se atualizou."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE class_logs SET course_id = %s, class_date = %s WHERE id = %s",
                    (str(course_id), class_date, str(class_log_id))
                )
                updated = cur.rowcount > 0
            conn.commit()
            return updated
        finally:
            conn.close()

    def update_attendance_record(self, class_log_id: UUID, student_id: UUID, status: int) -> bool:
        """Atualiza o status de presença de um aluno. Retorna True se atualizou."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE attendance_records SET status = %s
                       WHERE class_log_id = %s AND student_id = %s""",
                    (status, str(class_log_id), str(student_id))
                )
                updated = cur.rowcount > 0
            conn.commit()
            return updated
        finally:
            conn.close()

    def delete_class_log(self, class_log_id: UUID) -> bool:
        """Deleta um ClassLog e todos os seus registros. Retorna True se deletou."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM class_logs WHERE id = %s",
                    (str(class_log_id),)
                )
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    def delete_attendance_record(self, class_log_id: UUID, student_id: UUID) -> bool:
        """Remove um aluno de um diário. Retorna True se deletou."""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """DELETE FROM attendance_records
                       WHERE class_log_id = %s AND student_id = %s""",
                    (str(class_log_id), str(student_id))
                )
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()
