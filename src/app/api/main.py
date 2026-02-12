"""
FastAPI Backend para Eleições Dashboard.

Endpoints:
  GET /health - Status da API e banco
  GET /candidates - Lista candidatos com busca
  GET /candidates/{id}/assets - Bens de um candidato
  GET /candidates/{id}/votes_municipio - Votos por município
  GET /candidates/{id}/finance - Receitas/despesas detalhadas

Autenticação:
  Se ELEICOES_API_KEY está definida, /candidates requer token.
  Outros endpoints são públicos.
  
  Exemplo com token:
    curl -H "Authorization: Bearer seu-token" http://localhost:8000/candidates
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..auth import check_api_key
from ..config import (
    ASSETS_AGG_TABLE,
    ASSETS_TABLE,
    CANDIDATE_TABLE,
    DB_PATH,
    DONATIONS_TABLE,
    EXPENSES_TABLE,
    FINANCE_AGG_TABLE,
    VOTES_AGG_TABLE,
    VOTES_MUN_TABLE,
)
from ..db import ensure_indexes, get_tables, open_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Eleições Dashboard API",
    version="1.0.0",
    description="API para análise de dados eleitorais brasileiros (TSE)",
)

# CORS: permite requisições do Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    """Executado ao iniciar a API."""
    logger.info(f"[STARTUP] Conectando ao banco: {DB_PATH}")
    try:
        con = open_db(read_only=False)
        ensure_indexes(con)
        con.close()
        logger.info("[STARTUP] Índices verificados/criados")
    except Exception as e:
        logger.error(f"[STARTUP ERROR] {e}")


@app.get("/health")
def health() -> dict[str, Any]:
    """
    Status da API e banco de dados.
    
    Returns:
        {
            "status": "ok",
            "db": "/path/to/db",
            "db_exists": true,
            "version": "1.0.0"
        }
    """
    return {
        "status": "ok",
        "db": str(DB_PATH),
        "db_exists": DB_PATH.exists(),
        "version": "1.0.0",
    }


@app.get("/candidates")
def list_candidates(
    q: str = "",
    limit: int = 50,
    offset: int = 0,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """
    Lista candidatos com filtro de busca.
    
    Args:
        q: Texto para buscar (busca em nome_urna e nome_completo).
        limit: Número de resultados (padrão 50).
        offset: Deslocamento para paginação (padrão 0).
        authorization: Token Bearer (se API_KEY está definida).
    
    Returns:
        {
            "items": [
                {
                    "id": 123,
                    "nome_urna": "SILVA",
                    "total_votos": 1500,
                    ...
                }
            ],
            "assets_enabled": true,
            "votes_enabled": true,
            "finance_enabled": true
        }
    
    Raises:
        HTTPException: Se banco não existe ou erro na query.
    """
    try:
        check_api_key(authorization)
    except HTTPException as e:
        logger.warning(f"[AUTH] Acesso negado: {e.detail}")
        raise

    try:
        if not DB_PATH.exists():
            logger.error(f"[DB] Banco não encontrado: {DB_PATH}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Banco de dados não encontrado em {DB_PATH}",
            )

        con = open_db(read_only=True)
        tables = get_tables(con)

        # Verifica quais tabelas estão disponíveis
        assets_enabled = ASSETS_AGG_TABLE in tables
        votes_enabled = VOTES_AGG_TABLE in tables
        finance_enabled = FINANCE_AGG_TABLE in tables

        q_norm = q.strip().lower()

        sql = f"""
            SELECT
                c.id, c.numero, c.nome_urna, c.nome_completo, c.partido, c.uf, c.cargo, c.situacao,
                COALESCE(a.total_bens, 0) AS total_bens,
                COALESCE(a.qtd_bens, 0)   AS qtd_bens,
                COALESCE(v.total_votos, 0) AS total_votos,
                COALESCE(f.total_receitas, 0) AS total_receitas,
                COALESCE(f.total_despesas, 0) AS total_despesas,
                COALESCE(f.doadores_unicos, 0) AS doadores_unicos,
                COALESCE(f.fornecedores_unicos, 0) AS fornecedores_unicos
            FROM {CANDIDATE_TABLE} c
            LEFT JOIN {ASSETS_AGG_TABLE} a ON a.candidate_id = c.id
            LEFT JOIN {VOTES_AGG_TABLE} v ON v.candidate_id = c.id
            LEFT JOIN {FINANCE_AGG_TABLE} f ON f.candidate_id = c.id
            WHERE (? = '' OR lower(c.nome_urna) LIKE '%' || ? || '%'
                        OR lower(c.nome_completo) LIKE '%' || ? || '%')
            ORDER BY total_votos DESC, c.nome_urna
            LIMIT ? OFFSET ?
        """

        # Fallbacks para tabelas faltantes
        if not assets_enabled:
            sql = sql.replace(
                f"LEFT JOIN {ASSETS_AGG_TABLE} a",
                "LEFT JOIN (SELECT NULL::BIGINT AS candidate_id, 0::DOUBLE AS total_bens, 0::BIGINT AS qtd_bens LIMIT 0) a",
            )
        if not votes_enabled:
            sql = sql.replace(
                f"LEFT JOIN {VOTES_AGG_TABLE} v",
                "LEFT JOIN (SELECT NULL::BIGINT AS candidate_id, 0::BIGINT AS total_votos LIMIT 0) v",
            )
        if not finance_enabled:
            sql = sql.replace(
                f"LEFT JOIN {FINANCE_AGG_TABLE} f",
                "LEFT JOIN (SELECT NULL::BIGINT AS candidate_id, 0::DOUBLE AS total_receitas, 0::DOUBLE AS total_despesas, 0::BIGINT AS doadores_unicos, 0::BIGINT AS fornecedores_unicos LIMIT 0) f",
            )

        rows = con.execute(sql, [q_norm, q_norm, q_norm, limit, offset]).fetchall()
        con.close()

        items = [
            {
                "id": r[0],
                "numero": r[1],
                "nome_urna": r[2],
                "nome_completo": r[3],
                "partido": r[4],
                "uf": r[5],
                "cargo": r[6],
                "situacao": r[7],
                "total_bens": float(r[8]),
                "qtd_bens": int(r[9]),
                "total_votos": int(r[10]),
                "total_receitas": float(r[11]),
                "total_despesas": float(r[12]),
                "doadores_unicos": int(r[13]),
                "fornecedores_unicos": int(r[14]),
            }
            for r in rows
        ]

        logger.info(f"[API] /candidates: q='{q}', limit={limit}, offset={offset}, found={len(items)}")

        return {
            "items": items,
            "assets_enabled": assets_enabled,
            "votes_enabled": votes_enabled,
            "finance_enabled": finance_enabled,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API ERROR] /candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar candidatos: {str(e)[:100]}",
        )


@app.get("/candidates/{candidate_id}/assets")
def candidate_assets(
    candidate_id: int,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Bens declarados por um candidato.
    
    Args:
        candidate_id: ID do candidato.
        limit: Tamanho da página.
        offset: Deslocamento para paginação.
    
    Returns:
        {"items": [{"tipo": "...", "descricao": "...", "valor": 123.45}]}
    """
    try:
        if not DB_PATH.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Banco de dados não encontrado",
            )

        con = open_db(read_only=True)
        tables = get_tables(con)

        if ASSETS_TABLE not in tables:
            con.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tabela {ASSETS_TABLE} não existe. Execute ETL de bens.",
            )

        rows = con.execute(
            f"""
            SELECT tipo, descricao, valor
            FROM {ASSETS_TABLE}
            WHERE candidate_id = ?
            ORDER BY valor DESC NULLS LAST
            LIMIT ? OFFSET ?
            """,
            [candidate_id, limit, offset],
        ).fetchall()
        con.close()

        items = [{"tipo": str(r[0]) if r[0] else "", "descricao": str(r[1]) if r[1] else "", "valor": float(r[2]) if r[2] else 0.0} for r in rows]
        logger.info(f"[API] /candidates/{candidate_id}/assets: found={len(items)}")

        return {"items": items}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API ERROR] /candidates/{candidate_id}/assets: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar bens: {str(e)[:100]}",
        )


@app.get("/candidates/{candidate_id}/votes_municipio")
def candidate_votes_municipio(
    candidate_id: int,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Votos por município de um candidato.
    
    Args:
        candidate_id: ID do candidato.
        limit: Número máximo de municípios (padrão 20).
    
    Returns:
        {"items": [{"municipio": "São Paulo", "votos": 5000}]}
    """
    try:
        if not DB_PATH.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Banco de dados não encontrado",
            )

        con = open_db(read_only=True)
        tables = get_tables(con)

        if VOTES_MUN_TABLE not in tables:
            con.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tabela {VOTES_MUN_TABLE} não existe. Execute ETL de votos.",
            )

        rows = con.execute(
            f"""
            SELECT municipio, votos_municipio
            FROM {VOTES_MUN_TABLE}
            WHERE candidate_id = ?
            ORDER BY votos_municipio DESC
            LIMIT ?
            """,
            [candidate_id, limit],
        ).fetchall()
        con.close()

        items = [{"municipio": str(r[0]) if r[0] else "", "votos": int(r[1]) if r[1] else 0} for r in rows]
        logger.info(f"[API] /candidates/{candidate_id}/votes_municipio: found={len(items)}")

        return {"items": items}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API ERROR] /candidates/{candidate_id}/votes_municipio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar votos: {str(e)[:100]}",
        )


@app.get("/candidates/{candidate_id}/finance")
def candidate_finance(
    candidate_id: int,
    top: int = 15,
) -> dict[str, Any]:
    """
    Receitas, despesas e top doadores/fornecedores de um candidato.
    
    Args:
        candidate_id: ID do candidato.
        top: Número de top doadores/fornecedores (padrão 15).
    
    Returns:
        {
            "candidate_id": 123,
            "summary": {
                "total_receitas": 10000.0,
                "total_despesas": 8000.0,
                "doadores_unicos": 25,
                "fornecedores_unicos": 10
            },
            "top_doadores": [...],
            "top_fornecedores": [...]
        }
    """
    try:
        if not DB_PATH.exists():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Banco de dados não encontrado",
            )

        con = open_db(read_only=True)
        tables = get_tables(con)

        if FINANCE_AGG_TABLE not in tables:
            con.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tabela {FINANCE_AGG_TABLE} não existe. Execute ETL/agg de finanças.",
            )

        summary = con.execute(
            f"""
            SELECT total_receitas, total_despesas, doadores_unicos, fornecedores_unicos
            FROM {FINANCE_AGG_TABLE}
            WHERE candidate_id = ?
            """,
            [candidate_id],
        ).fetchone()

        if not summary:
            con.close()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidato {candidate_id} não encontrado em dados de finanças",
            )

        top_donors = []
        if DONATIONS_TABLE in tables:
            rows = con.execute(
                f"""
                SELECT
                    COALESCE(NULLIF(TRIM(CAST(doador_nome AS VARCHAR)), ''), '(sem nome)') AS nome,
                    COALESCE(TRIM(CAST(doador_doc AS VARCHAR)), '') AS doc,
                    SUM(COALESCE(valor,0)) AS total
                FROM {DONATIONS_TABLE}
                WHERE candidate_id = ?
                GROUP BY 1,2
                ORDER BY total DESC
                LIMIT ?
                """,
                [candidate_id, top],
            ).fetchall()
            top_donors = [{"nome": str(r[0]) if r[0] else "", "doc": str(r[1]) if r[1] else "", "total": float(r[2]) if r[2] else 0.0} for r in rows]

        top_suppliers = []
        if EXPENSES_TABLE in tables:
            rows = con.execute(
                f"""
                SELECT
                    COALESCE(NULLIF(TRIM(CAST(fornecedor_nome AS VARCHAR)), ''), '(sem nome)') AS nome,
                    COALESCE(TRIM(CAST(fornecedor_doc AS VARCHAR)), '') AS doc,
                    SUM(COALESCE(valor,0)) AS total
                FROM {EXPENSES_TABLE}
                WHERE candidate_id = ?
                GROUP BY 1,2
                ORDER BY total DESC
                LIMIT ?
                """,
                [candidate_id, top],
            ).fetchall()
            top_suppliers = [{"nome": str(r[0]) if r[0] else "", "doc": str(r[1]) if r[1] else "", "total": float(r[2]) if r[2] else 0.0} for r in rows]

        con.close()

        logger.info(f"[API] /candidates/{candidate_id}/finance: donors={len(top_donors)}, suppliers={len(top_suppliers)}")

        return {
            "candidate_id": candidate_id,
            "summary": {
                "total_receitas": float(summary[0]) if summary[0] else 0.0,
                "total_despesas": float(summary[1]) if summary[1] else 0.0,
                "doadores_unicos": int(summary[2]) if summary[2] else 0,
                "fornecedores_unicos": int(summary[3]) if summary[3] else 0,
            },
            "top_doadores": top_donors,
            "top_fornecedores": top_suppliers,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API ERROR] /candidates/{candidate_id}/finance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar finanças: {str(e)[:100]}",
        )
