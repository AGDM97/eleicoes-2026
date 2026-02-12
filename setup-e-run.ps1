#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup e execução automática do projeto (Windows PowerShell)
    
.DESCRIPTION
    Script one-click que faz tudo:
    1. Cria ambiente virtual
    2. Instala dependências
    3. Carrega dados do TSE
    4. Inicia API (background)
    5. Abre Dashboard no navegador

.EXAMPLE
    .\setup-e-run.ps1

.NOTES
    Requer: Python 3.9+ instalado
#>

$ErrorActionPreference = "Stop"

Write-Host @"
╔═══════════════════════════════════════════════════════════════╗
║   🚀 ELEIÇÕES DASHBOARD - SETUP AUTOMÁTICO                   ║
║                                                               ║
║   Este script configurará tudo em 5 minutos aproximadamente   ║
╚═══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# =============================================================================
# 1. Verificar Python
# =============================================================================
Write-Host "`n[1/6] ✓ Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      ✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "      ❌ Python não encontrado. Instale Python 3.9+ de https://www.python.org/" -ForegroundColor Red
    exit 1
}

# =============================================================================
# 2. Criar/Ativar Ambiente Virtual
# =============================================================================
Write-Host "`n[2/6] ✓ Preparando ambiente..." -ForegroundColor Yellow
if (-Not (Test-Path ".venv")) {
    Write-Host "      Criando ambiente virtual..." -ForegroundColor Cyan
    python -m venv .venv
}
Write-Host "      ✅ Ambiente pronto" -ForegroundColor Green

# Ativar venv
& ".\.venv\Scripts\Activate.ps1"

# =============================================================================
# 3. Instalar Dependências
# =============================================================================
Write-Host "`n[3/6] ✓ Instalando dependências (pode levar um minuto)..." -ForegroundColor Yellow
pip install -q --upgrade pip
pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ❌ Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}
Write-Host "      ✅ Dependências instaladas" -ForegroundColor Green

# =============================================================================
# 4. Carregar Dados (se não existir)
# =============================================================================
Write-Host "`n[4/6] ✓ Verificando dados..." -ForegroundColor Yellow
if (-Not (Test-Path "db/eleicoes.duckdb")) {
    Write-Host "      Baixando dados do TSE (pode levar 2-3 minutos)..." -ForegroundColor Cyan
    
    python -m src.app.etl.load_candidates_2022_sp_dep_fed | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "      ⚠️  Aviso ao carregar candidatos" -ForegroundColor Yellow }
    
    python -m src.app.etl.load_assets_2022_sp_dep_fed | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "      ⚠️  Aviso ao carregar bens" -ForegroundColor Yellow }
    
    python -m src.app.etl.load_votes_2022_sp_dep_fed | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "      ⚠️  Aviso ao carregar votos" -ForegroundColor Yellow }
    
    python -m src.app.etl.load_finance_2022_sp_dep_fed | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "      ⚠️  Aviso ao carregar finanças" -ForegroundColor Yellow }
    
    python scripts/rebuild_finance_agg.py | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "      ⚠️  Aviso ao agregar finanças" -ForegroundColor Yellow }
    
    Write-Host "      ✅ Dados carregados (eleicoes.duckdb)" -ForegroundColor Green
} else {
    Write-Host "      ✅ Dados já carregados" -ForegroundColor Green
}

# =============================================================================
# 5. Iniciar API (Background)
# =============================================================================
Write-Host "`n[5/6] ✓ Iniciando API..." -ForegroundColor Yellow
$apiProcess = Start-Process -FilePath python `
    -ArgumentList "-m", "uvicorn", "src.app.api.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -NoNewWindow `
    -PassThru

Write-Host "      ⏳ Aguardando API ficar pronta..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Verificar se API está rodando
$maxTries = 10
$tries = 0
while ($tries -lt $maxTries) {
    try {
        $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2
        if ($health.StatusCode -eq 200) {
            Write-Host "      ✅ API rodando em http://127.0.0.1:8000" -ForegroundColor Green
            break
        }
    } catch {
        $tries++
        Start-Sleep -Seconds 1
    }
}

if ($tries -eq $maxTries) {
    Write-Host "      ⚠️  API pode estar levando para iniciar..." -ForegroundColor Yellow
}

# =============================================================================
# 6. Abrir Dashboard
# =============================================================================
Write-Host "`n[6/6] ✓ Abrindo Dashboard..." -ForegroundColor Yellow

# Iniciar Streamlit em background
$dashboardProcess = Start-Process -FilePath python `
    -ArgumentList "-m", "streamlit", "run", "dashboard/streamlit_app.py", "--logger.level=warning" `
    -NoNewWindow `
    -PassThru

Write-Host "      ⏳ Dashboard iniciando..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Abrir no navegador
try {
    Start-Process "http://localhost:8501"
    Write-Host "      ✅ Dashboard aberto em http://localhost:8501" -ForegroundColor Green
} catch {
    Write-Host "      ⚠️  Abra manualmente: http://localhost:8501" -ForegroundColor Yellow
}

# =============================================================================
# Resumo Final
# =============================================================================
Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║               ✅ TUDO PRONTO!                                 ║
╚═══════════════════════════════════════════════════════════════╝

🌐 Dashboard: http://localhost:8501
📊 API: http://127.0.0.1:8000
📖 Documentação API: http://127.0.0.1:8000/docs

🎯 Próximos passos:
   1. Navegador abriu automaticamente
   2. Experimente buscar "silva" ou outro candidato
   3. Explore votos, bens e finanças

🛑 Para parar tudo:
   Pressione Ctrl+C nesta janela

📚 Para mais detalhes:
   - README.md → Guia completo
   - TESTE_RAPIDO.md → Teste dos componentes
   - CONTRIBUTING.md → Como contribuir

💡 Dica: Próximas execuções rodam mais rápido!
"@ -ForegroundColor Green

# Manter terminais abertos
Write-Host "`nPressione Ctrl+C para parar tudo..." -ForegroundColor Cyan
$apiProcess | Wait-Process
$dashboardProcess | Wait-Process
