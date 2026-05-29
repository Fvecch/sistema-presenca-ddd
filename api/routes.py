"""
CAMADA DE API
=============
Define os endpoints HTTP que o mundo externo pode chamar.

Usamos FastAPI — um framework moderno e rápido para criar APIs em Python.

Endpoints disponíveis:
- POST   /api/class-logs                           → Registrar chamada diária
- GET    /api/class-logs                           → Listar todos os diários
- GET    /api/class-logs/{id}                      → Consultar um diário
- PUT    /api/class-logs/{id}                      → Atualizar um diário
- DELETE /api/class-logs/{id}                      → Deletar um diário
- POST   /api/class-logs/{id}/justify              → Justificar falta
- PUT    /api/class-logs/{id}/records/{student_id} → Atualizar status de aluno
- DELETE /api/class-logs/{id}/records/{student_id} → Remover aluno da chamada
"""

from datetime import date
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from domain.entities import AttendanceStatus, ClassLog
from infrastructure.repository import ClassLogRepository, create_tables

# ── Inicialização ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sistema de Presença Escolar",
    description="API para controle de frequência com arquitetura DDD — feita em Python/FastAPI.",
    version="2.0.0"
)

repository = ClassLogRepository()


@app.on_event("startup")
def startup():
    """Cria as tabelas no banco quando a aplicação sobe."""
    create_tables()


# ── Schemas de entrada (o que a API recebe) ───────────────────────────────────

class CreateClassLogRequest(BaseModel):
    """
    Dados necessários para registrar uma chamada.

    Exemplo de body:
    {
        "course_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "class_date": "2026-05-18",
        "attendance_list": {
            "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d": 0,
            "1c9d6f3a-4b8c-4d2e-8f1a-9b3c4d5e6f7a": 1
        }
    }
    Valores de status: 0 = Presente, 1 = Ausente, 2 = Justificado
    """
    course_id:       UUID
    class_date:      date
    attendance_list: dict[UUID, int]


class UpdateClassLogRequest(BaseModel):
    """
    Dados para atualizar um diário de classe.

    Exemplo de body:
    {
        "course_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "class_date": "2026-05-20"
    }
    """
    course_id:  UUID
    class_date: date


class UpdateAttendanceRequest(BaseModel):
    """
    Dados para atualizar o status de presença de um aluno.

    Exemplo de body:
    {
        "status": 2
    }
    Valores: 0 = Presente, 1 = Ausente, 2 = Justificado
    """
    status: int


class JustifyAbsenceRequest(BaseModel):
    """
    Dados para justificar a falta de um aluno.

    Exemplo de body:
    {
        "student_id": "1c9d6f3a-4b8c-4d2e-8f1a-9b3c4d5e6f7a",
        "reason": "Atestado médico."
    }
    """
    student_id: UUID
    reason:     str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/api/class-logs", status_code=201)
def register_class_log(request: CreateClassLogRequest):
    """Registra a chamada de uma aula. Regra: não aceita datas futuras."""
    try:
        attendance = {
            student_id: AttendanceStatus(status)
            for student_id, status in request.attendance_list.items()
        }
        class_log = ClassLog(
            course_id=request.course_id,
            class_date=request.class_date,
            attendance_list=attendance
        )
        repository.save(class_log)
        return {
            "message": "Chamada registrada com sucesso!",
            "class_log": class_log.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.put("/api/class-logs/{class_log_id}", status_code=200)
def update_class_log(class_log_id: UUID, request: UpdateClassLogRequest):
    """Atualiza o course_id e/ou class_date de um diário existente."""
    try:
        updated = repository.update_class_log(
            class_log_id=class_log_id,
            course_id=request.course_id,
            class_date=request.class_date
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Diário de classe não encontrado.")

    return {"message": "Diário atualizado com sucesso!"}


@app.put("/api/class-logs/{class_log_id}/records/{student_id}", status_code=200)
def update_attendance_record(class_log_id: UUID, student_id: UUID, request: UpdateAttendanceRequest):
    """Atualiza o status de presença de um aluno em um diário."""
    if request.status not in [0, 1, 2]:
        raise HTTPException(status_code=422, detail="Status inválido. Use 0 (Presente), 1 (Ausente) ou 2 (Justificado).")

    updated = repository.update_attendance_record(
        class_log_id=class_log_id,
        student_id=student_id,
        status=request.status
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")

    return {"message": "Status de presença atualizado com sucesso!"}


@app.post("/api/class-logs/{class_log_id}/justify", status_code=200)
def justify_absence(class_log_id: UUID, request: JustifyAbsenceRequest):
    """Justifica a falta de um aluno. Regra: só aceita dentro do prazo de 5 dias."""
    class_log = repository.find_by_id(class_log_id)
    if class_log is None:
        raise HTTPException(status_code=404, detail="Diário de classe não encontrado.")
    try:
        class_log.excuse_absence(student_id=request.student_id, reason=request.reason)
        repository.update(class_log)
        return {
            "message": "Falta justificada com sucesso!",
            "class_log": class_log.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/api/class-logs/{class_log_id}")
def get_class_log(class_log_id: UUID):
    """Consulta um diário de classe pelo ID."""
    class_log = repository.find_by_id(class_log_id)
    if class_log is None:
        raise HTTPException(status_code=404, detail="Diário de classe não encontrado.")
    return class_log.to_dict()


@app.get("/")
def root():
    return {"message": "Sistema de Presença Escolar — API funcionando!"}
