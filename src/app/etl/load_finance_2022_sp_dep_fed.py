from __future__ import annotations

import csv
from pathlib import Path

import duckdb

UF = "SP"

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data" / "tse" / "prestacao_contas_candidatos_2022"
DB_PATH = BASE_DIR / "db" / "eleicoes.duckdb"

CAND_TABLE = "candidates_sp_dep_fed_2022"

DONATIONS_TABLE = "donations_sp_dep_fed_2022"
EXPENSES_TABLE = "expenses_sp_dep_fed_2022"
FINANCE_AGG_TABLE = "finance_agg_sp_dep_fed_2022"

# TSE files
RECEITAS_BASE = "receitas_candidatos_2022"
DESP_PAGAS_BASE = "despesas_pagas_candidatos_2022"
DESP_CONTR_BASE = "despesas_contratadas_candidatos_2022"


def pick_file_prefer_uf(base: str, uf: str) -> Path:
    """Prefere arquivo por UF, senão cai no BRASIL."""
    p_uf = DATA_DIR / f"{base}_{uf}.csv"
    p_br = DATA_DIR / f"{base}_BRASIL.csv"
    if p_uf.exists():
        return p_uf
    if p_br.exists():
        return p_br
    raise FileNotFoundError(f"Não achei {p_uf} nem {p_br}")


def read_header(csv_path: Path) -> list[str]:
    with open(csv_path, "r", encoding="cp1252", newline="") as f:
        r = csv.reader(f, delimiter=";")
        header = next(r)
    return [h.strip().lstrip("\ufeff") for h in header]


def pick_col(cols: set[str], options: list[str]) -> str | None:
    for c in options:
        if c in cols:
            return c
    return None


def detect_sq(header: list[str], preferred: list[str]) -> str | None:
    cols = set(header)
    for p in preferred:
        if p in cols:
            return p
    # heurística: qualquer SQ_ contendo um dos termos
    for h in header:
        u = h.upper()
        if u.startswith("SQ_"):
            for t in preferred:
                if t.upper().replace("SQ_", "") in u:
                    return h
    return None


def detect_by_contains(header: list[str], must_contain: str, prefix: str | None = None) -> str | None:
    mc = must_contain.upper()
    for h in header:
        u = h.upper()
        if mc in u and (prefix is None or u.startswith(prefix.upper())):
            return h
    return None


def br_to_double(expr: str) -> str:
    """
    Converte string BR tipo '1.234,56' ou '600,00' para DOUBLE:
    - remove '.' de milhar
    - troca ',' por '.'
    """
    return (
        "TRY_CAST("
        f"replace(replace(NULLIF(trim(CAST({expr} AS VARCHAR)), ''), '.', ''), ',', '.')"
        " AS DOUBLE)"
    )


def sql_str(s: str) -> str:
    """Escapa string pra SQL."""
    return s.replace("'", "''")


def main() -> None:
    Path("db").mkdir(parents=True, exist_ok=True)

    receitas_csv = pick_file_prefer_uf(RECEITAS_BASE, UF)
    despesas_pagas_csv = pick_file_prefer_uf(DESP_PAGAS_BASE, UF)
    despesas_contr_csv = pick_file_prefer_uf(DESP_CONTR_BASE, UF)

    print("[CSV] receitas:", receitas_csv)
    print("[CSV] despesas pagas:", despesas_pagas_csv)
    print("[CSV] despesas contratadas:", despesas_contr_csv)

    rec_header = read_header(receitas_csv)
    pag_header = read_header(despesas_pagas_csv)
    ctr_header = read_header(despesas_contr_csv)

    rec_cols = set(rec_header)
    pag_cols = set(pag_header)
    ctr_cols = set(ctr_header)

    # --- RECEITAS ---
    rec_sq_cand = pick_col(rec_cols, ["SQ_CANDIDATO"])
    rec_sq_prest = pick_col(rec_cols, ["SQ_PRESTADOR_CONTAS", "SQ_PRESTADOR_CONTA", "SQ_PRESTADOR"])
    if not rec_sq_prest:
        # heurística por contains
        rec_sq_prest = detect_by_contains(rec_header, "PRESTADOR", prefix="SQ_")

    rec_val = pick_col(rec_cols, ["VR_RECEITA"])
    rec_doc = pick_col(rec_cols, ["NR_CPF_CNPJ_DOADOR", "NR_CPF_CNPJ_DOADOR_ORIG", "NR_CPF_CNPJ_DOADOR_ORIGINAL"])
    rec_nome = pick_col(rec_cols, ["NM_DOADOR", "NM_DOADOR_ORIG", "NM_DOADOR_ORIGINAL"])

    if not rec_sq_cand or not rec_sq_prest or not rec_val:
        raise RuntimeError(
            f"Receitas: faltou colunas obrigatórias. SQ_CANDIDATO={rec_sq_cand}, SQ_PRESTADOR={rec_sq_prest}, VR={rec_val}"
        )

    # --- DESPESAS PAGAS ---
    pag_sq_prest = pick_col(pag_cols, ["SQ_PRESTADOR_CONTAS", "SQ_PRESTADOR_CONTA", "SQ_PRESTADOR"])
    if not pag_sq_prest:
        pag_sq_prest = detect_by_contains(pag_header, "PRESTADOR", prefix="SQ_")

    pag_sq_despesa = pick_col(pag_cols, ["SQ_DESPESA"])
    pag_val = pick_col(pag_cols, ["VR_PAGTO_DESPESA", "VR_PAGAMENTO_DESPESA"])

    # fornecedor em pagas (provavelmente não existe)
    pag_for_doc = detect_by_contains(pag_header, "FORNECEDOR", prefix="NR_")
    pag_for_nome = detect_by_contains(pag_header, "FORNECEDOR", prefix="NM_")

    if not pag_sq_prest or not pag_sq_despesa or not pag_val:
        raise RuntimeError(
            f"Despesas pagas: faltou colunas obrigatórias. PRESTADOR={pag_sq_prest}, SQ_DESPESA={pag_sq_despesa}, VR={pag_val}"
        )

    # --- DESPESAS CONTRATADAS (para pegar fornecedor) ---
    ctr_sq_prest = pick_col(ctr_cols, ["SQ_PRESTADOR_CONTAS", "SQ_PRESTADOR_CONTA", "SQ_PRESTADOR"])
    if not ctr_sq_prest:
        ctr_sq_prest = detect_by_contains(ctr_header, "PRESTADOR", prefix="SQ_")

    ctr_sq_despesa = pick_col(ctr_cols, ["SQ_DESPESA"])
    # fornecedor em contratadas (normalmente existe aqui)
    ctr_for_doc = detect_by_contains(ctr_header, "FORNECEDOR", prefix="NR_")
    ctr_for_nome = detect_by_contains(ctr_header, "FORNECEDOR", prefix="NM_")

    if not ctr_sq_prest or not ctr_sq_despesa:
        print("[WARN] despesas contratadas sem SQ_PRESTADOR/SQ_DESPESA. Vou tentar seguir sem join de fornecedor.")

    print("[MAP] receitas:", {"SQ_CAND": rec_sq_cand, "SQ_PREST": rec_sq_prest, "VR": rec_val, "DOC": rec_doc, "NOME": rec_nome})
    print("[MAP] pagas:", {"SQ_PREST": pag_sq_prest, "SQ_DESP": pag_sq_despesa, "VR": pag_val, "DOC": pag_for_doc, "NOME": pag_for_nome})
    print("[MAP] contratadas:", {"SQ_PREST": ctr_sq_prest, "SQ_DESP": ctr_sq_despesa, "DOC": ctr_for_doc, "NOME": ctr_for_nome})

    rec_path = sql_str(receitas_csv.resolve().as_posix())
    pag_path = sql_str(despesas_pagas_csv.resolve().as_posix())
    ctr_path = sql_str(despesas_contr_csv.resolve().as_posix())

    con = duckdb.connect(str(DB_PATH))

    tables = {t[0] for t in con.execute("SHOW TABLES").fetchall()}
    if CAND_TABLE not in tables:
        con.close()
        raise RuntimeError(f"Precisa existir {CAND_TABLE} antes. Rode o ETL de candidatos.")

    # --- DONATIONS (receitas) ---
    con.execute(f"DROP TABLE IF EXISTS {DONATIONS_TABLE}")
    con.execute(
        f"""
        CREATE TABLE {DONATIONS_TABLE} AS
        SELECT
            CAST(r."{rec_sq_cand}" AS BIGINT) AS candidate_id,
            {br_to_double(f'r."{rec_val}"')} AS valor,
            {f"TRIM(CAST(r.\"{rec_doc}\" AS VARCHAR))" if rec_doc else "NULL"} AS doador_doc,
            {f"TRIM(CAST(r.\"{rec_nome}\" AS VARCHAR))" if rec_nome else "NULL"} AS doador_nome
        FROM read_csv_auto(
            '{rec_path}',
            delim=';',
            header=true,
            encoding='CP1252'
        ) r
        WHERE CAST(r."{rec_sq_cand}" AS BIGINT) IN (SELECT id FROM {CAND_TABLE})
        """
    )

    # --- MAPA prestador -> candidato (vem das receitas) ---
    con.execute("DROP TABLE IF EXISTS _prestador_map")
    con.execute(
        f"""
        CREATE TEMP TABLE _prestador_map AS
        SELECT DISTINCT
            CAST(r."{rec_sq_prest}" AS BIGINT) AS prestador_id,
            CAST(r."{rec_sq_cand}" AS BIGINT) AS candidate_id
        FROM read_csv_auto(
            '{rec_path}',
            delim=';',
            header=true,
            encoding='CP1252'
        ) r
        WHERE CAST(r."{rec_sq_cand}" AS BIGINT) IN (SELECT id FROM {CAND_TABLE})
          AND CAST(r."{rec_sq_prest}" AS BIGINT) IS NOT NULL
        """
    )

    # --- EXPENSES (despesas pagas) com fornecedor via join em contratadas ---
    con.execute(f"DROP TABLE IF EXISTS {EXPENSES_TABLE}")

    # Expressões fornecedor: prefere pagas, senão contratadas, senão NULL
    if pag_for_doc:
        fornecedor_doc_expr = f"TRIM(CAST(e.\"{pag_for_doc}\" AS VARCHAR))"
    elif ctr_for_doc:
        fornecedor_doc_expr = f"TRIM(CAST(c.\"{ctr_for_doc}\" AS VARCHAR))"
    else:
        fornecedor_doc_expr = "NULL"

    if pag_for_nome:
        fornecedor_nome_expr = f"TRIM(CAST(e.\"{pag_for_nome}\" AS VARCHAR))"
    elif ctr_for_nome:
        fornecedor_nome_expr = f"TRIM(CAST(c.\"{ctr_for_nome}\" AS VARCHAR))"
    else:
        fornecedor_nome_expr = "NULL"

    # Join contratadas só se tiver chaves
    join_contratadas = ""
    if ctr_sq_prest and ctr_sq_despesa:
        join_contratadas = f"""
        LEFT JOIN read_csv_auto(
            '{ctr_path}',
            delim=';',
            header=true,
            encoding='CP1252'
        ) c
          ON CAST(c."{ctr_sq_prest}" AS BIGINT) = CAST(e."{pag_sq_prest}" AS BIGINT)
         AND CAST(c."{ctr_sq_despesa}" AS BIGINT) = CAST(e."{pag_sq_despesa}" AS BIGINT)
        """

    con.execute(
        f"""
        CREATE TABLE {EXPENSES_TABLE} AS
        SELECT
            pm.candidate_id AS candidate_id,
            {br_to_double(f'e."{pag_val}"')} AS valor,
            {fornecedor_doc_expr} AS fornecedor_doc,
            {fornecedor_nome_expr} AS fornecedor_nome
        FROM read_csv_auto(
            '{pag_path}',
            delim=';',
            header=true,
            encoding='CP1252'
        ) e
        JOIN _prestador_map pm
          ON pm.prestador_id = CAST(e."{pag_sq_prest}" AS BIGINT)
        {join_contratadas}
        WHERE pm.candidate_id IN (SELECT id FROM {CAND_TABLE})
        """
    )

    # --- AGG ---
    con.execute(f"DROP TABLE IF EXISTS {FINANCE_AGG_TABLE}")
    con.execute(
        f"""
        CREATE TABLE {FINANCE_AGG_TABLE} AS
        WITH d AS (
            SELECT
              candidate_id,
              SUM(COALESCE(valor, 0)) AS total_receitas,
              COUNT(DISTINCT NULLIF(TRIM(CAST(doador_doc AS VARCHAR)), '')) AS doadores_unicos
            FROM {DONATIONS_TABLE}
            GROUP BY 1
        ),
        x AS (
            SELECT
              candidate_id,
              SUM(COALESCE(valor, 0)) AS total_despesas,
              COUNT(DISTINCT NULLIF(TRIM(CAST(fornecedor_doc AS VARCHAR)), '')) AS fornecedores_unicos
            FROM {EXPENSES_TABLE}
            GROUP BY 1
        )
        SELECT
          c.id AS candidate_id,
          COALESCE(d.total_receitas, 0) AS total_receitas,
          COALESCE(x.total_despesas, 0) AS total_despesas,
          COALESCE(d.doadores_unicos, 0) AS doadores_unicos,
          COALESCE(x.fornecedores_unicos, 0) AS fornecedores_unicos
        FROM {CAND_TABLE} c
        LEFT JOIN d ON d.candidate_id = c.id
        LEFT JOIN x ON x.candidate_id = c.id
        """
    )

    # --- CHECKS ---
    print(
        "[CHK] donations rows/nulls/min/max:",
        con.execute(
            f"SELECT COUNT(*), SUM(CASE WHEN valor IS NULL THEN 1 ELSE 0 END), MIN(valor), MAX(valor) FROM {DONATIONS_TABLE}"
        ).fetchall(),
    )
    print(
        "[CHK] expenses rows/nulls/min/max:",
        con.execute(
            f"SELECT COUNT(*), SUM(CASE WHEN valor IS NULL THEN 1 ELSE 0 END), MIN(valor), MAX(valor) FROM {EXPENSES_TABLE}"
        ).fetchall(),
    )
    print(
        "[CHK] expenses fornecedor vazio:",
        con.execute(
            f"""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN fornecedor_nome IS NULL OR TRIM(CAST(fornecedor_nome AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS sem_nome,
              SUM(CASE WHEN fornecedor_doc IS NULL OR TRIM(CAST(fornecedor_doc AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS sem_doc
            FROM {EXPENSES_TABLE}
            """
        ).fetchall(),
    )
    print(
        "[CHK] agg top3:",
        con.execute(
            f"SELECT * FROM {FINANCE_AGG_TABLE} ORDER BY total_receitas DESC LIMIT 3"
        ).fetchall(),
    )

    con.close()
    print("[OK] finanças carregadas e agregadas:", DB_PATH)


if __name__ == "__main__":
    main()
