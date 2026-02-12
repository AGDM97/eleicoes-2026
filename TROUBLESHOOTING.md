# 🆘 Troubleshooting

Se encontrou algum problema durante setup, aqui estão as soluções.

---

## ❌ "Python não encontrado"

**Problema:** Script diz que Python não está instalado.

**Solução:**
1. Baixe Python de [python.org](https://www.python.org/downloads/)
2. **Importante:** marque "Add Python to PATH" durante instalação
3. Reinicie o PowerShell/Terminal
4. Verifique: `python --version`

---

## ❌ "Permissão negada ao executar setup-e-run.sh"

**Problema:** Linux/macOS retorna erro de permissão.

**Solução:**
```bash
chmod +x setup-e-run.sh
./setup-e-run.sh
```

---

## ❌ "API não inicia / Porta 8000 em uso"

**Problema:** API falha ao iniciar ou diz que porta está em uso.

**Solução:**
```powershell
# Windows - Encontrar processo usando porta 8000
netstat -ano | findstr :8000

# Matar processo (substitua PID)
taskkill /PID 12345 /F
```

```bash
# Linux/macOS
lsof -i :8000
kill -9 <PID>
```

---

## ❌ "Dashboard não conecta à API"

**Problema:** Dashboard mostra "API offline".

**Solução:**

1. Verifique se API está rodando:
   ```powershell
   curl http://127.0.0.1:8000/health
   ```

2. Se não funcionar, reinicie API:
   ```powershell
   python -m uvicorn src.app.api.main:app --reload
   ```

3. Dê 3-5 segundos para API iniciar
4. Atualize Dashboard no navegador (F5)

---

## ❌ "Erro ao carregar dados / 'Arquivo não encontrado'"

**Problema:** ETL scripts falham ao baixar dados.

**Solução:**

1. Verifique conexão de internet
2. Verifique permissões na pasta `data/`
3. Tente manualmente:
   ```powershell
   python -m src.app.etl.load_candidates_2022_sp_dep_fed
   ```

Se continuar falhando, abra uma [issue no GitHub](https://github.com/AGDM97/eleicoes-2026/issues).

---

## ❌ "ModuleNotFoundError: No module named 'src'"

**Problema:** Python não encontra o módulo `src`.

**Solução:**

1. Verifique que está na pasta correta:
   ```powershell
   cd C:\Users\asus\Documents\Projetos\eleicoes-dashboard
   ```

2. Verifique que `src/` existe:
   ```powershell
   dir src/
   ```

3. Se não existir, o repositório não clonou corretamente:
   ```powershell
   git clone https://github.com/AGDM97/eleicoes-2026.git
   cd eleicoes-2026
   .\setup-e-run.ps1
   ```

---

## ❌ "Erro de permissão ao criar .venv"

**Problema:** Erro ao criar ambiente virtual.

**Solução:**

1. Verifique permissões da pasta:
   ```powershell
   # Windows
   icacls C:\Users\asus\Documents\Projetos\eleicoes-dashboard
   ```

2. Se necessário, crie venv manualmente:
   ```powershell
   python -m venv .venv --clear
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

---

## ❌ "Database locked" / "DuckDB error"

**Problema:** Erro ao acessar banco de dados.

**Solução:**

1. Feche TODOS os terminais e navegadores
2. Espere 10 segundos
3. Inicie novamente com script

Se persistir:
```powershell
# Remover database (será recriado)
Remove-Item db/eleicoes.duckdb
.\setup-e-run.ps1
```

---

## ❌ "Out of memory" ou "Slow response"

**Problema:** Dashboard/API muito lento ou "out of memory".

**Solução:**

1. Feche outras aplicações
2. Reduza dataset editando `src/app/config.py`:
   ```python
   # Carregar apenas dados de uma única UF
   ELEICOES_UF = "SP"
   ```

3. Reinicie API e Dashboard

---

## ✅ Ainda não funcionou?

Abra uma [issue detalhada no GitHub](https://github.com/AGDM97/eleicoes-2026/issues) incluindo:

1. Sistema operacional (Windows/Linux/macOS)
2. Versão do Python (`python --version`)
3. **Erro completo** (copie/cole do terminal)
4. O que você tentou fazer

Estou aqui pra ajudar! 🚀
