# 🎓 Sistema de Presença Escolar (DDD Architecture)

API de controle de frequência escolar construída com **Python** e **FastAPI**, seguindo a arquitetura **Domain-Driven Design (DDD)**.

---

## 🏗️ Estrutura do Projeto

```
sistema-presenca/
│
├── domain/
│   └── entities.py        # Regras de negócio (ClassLog, AttendanceRecord)
│
├── infrastructure/
│   └── repository.py      # Acesso ao banco de dados PostgreSQL
│
├── api/
│   └── routes.py          # Endpoints HTTP (FastAPI)
│
├── main.py                # Ponto de entrada da aplicação
├── requirements.txt       # Dependências Python
└── Dockerfile             # Para deploy em produção
```

## 🧠 Arquitetura DDD

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| **Domínio** | `domain/entities.py` | Regras de negócio, invariantes |
| **Infraestrutura** | `infrastructure/repository.py` | Persistência no PostgreSQL |
| **Aplicação/API** | `api/routes.py` | Endpoints HTTP, entrada/saída |

## 📋 Regras de Negócio

1. **Bloqueio Temporal:** Não é possível abrir um Diário de Classe para datas futuras.
2. **Prazo de Justificativa:** Atestados só são aceitos em até **5 dias corridos** após a data da aula.
3. **Encapsulamento:** Nenhuma classe externa altera o status de presença sem passar pelas validações do domínio.

## 🗣️ Linguagem Ubíqua

| Termo | Definição |
|---|---|
| **ClassLog** (Diário de Classe) | Registro oficial de uma aula onde as presenças são computadas |
| **AttendanceRecord** | Status individual de um aluno em uma aula |
| **ExcuseAbsence** | Ação de justificar uma falta, mediante validação de prazo |

## 🚀 Como executar localmente

### 1. Pré-requisitos
- Python 3.12+
- PostgreSQL (local ou na nuvem, ex: [Neon.tech](https://neon.tech))

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variável de ambiente

**Windows (PowerShell):**
```powershell
$env:DATABASE_URL="postgresql://user:senha@host/db"
```

**Linux/Mac:**
```bash
export DATABASE_URL="postgresql://user:senha@host/db"
```

### 4. Rodar a aplicação

```bash
uvicorn main:app --reload
```

A API estará disponível em: `http://localhost:8000`

A documentação interativa fica em: `http://localhost:8000/docs`

---

## 📡 Endpoints

### Registrar Chamada Diária
**POST** `/api/class-logs`

```json
{
  "course_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "class_date": "2026-05-18",
  "attendance_list": {
    "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d": 0,
    "1c9d6f3a-4b8c-4d2e-8f1a-9b3c4d5e6f7a": 1
  }
}
```
*Valores de status → 0: Presente, 1: Ausente, 2: Justificado*

### Justificar Falta
**POST** `/api/class-logs/{id_do_diario}/justify`

```json
{
  "student_id": "1c9d6f3a-4b8c-4d2e-8f1a-9b3c4d5e6f7a",
  "reason": "Atestado médico anexado."
}
```

### Consultar Diário
**GET** `/api/class-logs/{id_do_diario}`

---

## 🚀 Tecnologias

- **Linguagem:** Python 3.12
- **Framework:** FastAPI
- **Banco de Dados:** PostgreSQL
- **Arquitetura:** Domain-Driven Design (DDD)
