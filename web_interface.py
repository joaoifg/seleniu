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
SESSION_PATH = os.path.join("output", "session")

# Variável global para controlar o status
scraping_status = {"running": False, "completed": False, "error": None}


def log(msg):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")


def check_session_valid():
    """Verifica se a sessão salva ainda é válida"""
    if not os.path.exists(SESSION_PATH):
        return False
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=SESSION_PATH)
            page = context.new_page()
            
            # Tenta acessar uma página que requer login
            page.goto("https://app.qconcursos.com/b/dashboard", timeout=10000)
            page.wait_for_timeout(3000)
            
            # Se ainda está na página de login, a sessão expirou
            if "entrar" in page.url or "login" in page.url:
                browser.close()
                return False
            
            browser.close()
            return True
    except:
        return False


def scroll_all(page, step=500, pause=1, max_iter=50):
    """
    Rola a página para carregar todo o conteúdo dinâmico.
    """
    log("INFO: Iniciando scroll da página")
    last = 0
    for i in range(max_iter):
        page.evaluate(f"window.scrollBy(0,{step});")
        time.sleep(pause)
        h = page.evaluate("document.body.scrollHeight")
        if h == last:
            log(f"INFO: Scroll completo após {i+1} iterações")
            break
        last = h
        if i % 10 == 0:
            log(f"INFO: Scrolling... iteração {i+1}/{max_iter}")
    else:
        log(f"WARNING: Scroll atingiu limite máximo de {max_iter} iterações")


def click_tab(page, text):
    """
    Clica em uma aba específica baseada no texto.
    """
    log(f"INFO: Procurando aba '{text}'...")
    
    click_tab_js = f"""
    (function() {{
        let found = false;
        document.querySelectorAll('.tab').forEach(tab => {{
            if (tab.textContent.includes('{text}')) {{
                tab.click();
                found = true;
                console.log('Clicou na aba: {text}');
            }}
        }});
        return found;
    }})();
    """
    
    try:
        time.sleep(1)
        result = page.evaluate(click_tab_js)
        if result:
            log(f"INFO: Aba '{text}' clicada com sucesso!")
            time.sleep(2)
        else:
            log(f"WARNING: Aba '{text}' não encontrada")
        time.sleep(1)
    except Exception as e:
        log(f"ERROR: Erro ao clicar na aba '{text}': {str(e)}")


def extract_gabarito_automatico(page):
    """
    Extrai o gabarito automaticamente usando estatísticas - baseado no bookmarklet
    """
    log("INFO: Extraindo gabaritos automaticamente...")
    
    extract_gabarito_js = """
    (function() {
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
                    respostas.push(`${numeroQuestao}:${alternativa}`);
                }
            } catch (error) {
                console.error('Erro ao processar questão:', error);
            }
        });
        
        if (respostas.length > 0) {
            let resultado = respostas.join(', ');
            console.log('Gabaritos extraídos:', resultado);
            return resultado;
        } else {
            console.log('Nenhuma resposta encontrada!');
            return '';
        }
    })();
    """
    
    try:
        resultado = page.evaluate(extract_gabarito_js)
        if resultado:
            log(f"INFO: Gabaritos extraídos: {resultado[:100]}..." if len(resultado) > 100 else f"INFO: Gabaritos extraídos: {resultado}")
            
            # Converte para dicionário
            gabarito_map = {}
            for item in resultado.split(', '):
                if ':' in item:
                    num, alt = item.split(':')
                    gabarito_map[num.strip()] = alt.strip()
            
            return gabarito_map
        else:
            log("WARNING: Nenhum gabarito encontrado")
            return {}
    except Exception as e:
        log(f"ERROR: Erro ao extrair gabaritos: {str(e)}")
        return {}


def extract_all_data_with_javascript(page, gabarito_map=None):
    """
    Extrai todos os dados usando JavaScript - baseado no bookmarklet de extração completa
    """
    log("INFO: Iniciando extração completa de dados com JavaScript...")
    
    # Se não foi fornecido gabarito, tenta extrair automaticamente
    if not gabarito_map:
        gabarito_map = {}
    
    # Converte o gabarito_map para string JavaScript
    gabarito_js = json.dumps(gabarito_map) if gabarito_map else "{}"
    
    extract_all_js = f"""
    (function() {{
        let m = {gabarito_js};
        let p = document.querySelectorAll(".mb-4");
        let nodes = [];
        
        p.forEach(e => {{
            let t = e.querySelector(".index.text-center.font-weight-bold.border-right.pr-2.svelte-1i1uol");
            t = t ? t.textContent.trim() : "";
            let n = m[t] ? "" + m[t] : "";
            
            // Se não tem gabarito no mapa, tenta extrair da estatística
            if (n === "") {{
                try {{
                    let statsEl = e.querySelector("[data-question-statistics-alternatives-statistics]");
                    if (statsEl) {{
                        let stats = JSON.parse(statsEl.getAttribute("data-question-statistics-alternatives-statistics"));
                        let correctAnswer = stats.find(item => item.hit > 0);
                        if (correctAnswer) {{
                            n = correctAnswer.id;
                        }}
                    }}
                }} catch (error) {{
                    console.error('Erro ao extrair estatística:', error);
                }}
            }}
            
            let o = e.querySelector(".title");
            let l = o ? o.textContent.trim() : "";
            let c = e.querySelector(".info.d-flex.flex-wrap.align-items-center.svelte-1i1uol");
            let s = c ? c.textContent.trim().replace(/\\s+/g, " ") : "";
            s.includes(l) && (s = s.replace(l, "").trim());
            
            let d = e.querySelector(".font-size-2.statement-container.svelte-18f2a5m");
            let i = d ? d.innerHTML.trim().replace(/\\n/g, " ") : "";
            let u = Array.from(e.querySelectorAll(".d-block.font-size-1")).map(e => e.outerHTML.trim()).join(" ");
            let b = Array.from(e.querySelectorAll(".question-commentary-text.font-size-2")).map(e => e.outerHTML.trim()).join(" ") + u;
            b = b.replace('<div class="question-commentary-text font-size-2">', '<div class="question-commentary-text font-size-2"><p>------------</p>');
            
            let h = e.querySelector(".question-commentary-text.font-size-2");
            let x = "";
            if (h) {{
                let e_html = h.outerHTML.trim();
                x = `<node MAX_WIDTH="40 cm"><richcontent TYPE="NODE"><html><head></head><body>${{e_html}}</body></html></richcontent></node>`;
            }}
            
            let y = "E" === n ? ' style="background-color: #ffcccc;"' : "";
            let v = [t, n, l, s].filter(Boolean).join(" | ");
            let q = `<span${{y}}>${{v}}</span><br>${{i}}`;
            let k = e.querySelector(".badge.badge-secondary.text-light.py-1.px-1.ml-2.font-size-1");
            k = k ? k.outerHTML.trim() : "";
            
            let N = Array.from(e.querySelectorAll(".text.px-3.font-size-2.svelte-1tiqrp1")).map(e => e.outerHTML.replace('<div class="text px-3.font-size-2 svelte-1tiqrp1">', '<div class="text px-3 font-size-2 svelte-1tiqrp1">&#9830 ')).join("");
            
            if (q.trim() !== "") {{
                let node = `<node MAX_WIDTH="40 cm"><richcontent TYPE="NODE"><html><head></head><body>${{q}}</body></html></richcontent><richcontent TYPE="NOTE" CONTENT-TYPE="xml/"><html><head></head><body>${{b}} | ${{k}}</body></html></richcontent>${{N ? `<node><richcontent TYPE="NODE"><html><head></head><body>${{N}}</body></html></richcontent></node>` : ""}}${{x}}</node>`;
                nodes.push({{gabarito: n, conteudo: node}});
            }}
        }});
        
        // Ordena por gabarito
        nodes.sort((a, b) => a.gabarito.localeCompare(b.gabarito));
        
        console.log(`Extraídos ${{nodes.length}} nódulos`);
        return nodes;
    }})();
    """
    
    try:
        nodes = page.evaluate(extract_all_js)
        log(f"INFO: Extraídos {len(nodes)} nódulos de dados!")
        return nodes
    except Exception as e:
        log(f"ERROR: Erro na extração de dados: {str(e)}")
        return []


def run_automation_thread(email, password, urls):
    """Executa a automação em uma thread separada"""
    global scraping_status
    try:
        scraping_status = {"running": True, "completed": False, "error": None}
        log("INFO: Iniciando automação Playwright...")
        all_nodes = []
        
        with sync_playwright() as p:
            log("INFO: Iniciando navegador Chromium...")
            browser = p.chromium.launch(headless=False)  # headless=False para debug
            
            # Verifica se há sessão salva e válida
            session_exists = os.path.exists(SESSION_PATH)
            session_valid = False
            
            if session_exists:
                log("INFO: Verificando sessão salva...")
                session_valid = check_session_valid()
                if session_valid:
                    log("INFO: Sessão válida encontrada! Reutilizando...")
                    context = browser.new_context(storage_state=SESSION_PATH)
                else:
                    log("INFO: Sessão expirada. Fazendo novo login...")
                    context = browser.new_context()
            else:
                log("INFO: Nenhuma sessão encontrada. Fazendo login...")
                context = browser.new_context()
            
            page = context.new_page()
            
            # Login apenas se necessário
            if not session_valid:
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
                
                # Salva a sessão
                log("INFO: Salvando sessão para uso futuro...")
                try:
                    os.makedirs("output", exist_ok=True)
                    context.storage_state(path=SESSION_PATH)
                    log("INFO: Sessão salva com sucesso!")
                except Exception as e:
                    log(f"WARNING: Erro ao salvar sessão: {str(e)}")
            else:
                log("INFO: Usando sessão existente - login não necessário!")
                # Verifica se realmente está logado
                try:
                    page.goto("https://app.qconcursos.com/b/dashboard", timeout=10000)
                    page.wait_for_timeout(3000)
                    if "entrar" in page.url or "login" in page.url:
                        log("WARNING: Sessão inválida, fazendo novo login...")
                        session_valid = False
                        # Continua para o bloco de login abaixo
                    else:
                        log("INFO: Sessão confirmada como válida!")
                except Exception as e:
                    log(f"WARNING: Erro ao verificar sessão: {str(e)}")
                    session_valid = False
            
            # Se a sessão não é válida, faz login
            if not session_valid:
                log("INFO: Fazendo login...")
                try:
                    page.goto("https://www.qconcursos.com/conta/entrar?return_url=https%3A%2F%2Fapp.qconcursos.com%2F", timeout=30000)
                    page.fill('#login_email', email)
                    page.fill('#login_password', password)
                    page.click('#btnLogin')
                    page.wait_for_timeout(5000)
                    
                    if "entrar" in page.url:
                        log("ERROR: Falha no login. Verifique suas credenciais.")
                        browser.close()
                        scraping_status = {"running": False, "completed": False, "error": "Falha no login"}
                        return
                    
                    log("INFO: Login realizado com sucesso!")
                    
                    # Salva a sessão
                    os.makedirs("output", exist_ok=True)
                    context.storage_state(path=SESSION_PATH)
                    log("INFO: Sessão salva com sucesso!")
                except Exception as e:
                    log(f"ERROR: Erro no login: {str(e)}")
                    browser.close()
                    scraping_status = {"running": False, "completed": False, "error": str(e)}
                    return
            
            # Processa cada URL seguindo a mesma lógica do scraper.py
            log("INFO: INICIANDO PROCESSO COMPLETO DE RASPAGEM DE DADOS")
            for i, url in enumerate(urls, 1):
                if not url.strip():
                    continue
                    
                log(f"INFO: PROCESSANDO URL {i}/{len(urls)}: {url.strip()}")
                try:
                    # Navega para a URL
                    page.goto(url.strip(), wait_until="domcontentloaded", timeout=60000)
                    log("INFO: Página carregada com sucesso!")
                    
                    # Aguarda a página estabilizar
                    time.sleep(5)  # Aumentado de 3 para 5 segundos
                    
                    # PASSO 1: Clica na aba "Estatísticas" para extrair gabaritos
                    log("INFO: PASSO 1: Acessando aba de Estatísticas...")
                    click_tab(page, "Estatísticas")
                    time.sleep(4)  # Aumentado de 2 para 4 segundos
                    
                    # PASSO 2: Extrai gabaritos automaticamente
                    log("INFO: PASSO 2: Extraindo gabaritos automaticamente...")
                    gabarito_map = extract_gabarito_automatico(page)
                    time.sleep(2)  # Aguarda um pouco após extrair gabaritos
                    
                    # PASSO 3: Clica na aba "Comentários de alunos"
                    log("INFO: PASSO 3: Acessando aba de Comentários de alunos...")
                    click_tab(page, "Comentários de alunos")
                    time.sleep(6)  # Aumentado de 3 para 6 segundos - mais tempo para carregar comentários
                    
                    # PASSO 4: Scroll completo para carregar todos os comentários
                    log("INFO: PASSO 4: Carregando todos os comentários (scroll completo)...")
                    scroll_all(page, step=300, pause=1.5, max_iter=80)  # Scroll mais lento e mais iterações
                    
                    # Aguarda um pouco mais para garantir que tudo carregou
                    time.sleep(4)  # Aumentado de 2 para 4 segundos
                    
                    # PASSO 5: Extração completa usando JavaScript
                    log("INFO: PASSO 5: Executando extração completa de dados...")
                    nodes = extract_all_data_with_javascript(page, gabarito_map)
                    
                    if nodes:
                        all_nodes.extend(nodes)
                        log(f"INFO: EXTRAÍDOS {len(nodes)} NÓDULOS DE DADOS!")
                        log(f"INFO: Total acumulado: {len(all_nodes)} nódulos")
                    else:
                        log("WARNING: Nenhum nódulo extraído desta URL")
                    
                    # Pausa entre URLs
                    if i < len(urls):
                        log(f"INFO: Aguardando 3s antes da próxima URL...")
                        time.sleep(3)  # Aumentado de 2 para 3 segundos
                    
                except Exception as e:
                    log(f"ERROR: Erro ao processar URL: {str(e)}")
                    continue
            
            log("INFO: Fechando navegador...")
            browser.close()
        
        # Gera o XML Freeplane usando a mesma lógica do scraper.py
        if all_nodes:
            log("INFO: INICIANDO FORMATAÇÃO DOS DADOS...")
            log("INFO: Construindo arquivo XML do Freeplane...")
            
            # Constrói o XML manualmente baseado na estrutura do bookmarklet
            xml_content = '<map version="freeplane 1.9.8"><node LOCALIZED_TEXT="new_mindmap">'
            for node in all_nodes:
                xml_content += node['conteudo']
            xml_content += '</node></map>'
            
            # Salvar arquivo
            os.makedirs("output", exist_ok=True)
            with open(MM_PATH, "w", encoding="utf-8") as f:
                f.write(xml_content)
            
            log(f"INFO: ARQUIVO SALVO: {MM_PATH}")
            log(f"INFO: PROCESSO FINALIZADO - {len(all_nodes)} NÓDULOS PROCESSADOS!")
            log("INFO: RASPAGEM CONCLUÍDA COM SUCESSO!")
        else:
            log("WARNING: Nenhum dado foi extraído. Verifique as URLs e configurações.")
        
        scraping_status = {"running": False, "completed": True, "error": None}
        
    except Exception as e:
        log(f"ERROR: Erro geral na automação: {str(e)}")
        scraping_status = {"running": False, "completed": False, "error": str(e)}


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

@app.route("/clear_session")
def clear_session():
    """Limpa a sessão salva"""
    try:
        if os.path.exists(SESSION_PATH):
            os.remove(SESSION_PATH)
        return jsonify({"success": True, "message": "Sessão limpa com sucesso"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/session_status")
def session_status():
    """Retorna o status da sessão"""
    session_exists = os.path.exists(SESSION_PATH)
    session_valid = check_session_valid() if session_exists else False
    
    return jsonify({
        "session_exists": session_exists,
        "session_valid": session_valid,
        "message": "Sessão válida" if session_valid else ("Sessão expirada" if session_exists else "Nenhuma sessão")
    })

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