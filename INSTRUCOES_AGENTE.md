# Instruções para Agente - Automação QConcursos

## Objetivo
Criar um sistema completo de automação para web scraping do QConcursos que:
1. Faz login automático
2. Navega para URLs específicas
3. Executa scripts JavaScript para capturar dados
4. Gera arquivo Freeplane (.mm) com o resultado

## Estrutura de Arquivos a Criar

```
seleniu/
├── web_interface.py          # Servidor Flask principal
├── templates/
│   └── monitor.html          # Interface web
├── output/                   # Pasta para arquivos gerados
├── logs/                     # Pasta para logs
├── requirements.txt          # Dependências Python
└── README.md                 # Documentação
```

## Passo 1: Criar requirements.txt

```txt
Flask
Flask-SocketIO
selenium
playwright
```

## Passo 2: Criar Interface HTML (templates/monitor.html)

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Automação QConcursos - Web Scraping</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #0001; padding: 32px; }
        h1 { text-align: center; }
        label { display: block; margin-top: 18px; font-weight: bold; }
        input, textarea, button { width: 100%; margin-top: 6px; padding: 10px; border-radius: 4px; border: 1px solid #ccc; font-size: 1em; }
        textarea { resize: vertical; min-height: 80px; }
        button { background: #007bff; color: #fff; border: none; font-weight: bold; cursor: pointer; margin-top: 18px; }
        button:disabled { background: #aaa; }
        #log { background: #222; color: #eee; font-size: 0.95em; margin-top: 24px; padding: 12px; border-radius: 4px; max-height: 200px; overflow-y: auto; }
        #download-mm { background: #28a745; margin-top: 12px; }
    </style>
</head>
<body>
<div class="container">
    <h1>Automação QConcursos</h1>
    <form id="scrape-form">
        <label for="email">E-mail</label>
        <input type="email" id="email" name="email" placeholder="Seu e-mail" required>
        <label for="password">Senha</label>
        <input type="password" id="password" name="password" placeholder="Sua senha" required>
        <label for="urls">URLs para scraping (uma por linha)</label>
        <textarea id="urls" name="urls" placeholder="Cole as URLs aqui" required></textarea>
        <button type="submit" id="btn-login">1. Login e Iniciar Scraping</button>
    </form>
    <button id="btn-download" style="display:none;">2. Baixar Freeplane (.mm)</button>
    <button id="btn-log" type="button">Ver Log</button>
    <div id="log" style="display:none;"></div>
</div>
<script>
    const form = document.getElementById('scrape-form');
    const btnDownload = document.getElementById('btn-download');
    const btnLog = document.getElementById('btn-log');
    const logDiv = document.getElementById('log');

    form.onsubmit = async (e) => {
        e.preventDefault();
        btnDownload.style.display = 'none';
        logDiv.style.display = 'block';
        logDiv.textContent = 'Iniciando automação...';
        const formData = new FormData(form);
        const res = await fetch('/start_scraping', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            logDiv.textContent += '\nScraping finalizado com sucesso!';
            btnDownload.style.display = 'block';
        } else {
            logDiv.textContent += '\nErro: ' + (data.error || 'Falha desconhecida');
        }
    };

    btnDownload.onclick = () => {
        window.location.href = '/download_mm';
    };

    btnLog.onclick = async () => {
        logDiv.style.display = 'block';
        const res = await fetch('/get_log');
        const data = await res.text();
        logDiv.textContent = data;
    };
</script>
</body>
</html>
```

## Passo 3: Criar Servidor Flask (web_interface.py)

```python
from flask import Flask, render_template, request, jsonify, send_file
import os
from playwright.sync_api import sync_playwright
import time
import json

app = Flask(__name__)

LOG_PATH = "logs/scraper.log"
MM_PATH = os.path.join("output", "resultado.mm")


def log(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")


def run_automation(email, password, urls):
    log("INFO: Iniciando automação Playwright...")
    all_responses = []
    all_content = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        log("INFO: Navegando para tela de login...")
        page.goto("https://www.qconcursos.com/conta/entrar?return_url=https%3A%2F%2Fapp.qconcursos.com%2F")
        page.fill('#login_email', email)
        page.fill('#login_password', password)
        page.click('#btnLogin')
        page.wait_for_timeout(3000)
        
        if "entrar" in page.url:
            log("ERROR: Falha no login. Verifique suas credenciais.")
            browser.close()
            return False
            
        log("INFO: Login realizado com sucesso!")
        
        # Para cada URL
        for i, url in enumerate(urls):
            if not url.strip():
                continue
                
            log(f"INFO: Processando URL {i+1}/{len(urls)}: {url.strip()}")
            page.goto(url.strip())
            page.wait_for_timeout(3000)
            
            # 1. Abrir estatísticas
            log("INFO: Abrindo estatísticas...")
            page.evaluate("""
                document.querySelectorAll('.tab').forEach(tab => {
                    if (tab.textContent.includes('Estatísticas')) {
                        tab.click();
                    }
                });
            """)
            page.wait_for_timeout(2000)
            
            # 2. Capturar respostas
            log("INFO: Capturando respostas...")
            responses = page.evaluate("""
                let respostas = [];
                document.querySelectorAll('.mb-4').forEach((questao, index) => {
                    try {
                        let el = questao.querySelector('[data-question-statistics-alternatives-statistics]');
                        if (!el) return;
                        let stats = JSON.parse(el.getAttribute('data-question-statistics-alternatives-statistics'));
                        let correctAnswer = stats.find(item => item.hit > 0);
                        
                        let numeroQuestaoEl = questao.querySelector('.index.text-center.font-weight-bold.border-right.pr-2.svelte-1i1uol');
                        let numeroQuestao = numeroQuestaoEl ? numeroQuestaoEl.textContent.trim().replace(/\\n/g, '') : (index + 1);
                        
                        if (correctAnswer) {
                            let alternativa = correctAnswer.id;
                            respostas.push(numeroQuestao + ':' + alternativa);
                        }
                    } catch (error) {
                        console.error('Erro ao processar questão:', error);
                    }
                });
                return respostas;
            """)
            
            all_responses.extend(responses)
            log(f"INFO: Capturadas {len(responses)} respostas")
            
            # 3. Abrir comentários
            log("INFO: Abrindo comentários...")
            page.evaluate("""
                document.querySelectorAll('.tab').forEach(tab => {
                    if (tab.textContent.includes('Comentários de alunos')) {
                        tab.click();
                    }
                });
            """)
            page.wait_for_timeout(2000)
            
            # 4. Scrollar para carregar tudo
            log("INFO: Scrollando para carregar conteúdo...")
            page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight);
            """)
            page.wait_for_timeout(3000)
            
            # 5. Capturar conteúdo completo
            log("INFO: Capturando conteúdo das questões...")
            content = page.evaluate("""
                let nodes = [];
                document.querySelectorAll('.mb-4').forEach(questao => {
                    let numeroEl = questao.querySelector('.index.text-center.font-weight-bold.border-right.pr-2.svelte-1i1uol');
                    let numero = numeroEl ? numeroEl.textContent.trim() : '';
                    
                    let tituloEl = questao.querySelector('.title');
                    let titulo = tituloEl ? tituloEl.textContent.trim() : '';
                    
                    let infoEl = questao.querySelector('.info.d-flex.flex-wrap.align-items-center.svelte-1i1uol');
                    let info = infoEl ? infoEl.textContent.trim().replace(/\\s+/g, ' ') : '';
                    
                    let enunciadoEl = questao.querySelector('.font-size-2.statement-container.svelte-18f2a5m');
                    let enunciado = enunciadoEl ? enunciadoEl.innerHTML.trim().replace(/\\n/g, ' ') : '';
                    
                    let alternativas = Array.from(questao.querySelectorAll('.d-block.font-size-1')).map(el => el.outerHTML.trim()).join(' ');
                    
                    let comentarios = Array.from(questao.querySelectorAll('.question-commentary-text.font-size-2')).map(el => el.outerHTML.trim()).join(' ') + alternativas;
                    
                    let badgeEl = questao.querySelector('.badge.badge-secondary.text-light.py-1.px-1.ml-2.font-size-1');
                    let badge = badgeEl ? badgeEl.outerHTML.trim() : '';
                    
                    let comentariosAlunos = Array.from(questao.querySelectorAll('.text.px-3.font-size-2.svelte-1tiqrp1')).map(el => el.outerHTML.replace('<div class="text px-3.font-size-2 svelte-1tiqrp1">', '<div class="text px-3 font-size-2 svelte-1tiqrp1">&#9830 ')).join('');
                    
                    nodes.push({
                        numero: numero,
                        titulo: titulo,
                        info: info,
                        enunciado: enunciado,
                        alternativas: alternativas,
                        comentarios: comentarios,
                        badge: badge,
                        comentariosAlunos: comentariosAlunos
                    });
                });
                return nodes;
            """)
            
            all_content.extend(content)
            log(f"INFO: Capturado conteúdo de {len(content)} questões")
        
        browser.close()
    
    # Gerar arquivo .mm
    log("INFO: Gerando arquivo Freeplane...")
    generate_mm_file(all_responses, all_content)
    log("INFO: Automação finalizada com sucesso!")
    return True


def generate_mm_file(responses, content):
    # Criar dicionário de respostas
    respostas_dict = {}
    for resp in responses:
        if ':' in resp:
            num, alt = resp.split(':', 1)
            respostas_dict[num.strip()] = alt.strip()
    
    # Gerar XML Freeplane
    xml_content = '<map version="freeplane 1.9.8">\n<node LOCALIZED_TEXT="new_mindmap">\n'
    
    for item in content:
        numero = item.get('numero', '')
        resposta = respostas_dict.get(numero, '')
        titulo = item.get('titulo', '')
        info = item.get('info', '')
        enunciado = item.get('enunciado', '')
        alternativas = item.get('alternativas', '')
        comentarios = item.get('comentarios', '')
        badge = item.get('badge', '')
        comentariosAlunos = item.get('comentariosAlunos', '')
        
        # Estilo para respostas erradas
        style = ' style="background-color: #ffcccc;"' if resposta == 'E' else ''
        
        # Cabeçalho da questão
        header = f"{numero} | {resposta} | {titulo} | {info}".strip()
        if header.endswith('|'):
            header = header[:-1].strip()
        
        # Conteúdo principal
        node_content = f'<span{style}>{header}</span><br>{enunciado}'
        
        # Nota com comentários
        note_content = f"{comentarios} | {badge}"
        
        # XML do nó
        xml_node = f'''<node MAX_WIDTH="40 cm">
<richcontent TYPE="NODE">
<html>
<head></head>
<body>{node_content}</body>
</html>
</richcontent>
<richcontent TYPE="NOTE" CONTENT-TYPE="xml/">
<html>
<head></head>
<body>{note_content}</body>
</html>
</richcontent>'''
        
        # Adicionar comentários de alunos se existirem
        if comentariosAlunos:
            xml_node += f'''
<node>
<richcontent TYPE="NODE">
<html>
<head></head>
<body>{comentariosAlunos}</body>
</html>
</richcontent>
</node>'''
        
        xml_node += '</node>\n'
        xml_content += xml_node
    
    xml_content += '</node>\n</map>'
    
    # Salvar arquivo
    os.makedirs("output", exist_ok=True)
    with open(MM_PATH, "w", encoding="utf-8") as f:
        f.write(xml_content)


@app.route("/")
def index():
    return render_template("monitor.html")

@app.route("/start_scraping", methods=["POST"])
def start_scraping():
    email = request.form.get("email")
    password = request.form.get("password")
    urls = request.form.get("urls", "").splitlines()
    # Limpa log
    open(LOG_PATH, "w").close()
    ok = run_automation(email, password, urls)
    return jsonify({"success": ok, "error": None if ok else "Falha no login ou scraping."})

@app.route("/download_mm")
def download_mm():
    if os.path.exists(MM_PATH):
        return send_file(MM_PATH, as_attachment=True)
    return "Arquivo não encontrado", 404

@app.route("/get_log")
def get_log():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "Sem logs ainda."

if __name__ == "__main__":
    app.run(debug=True)
```

## Passo 4: Criar README.md

```markdown
# Automação QConcursos - Web Scraping

Sistema automatizado para fazer web scraping do QConcursos e gerar arquivos Freeplane (.mm) com questões, respostas e comentários.

## 🚀 Como Usar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Executar a Interface Web

```bash
python web_interface.py
```

Acesse: http://localhost:5000

### 3. Fluxo de Automação

1. **Login**: Digite seu email e senha do QConcursos
2. **URLs**: Cole as URLs das questões (uma por linha)
3. **Iniciar**: Clique em "Login e Iniciar Scraping"
4. **Download**: Após finalizar, clique em "Baixar Freeplane (.mm)"

## 📋 Exemplo de URLs

```
https://app.qconcursos.com/playground/questoes?discipline_ids[]=100&examining_board_ids[]=2&per_page=50&subject_ids[]=315
https://app.qconcursos.com/playground/questoes?discipline_ids%5B%5D=96&per_page=50&examining_board_ids%5B%5D=2&subject_ids%5B%5D=26271
```

## 🔧 Funcionalidades

- **Login Automático**: Autenticação no QConcursos
- **Captura de Respostas**: Extrai gabarito das estatísticas
- **Comentários**: Coleta comentários de alunos e professores
- **Scroll Automático**: Carrega todo o conteúdo da página
- **Arquivo Freeplane**: Gera arquivo .mm pronto para uso

## 📁 Estrutura de Arquivos

```
seleniu/
├── web_interface.py      # Servidor Flask
├── templates/
│   └── monitor.html      # Interface web
├── output/
│   └── resultado.mm      # Arquivo gerado
├── logs/
│   └── scraper.log       # Logs da automação
└── requirements.txt      # Dependências
```

## ⚠️ Observações

- Use apenas para fins educacionais
- Respeite os termos de uso do QConcursos
- O sistema funciona em modo headless (sem interface gráfica)
- Os logs são salvos em tempo real

## 🐛 Troubleshooting

Se houver problemas:

1. Verifique suas credenciais de login
2. Confirme se as URLs estão corretas
3. Verifique os logs em `logs/scraper.log`
4. Certifique-se de que o Chromium foi instalado: `python -m playwright install chromium`
```

## Passo 5: Comandos de Instalação e Execução

```bash
# 1. Criar pastas necessárias
mkdir -p templates output logs

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Instalar navegador Chromium
python -m playwright install chromium

# 4. Executar o sistema
python web_interface.py
```

## Fluxo de Funcionamento

1. **Interface Web**: Usuário acessa http://localhost:5000
2. **Login**: Sistema faz login automático no QConcursos
3. **Navegação**: Para cada URL, navega e executa scripts JS
4. **Captura**: Extrai respostas, enunciados e comentários
5. **Geração**: Cria arquivo .mm no formato Freeplane
6. **Download**: Usuário baixa o arquivo gerado

## Scripts JavaScript Executados

1. **Abrir Estatísticas**: Clica na aba "Estatísticas"
2. **Capturar Respostas**: Extrai gabarito das estatísticas
3. **Abrir Comentários**: Clica na aba "Comentários de alunos"
4. **Scroll**: Rola a página para carregar todo conteúdo
5. **Extrair Dados**: Captura enunciados, alternativas e comentários

## Formato do Arquivo .mm

O arquivo gerado segue o formato XML do Freeplane com:
- Nós para cada questão
- Cabeçalho com número, resposta, título e info
- Enunciado no corpo do nó
- Comentários na nota
- Comentários de alunos em nós filhos
- Destaque vermelho para respostas erradas 