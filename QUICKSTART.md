# 🚀 Guia de Início Rápido - QConcursos Scraper

## ⚡ 3 Passos para Começar

### 1️⃣ **Configure suas credenciais**
```bash
python setup_env.py
```
- Digite seu email do QConcursos
- Digite sua senha
- Arquivo `.env` será criado automaticamente

### 2️⃣ **Adicione URLs no arquivo urls.txt**
```bash
# Exemplo:
https://www.qconcursos.com/questoes-de-concursos/questoes/123456
https://www.qconcursos.com/questoes-de-concursos/questoes/789012
```

### 3️⃣ **Execute com interface web**
```bash
python start_monitor.py
```
- Acesse: **http://localhost:5000** 
- Acompanhe o progresso em tempo real! 📊

---

## 🐳 Com Docker (Ainda Mais Fácil!)

```bash
# 1. Configure credenciais no .env
QC_EMAIL=seu_email@exemplo.com
QC_PASSWORD=sua_senha

# 2. Suba tudo
docker-compose up

# 3. Acesse: http://localhost:5000
```

---

## 🎯 O Que Você Verá na Interface

### ✅ **Dashboard ao Vivo**
- Status: **Executando** / **Parado**
- Progresso: **Barra visual** com porcentagem
- Estatísticas: **URLs processadas**, **nós extraídos**
- **URL atual** sendo processada

### 📝 **Logs em Tempo Real**
- **Logs coloridos** por tipo (INFO, SUCCESS, ERROR)
- **Auto-scroll** automático
- **Timestamps** precisos

### 📸 **Screenshots Automáticos**
- Quando ocorrem erros
- **Galeria visual** das imagens
- **Clique para ampliar**

---

## 🔧 Comandos Úteis

### **Apenas Interface Web**
```bash
python start_monitor.py --mode web
```

### **Apenas Scraper**
```bash
python start_monitor.py --mode scraper
```

### **Testar Login**
```bash
python test_login.py
```

### **Verificar Configuração**
```bash
python setup_env.py
# Escolha opção 2 para verificar
```

---

## 🚨 Resolução Rápida de Problemas

### ❌ **Erro de Login**
```bash
# Teste suas credenciais
python test_login.py
```

### ❌ **Página não carrega**
- Verifique se está usando **urls.txt** correto
- URLs devem ser do QConcursos
- Exemplo: `https://www.qconcursos.com/questoes-de-concursos/...`

### ❌ **Interface não abre**
- Verifique se a porta 5000 está livre
- Tente: `http://127.0.0.1:5000`

---

## 📦 Resultado Final

Após a execução, você terá:

- **📄 XML Freeplane**: `output/qc_freeplane.xml`
- **📝 Logs completos**: `logs/scraper.log`
- **📸 Screenshots**: `screenshots/` (se houver erros)

---

## 🎉 Pronto!

Agora você tem um **monitor visual completo** para acompanhar seu scraping do QConcursos em tempo real! 

**🌐 Acesse: http://localhost:5000** 