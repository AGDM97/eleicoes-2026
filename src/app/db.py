"""
Utilitários para gerenciar conexão e índices no DuckDB.
"""

from __future__ import annotations

from typing import Any

import duckdb

from .config import DB_PATH


def open_db(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """
    Abre conexão com DuckDB.
    
    Args:
        read_only: Se True, abre em modo read-only (mais rápido).
    
    Returns:
        Conexão DuckDB.
    """
    return duckdb.connect(str(DB_PATH), read_only=read_only)


def get_tables(con: duckdb.DuckDBPyConnection) -> set[str]:
    """
    Retorna lista de tabelas presentes no banco.
    
    Args:
        con: Conexão DuckDB.
    
    Returns:
        Set com nomes das tabelas.
    """
    return {t[0] for t in con.execute("SHOW TABLES").fetchall()}


def create_indexes(con: duckdb.DuckDBPyConnection, tables_config: dict[str, list[str]]) -> None:
    """
    Cria índices para otimizar queries.
    
    Args:
        con: Conexão DuckDB (não read-only).
        tables_config: Dicionário {nome_tabela: [colunas_para_index]}.
    
    Exemplo:
        create_indexes(con, {
            "candidates_sp_dep_fed_2022": ["id", "nome_urna"],
            "donations_sp_dep_fed_2022": ["candidate_id"],
        })
    """
    existing_tables = get_tables(con)
    
    for table_name, columns in tables_config.items():
        if table_name not in existing_tables:
            print(f"[SKIP] Tabela {table_name} não existe")
            continue
        
        for col in columns:
            index_name = f"idx_{table_name}_{col}"
            try:
                con.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({col})")
                print(f"[OK] Index: {index_name}")
            except Exception as e:
                print(f"[WARN] Não pude criar index {index_name}: {e}")


def ensure_indexes(con: duckdb.DuckDBPyConnection) -> None:
    """
    Garante que todos os índices importantes existem.
    
    Args:
        con: Conexão DuckDB (não read-only).
    """
    from .config import (
        ASSETS_AGG_TABLE,
        ASSETS_TABLE,
        CANDIDATE_TABLE,
        DONATIONS_TABLE,
        EXPENSES_TABLE,
        FINANCE_AGG_TABLE,
        VOTES_AGG_TABLE,
        VOTES_MUN_TABLE,
    )
    
    tables_config = {
        CANDIDATE_TABLE: ["id", "nome_urna", "partido"],
        ASSETS_TABLE: ["candidate_id"],
        ASSETS_AGG_TABLE: ["candidate_id"],
        VOTES_AGG_TABLE: ["candidate_id"],
        VOTES_MUN_TABLE: ["candidate_id"],
        DONATIONS_TABLE: ["candidate_id"],
        EXPENSES_TABLE: ["candidate_id"],
        FINANCE_AGG_TABLE: ["candidate_id"],
    }
    
    create_indexes(con, tables_config)
