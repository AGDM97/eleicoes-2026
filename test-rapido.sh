#!/bin/bash
# Teste rápido do projeto (Linux/macOS)

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           🧪 TESTE RÁPIDO - ELEIÇÕES DASHBOARD              ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ============================================================================
# 1. Verificar Python
# ============================================================================
echo -e "\n1️⃣  Verificando Python..."
python_version=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ Python encontrado: $python_version"
else
    echo "❌ Python não encontrado"
    exit 1
fi

# ============================================================================
# 2. Criar ambiente virtual
# ============================================================================
echo -e "\n2️⃣  Criando ambiente virtual..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Ambiente criado em .venv"
else
    echo "⚠️  Ambiente já existe"
fi

# ============================================================================
# 3. Ativar ambiente
# ============================================================================
echo -e "\n3️⃣  Ativando ambiente..."
source .venv/bin/activate
echo "✅ Ambiente ativado"

# ============================================================================
# 4. Instalar dependências
# ============================================================================
echo -e "\n4️⃣  Instalando dependências..."
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas"
else
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

# ============================================================================
# 5. Rodar testes
# ============================================================================
echo -e "\n5️⃣  Executando testes..."
pip install -q pytest pytest-asyncio
pytest tests/test_api.py -v --tb=short

echo "
╔══════════════════════════════════════════════════════════════╗
║                    ✅ PRONTO PARA TESTAR!                    ║
╚══════════════════════════════════════════════════════════════╝

Próximos passos (em terminais separados):

📌 Terminal 1: Rodar API
   python -m uvicorn src.app.api.main:app --reload
   Acesse: http://127.0.0.1:8000/health

📌 Terminal 2: Rodar Dashboard
   streamlit run dashboard/streamlit_app.py
   Acesse: http://localhost:8501

📌 Terminal 3: Testar API
   curl http://127.0.0.1:8000/health

Ou use TESTE_RAPIDO.md para mais detalhes!
"
