from pathlib import Path

import duckdb
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP("Eleicoes Brasil (MVP)")

DB_PATH = Path("db/eleicoes.duckdb")
TABLE = "candidates_sp_dep_fed_2022"

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "ok"})

@mcp.tool
def search_candidates_sp_dep_fed_2022(q: str = "", limit: int = 25, offset: int = 0) -> dict:
    """
    Busca candidatos (SP / Dep. Federal / 2022) no DuckDB.
    """
    if not DB_PATH.exists():
        return {"items": [], "error": "DB não encontrado. Rode o ETL primeiro."}

    con = duckdb.connect(str(DB_PATH), read_only=True)
    q_norm = q.strip().lower()

    sql = f"""
      SELECT id, numero, nome_urna, partido, situacao
      FROM {TABLE}
      WHERE (? = '' OR lower(nome_urna) LIKE '%' || ? || '%'
                  OR lower(nome_completo) LIKE '%' || ? || '%')
      ORDER BY nome_urna
      LIMIT ? OFFSET ?
    """
    rows = con.execute(sql, [q_norm, q_norm, q_norm, limit, offset]).fetchall()
    con.close()

    items = [{"id": r[0], "numero": r[1], "nome_urna": r[2], "partido": r[3], "situacao": r[4]} for r in rows]
    return {"items": items}

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8001)
