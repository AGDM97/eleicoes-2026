# 📥 Guia Completo de Instalação

Siga este guia passo-a-passo para iniciantes.

---

## 📋 Pré-requisitos

Você precisa ter **Python 3.9+** instalado.

### ✅ Verificar se Python está instalado

**Windows (PowerShell):**
```powershell
python --version
```

**Linux/macOS:**
```bash
python3 --version
```

Se retornar algo como `Python 3.11.0`, você está pronto! ✅

Se retornar `command not found`, [baixe Python aqui](https://www.python.org/downloads/).

> **⚠️ Importante:** Ao instalar Python no Windows, **marque "Add Python to PATH"**

---

## 🚀 Instalação com Um Click

Este projeto foi feito para ser super fácil de instalar.

### 1️⃣ Clonar o Repositório

Abra PowerShell (Windows) ou Terminal (Linux/macOS) e vá para uma pasta onde quer guardar o projeto:

```powershell
# Exemplo: C:\Users\voce\Projetos\
cd $HOME\Projetos

# Clonar repositório
git clone https://github.com/AGDM97/eleicoes-2026.git
cd eleicoes-2026
```

### 2️⃣ Executar o Script de Setup

Agora é só executar o script apropriado:

#### 🪟 Windows (PowerShell)

```powershell
.\setup-e-run.ps1
```

Aguarde enquanto o script:
- ✅ Cria ambiente virtual
- ✅ Instala dependências (FastAPI, DuckDB, Streamlit)
- ✅ Baixa dados eleitorais do TSE
- ✅ Inicia API
- ✅ Abre Dashboard automaticamente

Tudo deve estar pronto em **~3-5 minutos** 🎉

#### 🐧 Linux / 🍎 macOS

```bash
chmod +x setup-e-run.sh
./setup-e-run.sh
```

---

## 🌐 Usar o Dashboard

Depois que o script termina, o navegador abre automaticamente em:

### **http://localhost:8501**

Você verá:
- 🔍 Campo de busca para candidatos
- 📊 Tabela com resultados
- 💰 Abas com detalhes (votos, bens, finanças)

### Exemplo: Buscar um candidato

1. Digite na barra de busca: `"silva"`
2. Pressione Enter
3. Veja todos os candidatos com "Silva" no nome
4. Clique em um para ver detalhes

---

## 🛑 Parar o Sistema

Para parar tudo, pressione **Ctrl+C** no terminal.

---

## 🔄 Próximas Execuções (Mais Rápido)

Depois da primeira vez, rodar novamente é muito mais rápido (apenas 30 segundos):

```powershell
.\setup-e-run.ps1    # Windows
```

```bash
./setup-e-run.sh     # Linux/macOS
```

Dashboard abre em http://localhost:8501

---

## 🆘 Algo Deu Errado?

Veja [**TROUBLESHOOTING.md**](../TROUBLESHOOTING.md) para soluções de problemas comuns.

---

## 📚 Próximos Passos (Opcional)

### Testar a API diretamente

A API está em http://127.0.0.1:8000

Abra seu navegador:
```
http://127.0.0.1:8000/docs
```

Você verá a documentação interativa da API (Swagger UI).

### Configurar para outro estado

Edite `.env` na raiz do projeto:

```bash
ELEICOES_UF=MG
ELEICOES_CARGO=GOVERNADOR
ELEICOES_ANO=2022
```

E rode o script novamente.

### Executar testes

```powershell
pip install -r requirements.txt
python -m pytest tests/ -v
```

---

## 💡 Dicas Importantes

1. **Python não encontrado?**
   - Reinstale Python e marque "Add Python to PATH"
   - Reinicie o PowerShell/Terminal

2. **Porta 8000/8501 em uso?**
   - Feche outro application que esteja usando a porta
   - Veja [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)

3. **Quer contribuir?**
   - Veja [CONTRIBUTING.md](../CONTRIBUTING.md)

4. **Dados históricos?**
   - Temos dados de eleições brasileiras públicas do TSE
   - Fácil adicionar 2014, 2018, 2026, etc.

---

## 📞 Precisa de Ajuda?

Abra uma [issue no GitHub](https://github.com/AGDM97/eleicoes-2026/issues) descrevendo o problema. ❤️
