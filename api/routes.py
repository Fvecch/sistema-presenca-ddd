"""
CAMADA DE API
=============
Define os endpoints HTTP que o mundo externo pode chamar.

Usamos FastAPI — um framework moderno e rápido para criar APIs em Python.

Endpoints disponíveis:
- POST /api/class-logs         → Registrar chamada diária
- POST /api/class-logs/{id}/justify → Justificar falta de um aluno
- GET  /api/class-logs/{id}    → Consultar um diário (bônus)
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
    version="1.0.0"
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
    """
    Registra a chamada de uma aula.
    
    Regra aplicada: não aceita datas futuras.
    """
    try:
        # Converte os inteiros do JSON para o enum AttendanceStatus
        attendance = {
            student_id: AttendanceStatus(status)
            for student_id, status in request.attendance_list.items()
        }

        # Cria o agregado — as regras de negócio são validadas aqui dentro
        class_log = ClassLog(
            course_id=request.course_id,
            class_date=request.class_date,
            attendance_list=attendance
        )

        # Salva no banco
        repository.save(class_log)

        return {
            "message": "Chamada registrada com sucesso!",
            "class_log": class_log.to_dict()
        }

    except ValueError as e:
        # Erro de regra de negócio (ex: data futura)
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/class-logs/{class_log_id}/justify", status_code=200)
def justify_absence(class_log_id: UUID, request: JustifyAbsenceRequest):
    """
    Justifica a falta de um aluno em uma aula específica.
    
    Regra aplicada: só aceita dentro do prazo de 5 dias.
    """
    # Busca o diário no banco
    class_log = repository.find_by_id(class_log_id)
    if class_log is None:
        raise HTTPException(status_code=404, detail="Diário de classe não encontrado.")

    try:
        # Aplica a regra de negócio — prazo de justificativa
        class_log.excuse_absence(
            student_id=request.student_id,
            reason=request.reason
        )

        # Salva a alteração no banco
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
