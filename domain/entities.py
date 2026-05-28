"""
CAMADA DE DOMÍNIO
=================
Aqui ficam as REGRAS DE NEGÓCIO do sistema.
Nenhuma outra parte do código pode burlar essas regras.

Conceitos DDD usados:
- Entity: objeto com identidade única (ClassLog, AttendanceRecord)
- Aggregate: conjunto de entidades tratadas como uma unidade (ClassLog é o agregado raiz)
- Value Object: enum de status de presença
"""

from datetime import date, datetime, timezone
from enum import IntEnum
from uuid import UUID, uuid4


# ── Value Object ──────────────────────────────────────────────────────────────

class AttendanceStatus(IntEnum):
    """Status possíveis de presença de um aluno em uma aula."""
    PRESENT = 0   # Presente
    ABSENT  = 1   # Ausente
    EXCUSED = 2   # Falta justificada


# ── Entity: AttendanceRecord ──────────────────────────────────────────────────

class AttendanceRecord:
    """
    Registro individual de presença de UM aluno em UMA aula.
    Equivale ao 'AttendanceRecord' do sistema original em C#.
    """

    def __init__(self, student_id: UUID, status: AttendanceStatus):
        self.student_id = student_id
        self.status = status

    def excuse(self) -> None:
        """Muda o status para EXCUSED (justificado)."""
        self.status = AttendanceStatus.EXCUSED

    def to_dict(self) -> dict:
        return {
            "student_id": str(self.student_id),
            "status": self.status.name  # "PRESENT", "ABSENT" ou "EXCUSED"
        }


# ── Aggregate Root: ClassLog ──────────────────────────────────────────────────

class ClassLog:
    """
    Diário de Classe — o AGREGADO RAIZ do sistema.
    
    Responsável por proteger as seguintes regras de negócio (invariantes):
    
    1. BLOQUEIO TEMPORAL: não é possível abrir um diário para datas FUTURAS.
    2. PRAZO DE JUSTIFICATIVA: atestados só são aceitos em até 5 dias corridos
       após a data da aula.
    3. ENCAPSULAMENTO: ninguém altera status de presença sem passar por aqui.
    """

    EXCUSE_DEADLINE_DAYS = 5  # prazo em dias para justificar uma falta

    def __init__(self, course_id: UUID, class_date: date, attendance_list: dict[UUID, AttendanceStatus]):
        # ── Regra 1: data não pode ser futura ────────────────────────────────
        today = datetime.now(timezone.utc).date()
        if class_date > today:
            raise ValueError(
                f"Não é possível registrar chamada para uma data futura. "
                f"Data informada: {class_date}, hoje: {today}."
            )

        self.id         = uuid4()
        self.course_id  = course_id
        self.class_date = class_date
        self.records: list[AttendanceRecord] = [
            AttendanceRecord(student_id, status)
            for student_id, status in attendance_list.items()
        ]

    def excuse_absence(self, student_id: UUID, reason: str) -> None:
        """
        Justifica a falta de um aluno.
        
        Aplica a Regra 2: só aceita se estiver dentro do prazo de 5 dias.
        """
        # ── Regra 2: verificar prazo ─────────────────────────────────────────
        today = datetime.now(timezone.utc).date()
        days_since_class = (today - self.class_date).days
        if days_since_class > self.EXCUSE_DEADLINE_DAYS:
            raise ValueError(
                f"Prazo para justificar encerrado. "
                f"A aula foi em {self.class_date} ({days_since_class} dias atrás). "
                f"O prazo máximo é de {self.EXCUSE_DEADLINE_DAYS} dias."
            )

        # ── Encontrar o registro do aluno ────────────────────────────────────
        record = next((r for r in self.records if r.student_id == student_id), None)
        if record is None:
            raise ValueError(f"Aluno {student_id} não encontrado neste diário.")

        if record.status != AttendanceStatus.ABSENT:
            raise ValueError(
                f"Só é possível justificar faltas. "
                f"Status atual do aluno: {record.status.name}."
            )

        record.excuse()

    def to_dict(self) -> dict:
        return {
            "id":          str(self.id),
            "course_id":   str(self.course_id),
            "class_date":  self.class_date.isoformat(),
            "records":     [r.to_dict() for r in self.records]
        }
