import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from config import LOGIN_URL, SEL, SCRAPING_CONFIG, OUTPUT_CONFIG, DEBUG_CONFIG

# Importar o handler da interface web se disponível
web_handler = None
try:
    from web_interface import WebSocketLogHandler
    web_handler = WebSocketLogHandler
except ImportError:
    pass

def log_message(message, level="INFO"):
    """
    Envia mensagem de log para a interface web e para o console.
    """
    print(f"[{level}] {message}")
    if web_handler:
        web_handler.log(message, level)

def update_progress(processed, total, current_url=""):
    """
    Atualiza o progresso na interface web.
    """
    if web_handler:
        web_handler.update_progress(processed, total, current_url)

def add_screenshot(filename):
    """
    Adiciona screenshot à interface web.
    """
    if web_handler:
        web_handler.add_screenshot(filename)

def set_running_status(running):
    """
    Define o status de execução na interface web.
    """
    if web_handler:
        web_handler.set_running(running)

def scroll_all(page, step=None, pause=None, max_iter=None):
    """
    Rola a página para carregar todo o conteúdo dinâmico.
    
    Args:
        page: Página do Playwright
        step: Quantidade de pixels para rolar a cada iteração
        pause: Tempo de pausa entre rolagens
        max_iter: Número máximo de iterações
    """
    # Usa configurações padrão se não especificado
    step = step or SCRAPING_CONFIG["scroll_step"]
    pause = pause or SCRAPING_CONFIG["scroll_pause"]
    max_iter = max_iter or SCRAPING_CONFIG["scroll_max_iter"]
    
    log_message(f"🔄 Iniciando scroll da página (step={step}, pause={pause}s, max_iter={max_iter})")
    last = 0
    for i in range(max_iter):
        page.evaluate(f"window.scrollBy(0,{step});")
        time.sleep(pause)
        h = page.evaluate("document.body.scrollHeight")
        if h == last:
            log_message(f"✅ Scroll completo após {i+1} iterações (altura final: {h}px)")
            break
        last = h
        if i % 10 == 0:  # Log a cada 10 iterações
            log_message(f"   Scrolling... iteração {i+1}/{max_iter} (altura: {h}px)")
    else:
        log_message(f"⚠️ Scroll atingiu limite máximo de {max_iter} iterações")

def click_tab(page, text):
    """
    Clica em uma aba específica baseada no texto.
    Garante que a aba está visível e estável antes de clicar.
    Args:
        page: Página do Playwright
        text: Texto da aba a ser clicada
    """
    log_message(f"🎯 Procurando aba '{text}'...")
    
    # JavaScript para clicar na aba - baseado no bookmarklet
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
        # Aguarda um pouco para garantir que as abas estão carregadas
        time.sleep(1)
        
        result = page.evaluate(click_tab_js)
        if result:
            log_message(f"✅ Aba '{text}' clicada com sucesso!")
            time.sleep(2)  # Aguarda o conteúdo da aba carregar
        else:
            log_message(f"⚠️ Aba '{text}' não encontrada")
            
        # Aguarda um pouco mais para estabilizar
        time.sleep(1)
        
    except Exception as e:
        log_message(f"❌ Erro ao clicar na aba '{text}': {e}", "ERROR")

def extract_gabarito_automatico(page):
    """
    Extrai o gabarito automaticamente usando estatísticas - baseado no bookmarklet
    """
    log_message("🎯 Extraindo gabaritos automaticamente...")
    
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
            log_message(f"✅ Gabaritos extraídos: {resultado[:100]}..." if len(resultado) > 100 else f"✅ Gabaritos extraídos: {resultado}")
            
            # Converte para dicionário
            gabarito_map = {}
            for item in resultado.split(', '):
                if ':' in item:
                    num, alt = item.split(':')
                    gabarito_map[num.strip()] = alt.strip()
            
            return gabarito_map
        else:
            log_message("⚠️ Nenhum gabarito encontrado")
            return {}
    except Exception as e:
        log_message(f"❌ Erro ao extrair gabaritos: {e}", "ERROR")
        return {}

def extract_all_data_with_javascript(page, gabarito_map=None):
    """
    Extrai todos os dados usando JavaScript - baseado no bookmarklet de extração completa
    """
    log_message("🔍 Iniciando extração completa de dados com JavaScript...")
    
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
        log_message(f"✅ Extraídos {len(nodes)} nódulos de dados!")
        return nodes
    except Exception as e:
        log_message(f"❌ Erro na extração de dados: {e}", "ERROR")
        return []

def debug_page_elements(page, description=""):
    """
    Debug helper para inspecionar elementos da página.
    
    Args:
        page: Página do Playwright
        description: Descrição do momento da debug
    """
    log_message(f"=== DEBUG: {description} ===")
    log_message(f"URL atual: {page.url}")
    log_message(f"Título da página: {page.title()}")
    
    # Verifica se elementos de login existem
    email_exists = page.locator("#login_email").count() > 0
    password_exists = page.locator("#login_password").count() > 0
    submit_exists = page.locator("#btnLogin").count() > 0
    
    log_message(f"Email field exists: {email_exists}")
    log_message(f"Password field exists: {password_exists}")
    log_message(f"Submit button exists: {submit_exists}")
    
    # Procura por campos de input alternativos
    all_inputs = page.locator("input").count()
    log_message(f"Total input fields found: {all_inputs}")
    
    for i in range(min(all_inputs, 10)):  # Máximo 10 inputs
        input_elem = page.locator("input").nth(i)
        try:
            input_type = input_elem.get_attribute("type") or "text"
            input_id = input_elem.get_attribute("id") or "no-id"
            input_name = input_elem.get_attribute("name") or "no-name"
            input_class = input_elem.get_attribute("class") or "no-class"
            log_message(f"  Input {i}: type='{input_type}', id='{input_id}', name='{input_name}', class='{input_class}'")
        except Exception as e:
            log_message(f"  Input {i}: Error reading attributes - {e}")
    
    # Procura por buttons alternativos
    all_buttons = page.locator("button").count()
    log_message(f"Total buttons found: {all_buttons}")
    
    for i in range(min(all_buttons, 5)):  # Máximo 5 buttons
        button_elem = page.locator("button").nth(i)
        try:
            button_id = button_elem.get_attribute("id") or "no-id"
            button_text = button_elem.inner_text().strip()[:50] or "no-text"
            button_class = button_elem.get_attribute("class") or "no-class"
            log_message(f"  Button {i}: id='{button_id}', text='{button_text}', class='{button_class}'")
        except Exception as e:
            log_message(f"  Button {i}: Error reading attributes - {e}")

def main():
    """
    Função principal que executa todo o processo de scraping.
    """
    # Marca o início da execução
    set_running_status(True)
    
    try:
        # Carrega variáveis de ambiente
        load_dotenv()
        email = os.getenv("QC_EMAIL")
        password = os.getenv("QC_PASSWORD")
        
        if not email or not password:
            raise RuntimeError("Defina QC_EMAIL e QC_PASSWORD no arquivo .env")

        # Lê URLs do arquivo
        urls = [u.strip() for u in Path("urls.txt").read_text().splitlines() if u.strip()]

        # Cria diretório de saída
        out_dir = Path(OUTPUT_CONFIG["output_dir"])
        out_dir.mkdir(exist_ok=True)
        
        # Cria diretório de screenshots
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(exist_ok=True)

        log_message("🚀 INICIANDO SCRAPING COMPLETO DO QCONCURSOS...")
        log_message(f"📊 Total de URLs a processar: {len(urls)}")
        
        # Atualiza progresso inicial
        update_progress(0, len(urls))
        
        with sync_playwright() as p:
            # Inicia o navegador com configurações anti-detecção
            browser = p.chromium.launch(
                headless=SCRAPING_CONFIG["headless"],
                args=['--disable-blink-features=AutomationControlled']  # Reduz detecção de automação
            )
            context = browser.new_context(
                user_agent=SCRAPING_CONFIG["user_agent"]
            )
            page = context.new_page()
            
            # Configura headers adicionais se especificado
            if SCRAPING_CONFIG["user_agent"]:
                page.set_extra_http_headers({
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                })

            try:
                # === NOVO LOGIN PADRONIZADO ===
                log_message("🔐 INICIANDO PROCESSO DE LOGIN...", "INFO")
                log_message("1. Navegando para a página de login...", "INFO")
                page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

                log_message("2. Aguardando formulário de login...", "INFO")
                try:
                    page.wait_for_selector("#login_form", state="visible", timeout=15000)
                    log_message("✓ Formulário de login encontrado!", "SUCCESS")
                except Exception as form_error:
                    log_message(f"✗ Erro ao aguardar formulário: {form_error}", "WARNING")

                log_message("3. Aguardando JavaScript carregar completamente...", "INFO")
                time.sleep(3)
                if DEBUG_CONFIG["verbose_logging"]:
                    debug_page_elements(page, "Página de login carregada")

                log_message("4. Tentando aguardar pelo campo de email...", "INFO")
                try:
                    page.wait_for_selector(SEL["email"], state="visible", timeout=10000)
                    email_element = page.locator(SEL["email"])
                    if email_element.is_enabled():
                        log_message("✓ Campo de email encontrado e habilitado!", "SUCCESS")
                    else:
                        log_message("⚠️ Campo de email encontrado mas não está habilitado", "WARNING")
                        time.sleep(2)
                except Exception as wait_error:
                    log_message(f"✗ Erro ao aguardar campo de email: {wait_error}", "ERROR")
                    if DEBUG_CONFIG["verbose_logging"]:
                        debug_page_elements(page, "Após timeout aguardando campo de email")

                log_message("5. Tentando preencher email...", "INFO")
                try:
                    page.click(SEL["email"], timeout=10000)
                    time.sleep(0.5)
                    page.fill(SEL["email"], email, timeout=15000)
                    log_message("✓ Email preenchido com sucesso!", "SUCCESS")
                except Exception as email_error:
                    log_message(f"✗ Erro ao preencher email: {email_error}", "ERROR")
                    alternative_selectors = [
                        'input[name="user[email]"]',
                        'input[type="text"][placeholder*="E-mail"]',
                        'input[type="email"]',
                        'input[name="email"]',
                        'input[name="login"]',
                        'input[placeholder*="email" i]',
                        'input[placeholder*="E-mail" i]'
                    ]
                    email_filled = False
                    for alt_selector in alternative_selectors:
                        try:
                            if page.locator(alt_selector).count() > 0:
                                page.click(alt_selector, timeout=5000)
                                time.sleep(0.5)
                                page.fill(alt_selector, email, timeout=5000)
                                log_message(f"✓ Email preenchido usando seletor alternativo: {alt_selector}", "SUCCESS")
                                email_filled = True
                                break
                        except Exception:
                            continue
                    if not email_filled:
                        raise Exception("Não foi possível preencher o campo de email")

                log_message("6. Tentando preencher senha...", "INFO")
                try:
                    page.click(SEL["password"], timeout=10000)
                    time.sleep(0.5)
                    page.fill(SEL["password"], password, timeout=15000)
                    log_message("✓ Senha preenchida com sucesso!", "SUCCESS")
                except Exception as password_error:
                    log_message(f"✗ Erro ao preencher senha: {password_error}", "ERROR")
                    alternative_selectors = [
                        'input[name="user[password]"]',
                        'input[type="password"]',
                        'input[name="password"]',
                        'input[name="senha"]'
                    ]
                    password_filled = False
                    for alt_selector in alternative_selectors:
                        try:
                            if page.locator(alt_selector).count() > 0:
                                page.click(alt_selector, timeout=5000)
                                time.sleep(0.5)
                                page.fill(alt_selector, password, timeout=5000)
                                log_message(f"✓ Senha preenchida usando seletor alternativo: {alt_selector}", "SUCCESS")
                                password_filled = True
                                break
                        except Exception:
                            continue
                    if not password_filled:
                        raise Exception("Não foi possível preencher o campo de senha")

                if DEBUG_CONFIG["verbose_logging"]:
                    debug_page_elements(page, "Após preencher credenciais")

                log_message("7. Aguardando um momento antes de submeter...", "INFO")
                time.sleep(2)

                log_message("8. Tentando clicar no botão de login...", "INFO")
                try:
                    page.click(SEL["submit"], timeout=10000)
                    log_message("✓ Botão de login clicado!", "SUCCESS")
                except Exception as submit_error:
                    log_message(f"✗ Erro ao clicar no botão: {submit_error}", "ERROR")
                    alternative_selectors = [
                        'input[type="submit"][value="Entrar"]',
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("Entrar")',
                        'button:has-text("Login")',
                        'button:has-text("Acessar")'
                    ]
                    submit_clicked = False
                    for alt_selector in alternative_selectors:
                        try:
                            if page.locator(alt_selector).count() > 0:
                                page.click(alt_selector, timeout=5000)
                                log_message(f"✓ Botão clicado usando seletor alternativo: {alt_selector}", "SUCCESS")
                                submit_clicked = True
                                break
                        except Exception:
                            continue
                    if not submit_clicked:
                        try:
                            page.keyboard.press("Enter")
                            log_message("✓ Pressionado Enter como alternativa", "SUCCESS")
                        except Exception:
                            raise Exception("Não foi possível submeter o formulário de login")

                log_message("9. Aguardando redirecionamento...", "INFO")
                try:
                    page.wait_for_url("**/app.qconcursos.com/**", timeout=60000)
                    log_message("✅ LOGIN REALIZADO COM SUCESSO!", "SUCCESS")
                    log_message(f"🔗 URL final: {page.url}", "SUCCESS")
                except Exception as redirect_error:
                    log_message(f"✗ Erro no redirecionamento: {redirect_error}", "ERROR")
                    log_message(f"URL atual: {page.url}", "ERROR")
                    error_selectors = [
                        '.alert-danger',
                        '.error',
                        '[class*="error"]',
                        '[class*="alert"]'
                    ]
                    for error_sel in error_selectors:
                        try:
                            if page.locator(error_sel).count() > 0:
                                error_text = page.locator(error_sel).first.inner_text()
                                log_message(f"Mensagem de erro encontrada: {error_text}", "ERROR")
                        except Exception:
                            pass
                    raise Exception("Falha no login - redirecionamento não ocorreu")
                # === FIM DO NOVO LOGIN PADRONIZADO ===

            except Exception as login_error:
                log_message(f"❌ FALHA NO LOGIN: {login_error}", "ERROR")
                log_message("🔒 SESSÃO NÃO FOI ESTABELECIDA", "ERROR")
                
                # Screenshot de debug
                if DEBUG_CONFIG["screenshot_on_error"]:
                    try:
                        screenshot_path = "login_error.png"
                        page.screenshot(path=screenshot_path)
                        log_message("Screenshot de erro salvo em login_error.png", "INFO")
                        add_screenshot("login_error.png")
                    except Exception as screenshot_error:
                        log_message(f"Erro ao salvar screenshot: {screenshot_error}", "ERROR")
                
                # Salva HTML bruto
                if DEBUG_CONFIG["save_raw_html"]:
                    try:
                        html_content = page.content()
                        with open("login_error.html", "w", encoding="utf-8") as f:
                            f.write(html_content)
                        log_message("HTML bruto salvo em login_error.html", "INFO")
                    except Exception as html_error:
                        log_message(f"Erro ao salvar HTML: {html_error}", "ERROR")
                
                browser.close()
                raise

            all_nodes = []
            
            # Processa cada URL
            log_message("🚀 INICIANDO PROCESSO COMPLETO DE RASPAGEM DE DADOS", "SUCCESS")
            for i, url in enumerate(urls, 1):
                log_message(f"📄 PROCESSANDO URL {i}/{len(urls)}", "INFO")
                log_message(f"🔗 Navegando para: {url[:80]}...", "INFO")
                update_progress(i-1, len(urls), url)
                
                try:
                    # Navega para a URL
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    log_message("✅ Página carregada com sucesso!", "SUCCESS")
                    
                    # Aguarda a página estabilizar
                    time.sleep(3)
                    
                    # PASSO 1: Clica na aba "Estatísticas" para extrair gabaritos
                    log_message("📊 PASSO 1: Acessando aba de Estatísticas...")
                    click_tab(page, "Estatísticas")
                    time.sleep(2)  # Aguarda carregar
                    
                    # PASSO 2: Extrai gabaritos automaticamente
                    log_message("🎯 PASSO 2: Extraindo gabaritos automaticamente...")
                    gabarito_map = extract_gabarito_automatico(page)
                    
                    # PASSO 3: Clica na aba "Comentários de alunos"
                    log_message("💬 PASSO 3: Acessando aba de Comentários de alunos...")
                    click_tab(page, "Comentários de alunos")
                    time.sleep(3)  # Aguarda carregar comentários
                    
                    # PASSO 4: Scroll completo para carregar todos os comentários
                    log_message("📜 PASSO 4: Carregando todos os comentários (scroll completo)...")
                    scroll_all(page, 
                              step=SCRAPING_CONFIG["scroll_step"], 
                              pause=SCRAPING_CONFIG["scroll_pause"], 
                              max_iter=SCRAPING_CONFIG["scroll_max_iter"])
                    
                    # Aguarda um pouco mais para garantir que tudo carregou
                    time.sleep(2)
                    
                    # PASSO 5: Extração completa usando JavaScript
                    log_message("🔍 PASSO 5: Executando extração completa de dados...")
                    nodes = extract_all_data_with_javascript(page, gabarito_map)
                    
                    if nodes:
                        all_nodes.extend(nodes)
                        log_message(f"✅ EXTRAÍDOS {len(nodes)} NÓDULOS DE DADOS!", "SUCCESS")
                        log_message(f"📊 Total acumulado: {len(all_nodes)} nódulos", "INFO")
                    else:
                        log_message("⚠️ Nenhum nódulo extraído desta URL", "WARNING")
                    
                    update_progress(i, len(urls))
                    
                    # Pausa entre URLs
                    if i < len(urls):  # Não pausa na última URL
                        log_message(f"⏳ Aguardando {SCRAPING_CONFIG['url_pause']}s antes da próxima URL...")
                        time.sleep(SCRAPING_CONFIG['url_pause'])
                    
                except Exception as e:
                    log_message(f"❌ Erro ao processar URL: {e}", "ERROR")
                    
                    # Screenshot de debug se habilitado
                    if DEBUG_CONFIG["screenshot_on_error"]:
                        try:
                            error_screenshot = f"error_url_{i}.png"
                            page.screenshot(path=error_screenshot)
                            log_message(f"Screenshot salvo em {error_screenshot}", "INFO")
                            add_screenshot(error_screenshot)
                        except Exception as screenshot_error:
                            log_message(f"Erro ao salvar screenshot: {screenshot_error}", "ERROR")
                    
                    # Salva HTML bruto se habilitado
                    if DEBUG_CONFIG["save_raw_html"]:
                        try:
                            html_content = page.content()
                            with open(f"error_url_{i}.html", "w", encoding="utf-8") as f:
                                f.write(html_content)
                            log_message(f"HTML bruto salvo em error_url_{i}.html", "INFO")
                        except Exception as html_error:
                            log_message(f"Erro ao salvar HTML: {html_error}", "ERROR")
                    
                    continue

            # Gera o XML Freeplane
            if all_nodes:
                log_message("📋 INICIANDO FORMATAÇÃO DOS DADOS...", "INFO")
                log_message("🔄 Construindo arquivo XML do Freeplane...", "INFO")
                
                # Constrói o XML manualmente baseado na estrutura do bookmarklet
                xml_content = '<map version="freeplane 1.9.8"><node LOCALIZED_TEXT="new_mindmap">'
                for node in all_nodes:
                    xml_content += node['conteudo']
                xml_content += '</node></map>'
                
                output_file = out_dir / OUTPUT_CONFIG["filename"]
                output_file.write_text(xml_content, encoding=OUTPUT_CONFIG["encoding"])
                
                log_message(f"💾 ARQUIVO SALVO: {output_file}", "SUCCESS")
                log_message(f"🎯 PROCESSO FINALIZADO - {len(all_nodes)} NÓDULOS PROCESSADOS!", "SUCCESS")
                log_message("🎉 RASPAGEM CONCLUÍDA COM SUCESSO!", "SUCCESS")
            else:
                log_message("⚠️ Nenhum dado foi extraído. Verifique as URLs e configurações.", "WARNING")

            browser.close()
            
    except Exception as e:
        log_message(f"💥 ERRO CRÍTICO NO PROCESSO: {e}", "ERROR")
        raise
    finally:
        # Marca o fim da execução
        set_running_status(False)

if __name__ == "__main__":
    main() 