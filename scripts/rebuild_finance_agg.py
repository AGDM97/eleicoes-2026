from pathlib import Path
import duckdb

DB_PATH = Path("db/eleicoes.duckdb")

CAND_TABLE = "candidates_sp_dep_fed_2022"
DONATIONS_TABLE = "donations_sp_dep_fed_2022"
EXPENSES_TABLE = "expenses_sp_dep_fed_2022"
FINANCE_AGG_TABLE = "finance_agg_sp_dep_fed_2022"


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"DB não encontrado: {DB_PATH}")

    con = duckdb.connect(str(DB_PATH))
    tables = {t[0] for t in con.execute("SHOW TABLES").fetchall()}

    missing = [t for t in (CAND_TABLE, DONATIONS_TABLE, EXPENSES_TABLE) if t not in tables]
    if missing:
        con.close()
        raise SystemExit(f"Faltando tabelas base: {missing}. Rode os ETLs antes.")

    con.execute(f"DROP TABLE IF EXISTS {FINANCE_AGG_TABLE}")
    con.execute(f"""
        CREATE TABLE {FINANCE_AGG_TABLE} AS
        WITH d AS (
            SELECT
                candidate_id,
                SUM(COALESCE(valor,0)) AS total_receitas,
                COUNT(DISTINCT NULLIF(TRIM(CAST(doador_doc AS VARCHAR)), '')) AS doadores_unicos
            FROM {DONATIONS_TABLE}
            GROUP BY 1
        ),
        x AS (
            SELECT
                candidate_id,
                SUM(COALESCE(valor,0)) AS total_despesas,
                COUNT(DISTINCT NULLIF(TRIM(CAST(fornecedor_doc AS VARCHAR)), '')) AS fornecedores_unicos

            FROM {EXPENSES_TABLE}
            GROUP BY 1
        )
        SELECT
            c.id AS candidate_id,
            COALESCE(d.total_receitas,0) AS total_receitas,
            COALESCE(x.total_despesas,0) AS total_despesas,
            COALESCE(d.doadores_unicos,0) AS doadores_unicos,
            COALESCE(x.fornecedores_unicos,0) AS fornecedores_unicos
        FROM {CAND_TABLE} c
        LEFT JOIN d ON d.candidate_id = c.id
        LEFT JOIN x ON x.candidate_id = c.id
    """)

    print("[OK] finance_agg criado:",
          con.execute(f"SELECT COUNT(*), SUM(total_receitas), SUM(total_despesas) FROM {FINANCE_AGG_TABLE}").fetchall())
    con.close()


if __name__ == "__main__":
    main()
