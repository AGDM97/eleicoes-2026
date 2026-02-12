# 🗳️ Eleições Dashboard

Dashboard interativo para análise de dados eleitorais brasileiros de 2022 usando dados públicos do TSE (Tribunal Superior Eleitoral).

**Stack**: FastAPI + DuckDB + Streamlit — Sistema modular e extensível para análise eleitoral.

---

## 🎯 Funcionalidades

### Dashboard (Streamlit)
- 🔍 Busca full-text de candidatos (nome de urna + nome completo)
- 📊 Tabelas com métricas de votos, receitas, despesas e bens
- 💰 Análise detalhada de finanças (doadores/fornecedores)
- 🗺️ Distribuição de votos por município
- 🏠 Declaração de bens
- 📱 Modo apresentação (UI limpa, sem sidebar)
- ⚡ Cache inteligente para performance

### API (FastAPI)
- `GET /health` — Status da API e banco de dados
- `GET /candidates` — Lista candidatos com paginação e busca
- `GET /candidates/{id}/assets` — Bens declarados
- `GET /candidates/{id}/votes_municipio` — Votos por município
- `GET /candidates/{id}/finance` — Receitas/despesas + top doadores/fornecedores

### Backend (DuckDB)
- 📦 Banco de dados coluna-analítico embarcado
- 🚀 Otimizado para queries analíticas
- 📈 Índices automáticos para performance
- 🔄 Sem servidor necessário

---

## 🚀 Início Rápido

### 1. Clonar repositório
```bash
git clone https://github.com/seu-usuario/eleicoes-dashboard.git
cd eleicoes-dashboard
```

### 2. Criar ambiente virtual
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Preparar dados (primeiras execuções)
```bash
# Baixa e carrega dados candidatos
python -m src.app.etl.load_candidates_2022_sp_dep_fed

# Carrega dados de bens
python -m src.app.etl.load_assets_2022_sp_dep_fed

# Carrega dados de votos
python -m src.app.etl.load_votes_2022_sp_dep_fed

# Carrega dados de finanças
python -m src.app.etl.load_finance_2022_sp_dep_fed

# Agregações de finanças
python scripts/rebuild_finance_agg.py
```

### 5. Iniciar Backend (Terminal 1)
```bash
python -m uvicorn src.app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 6. Iniciar Frontend (Terminal 2)
```bash
streamlit run dashboard/streamlit_app.py
```

Acesse: http://localhost:8501

---

## 🔧 Configuração

### Variáveis de Ambiente

Altere estado/cargo criando um arquivo `.env` na raiz:

```bash
# Estado (padrão: SP)
ELEICOES_UF=MG

# Cargo (padrão: DEPUTADO FEDERAL)
ELEICOES_CARGO=DEPUTADO ESTADUAL

# Chave de API (opcional, deixe vazio para API pública)
ELEICOES_API_KEY=seu-secreto-aqui
```

### Tabelas DuckDB (config.py)

As tabelas são nomeadas dinamicamente baseadas em UF/CARGO/ANO:

```python
# Padrão (SP + Dep Federal + 2022):
CANDIDATE_TABLE = "candidates_sp_dep_fed_2022"
DONATIONS_TABLE = "donations_sp_dep_fed_2022"
...

# Alterando UF para MG:
CANDIDATE_TABLE = "candidates_mg_dep_fed_2022"
DONATIONS_TABLE = "donations_mg_dep_fed_2022"
...
```

---

## 📁 Estrutura do Projeto

```
eleicoes-dashboard/
├── dashboard/
│   └── streamlit_app.py          # Interface Streamlit
├── src/app/
│   ├── api/
│   │   └── main.py               # Endpoints FastAPI
│   ├── etl/
│   │   ├── load_candidates_*.py   # Carregamento de candidatos
│   │   ├── load_assets_*.py       # Carregamento de bens
│   │   ├── load_votes_*.py        # Carregamento de votos
│   │   └── load_finance_*.py      # Carregamento de finanças
│   ├── config.py                 # Configuração centralizada
│   ├── db.py                     # Utilidades DuckDB
│   └── auth.py                   # Autenticação
├── scripts/
│   ├── rebuild_finance_agg.py    # Agregação de finanças
│   └── inspect_finance_files.py  # Inspeção de CSVs
├── data/tse/                     # Dados baixados do TSE
├── db/
│   └── eleicoes.duckdb           # Banco de dados (gerado)
├── tests/
│   └── test_api.py               # Testes da API
├── requirements.txt              # Dependências Python
├── .gitignore                    # Arquivos ignorados
└── README.md                     # Este arquivo
```

---

## 🔐 Autenticação

### API Pública (padrão)
Se `ELEICOES_API_KEY` não está definida, todos os endpoints são públicos.

### API Protegida
Defina `ELEICOES_API_KEY=seu-token-secreto` para proteger `/candidates`:

```bash
# Solicitação sem token (erro 401)
curl http://localhost:8000/candidates

# Solicitação com token (sucesso)
curl -H "Authorization: Bearer seu-token-secreto" \
  http://localhost:8000/candidates
```

**Nota**: `/health`, `/assets`, `/votes_municipio` e `/finance` são sempre públicos.

---

## 📊 Dados

### Fonte
- **TSE (Tribunal Superior Eleitoral)**: https://www.tse.jus.br/
- **Eleições**: 2022
- **Cargos**: Deputados Federais (customizável)
- **Estados**: Todos (27 + DF)

### Arquivos Baixados
```
data/tse/
├── bem_candidato_2022/          # Bens declarados
├── consulta_cand_2022/          # Dados candidatos
├── votacao_candidato_munzona_2022/  # Votos por município
└── prestacao_contas_candidatos_2022/  # Receitas/despesas
```

**Nota**: Arquivos grandes são ignorados pelo `.gitignore`. Rode ETLs para gerar dados localmente.

---

## ⚙️ Índices DuckDB

Índices automáticos criados no startup:

```sql
CREATE INDEX idx_candidates_sp_dep_fed_2022_id
CREATE INDEX idx_candidates_sp_dep_fed_2022_nome_urna
CREATE INDEX idx_candidates_sp_dep_fed_2022_partido
CREATE INDEX idx_donations_sp_dep_fed_2022_candidate_id
CREATE INDEX idx_expenses_sp_dep_fed_2022_candidate_id
... (e demais tabelas)
```

Aceleram buscas por ID e nome. Para otimizações customizadas, edite `src/app/db.py:ensure_indexes()`.

---

## 🧪 Testes

### Rodar testes
```bash
pytest tests/ -v
```

### Cobertura
```bash
pip install pytest-cov
pytest tests/ --cov=src/app --cov-report=html
```

Testes cobrem:
- Endpoints da API
- Paginação
- Busca
- Tratamento de erros
- Validação de dados

---

## 🚀 Deployment

### Servidor (Produção)
```bash
# Uvicorn com workers
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.app.api.main:app --bind 0.0.0.0:8000
```

### Dashboard (Produção)
```bash
# Streamlit Cloud (recomendado)
streamlit run dashboard/streamlit_app.py --logger.level=warning
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "src.app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📈 Performance

### Cache Streamlit
- **TTL 15s**: `/candidates` (muda frequentemente)
- **TTL 120s**: Detalhes (bens, votos, finanças)

Limpar cache:
```bash
streamlit cache clear
```

### Índices DuckDB
Criados automaticamente no startup. Para adicionar:

```python
# em src/app/db.py
tables_config = {
    "candidates_sp_dep_fed_2022": ["id", "nome_urna", "partido"],
    ...
}
create_indexes(con, tables_config)
```

---

## 🐛 Troubleshooting

### Banco de dados não encontrado
```
[ERROR] [DB] Banco não encontrado em db/eleicoes.duckdb
```
**Solução**: Rode os scripts ETL (`load_*.py`) para criar e popular o banco.

### Tabela não existe
```
HTTPException: 404 Tabela assets_sp_dep_fed_2022 não existe
```
**Solução**: Execute `python -m src.app.etl.load_assets_2022_sp_dep_fed`

### CORS origin not allowed
**Solução**: A API tem CORS habilitado globalmente (`allow_origins=["*"]`). Se usar reverse proxy, configure apropriadamente.

### Streamlit connection timeout
**Solução**: Certifique-se que a API está rodando em `http://127.0.0.1:8000`

---

## 📝 Logs

### API
```python
# Configurable em main.py
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Exemplos:
[STARTUP] Conectando ao banco...
[API] /candidates: q='silva', limit=50, offset=0, found=23
[AUTH] Acesso negado: Token inválido
[API ERROR] /candidates/1/assets: ...
```

### Streamlit
Veja em `~/.streamlit/logs/`

---

## 🤝 Contribuições

Sugestões de melhorias:
1. Suporte a mais eleições/anos
2. Novos widgets de visualização
3. Exportação de dados (CSV/PDF)
4. Autenticação de usuários
5. Deploy em ambiente cloud

---

## 📄 Licença

[Escolha uma licença - ex: MIT, Apache 2.0]

---

## 📧 Contato

- **Email**: seu-email@example.com
- **GitHub**: https://github.com/seu-usuario

---

## 🔗 Referências

- [TSE - Dados Abertos](https://www.tse.jus.br/eleitor/repositorio-de-dados-eleitorais)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [DuckDB Docs](https://duckdb.org/)
- [Streamlit Docs](https://docs.streamlit.io/)

---

**Última atualização**: Fevereiro 2026
