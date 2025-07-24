# QConcursos Scraper com Interface Web 🕷️📊

Scraper automatizado para extrair questões do QConcursos e gerar mapas mentais no formato Freeplane (.mm), agora com **interface web em tempo real** para monitoramento completo do processo!

## ✨ Funcionalidades

### 🔄 Scraping Automatizado
- **Login automático** com múltiplos seletores de fallback
- **Processamento de múltiplas URLs** em lote
- **Extração inteligente** de questões, gabaritos e comentários
- **Geração automática** de mapas mentais Freeplane

### 📊 Interface Web em Tempo Real
- **Monitor visual** com dashboard moderno e responsivo
- **Logs em tempo real** via WebSocket
- **Progresso visual** com barras de progresso e estatísticas
- **Screenshots automáticos** quando ocorrem erros
- **Status detalhado** de cada URL processada

### 🐳 Deploy com Docker
- **Containerização completa** com Docker Compose
- **Redis integrado** para comunicação em tempo real
- **Volumes persistentes** para logs, screenshots e outputs

## 🚀 Como Usar

### 📋 Pré-requisitos

1. **Python 3.8+** ou **Docker**
2. **Credenciais do QConcursos**
3. **Arquivo urls.txt** com as URLs a processar

### 🔧 Configuração Rápida

#### 1. **Configure as credenciais:**
```bash
python setup_env.py
```

#### 2. **Crie o arquivo urls.txt:**
```
https://www.qconcursos.com/questoes-de-concursos/prova/123
https://www.qconcursos.com/questoes-de-concursos/prova/456
```

### 🖥️ Executar Localmente

#### **Opção 1: Interface Completa (Recomendado)**
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar interface web + scraper
python start_monitor.py

# Acessar: http://localhost:5000
```

#### **Opção 2: Apenas Interface Web**
```bash
python start_monitor.py --mode web
```

#### **Opção 3: Apenas Scraper**
```bash
python start_monitor.py --mode scraper
```

#### **Opção 4: Teste de Login**
```bash
python test_login.py
```

### 🐳 Executar com Docker

#### **Método 1: Interface Completa**
```bash
# Subir todos os serviços
docker-compose up

# Acessar: http://localhost:5000
```

#### **Método 2: Apenas Interface Web**
```bash
docker-compose up redis web-interface
```

## 📊 Interface Web - Funcionalidades

### 🎯 Dashboard Principal
- **Status do Sistema**: Running/Stopped com ícones visuais
- **Tempo Decorrido**: Cronômetro em tempo real
- **Progresso Geral**: Barra de progresso com porcentagem
- **Estatísticas**: URLs processadas, nós extraídos, etc.

### 📝 Logs em Tempo Real
- **Auto-scroll** configurável
- **Filtros por nível**: INFO, SUCCESS, WARNING, ERROR
- **Timestamps** precisos
- **Colorização** por tipo de log

### 📸 Galeria de Screenshots
- **Screenshots automáticos** em caso de erro
- **Visualização em grid**
- **Clique para ampliar**
- **Organização cronológica**

### 📈 Monitoramento Avançado
- **URL atual** sendo processada
- **Progress tracking** detalhado
- **WebSocket** para atualizações instantâneas
- **Responsivo** para mobile e desktop

## 🔧 Configuração Avançada

### ⚙️ config.py
```python
# Configurações de scraping
SCRAPING_CONFIG = {
    "headless": False,          # True para execução em background
    "timeout": 30000,           # Timeout de login (ms)
    "scroll_step": 1500,        # Pixels por scroll
    "url_pause": 1,             # Pausa entre URLs (s)
}

# Configurações de debug
DEBUG_CONFIG = {
    "screenshot_on_error": True,  # Screenshots automáticos
    "verbose_logging": True,      # Logs detalhados
    "save_raw_html": True,       # Salvar HTML para debug
}
```

### 🌐 Interface Web
- **Porta**: 5000 (configurável)
- **Redis**: Comunicação em tempo real
- **WebSocket**: Logs instantâneos
- **API REST**: Status e dados

## 📁 Estrutura de Arquivos

```
seleniu/
├── 📊 Interface Web
│   ├── web_interface.py          # Servidor Flask principal
│   ├── templates/monitor.html    # Interface HTML
│   └── start_monitor.py          # Script de inicialização
├── 🕷️ Scraping
│   ├── scraper.py                # Scraper principal
│   ├── config.py                 # Configurações
│   ├── freeplane.py              # Gerador XML
│   └── test_login.py             # Teste de login
├── 🔧 Configuração
│   ├── setup_env.py              # Configurador de credenciais
│   ├── requirements.txt          # Dependências Python
│   ├── Dockerfile                # Container
│   └── docker-compose.yml        # Orquestração
├── 📂 Dados
│   ├── urls.txt                  # URLs a processar
│   ├── .env                      # Credenciais (criar)
│   ├── logs/                     # Logs automáticos
│   ├── screenshots/              # Screenshots de erro
│   └── output/                   # XMLs gerados
```

## 🔍 Monitoramento e Debug

### 📊 Acesso à Interface
- **URL**: http://localhost:5000
- **Auto-refresh**: Dados atualizados a cada 5s
- **WebSocket**: Logs instantâneos

### 🐛 Debugging
- **Screenshots**: Salvos automaticamente em erros
- **Logs detalhados**: Todos os passos do processo
- **HTML bruto**: Para análise de seletores
- **Modo visual**: Navegador visível para debug

### 📝 Logs Estruturados
```
[12:34:56] INFO: Iniciando scraping do QConcursos...
[12:34:58] SUCCESS: Login realizado com sucesso!
[12:35:02] INFO: Scraping URL 1/5: https://...
[12:35:10] SUCCESS: Extraídos 25 nós desta URL
```

## 🚨 Solução de Problemas

### ❌ Erro de Login
1. **Verificar credenciais**: `python setup_env.py`
2. **Testar login**: `python test_login.py`
3. **Verificar seletores**: Interface web mostra elementos encontrados

### ❌ Timeout na Interface
1. **Verificar Redis**: `docker-compose logs redis`
2. **Verificar logs**: Pasta `logs/`
3. **Reiniciar serviços**: `docker-compose restart`

### ❌ Seletores Desatualizados
1. **Debug visual**: `headless: False` no config.py
2. **Analisar HTML**: Screenshots e HTML salvos automaticamente
3. **Atualizar seletores**: config.py > SEL

## 📦 Dependências

### 🐍 Python
- **playwright**: Automação de navegador
- **flask**: Servidor web
- **flask-socketio**: WebSocket para tempo real
- **redis**: Cache e comunicação
- **python-dotenv**: Variáveis de ambiente

### 🐳 Docker
- **Python 3.11**: Base
- **Redis 7**: Cache e pub/sub
- **Volumes**: Persistência de dados

## 🎯 Próximas Funcionalidades

- [ ] **API REST** completa para integração
- [ ] **Agendamento** de execuções
- [ ] **Múltiplos sites** de concurso
- [ ] **Export** em múltiplos formatos
- [ ] **Dashboard** com métricas históricas

## 🤝 Contribuindo

1. **Fork** o projeto
2. **Crie** uma branch: `git checkout -b feature/nova-funcionalidade`
3. **Commit** suas mudanças: `git commit -m 'Add nova funcionalidade'`
4. **Push** para a branch: `git push origin feature/nova-funcionalidade`
5. **Abra** um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

**🚀 Desenvolvido para automatizar e monitorar o scraping de questões de concurso com interface web moderna e tempo real!** 