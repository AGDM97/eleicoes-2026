from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from typing import Optional

import duckdb
import httpx

# Fonte oficial (TSE)
TSE_VOTOS_2022_ZIP_URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    "votacao_candidato_munzona/votacao_candidato_munzona_2022.zip"
)

ZIP_PATH = Path("data/tse/votacao_candidato_munzona_2022.zip")
EXTRACT_DIR = Path("data/tse/votacao_candidato_munzona_2022")
DB_PATH = Path("db/eleicoes.duckdb")

CAND_TABLE = "candidates_sp_dep_fed_2022"
VOTES_RAW_TABLE = "votes_munzona_sp_dep_fed_2022"
VOTES_AGG_TABLE = "votes_agg_sp_dep_fed_2022"
VOTES_MUN_TABLE = "votes_municipio_agg_sp_dep_fed_2022"

UF = "SP"
CARGO_LIKE = "DEPUTADO FEDERAL"


def download_zip(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[OK] ZIP já existe: {dest}")
        return

    print(f"[DL] Baixando: {url}")
    with httpx.stream("GET", url, timeout=300) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    print(f"[OK] Salvo em: {dest}")


def extract_zip(zip_path: Path, out_dir: Path) -> None:
    if out_dir.exists() and any(out_dir.rglob("*.csv")):
        print(f"[OK] Já extraído: {out_dir}")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[UNZIP] Extraindo: {zip_path} -> {out_dir}")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)
    print("[OK] Extração concluída")


def pick_csv(extract_dir: Path) -> Path:
    csvs = list(extract_dir.rglob("*.csv"))
    if not csvs:
        raise FileNotFoundError("Não encontrei nenhum .csv dentro do ZIP extraído.")
    brasil = [p for p in csvs if "BRASIL" in p.name.upper()]
    chosen = brasil[0] if brasil else csvs[0]
    print(f"[CSV] Usando: {chosen}")
    return chosen


def read_header_columns(csv_path: Path) -> set[str]:
    with open(csv_path, "r", encoding="cp1252", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader)
    header = [h.strip().lstrip("\ufeff") for h in header]
    return set(header)


def pick_optional_column(cols: set[str], options: list[str]) -> Optional[str]:
    for c in options:
        if c in cols:
            return c
    return None


def main() -> None:
    Path("db").mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    tables = {t[0] for t in con.execute("SHOW TABLES").fetchall()}
    if CAND_TABLE not in tables:
        con.close()
        raise RuntimeError(f"Tabela {CAND_TABLE} não existe. Rode o ETL de candidatos primeiro.")

    download_zip(TSE_VOTOS_2022_ZIP_URL, ZIP_PATH)
    extract_zip(ZIP_PATH, EXTRACT_DIR)
    csv_path = pick_csv(EXTRACT_DIR)

    csv_path_sql = csv_path.resolve().as_posix().replace("'", "''")
    print("[FS] CSV absoluto:", csv_path_sql)

    cols = read_header_columns(csv_path)

    # essenciais
    cand_col = pick_optional_column(cols, ["SQ_CANDIDATO"])
    if not cand_col:
        con.close()
        raise RuntimeError("Não encontrei SQ_CANDIDATO no arquivo de votação.")

    votos_col = pick_optional_column(
        cols,
        [
            "QT_VOTOS_NOMINAIS",
            "QT_VOTOS_NOMINAIS_VALIDOS",
            "QT_VOTOS",
            "QT_VOTOS_VALIDOS",
        ],
    )
    if not votos_col:
        con.close()
        raise RuntimeError("Não encontrei coluna de votos (QT_*) no arquivo.")

    # opcionais úteis para drill-down
    mun_nome_col = pick_optional_column(cols, ["NM_MUNICIPIO"])
    mun_cd_col = pick_optional_column(cols, ["CD_MUNICIPIO"])
    zona_col = pick_optional_column(cols, ["NR_ZONA"])
    turno_col = pick_optional_column(cols, ["NR_TURNO"])
    uf_col = pick_optional_column(cols, ["SG_UF"])
    cargo_col = pick_optional_column(cols, ["DS_CARGO"])

    print("[CSV] votos_col:", votos_col)
    print("[CSV] NM_MUNICIPIO:", mun_nome_col or "None")
    print("[CSV] NR_ZONA:", zona_col or "None")
    print("[CSV] NR_TURNO:", turno_col or "None")
    print("[CSV] SG_UF:", uf_col or "None")
    print("[CSV] DS_CARGO:", cargo_col or "None")

    # expressões seguras
    mun_nome_expr = f"{mun_nome_col} AS municipio" if mun_nome_col else "NULL AS municipio"
    mun_cd_expr = f"CAST({mun_cd_col} AS INTEGER) AS cd_municipio" if mun_cd_col else "NULL AS cd_municipio"
    zona_expr = f"CAST({zona_col} AS INTEGER) AS zona" if zona_col else "NULL AS zona"
    turno_expr = f"CAST({turno_col} AS INTEGER) AS turno" if turno_col else "NULL AS turno"

    votos_expr = f"TRY_CAST({votos_col} AS BIGINT) AS votos"

    # filtros opcionais (se as colunas existirem, reduz o volume)
    where_parts = []
    if uf_col:
        where_parts.append(f"b.{uf_col} = '{UF}'")
    if cargo_col:
        where_parts.append(f"b.{cargo_col} ILIKE '{CARGO_LIKE}%'")
    if turno_col:
        where_parts.append("b.NR_TURNO = 1")  # Dep. Federal só 1º turno (seguro e reduz)
    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

    con.execute(f"DROP TABLE IF EXISTS {VOTES_RAW_TABLE}")
    con.execute(f"DROP TABLE IF EXISTS {VOTES_AGG_TABLE}")
    con.execute(f"DROP TABLE IF EXISTS {VOTES_MUN_TABLE}")

    create_raw_sql = f"""
    CREATE TABLE {VOTES_RAW_TABLE} AS
    SELECT
      CAST(b.{cand_col} AS BIGINT) AS candidate_id,
      {mun_nome_expr},
      {mun_cd_expr},
      {zona_expr},
      {turno_expr},
      {votos_expr}
    FROM read_csv_auto(
      '{csv_path_sql}',
      delim=';',
      header=true,
      encoding='CP1252'
    ) b
    INNER JOIN {CAND_TABLE} c
      ON CAST(b.{cand_col} AS BIGINT) = c.id
    {where_sql}
    ;
    """
    con.execute(create_raw_sql)

    con.execute(f"""
    CREATE TABLE {VOTES_AGG_TABLE} AS
    SELECT
      candidate_id,
      SUM(COALESCE(votos, 0)) AS total_votos
    FROM {VOTES_RAW_TABLE}
    GROUP BY candidate_id
    ;
    """)

    con.execute(f"""
    CREATE TABLE {VOTES_MUN_TABLE} AS
    SELECT
      candidate_id,
      municipio,
      SUM(COALESCE(votos, 0)) AS votos_municipio
    FROM {VOTES_RAW_TABLE}
    GROUP BY candidate_id, municipio
    ;
    """)

    raw_n = con.execute(f"SELECT COUNT(*) FROM {VOTES_RAW_TABLE}").fetchone()[0]
    agg_n = con.execute(f"SELECT COUNT(*) FROM {VOTES_AGG_TABLE}").fetchone()[0]
    print(f"[DB] Votos RAW linhas: {raw_n}")
    print(f"[DB] Votos agregados (candidatos): {agg_n}")

    sample = con.execute(f"""
      SELECT candidate_id, total_votos
      FROM {VOTES_AGG_TABLE}
      ORDER BY total_votos DESC
      LIMIT 5
    """).fetchall()
    print("[DB] Top 5 votos (amostra):")
    for row in sample:
        print("  ", row)

    con.close()
    print("[OK] ETL de votos finalizado.")


if __name__ == "__main__":
    main()
