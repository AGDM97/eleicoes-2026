from __future__ import annotations

import csv
import zipfile
from pathlib import Path
from typing import Optional

import duckdb
import httpx

TSE_CAND_2022_ZIP_URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2022.zip"
)

ZIP_PATH = Path("data/tse/consulta_cand_2022.zip")
EXTRACT_DIR = Path("data/tse/consulta_cand_2022")
DB_PATH = Path("db/eleicoes.duckdb")

UF = "SP"
CARGO_LIKE = "DEPUTADO FEDERAL"


def download_zip(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[OK] ZIP já existe: {dest}")
        return

    print(f"[DL] Baixando: {url}")
    with httpx.stream("GET", url, timeout=120) as r:
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

    # Preferir o arquivo BRASIL
    brasil = [p for p in csvs if "BRASIL" in p.name.upper()]
    chosen = brasil[0] if brasil else csvs[0]
    print(f"[CSV] Usando: {chosen}")
    return chosen


def read_header_columns(csv_path: Path) -> set[str]:
    # O arquivo do TSE costuma ser CP1252 no Windows
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

    # 1) Baixa + extrai
    download_zip(TSE_CAND_2022_ZIP_URL, ZIP_PATH)
    extract_zip(ZIP_PATH, EXTRACT_DIR)
    csv_path = pick_csv(EXTRACT_DIR)

    # 2) Caminho absoluto em formato POSIX (evita escapes \t \n no SQL)
    csv_path_sql = csv_path.resolve().as_posix().replace("'", "''")
    print("[FS] CSV absoluto:", csv_path_sql)

    # 3) Detecta colunas disponíveis no CSV (evita Binder Error)
    cols = read_header_columns(csv_path)
    detalhe_col = pick_optional_column(
        cols,
        [
            "DS_DETALHE_SITUACAO_CAND",
            "DS_DETALHE_SITUACAO_CANDIDATURA",
            "DS_DETALHE_SITUACAO",
        ],
    )
    detalhe_expr = f"{detalhe_col} AS detalhe_situacao" if detalhe_col else "NULL AS detalhe_situacao"
    print("[CSV] detalhe_col:", detalhe_col if detalhe_col else "None (vai virar NULL)")

    # 4) Conecta no DuckDB e cria tabela filtrada (SP + Dep. Federal)
    con = duckdb.connect(str(DB_PATH))

    con.execute("DROP TABLE IF EXISTS candidates_sp_dep_fed_2022")

    create_sql = f"""
    CREATE TABLE candidates_sp_dep_fed_2022 AS
    SELECT
      CAST(SQ_CANDIDATO AS BIGINT) AS id,
      NR_CANDIDATO               AS numero,
      NM_URNA_CANDIDATO          AS nome_urna,
      NM_CANDIDATO               AS nome_completo,
      SG_PARTIDO                 AS partido,
      SG_UF                      AS uf,
      DS_CARGO                   AS cargo,
      DS_SITUACAO_CANDIDATURA    AS situacao,
      {detalhe_expr},
      DS_OCUPACAO                AS ocupacao,
      DS_GRAU_INSTRUCAO          AS escolaridade,
      DS_ESTADO_CIVIL            AS estado_civil,
      DS_GENERO                  AS genero,
      DT_NASCIMENTO              AS dt_nascimento
    FROM read_csv_auto(
      '{csv_path_sql}',
      delim=';',
      header=true,
      encoding='CP1252'
    )
    WHERE SG_UF = '{UF}'
      AND DS_CARGO ILIKE '{CARGO_LIKE}%'
    ;
    """

    con.execute(create_sql)

    total = con.execute("SELECT COUNT(*) FROM candidates_sp_dep_fed_2022").fetchone()[0]
    print(f"[DB] Linhas carregadas: {total}")

    sample = con.execute(
        """
        SELECT id, numero, nome_urna, partido, uf, cargo, situacao
        FROM candidates_sp_dep_fed_2022
        ORDER BY nome_urna
        LIMIT 5
        """
    ).fetchall()
    print("[DB] Amostra (5):")
    for row in sample:
        print("  ", row)

    con.close()
    print(f"[OK] DuckDB pronto em: {DB_PATH.resolve()}")


if __name__ == "__main__":
    main()
