# Instruções de Publicação no GitHub

## 📋 Checklist Pré-Publicação

- [ ] Código testado localmente
- [ ] Todos os testes passando (`pytest tests/`)
- [ ] `.gitignore` configurado (já está!)
- [ ] `requirements.txt` atualizado
- [ ] README.md completo e clara
- [ ] Sem dados sensíveis nos commits
- [ ] Versão atualizada em `CHANGELOG.md`

---

## 🚀 Passo a Passo

### 1. Criar repositório no GitHub

1. Acesse https://github.com/new
2. Nome: `eleicoes-dashboard`
3. Descrição: "Dashboard interativo de análise de dados eleitorais brasileiros"
4. Público/Privado: (sua escolha)
5. **Não** inicialize com README (vamos usar o nosso)
6. Clique "Create repository"
7. Copie a URL (ex: `https://github.com/seu-usuario/eleicoes-dashboard.git`)

### 2. Inicializar Git localmente

```bash
cd c:\Users\asus\Documents\Projetos\eleicoes-dashboard

# Se ainda não tiver git inicializado:
git init
git config user.name "Seu Nome"
git config user.email "seu-email@github.com"
```

### 3. Adicionar e fazer commit

```bash
git add .
git commit -m "🚀 Commit inicial: Eleições Dashboard v1.0.0"
git branch -M main
```

### 4. Conectar ao GitHub e fazer push

```bash
git remote add origin https://github.com/seu-usuario/eleicoes-dashboard.git
git push -u origin main
```

**Se pedir autenticação:**
- Use GitHub CLI: `gh auth login`
- Ou configure SSH key
- Ou use Personal Access Token (vá em Settings → Developer settings → Personal access tokens)

---

## ⚙️ Configuração Pós-Publicação

### No GitHub (via web)

1. **Settings → General**
   - ✅ Desabilitar Wiki (opcional)
   - ✅ Desabilitar Projects (opcional)

2. **Settings → Code and automation → Environments**
   - Criar `production` se quiser deploy

3. **Settings → Secrets and variables**
   - Se usar CI/CD com tokens (opcional)

4. **Insights → Community**
   - Verifique saúde do projeto

---

## 🔄 Workflow Git Recomendado

### Para desenvolvimento:

```bash
# Criar nova feature
git checkout -b feature/minha-feature
# ... fazer mudanças ...
git add .
git commit -m "feat: descrição da feature"
git push origin feature/minha-feature

# Abra um Pull Request no GitHub
# Após aprovação, faça merge via web
```

### Para releases:

```bash
# Tag de versão
git tag v1.0.0
git push origin v1.0.0

# No GitHub, crie Release a partir da tag
```

---

## 📊 Badges e Documentação Extra

### README com Badges

Adicione ao topo do `README.md`:

```markdown
[![Tests](https://github.com/seu-usuario/eleicoes-dashboard/workflows/Tests/badge.svg)](https://github.com/seu-usuario/eleicoes-dashboard/actions)
[![Lint](https://github.com/seu-usuario/eleicoes-dashboard/workflows/Lint/badge.svg)](https://github.com/seu-usuario/eleicoes-dashboard/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
```

### Adicionar LICENSE

```bash
# Crie um arquivo LICENSE na raiz
# Copie o texto de uma licença (MIT é recomendada)
# https://choosealicense.com/
```

---

## 🚨 Proteger Branch Main

No GitHub → Settings → Branches:

- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass
- ✅ Require branches to be up to date before merging

---

## 📝 Configuração de Issues e PRs

No `.github/ISSUE_TEMPLATE/`:

```markdown
## 🐛 Bug Report
**Descrição**: ...
**Steps to reproduce**: ...
**Expected**: ...
**Actual**: ...
```

---

## 💬 Habilitar Discussions

Settings → General → Discussions → Enable

Categorias:
- Ideias
- Q&A
- Anúncios
- Mostrar e Contar

---

## 🌐 GitHub Pages (Documentação)

1. Settings → Pages
2. Source: `main`
3. Folder: `/docs`
4. Salve

Sua documentação estará em: `https://seu-usuario.github.io/eleicoes-dashboard/`

---

## ✅ Verificar Saúde do Projeto

Insights → Community → Community Standards Checklist

Debe estar tudo verde! Faltando:
- [ ] README
- [ ] CODE_OF_CONDUCT.md
- [ ] LICENSE
- [ ] CONTRIBUTING.md
- [ ] Security policy

---

## 🔐 Segurança

### Dependabot

Settings → Code security and analysis → Enable Dependabot

Rastreará dependências desatualizadas automaticamente.

### Secret Scanning

Automatic para repositórios públicos.

---

## 📈 Marketing do Projeto

1. Adicione topics em Settings:
   - `python`
   - `fastapi`
   - `streamlit`
   - `duckdb`
   - `eleições`
   - `tse`
   - `dados-abertos`

2. Submeta a repositórios temáticos:
   - Awesome Python
   - Awesome Data Viz
   - Awesome Brazilian Projects

---

## 🎓 Primeiro Commit

```bash
git log --oneline
```

Deverá mostrar algo como:

```
abc1234 🚀 Commit inicial: Eleições Dashboard v1.0.0
```

---

## ✨ Próximos Passos

1. ✅ Publicar no GitHub
2. ✅ Ativar CI/CD (Actions já está configurado)
3. ⭐ Pedir stars para amigos
4. 📢 Compartilhar em comunidades Python
5. 🤝 Aceitar pull requests

---

## 🆘 Problemas Comuns

### "Permission denied (publickey)"
```bash
# Configure SSH ou use HTTPS
git config --global credential.helper store
git push  # Irá pedir usuário/senha
```

### "fatal: remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/seu-usuario/eleicoes-dashboard.git
```

### Accesso negado ao tentar push
```bash
# Gere Personal Access Token:
# Settings → Developer settings → Personal access tokens → Generate new token
# Use como senha ao fazer push
```

---

**Parabéns! Seu projeto agora está no mundo!** 🎉
