from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from typing import Optional

import duckdb
import httpx

TSE_BENS_2022_ZIP_URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/bem_candidato/bem_candidato_2022.zip"
)

ZIP_PATH = Path("data/tse/bem_candidato_2022.zip")
EXTRACT_DIR = Path("data/tse/bem_candidato_2022")
DB_PATH = Path("db/eleicoes.duckdb")

CAND_TABLE = "candidates_sp_dep_fed_2022"
ASSETS_TABLE = "assets_sp_dep_fed_2022"
ASSETS_AGG_TABLE = "assets_agg_sp_dep_fed_2022"


def download_zip(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[OK] ZIP já existe: {dest}")
        return

    print(f"[DL] Baixando: {url}")
    with httpx.stream("GET", url, timeout=180) as r:
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

    download_zip(TSE_BENS_2022_ZIP_URL, ZIP_PATH)
    extract_zip(ZIP_PATH, EXTRACT_DIR)
    csv_path = pick_csv(EXTRACT_DIR)

    csv_path_sql = csv_path.resolve().as_posix().replace("'", "''")
    print("[FS] CSV absoluto:", csv_path_sql)

    cols = read_header_columns(csv_path)

    # nomes de colunas podem variar; tentamos algumas opções
    tipo_col = pick_optional_column(cols, ["DS_TIPO_BEM_CANDIDATO", "DS_TIPO_BEM"])
    desc_col = pick_optional_column(cols, ["DS_BEM_CANDIDATO", "DS_BEM"])
    valor_col = pick_optional_column(cols, ["VR_BEM_CANDIDATO", "VR_BEM"])

    if not valor_col:
        con.close()
        raise RuntimeError("Não encontrei coluna de valor (VR_BEM_CANDIDATO / VR_BEM).")

    print("[CSV] tipo_col:", tipo_col or "None (vai virar NULL)")
    print("[CSV] desc_col:", desc_col or "None (vai virar NULL)")
    print("[CSV] valor_col:", valor_col)

    tipo_expr = f"{tipo_col} AS tipo" if tipo_col else "NULL AS tipo"
    desc_expr = f"{desc_col} AS descricao" if desc_col else "NULL AS descricao"

    # normaliza valor: remove '.' milhares e troca ',' por '.'
    valor_expr = f"""
    TRY_CAST(
      REPLACE(
        REPLACE(CAST({valor_col} AS VARCHAR), '.', ''),
        ',', '.'
      ) AS DOUBLE
    ) AS valor
    """

    con.execute(f"DROP TABLE IF EXISTS {ASSETS_TABLE}")
    con.execute(f"DROP TABLE IF EXISTS {ASSETS_AGG_TABLE}")

    # Importa bens apenas dos candidatos do seu recorte (join por SQ_CANDIDATO)
    create_assets_sql = f"""
    CREATE TABLE {ASSETS_TABLE} AS
    SELECT
      CAST(b.SQ_CANDIDATO AS BIGINT) AS candidate_id,
      {tipo_expr},
      {desc_expr},
      {valor_expr}
    FROM read_csv_auto(
      '{csv_path_sql}',
      delim=';',
      header=true,
      encoding='CP1252'
    ) b
    INNER JOIN {CAND_TABLE} c
      ON CAST(b.SQ_CANDIDATO AS BIGINT) = c.id
    ;
    """
    con.execute(create_assets_sql)

    con.execute(f"""
    CREATE TABLE {ASSETS_AGG_TABLE} AS
    SELECT
      candidate_id,
      SUM(COALESCE(valor, 0)) AS total_bens,
      COUNT(*) AS qtd_bens
    FROM {ASSETS_TABLE}
    GROUP BY candidate_id
    ;
    """)

    total_rows = con.execute(f"SELECT COUNT(*) FROM {ASSETS_TABLE}").fetchone()[0]
    total_cands = con.execute(f"SELECT COUNT(*) FROM {ASSETS_AGG_TABLE}").fetchone()[0]
    print(f"[DB] Bens carregados (linhas): {total_rows}")
    print(f"[DB] Candidatos com bens (agregado): {total_cands}")

    sample = con.execute(f"""
      SELECT candidate_id, total_bens, qtd_bens
      FROM {ASSETS_AGG_TABLE}
      ORDER BY total_bens DESC
      LIMIT 5
    """).fetchall()
    print("[DB] Top 5 por patrimônio (amostra):")
    for row in sample:
        print("  ", row)

    con.close()
    print("[OK] ETL de bens finalizado.")


if __name__ == "__main__":
    main()
