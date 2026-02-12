"""
Configuração centralizada do projeto.

Permite customização de:
- Estado (UF)
- Cargo político
- Caminhos de dados
- Autenticação
"""

from __future__ import annotations

import os
from pathlib import Path

# ===== Projeto =====
BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "db" / "eleicoes.duckdb"
DATA_DIR = BASE_DIR / "data" / "tse"

# ===== Eleições (CUSTOMIZÁVEL) =====
"""
Altere estas variáveis para filtrar por estado/cargo diferentes.
Exemplos:
    UF = "MG"  # Minas Gerais
    CARGO_LIKE = "DEPUTADO ESTADUAL"
"""
UF = os.getenv("ELEICOES_UF", "SP")  # São Paulo
CARGO_LIKE = os.getenv("ELEICOES_CARGO", "DEPUTADO FEDERAL")
ANO = 2022

# ===== Autenticação (CUSTOMIZÁVEL) =====
"""
Se vazio, API é pública. Defina uma chave para proteger endpoints.
Exemplo: ELEICOES_API_KEY="seu-secreto-aqui"
"""
API_KEY = os.getenv("ELEICOES_API_KEY", "")

# ===== URLs externas =====
"""
URL base para download de dados do TSE.
"""
TSE_BASE_URL = "https://cdn.tse.jus.br/estatistica/sead/odsele"

# ===== Performance =====
"""
TTL (time-to-live) para cache no Streamlit (segundos).
"""
STREAMLIT_CACHE_TTL_SHORT = 15  # queries de busca (mutáveis)
STREAMLIT_CACHE_TTL_LONG = 120   # dados agregados (estáticos)

# ===== Tabelas DuckDB (CUSTOMIZÁVEIS) =====
"""
Nomes das tabelas no banco. Se trocar UF/CARGO, ajuste aqui.
"""
CANDIDATE_TABLE = f"candidates_{UF.lower()}_dep_fed_{ANO}"
ASSETS_AGG_TABLE = f"assets_agg_{UF.lower()}_dep_fed_{ANO}"
ASSETS_TABLE = f"assets_{UF.lower()}_dep_fed_{ANO}"
VOTES_AGG_TABLE = f"votes_agg_{UF.lower()}_dep_fed_{ANO}"
VOTES_MUN_TABLE = f"votes_municipio_agg_{UF.lower()}_dep_fed_{ANO}"
DONATIONS_TABLE = f"donations_{UF.lower()}_dep_fed_{ANO}"
EXPENSES_TABLE = f"expenses_{UF.lower()}_dep_fed_{ANO}"
FINANCE_AGG_TABLE = f"finance_agg_{UF.lower()}_dep_fed_{ANO}"


def get_env_bool(key: str, default: bool = False) -> bool:
    """Obtém valor booleano de variável de ambiente."""
    val = os.getenv(key, "").lower()
    if val in ("true", "1", "yes"):
        return True
    if val in ("false", "0", "no"):
        return False
    return default


def get_env_int(key: str, default: int) -> int:
    """Obtém valor inteiro de variável de ambiente."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default
