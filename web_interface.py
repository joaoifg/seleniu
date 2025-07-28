#!/usr/bin/env python3
"""
Interface web para monitorar o scraping do QConcursos em tempo real.
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
from playwright.sync_api import sync_playwright
import time
import json
import threading

app = Flask(__name__)

LOG_PATH = "logs/scraper.log"
MM_PATH = os.path.join("output", "resultado.mm")

# Variável global para controlar o status
scraping_status = {"running": False, "completed": False, "error": None}


def log(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")


def run_automation_thread(email, password, urls):
    """Executa a automação em uma thread separada"""
    global scraping_status
    try:
        scraping_status = {"running": True, "completed": False, "error": None}
        log("INFO: Iniciando automação Playwright...")
        all_responses = []
        all_content = []
        
        with sync_playwright() as p:
            log("INFO: Iniciando navegador Chromium...")
            browser = p.chromium.launch(headless=False)  # headless=False para debug
            context = browser.new_context()
            page = context.new_page()
            
            # Login
            log("INFO: Navegando para tela de login...")
            try:
                page.goto("https://www.qconcursos.com/conta/entrar?return_url=https%3A%2F%2Fapp.qconcursos.com%2F", timeout=30000)
                log("INFO: Página de login carregada com sucesso")
            except Exception as e:
                log(f"ERROR: Erro ao carregar página de login: {str(e)}")
                browser.close()
                scraping_status = {"running": False, "completed": False, "error": str(e)}
                return
            
            log("INFO: Preenchendo credenciais...")
            try:
                page.fill('#login_email', email)
                page.fill('#login_password', password)
                log("INFO: Credenciais preenchidas")
            except Exception as e:
                log(f"ERROR: Erro ao preencher credenciais: {str(e)}")
                browser.close()
                scraping_status = {"running": False, "completed": False, "error": str(e)}
                return
            
            log("INFO: Clicando no botão de login...")
            try:
                page.click('#btnLogin')
                page.wait_for_timeout(5000)
                log("INFO: Botão de login clicado")
            except Exception as e:
                log(f"ERROR: Erro ao clicar no botão de login: {str(e)}")
                browser.close()
                scraping_status = {"running": False, "completed": False, "error": str(e)}
                return
            
            log(f"INFO: URL atual após login: {page.url}")
            if "entrar" in page.url:
                log("ERROR: Falha no login. Verifique suas credenciais.")
                browser.close()
                scraping_status = {"running": False, "completed": False, "error": "Falha no login"}
                return
                
            log("INFO: Login realizado com sucesso!")
            
            # Para cada URL
            for i, url in enumerate(urls):
                if not url.strip():
                    continue
                    
                log(f"INFO: Processando URL {i+1}/{len(urls)}: {url.strip()}")
                try:
                    page.goto(url.strip(), timeout=30000)
                    page.wait_for_timeout(3000)
                    log("INFO: URL carregada com sucesso")
                except Exception as e:
                    log(f"ERROR: Erro ao carregar URL {url.strip()}: {str(e)}")
                    continue
                
                # 1. Abrir estatísticas
                log("INFO: Abrindo estatísticas...")
                try:
                    page.evaluate("""
                        document.querySelectorAll('.tab').forEach(tab => {
                            if (tab.textContent.includes('Estatísticas')) {
                                tab.click();
                            }
                        });
                    """)
                    page.wait_for_timeout(2000)
                    log("INFO: Estatísticas abertas")
                except Exception as e:
                    log(f"ERROR: Erro ao abrir estatísticas: {str(e)}")
                
                # 2. Capturar respostas
                log("INFO: Capturando respostas...")
                try:
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
                except Exception as e:
                    log(f"ERROR: Erro ao capturar respostas: {str(e)}")
                
                # 3. Abrir comentários
                log("INFO: Abrindo comentários...")
                try:
                    page.evaluate("""
                        document.querySelectorAll('.tab').forEach(tab => {
                            if (tab.textContent.includes('Comentários de alunos')) {
                                tab.click();
                            }
                        });
                    """)
                    page.wait_for_timeout(2000)
                    log("INFO: Comentários abertos")
                except Exception as e:
                    log(f"ERROR: Erro ao abrir comentários: {str(e)}")
                
                # 4. Scrollar para carregar tudo
                log("INFO: Scrollando para carregar conteúdo...")
                try:
                    page.evaluate("""
                        window.scrollTo(0, document.body.scrollHeight);
                    """)
                    page.wait_for_timeout(3000)
                    log("INFO: Scroll realizado")
                except Exception as e:
                    log(f"ERROR: Erro ao scrollar: {str(e)}")
                
                # 5. Capturar conteúdo completo
                log("INFO: Capturando conteúdo das questões...")
                try:
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
                except Exception as e:
                    log(f"ERROR: Erro ao capturar conteúdo: {str(e)}")
            
            log("INFO: Fechando navegador...")
            browser.close()
        
        # Gerar arquivo .mm
        log("INFO: Gerando arquivo Freeplane...")
        generate_mm_file(all_responses, all_content)
        log("INFO: Automação finalizada com sucesso!")
        scraping_status = {"running": False, "completed": True, "error": None}
        
    except Exception as e:
        log(f"ERROR: Erro geral na automação: {str(e)}")
        scraping_status = {"running": False, "completed": False, "error": str(e)}


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
    try:
        email = request.form.get("email")
        password = request.form.get("password")
        urls = request.form.get("urls", "").splitlines()
        
        # Limpa log
        open(LOG_PATH, "w").close()
        
        # Inicia a automação em uma thread separada
        thread = threading.Thread(target=run_automation_thread, args=(email, password, urls))
        thread.daemon = True
        thread.start()
        
        return jsonify({"success": True, "message": "Automação iniciada"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/status")
def get_status():
    return jsonify(scraping_status)

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