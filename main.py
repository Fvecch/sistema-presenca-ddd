"""
PONTO DE ENTRADA DA APLICAÇÃO
==============================
Este é o arquivo que você executa para rodar o servidor.

Como rodar:
    uvicorn main:app --reload

A documentação automática da API fica em:
    http://localhost:8000/docs
"""

import sys
import os

# Garante que Python encontre os módulos do projeto
sys.path.insert(0, os.path.dirname(__file__))

from api.routes import app  # noqa: F401 — importado para o uvicorn encontrar
