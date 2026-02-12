#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script para publicar o projeto no GitHub (Windows PowerShell)

.DESCRIPTION
    Automatiza os passos de git init, commit e push para GitHub

.PARAMETER RepoUrl
    URL do repositório GitHub (ex: https://github.com/usuario/eleicoes-dashboard.git)

.EXAMPLE
    .\publish-to-github.ps1 -RepoUrl "https://github.com/seu-usuario/eleicoes-dashboard.git"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl
)

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host @"
╔════════════════════════════════════════════════════════════╗
║      PUBLICANDO ELEIÇÕES DASHBOARD NO GITHUB               ║
╚════════════════════════════════════════════════════════════╝

📍 Projeto: $projectRoot
🔗 Repositório: $RepoUrl

"@ -ForegroundColor Cyan

Set-Location $projectRoot

# 1. Inicializar git
if (-Not (Test-Path ".git")) {
    Write-Host "📦 Inicializando repositório git..." -ForegroundColor Yellow
    git init
    git config user.name "Seu Nome"
    git config user.email "seu-email@github.com"
}

# 2. Add files
Write-Host "📝 Adicionando arquivos..." -ForegroundColor Yellow
git add .

# 3. Commit
Write-Host "💾 Fazendo commit inicial..." -ForegroundColor Yellow
git commit -m "🚀 Commit inicial: Eleições Dashboard v1.0.0"

# 4. Rename branch
Write-Host "🔄 Renomeando branch para 'main'..." -ForegroundColor Yellow
git branch -M main

# 5. Add remote
Write-Host "🌐 Conectando ao repositório remoto..." -ForegroundColor Yellow
git remote remove origin 2>$null
git remote add origin $RepoUrl

# 6. Push
Write-Host "⬆️  Fazendo push para GitHub (pode pedir autenticação)..." -ForegroundColor Yellow
git push -u origin main

Write-Host @"

╔════════════════════════════════════════════════════════════╗
║                    ✅ CONCLUÍDO!                           ║
╚════════════════════════════════════════════════════════════╝

Seu projeto está no GitHub! 🎉

Próximos passos:
  1. Acesse: $RepoUrl
  2. Configure topics, descrição, etc
  3. Ative GitHub Actions (CI/CD)
  4. Convide colaboradores

Use:
  git status     # Ver status
  git log        # Ver histórico
  git push       # Fazer push de novas mudanças

"@ -ForegroundColor Green
