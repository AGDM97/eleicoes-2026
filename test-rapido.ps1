#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script para testar o projeto rapidamente (Windows PowerShell)

.DESCRIPTION
    Automatiza: ambiente virtual → instalar → rodar API + Dashboard + Testes

.EXAMPLE
    .\test-rapido.ps1
#>

Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║           🧪 TESTE RÁPIDO - ELEIÇÕES DASHBOARD              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

$projectRoot = Get-Location

# ============================================================================
# 1. Verificar Python
# ============================================================================
Write-Host "`n1️⃣  Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python não encontrado" -ForegroundColor Red
    exit 1
}

# ============================================================================
# 2. Criar ambiente virtual
# ============================================================================
Write-Host "`n2️⃣  Criando ambiente virtual..." -ForegroundColor Yellow
if (-Not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ Ambiente criado em .venv" -ForegroundColor Green
} else {
    Write-Host "⚠️  Ambiente já existe" -ForegroundColor Cyan
}

# ============================================================================
# 3. Ativar ambiente
# ============================================================================
Write-Host "`n3️⃣  Ativando ambiente..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"
Write-Host "✅ Ambiente ativado" -ForegroundColor Green

# ============================================================================
# 4. Instalar dependências
# ============================================================================
Write-Host "`n4️⃣  Instalando dependências..." -ForegroundColor Yellow
pip install -q -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependências instaladas" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}

# ============================================================================
# 5. Rodar testes
# ============================================================================
Write-Host "`n5️⃣  Executando testes..." -ForegroundColor Yellow
pip install -q pytest pytest-asyncio
pytest tests/test_api.py -v --tb=short

Write-Host @"

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
"@ -ForegroundColor Green
