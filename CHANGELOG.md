# Changelog

Todas as mudanças notáveis neste projeto são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere a [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2026-02-12

### Adicionado
- ✨ Arquitetura modular com separação de responsabilidades
- 🔧 Configuração centralizada (`config.py`) para parametrização de estado/cargo
- 🔐 Autenticação opcional com tokens Bearer
- 📊 Índices automáticos no DuckDB para otimização de queries
- 🧪 Suite de testes com pytest
- 📚 Documentação completa (README.md, CONTRIBUTING.md)
- 🎨 Dashboard Streamlit com modo apresentação
- ⚡ Cache inteligente no Streamlit (TTL 15s/120s)
- 🚀 API FastAPI com 5 endpoints principais
- 📝 Logging estruturado em API e ETLs
- 🛡️ Tratamento robusto de erros com HTTP status codes apropriados
- 📦 Ambiente virtual + requirements.txt
- 🚫 .gitignore para dados/banco/ambientes

### Changed
- 🔄 Refatoração da API: substituição de JSONResponse por HTTPException
- 📈 Melhor tratamento de valores nulos e defaults em respostas
- 🎯 Type hints em todos os endpoints

### Fixed
- 🐛 Fallbacks para tabelas opcionais no DuckDB
- 🐛 Validação de tipos em respostas JSON

---

## [0.1.0] - 2025-XX-XX

### Adicionado
- 🚀 MVP inicial com API e Dashboard básico
- 📊 Carregamento de dados do TSE
- 🗳️ Análise de candidatos e votos

---

## Futuro

### Planejado
- [ ] Suporte a múltiplas eleições (2018, 2020, 2024)
- [ ] Dashboard em mais idiomas (EN, ES)
- [ ] Exportação de dados (CSV, PDF)
- [ ] Gráficos avançados com Plotly
- [ ] Autenticação de usuários (JWT)
- [ ] API documentação interativa (Swagger UI)
- [ ] Deploy em cloud (AWS, GCP, Azure)

---
