#!/bin/bash
# Setup e execução automática do projeto (Linux/macOS)
set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   🚀 ELEIÇÕES DASHBOARD - SETUP AUTOMÁTICO                   ║"
echo "║                                                               ║"
echo "║   Este script configurará tudo em 5 minutos aproximadamente   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# =============================================================================
# 1. Verificar Python
# =============================================================================
echo -e "\n[1/6] ✓ Verificando Python..."
python_version=$(python3 --version 2>&1)
echo "      ✅ Python encontrado: $python_version"

# =============================================================================
# 2. Criar/Ativar Ambiente Virtual
# =============================================================================
echo -e "\n[2/6] ✓ Preparando ambiente..."
if [ ! -d ".venv" ]; then
    echo "      Criando ambiente virtual..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo "      ✅ Ambiente pronto"

# =============================================================================
# 3. Instalar Dependências
# =============================================================================
echo -e "\n[3/6] ✓ Instalando dependências (pode levar um minuto)..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "      ✅ Dependências instaladas"

# =============================================================================
# 4. Carregar Dados (se não existir)
# =============================================================================
echo -e "\n[4/6] ✓ Verificando dados..."
if [ ! -f "db/eleicoes.duckdb" ]; then
    echo "      Baixando dados do TSE (pode levar 2-3 minutos)..."
    
    python -m src.app.etl.load_candidates_2022_sp_dep_fed > /dev/null 2>&1 || echo "      ⚠️  Aviso ao carregar candidatos"
    python -m src.app.etl.load_assets_2022_sp_dep_fed > /dev/null 2>&1 || echo "      ⚠️  Aviso ao carregar bens"
    python -m src.app.etl.load_votes_2022_sp_dep_fed > /dev/null 2>&1 || echo "      ⚠️  Aviso ao carregar votos"
    python -m src.app.etl.load_finance_2022_sp_dep_fed > /dev/null 2>&1 || echo "      ⚠️  Aviso ao carregar finanças"
    python scripts/rebuild_finance_agg.py > /dev/null 2>&1 || echo "      ⚠️  Aviso ao agregar finanças"
    
    echo "      ✅ Dados carregados (eleicoes.duckdb)"
else
    echo "      ✅ Dados já carregados"
fi

# =============================================================================
# 5. Iniciar API (Background)
# =============================================================================
echo -e "\n[5/6] ✓ Iniciando API..."
python -m uvicorn src.app.api.main:app --host 127.0.0.1 --port 8000 > /tmp/eleicoes-api.log 2>&1 &
API_PID=$!
echo "      ⏳ Aguardando API ficar pronta..."
sleep 3

# Verificar se API está rodando
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "      ✅ API rodando em http://127.0.0.1:8000"
else
    echo "      ⚠️  API pode estar levando para iniciar..."
fi

# =============================================================================
# 6. Abrir Dashboard
# =============================================================================
echo -e "\n[6/6] ✓ Abrindo Dashboard..."
python -m streamlit run dashboard/streamlit_app.py --logger.level=warning > /tmp/eleicoes-dash.log 2>&1 &
DASH_PID=$!
echo "      ⏳ Dashboard iniciando..."
sleep 5

# Abrir no navegador (se disponível)
if command -v open &> /dev/null; then
    open http://localhost:8501  # macOS
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501  # Linux
else
    echo "      ⚠️  Abra manualmente: http://localhost:8501"
fi
echo "      ✅ Dashboard aberto em http://localhost:8501"

# =============================================================================
# Resumo Final
# =============================================================================
echo "
╔═══════════════════════════════════════════════════════════════╗
║               ✅ TUDO PRONTO!                                 ║
╚═══════════════════════════════════════════════════════════════╝

🌐 Dashboard: http://localhost:8501
📊 API: http://127.0.0.1:8000
📖 Documentação API: http://127.0.0.1:8000/docs

🎯 Próximos passos:
   1. Navegador abriu automaticamente
   2. Experimente buscar \"silva\" ou outro candidato
   3. Explore votos, bens e finanças

🛑 Para parar tudo:
   Pressione Ctrl+C

📚 Para mais detalhes:
   - README.md → Guia completo
   - TESTE_RAPIDO.md → Teste dos componentes
   - CONTRIBUTING.md → Como contribuir

💡 Dica: Próximas execuções rodam mais rápido!
"

# Manter processo rodando
wait $API_PID $DASH_PID
