"""
CAMADA DE API — CRUD Completo
==============================
Endpoints disponíveis:
- POST   /api/class-logs                           → Criar chamada
- GET    /api/class-logs                           → Listar todas
- GET    /api/class-logs/{id}                      → Buscar uma
- PUT    /api/class-logs/{id}                      → Atualizar
- DELETE /api/class-logs/{id}                      → Deletar
- POST   /api/class-logs/{id}/justify              → Justificar falta
- PUT    /api/class-logs/{id}/records/{student_id} → Atualizar status
- DELETE /api/class-logs/{id}/records/{student_id} → Remover aluno
"""

from datetime import date
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from domain.entities import AttendanceStatus, ClassLog
from infrastructure.repository import ClassLogRepository, create_tables

app = FastAPI(
    title="Sistema de Presença Escolar",
    description="API para controle de frequência com arquitetura DDD — feita em Python/FastAPI.",
    version="2.0.0"
)

repository = ClassLogRepository()


@app.on_event("startup")
def startup():
    create_tables()


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateClassLogRequest(BaseModel):
    course_id:       UUID
    class_date:      date
    attendance_list: dict[UUID, int]


class UpdateClassLogRequest(BaseModel):
    course_id:  UUID
    class_date: date


class UpdateAttendanceRequest(BaseModel):
    status: int


class JustifyAbsenceRequest(BaseModel):
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
        return {"message": "Chamada registrada com sucesso!", "class_log": class_log.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/api/class-logs")
def get_all_class_logs():
    """Lista todos os diários de classe."""
    class_logs = repository.find_all()
    return {"total": len(class_logs), "class_logs": [cl.to_dict() for cl in class_logs]}


@app.get("/api/class-logs/{class_log_id}")
def get_class_log(class_log_id: UUID):
    """Consulta um diário de classe pelo ID."""
    class_log = repository.find_by_id(class_log_id)
    if class_log is None:
        raise HTTPException(status_code=404, detail="Diário de classe não encontrado.")
    return class_log.to_dict()


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


@app.delete("/api/class-logs/{class_log_id}", status_code=200)
def delete_class_log(class_log_id: UUID):
    """Deleta um diário de classe e todos os seus registros de presença."""
    deleted = repository.delete_class_log(class_log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Diário de classe não encontrado.")
    return {"message": "Diário deletado com sucesso!"}


@app.post("/api/class-logs/{class_log_id}/justify", status_code=200)
def justify_absence(class_log_id: UUID, request: JustifyAbsenceRequest):
    """Justifica a falta de um aluno. Regra: só aceita dentro do prazo de 5 dias."""
    class_log = repository.find_by_id(class_log_id)
    if class_log is None:
        raise HTTPException(status_code=404, detail="Diário de classe não encontrado.")
    try:
        class_log.excuse_absence(student_id=request.student_id, reason=request.reason)
        repository.update(class_log)
        return {"message": "Falta justificada com sucesso!", "class_log": class_log.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


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


@app.delete("/api/class-logs/{class_log_id}/records/{student_id}", status_code=200)
def delete_attendance_record(class_log_id: UUID, student_id: UUID):
    """Remove um aluno de um diário de classe."""
    deleted = repository.delete_attendance_record(class_log_id, student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    return {"message": "Aluno removido da chamada com sucesso!"}


@app.get("/")
def root():
    return {"message": "Sistema de Presença Escolar — API funcionando!"}
