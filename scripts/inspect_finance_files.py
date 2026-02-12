from __future__ import annotations

import csv
from pathlib import Path
import duckdb

DATA_DIR = Path("data/tse/prestacao_contas_candidatos_2022")

def find_files():
    files = []
    for ext in ("*.csv", "*.txt"):
        files += list(DATA_DIR.rglob(ext))
    return files

def read_header(p: Path):
    with open(p, "r", encoding="cp1252", newline="") as f:
        r = csv.reader(f, delimiter=";")
        header = next(r)
    return [h.strip().lstrip("\ufeff") for h in header]

def main():
    files = find_files()
    if not files:
        raise SystemExit(f"Nenhum arquivo encontrado em {DATA_DIR}")

    print(f"[OK] arquivos encontrados: {len(files)}")

    # pega os 2 primeiros arquivos "grandes" pra inspecionar
    files = sorted(files, key=lambda x: x.stat().st_size, reverse=True)[:4]

    con = duckdb.connect()

    for p in files:
        header = read_header(p)
        cols = set(header)

        # lista colunas que parecem valor
        candidates = [c for c in header if c.upper().startswith("VR_") or "VALOR" in c.upper()]
        print("\n===============================")
        print("ARQUIVO:", p)
        print("TAMANHO:", p.stat().st_size)
        print("COLUNAS VR_/VALOR:", candidates[:50])

        if not candidates:
            continue

        # tenta selecionar as colunas candidatas (as 5 primeiras) e mostra 5 linhas
        pick = candidates[:5]
        pick_sql = ", ".join([f'"{c}"' for c in pick])
        path_sql = p.resolve().as_posix().replace("'", "''")

        q = f"""
        SELECT {pick_sql}
        FROM read_csv_auto('{path_sql}', delim=';', header=true, encoding='CP1252')
        LIMIT 5
        """
        try:
            rows = con.execute(q).fetchall()
            print("AMOSTRA 5 LINHAS (colunas escolhidas):")
            for r in rows:
                print(r)
        except Exception as e:
            print("ERRO lendo amostra:", e)

    con.close()

if __name__ == "__main__":
    main()
