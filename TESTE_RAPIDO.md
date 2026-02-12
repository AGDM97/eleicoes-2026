# 🧪 Guia de Testes Rápido

## 1️⃣ Preparar Ambiente (5 minutos)

```bash
# Abra PowerShell em c:\Users\asus\Documents\Projetos\eleicoes-dashboard

# Criar ambiente virtual
python -m venv .venv

# Ativar
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt

# Verificar instalação
pip list | grep fastapi
```

---

## 2️⃣ Testar API (sem dados, símbolo ok)

### Terminal 1: Rodar API

```bash
# Na pasta do projeto
python -m uvicorn src.app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Você verá:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Terminal 2: Testar endpoints

```powershell
# Health check (sempre funciona)
curl http://127.0.0.1:8000/health

# Esperado:
# {"status":"ok","db_exists":false,"version":"1.0.0"}
```

**Resultado**: ✅ API rodando mesmo sem banco de dados!

---

## 3️⃣ Testar Dashboard (sem dados, interface ok)

### Terminal 3: Rodar Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

Você verá:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

**Abra no navegador**: http://localhost:8501

**Resultado**: ✅ Interface carrega, mostra "API offline" (esperado, sem banco)

---

## 4️⃣ Testar Testes Automatizados (2 minutos)

```bash
# Terminal qualquer (com venv ativo)
pip install pytest pytest-asyncio

cd c:\Users\asus\Documents\Projetos\eleicoes-dashboard

pytest tests/test_api.py -v
```

**Resultado esperado**:
```
tests/test_api.py::test_health_endpoint PASSED
tests/test_api.py::test_candidates_pagination PASSED
... 10+ testes PASSANDO ✅
```

---

## 5️⃣ Testar com Dados Reais (20+ minutos)

Se quiser testar com dados:

```bash
# Terminal separado
python -m src.app.etl.load_candidates_2022_sp_dep_fed
python -m src.app.etl.load_assets_2022_sp_dep_fed
python -m src.app.etl.load_votes_2022_sp_dep_fed
python -m src.app.etl.load_finance_2022_sp_dep_fed
python scripts/rebuild_finance_agg.py
```

Depois:
- API listará candidatos reais
- Dashboard mostrará dados completos
- Testes mostrará 200 OK (não 503)

---

## 📋 Checklist Rápido

- [ ] Ambiente virtual criado `.venv`
- [ ] Dependências instaladas `pip install -r requirements.txt`
- [ ] API rodando em `http://127.0.0.1:8000` ✅
- [ ] Health check retorna 200 ✅
- [ ] Dashboard abre em `http://localhost:8501` ✅
- [ ] Testes rodam com `pytest tests/` ✅

---

## 🚀 Atalhos Úteis

### Ver estrutura de arquivos
```powershell
tree /f src/app/
```

### Ver status git
```powershell
git status
git log --oneline -3
```

### Testar endpoint específico
```powershell
# Buscar candidatos
curl "http://127.0.0.1:8000/candidates?q=silva&limit=5"

# Com token (se configurado)
curl -H "Authorization: Bearer seu-token" `
  "http://127.0.0.1:8000/candidates"
```

### Limpar cache Streamlit
```powershell
streamlit cache clear
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Certifique-se que venv está ATIVADO
.\.venv\Scripts\Activate.ps1

# Reinstale
pip install -r requirements.txt
```

### "Port 8000 already in use"
```bash
# Use porta diferente
python -m uvicorn src.app.api.main:app --port 8001
```

### "port 8501 already in use"
```bash
# Use porta diferente
streamlit run dashboard/streamlit_app.py --server.port 8502
```

### API offline no Dashboard
- É esperado se você não carregou os dados
- Veja seção "5️⃣ Testar com Dados Reais"

---

## 📊 O que Esperar

| Teste | Sem Dados | Com Dados |
|-------|-----------|-----------|
| API Health | ✅ 200 | ✅ 200 |
| Lista Candidatos | ⚠️ 503 DB não existe | ✅ 200 + dados |
| Dashboard Carrega | ✅ Abre | ✅ Abre |
| Dashboard exibe dados | ❌ "API Offline" | ✅ Exibe |
| Testes pytest | ✅ PASS/SKIP | ✅ PASS |

---

## 💡 Dica Pro

Abra 3 terminais lado a lado:

```
┌─────────────────────────────────────────┐
│ Terminal 1: API (port 8000)             │
├─────────────────────────────────────────┤
│ Terminal 2: Dashboard (port 8501)       │
├─────────────────────────────────────────┤
│ Terminal 3: Testes & Comandos           │
└─────────────────────────────────────────┘
```

Assim você vê tudo acontecendo em tempo real! 👀

---

**Pronto?** É isso! Simples, não? 🚀
