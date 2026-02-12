from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st


# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Eleições Dashboard (MVP)", layout="wide")

DEFAULT_API_BASE = "http://127.0.0.1:8000"


# -----------------------------
# State
# -----------------------------
if "presentation_mode" not in st.session_state:
    st.session_state.presentation_mode = False

if "page" not in st.session_state:
    st.session_state.page = 1

if "last_filters" not in st.session_state:
    st.session_state.last_filters = {"q": "", "page_size": 50, "sort_key": "Votos (desc)", "api_base": DEFAULT_API_BASE}


# -----------------------------
# CSS (toggleable)
# -----------------------------
def apply_css(presentation: bool) -> None:
    base_css = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none !important;}
.block-container {padding-top: 1.1rem; padding-bottom: 1.2rem;}
section[data-testid="stSidebar"] .block-container {padding-top: 1.0rem;}
</style>
"""
    if presentation:
        # Esconde sidebar e reduz ruído visual
        pres_css = """
<style>
section[data-testid="stSidebar"] {display:none !important;}
div[data-testid="stSidebarNav"] {display:none !important;}
.block-container {padding-left: 2rem; padding-right: 2rem;}
</style>
"""
        st.markdown(base_css + pres_css, unsafe_allow_html=True)
    else:
        st.markdown(base_css, unsafe_allow_html=True)


apply_css(st.session_state.presentation_mode)


# -----------------------------
# HTTP helpers
# -----------------------------
def _normalize_base_url(base_url: str) -> str:
    base = (base_url or "").strip()
    if not base:
        return DEFAULT_API_BASE
    return base.rstrip("/")


def _get_json(url: str, params: Optional[dict] = None, timeout: float = 10.0) -> Dict[str, Any]:
    try:
        r = requests.get(url, params=params, timeout=timeout)
        if r.status_code >= 400:
            text = (r.text or "").strip()
            return {"error": f"HTTP {r.status_code}", "details": text[:1200], "url": url}
        try:
            return r.json()
        except Exception:
            text = (r.text or "").strip()
            return {"error": "Resposta não-JSON", "details": text[:1200], "url": url}
    except requests.exceptions.RequestException as e:
        return {"error": "Falha de rede", "details": str(e), "url": url}


@st.cache_data(ttl=15)
def fetch_health(base_url: str) -> Dict[str, Any]:
    base_url = _normalize_base_url(base_url)
    return _get_json(f"{base_url}/health", timeout=5.0)


@st.cache_data(ttl=15)
def fetch_candidates(base_url: str, q: str, limit: int, offset: int) -> Dict[str, Any]:
    base_url = _normalize_base_url(base_url)
    return _get_json(
        f"{base_url}/candidates",
        params={"q": q or "", "limit": int(limit), "offset": int(offset)},
        timeout=25.0,
    )


@st.cache_data(ttl=60)
def fetch_candidate_finance(base_url: str, candidate_id: int, top: int) -> Dict[str, Any]:
    base_url = _normalize_base_url(base_url)
    return _get_json(
        f"{base_url}/candidates/{int(candidate_id)}/finance",
        params={"top": int(top)},
        timeout=25.0,
    )


@st.cache_data(ttl=120)
def fetch_candidate_votes_mun(base_url: str, candidate_id: int, limit: int) -> Dict[str, Any]:
    base_url = _normalize_base_url(base_url)
    return _get_json(
        f"{base_url}/candidates/{int(candidate_id)}/votes_municipio",
        params={"limit": int(limit)},
        timeout=25.0,
    )


@st.cache_data(ttl=120)
def fetch_candidate_assets(base_url: str, candidate_id: int, limit: int, offset: int) -> Dict[str, Any]:
    base_url = _normalize_base_url(base_url)
    return _get_json(
        f"{base_url}/candidates/{int(candidate_id)}/assets",
        params={"limit": int(limit), "offset": int(offset)},
        timeout=25.0,
    )


# -----------------------------
# Utils
# -----------------------------
def safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def safe_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def df_from_items(items: List[Dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(items or [])


def br_money(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def sort_df(df: pd.DataFrame, sort_key: str) -> pd.DataFrame:
    if df.empty:
        return df

    mapping = {
        "Votos (desc)": ("total_votos", False),
        "Receitas (desc)": ("total_receitas", False),
        "Despesas (desc)": ("total_despesas", False),
        "Nome (asc)": ("nome_urna", True),
    }
    col, asc = mapping.get(sort_key, ("total_votos", False))

    out = df.copy()
    if col in out.columns and col != "nome_urna":
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    if "nome_urna" in out.columns and col != "nome_urna":
        return out.sort_values(by=[col, "nome_urna"], ascending=[asc, True])
    if col in out.columns:
        return out.sort_values(by=[col], ascending=[asc])
    return out


def reset_page_if_filters_changed(api_base: str, q: str, page_size: int, sort_key: str) -> None:
    current = {"api_base": api_base, "q": q, "page_size": page_size, "sort_key": sort_key}
    if current != st.session_state.last_filters:
        st.session_state.page = 1
        st.session_state.last_filters = current


# -----------------------------
# Sidebar (minimal + advanced)
# -----------------------------
if not st.session_state.presentation_mode:
    st.sidebar.header("Config")

    api_base = st.sidebar.text_input("API Base URL", value=st.session_state.last_filters.get("api_base", DEFAULT_API_BASE))
    api_base = _normalize_base_url(api_base)

    q = st.sidebar.text_input("Buscar (nome/urna)", value=st.session_state.last_filters.get("q", "silva"))

    with st.sidebar.expander("Avançado", expanded=False):
        page_size = st.selectbox("Page size", options=[10, 25, 50, 100], index=2)
        sort_key = st.selectbox(
            "Ordenar por",
            options=["Votos (desc)", "Receitas (desc)", "Despesas (desc)", "Nome (asc)"],
            index=0,
        )
        top_n = st.slider("Top (doadores/fornecedores)", min_value=5, max_value=30, value=10, step=5)
        show_debug = st.toggle("Mostrar diagnóstico", value=False)

        st.divider()
        st.caption("Rodar API (terminal):")
        st.code(
            "python -m uvicorn src.app.api.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir src",
            language="bash",
        )
else:
    # Modo apresentação: defaults e sem sidebar
    api_base = st.session_state.last_filters.get("api_base", DEFAULT_API_BASE)
    q = st.session_state.last_filters.get("q", "silva")
    page_size = st.session_state.last_filters.get("page_size", 50)
    sort_key = st.session_state.last_filters.get("sort_key", "Votos (desc)")
    top_n = 10
    show_debug = False

api_base = _normalize_base_url(api_base)
reset_page_if_filters_changed(api_base, q, int(page_size), sort_key)


# -----------------------------
# Header (clean)
# -----------------------------
h1, h2 = st.columns([8, 2])
with h1:
    st.title("🗳️ Eleições Dashboard (MVP)")
    st.caption("FastAPI + DuckDB + Streamlit — consumo via API local")

with h2:
    # Botão no topo (funciona mesmo com sidebar escondida)
    if st.session_state.presentation_mode:
        if st.button("Sair do modo apresentação", use_container_width=True):
            st.session_state.presentation_mode = False
            apply_css(False)
            st.rerun()
    else:
        if st.button("Modo apresentação", use_container_width=True):
            st.session_state.presentation_mode = True
            apply_css(True)
            st.rerun()

health = fetch_health(api_base)
if "error" in health:
    st.error("API offline")
    if show_debug:
        st.write(health)
    st.stop()

db_exists = bool(health.get("db_exists", False))

c1, c2, c3 = st.columns([1, 1, 6])
with c1:
    st.success("API OK")
with c2:
    # ✅ SEM “magic” (sem ternário solto)
    if db_exists:
        st.success("DB OK")
    else:
        st.warning("DB?")

if show_debug:
    st.write({"base_url": api_base, "health": health})

st.divider()


# -----------------------------
# Fetch list
# -----------------------------
page = int(st.session_state.page)
offset = (page - 1) * int(page_size)

resp = fetch_candidates(api_base, q=q, limit=int(page_size), offset=int(offset))
if "error" in resp:
    st.error("Erro ao buscar candidatos")
    if show_debug:
        st.write(resp)
    st.stop()

items = resp.get("items", []) or []
df = df_from_items(items)

# garante colunas mínimas
for col in ["id", "nome_urna", "partido", "total_votos", "total_receitas", "total_despesas"]:
    if col not in df.columns:
        df[col] = 0

for col in ["total_bens", "qtd_bens", "doadores_unicos", "fornecedores_unicos", "situacao", "numero"]:
    if col not in df.columns:
        df[col] = 0

df = sort_df(df, sort_key)


# -----------------------------
# Pagination (buttons)
# -----------------------------
nav1, nav2, nav3, nav4 = st.columns([1.2, 1.2, 2.5, 5.1])

has_prev = page > 1
has_next = len(items) == int(page_size)  # heurística

with nav1:
    if st.button("⬅️ Anterior", disabled=not has_prev, use_container_width=True):
        st.session_state.page = max(1, page - 1)
        st.rerun()

with nav2:
    if st.button("Próxima ➡️", disabled=not has_next, use_container_width=True):
        st.session_state.page = page + 1
        st.rerun()

with nav3:
    st.markdown(f"**Página:** {page}")

with nav4:
    # limpa ruído: sem "Mostrando X itens..." (só um hint discreto)
    st.caption(f"Page size: {page_size} • Ordenação: {sort_key}" if not st.session_state.presentation_mode else "")


# -----------------------------
# Main table (clean + currency formatting)
# -----------------------------
st.subheader("Resultados")

view = df[["id", "nome_urna", "partido", "total_votos", "total_receitas", "total_despesas", "total_bens", "qtd_bens"]].copy()
view = view.rename(
    columns={
        "id": "ID",
        "nome_urna": "Nome",
        "partido": "Partido",
        "total_votos": "Votos",
        "total_receitas": "Receitas",
        "total_despesas": "Despesas",
        "total_bens": "Bens",
        "qtd_bens": "Qtd. bens",
    }
)

st.dataframe(
    view,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Votos": st.column_config.NumberColumn(format="%d"),
        "Receitas": st.column_config.NumberColumn(format="R$ %.2f"),
        "Despesas": st.column_config.NumberColumn(format="R$ %.2f"),
        "Bens": st.column_config.NumberColumn(format="R$ %.2f"),
        "Qtd. bens": st.column_config.NumberColumn(format="%d"),
    },
)

st.divider()


# -----------------------------
# Details
# -----------------------------
with st.expander("Detalhes do candidato", expanded=False):
    if df.empty:
        st.info("Sem resultados.")
        st.stop()

    id_list = df["id"].astype("int64", errors="ignore").tolist()

    label_map: Dict[int, str] = {}
    for _, row in df.iterrows():
        cid = int(row["id"])
        nome = str(row.get("nome_urna", "")).strip()
        partido = str(row.get("partido", "")).strip()
        votos = safe_int(row.get("total_votos", 0))
        label_map[cid] = f"{nome} ({partido}) — {votos} votos"

    selected_id = st.selectbox(
        "Selecione",
        options=id_list,
        index=0,
        format_func=lambda cid: label_map.get(int(cid), str(cid)),
    )

    selected_row = df[df["id"] == selected_id].head(1)
    row = selected_row.iloc[0].to_dict() if not selected_row.empty else {}

    finance = fetch_candidate_finance(api_base, selected_id, top=int(top_n))
    votes_mun = fetch_candidate_votes_mun(api_base, selected_id, limit=20)
    assets = fetch_candidate_assets(api_base, selected_id, limit=200, offset=0)

    tab1, tab2, tab3 = st.tabs(["Visão geral", "Finanças", "Votos/Bens"])

    with tab1:
        nome = str(row.get("nome_urna", "")).strip()
        partido = str(row.get("partido", "")).strip()
        numero = safe_int(row.get("numero", 0))
        situacao = str(row.get("situacao", "")).strip()
        total_votos = safe_int(row.get("total_votos", 0))
        total_bens = safe_float(row.get("total_bens", 0))

        if "error" in finance:
            total_receitas = safe_float(row.get("total_receitas", 0))
            total_despesas = safe_float(row.get("total_despesas", 0))
            doadores_unicos = safe_int(row.get("doadores_unicos", 0))
            fornecedores_unicos = safe_int(row.get("fornecedores_unicos", 0))
        else:
            s = finance.get("summary", {}) or {}
            total_receitas = safe_float(s.get("total_receitas", row.get("total_receitas", 0)))
            total_despesas = safe_float(s.get("total_despesas", row.get("total_despesas", 0)))
            doadores_unicos = safe_int(s.get("doadores_unicos", row.get("doadores_unicos", 0)))
            fornecedores_unicos = safe_int(s.get("fornecedores_unicos", row.get("fornecedores_unicos", 0)))

        saldo = total_receitas - total_despesas

        st.markdown(f"**{nome}** • {partido} • Nº {numero} • {situacao}")

        a, b, c, d, e = st.columns(5)
        a.metric("Votos", f"{total_votos:,}".replace(",", "."))
        b.metric("Receitas", br_money(total_receitas))
        c.metric("Despesas", br_money(total_despesas))
        d.metric("Saldo", br_money(saldo))
        e.metric("Bens", br_money(total_bens))

        st.caption(f"Doadores: {doadores_unicos} • Fornecedores: {fornecedores_unicos}")

    with tab2:
        if "error" in finance:
            st.warning("Sem dados de finanças.")
            if show_debug:
                st.write(finance)
        else:
            s = finance.get("summary", {}) or {}
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Receitas", br_money(safe_float(s.get("total_receitas", 0))))
            c2.metric("Despesas", br_money(safe_float(s.get("total_despesas", 0))))
            c3.metric("Doadores", safe_int(s.get("doadores_unicos", 0)))
            c4.metric("Fornecedores", safe_int(s.get("fornecedores_unicos", 0)))

            st.markdown("**Top doadores**")
            donors = finance.get("top_doadores", []) or []
            df_d = df_from_items(donors)
            if df_d.empty:
                st.info("Sem doadores.")
            else:
                df_d["total"] = pd.to_numeric(df_d.get("total", 0), errors="coerce").fillna(0.0)
                df_d = df_d.rename(columns={"nome": "Nome", "doc": "Doc", "total": "Total"})
                st.dataframe(
                    df_d[["Nome", "Doc", "Total"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={"Total": st.column_config.NumberColumn(format="R$ %.2f")},
                )

            st.markdown("**Top fornecedores**")
            sups = finance.get("top_fornecedores", []) or []
            df_s = df_from_items(sups)
            if df_s.empty:
                st.info("Sem fornecedores.")
            else:
                df_s["total"] = pd.to_numeric(df_s.get("total", 0), errors="coerce").fillna(0.0)
                df_s = df_s.rename(columns={"nome": "Nome", "doc": "Doc", "total": "Total"})
                st.dataframe(
                    df_s[["Nome", "Doc", "Total"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={"Total": st.column_config.NumberColumn(format="R$ %.2f")},
                )

    with tab3:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("**Votos por município (Top 20)**")
            if "error" in votes_mun:
                st.info("Sem dados.")
                if show_debug:
                    st.write(votes_mun)
            else:
                mun_items = votes_mun.get("items", []) or []
                df_m = df_from_items(mun_items)
                if df_m.empty:
                    st.info("Sem dados.")
                else:
                    df_m["votos"] = pd.to_numeric(df_m.get("votos", 0), errors="coerce").fillna(0).astype(int)
                    st.dataframe(
                        df_m.rename(columns={"municipio": "Município", "votos": "Votos"}),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.bar_chart(df_m.set_index("municipio")[["votos"]])

        with col_right:
            st.markdown("**Bens**")
            if "error" in assets:
                st.info("Sem dados.")
                if show_debug:
                    st.write(assets)
            else:
                a_items = assets.get("items", []) or []
                df_a = df_from_items(a_items)
                if df_a.empty:
                    st.info("Sem bens declarados.")
                else:
                    df_a["valor"] = pd.to_numeric(df_a.get("valor", 0), errors="coerce").fillna(0.0)
                    df_a = df_a.sort_values("valor", ascending=False)
                    df_a = df_a.rename(columns={"tipo": "Tipo", "descricao": "Descrição", "valor": "Valor"})
                    st.dataframe(
                        df_a[["Tipo", "Descrição", "Valor"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={"Valor": st.column_config.NumberColumn(format="R$ %.2f")},
                    )
