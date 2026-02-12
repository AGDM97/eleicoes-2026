#!/usr/bin/env python3
"""
Script para preparar o projeto para publicação no GitHub.

Antes de executar:
1. Crie um repositório vazio no GitHub
2. Copie a URL do repositório (ex: https://github.com/seu-usuario/eleicoes-dashboard.git)
3. Execute este script com a URL como argumento

Uso:
    python scripts/setup_git.py https://github.com/seu-usuario/eleicoes-dashboard.git
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Executa um comando git."""
    print(f"\n[GIT] {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[OK] {result.stdout.strip() if result.stdout else description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {e.stderr}")
        return False


def main() -> None:
    """Inicializa repo git e publica no GitHub."""
    if len(sys.argv) < 2:
        print("Uso: python scripts/setup_git.py <https://github.com/usuario/repo.git>")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    project_root = Path(__file__).parent.parent
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║         Preparando para publicação no GitHub                   ║
╚════════════════════════════════════════════════════════════════╝

📍 Raiz do projeto: {project_root}
🔗 URL do repositório: {repo_url}

""")
    
    # Mudar para raiz do projeto
    import os
    os.chdir(project_root)
    
    # 1. Inicializar git (se necessário)
    if not (project_root / ".git").exists():
        run_command(["git", "init"], "Inicializando repositório git")
    
    # 2. Adicionar arquivo de configuração git
    run_command(["git", "config", "user.name", "Seu Nome"], "Configurando nome")
    run_command(["git", "config", "user.email", "seu-email@example.com"], 
                "Configurando email (altere depois!)")
    
    # 3. Adicionar todos os arquivos
    run_command(["git", "add", "."], "Adicionando arquivos")
    
    # 4. Fazer commit inicial
    run_command(["git", "commit", "-m", "🚀 Commit inicial: Eleições Dashboard v1.0.0"],
                "Fazendo commit inicial")
    
    # 5. Renomear branch para main (se necessário)
    run_command(["git", "branch", "-M", "main"], "Renomeando branch para 'main'")
    
    # 6. Adicionar remote
    run_command(["git", "remote", "remove", "origin"], "Removendo remote anterior (se existia)")
    run_command(["git", "remote", "add", "origin", repo_url], "Adicionando remote 'origin'")
    
    # 7. Push inicial
    print("\n[GIT] Fazendo push para GitHub (pode pedir autenticação)...")
    result = subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] Push concluído com sucesso!")
    else:
        print(f"[INFO] Push retornou: {result.stderr}")
        print("""
⚠️  Se você viu erro de autenticação:
   1. Use GitHub CLI: gh auth login
   2. Ou configure SSH keys
   3. Ou use Personal Access Token

Próximos passos manuais:
   git push -u origin main
        """)
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                     ✅ Concluído!                              ║
╚════════════════════════════════════════════════════════════════╝

Seu repositório está quase pronto! Agora:

1️⃣  Acesse: {repo_url}

2️⃣  Configure no GitHub:
   - Descrição do projeto
   - Topics (tags): python, fastapi, streamlit, duckdb, eleições
   - Habilitação de Discussions/Releases

3️⃣  Opcional: Ative GitHub Pages para docs
   - Settings → Pages → Source: main /docs

4️⃣  Para colaboradores:
   - Adicione como contribuidor via Settings → Collaborators

🎉 Seu projeto está publicado!

""")


if __name__ == "__main__":
    main()
