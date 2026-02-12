# 🤝 Contribuindo para Eleições Dashboard

Obrigado por considerar contribuir para este projeto! Este documento apresenta as diretrizes para contribuições.

## 📋 Como Contribuir

### 1. Fork e Clone
```bash
git clone https://github.com/seu-usuario/eleicoes-dashboard.git
cd eleicoes-dashboard
```

### 2. Criar Branch
```bash
git checkout -b feature/sua-feature
# ou
git checkout -b bugfix/seu-bugfix
```

### 3. Fazer Alterações
- Siga o estilo de código existente
- Adicione docstrings em Português
- Escreva testes para novas features

### 4. Testar
```bash
pytest tests/ -v
```

### 5. Commit e Push
```bash
git add .
git commit -m "Descrição clara da mudança"
git push origin feature/sua-feature
```

### 6. Pull Request
- Abra um PR no repositório original
- Descreva sua mudança e por que ela é necessária
- Referencie issues relacionadas (#123)

---

## 🎯 Áreas de Contribuição

### Features Novas
- Suporte a novos estados/eleições
- Novos widgets de visualização
- Exportação de dados (CSV, PDF, JSON)
- Gráficos avançados

### Bugfixes
- Erros de UI/UX
- Performance
- Tratamento de edge cases

### Documentação
- Melhorias no README
- Tutorais
- Docstrings
- Exemplos

### Tests
- Novos testes unitários
- Testes de integração
- Cobertura de edge cases

---

## 🔧 Setup de Desenvolvimento

```bash
# Ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.\.venv\Scripts\Activate.ps1  # Windows

# Instalar dependências + dev
pip install -r requirements.txt
pip install pytest pytest-cov pylint

# Preparar dados (primeiro uso)
python -m src.app.etl.load_candidates_2022_sp_dep_fed
# ... outros scripts ETL
```

---

## 📝 Padrões de Código

### Python
- Usar type hints: `def foo(x: int) -> str:`
- Docstrings em Português
- PEP 8 (max 99 caracteres)
- Imports: stdlib → third-party → local

### Exemplo:
```python
"""Módulo de exemplo."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def processar_dados(dados: list[dict[str, Any]]) -> int:
    """
    Processa dados e retorna contagem.
    
    Args:
        dados: Lista de dicionários a processar.
    
    Returns:
        Número de itens processados.
    
    Raises:
        ValueError: Se dados inválidos.
    """
    if not isinstance(dados, list):
        raise ValueError("Esperado lista")
    
    logger.info(f"[PROCESS] Processando {len(dados)} itens")
    return len(dados)
```

---

## 🧪 Testes

### Estrutura
```python
def test_feature_basico(client):
    """Testa comportamento básico."""
    response = client.get("/endpoint")
    assert response.status_code == 200
    assert "campo" in response.json()
```

### Cobertura esperada: > 70%

```bash
pytest tests/ --cov=src/app --cov-report=term-missing
```

---

## 📦 Merge de Pull Request

Um PR será mergeado após:
- ✅ Testes passarem
- ✅ Code review aprovado
- ✅ Nenhum conflito com `main`
- ✅ Documentação atualizada

---

## 🐛 Reportar Bugs

Abra uma Issue com:
- **Título claro**: "API retorna erro 500 em `/candidates`"
- **Descrição**: O que você tentou fazer?
- **Steps to reproduce**: Comandos exatos para reproduzir
- **Expected vs Actual**: O que era esperado vs o que aconteceu
- **Environment**: Python version, SO, etc.

---

## 💡 Sugerir Features

Abra uma Issue com:
- **Use case**: Por que isso é necessário?
- **Solução proposta**: Como implementar?
- **Alternativas**: Há outras abordagens?

---

## 📚 Recursos

- [FastAPI Contributing](https://fastapi.tiangolo.com/contributing/)
- [Python Code Style](https://pep8.org/)
- [Semantic Versioning](https://semver.org/)

---

Obrigado por contribuir! 🎉
