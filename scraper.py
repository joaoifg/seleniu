import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from freeplane import build_freeplane
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
    """
    Rola a página para carregar todo o conteúdo dinâmico.
    
    Args:
        page: Página do Playwright
        step: Quantidade de pixels para rolar a cada iteração
        pause: Tempo de pausa entre rolagens
        max_iter: Número máximo de iterações
    """
    last = 0
    for _ in range(max_iter):
        page.evaluate(f"window.scrollBy(0,{step});")
        time.sleep(pause)
        h = page.evaluate("document.body.scrollHeight")
        if h == last:
            break
        last = h

def click_tab(page, text):
    """
    Clica em uma aba específica baseada no texto.
    Garante que a aba está visível e estável antes de clicar.
    Args:
        page: Página do Playwright
        text: Texto da aba a ser clicada
    """
    tabs = page.locator(SEL["tab"])
    for i in range(tabs.count()):
        t = tabs.nth(i)
        try:
            if text in t.inner_text():
                t.scroll_into_view_if_needed()
                time.sleep(0.5)  # Pequeno delay para garantir estabilidade
                t.click(timeout=8000)
                return
        except Exception as e:
            log_message(f"Aviso: Falha ao clicar na aba '{text}' (index {i}): {e}", "WARNING")

def extract_nodes(page, gabarito_map):
    """
    Extrai os dados dos cards de questões da página.
    
    Args:
        page: Página do Playwright
        gabarito_map: Dicionário com gabaritos conhecidos
        
    Returns:
        Lista de dicionários com os dados extraídos
    """
    cards = page.locator(SEL["card"])
    nodes = []

    for i in range(cards.count()):
        card = cards.nth(i)
        
        # Extrai número da questão
        num = card.locator(SEL["num"]).inner_text().strip() if card.locator(SEL["num"]).count() else str(i+1)
        gab = gabarito_map.get(num, "")

        # Detecta automaticamente a correta via estatística
        if gab == "":
            if card.locator(SEL["statsAttr"]).count():
                stats_raw = card.locator(SEL["statsAttr"]).get_attribute("data-question-statistics-alternatives-statistics")
                if stats_raw:
                    try:
                        stats = json.loads(stats_raw)
                        corr = next((s for s in stats if s.get("hit",0)>0), None)
                        if corr:
                            gab = corr.get("id","")
                    except json.JSONDecodeError:
                        pass

        # Extrai título e informações
        title = card.locator(SEL["title"]).inner_text().strip() if card.locator(SEL["title"]).count() else ""
        info = card.locator(SEL["info"]).inner_text().strip().replace("\n"," ") if card.locator(SEL["info"]).count() else ""
        if title in info:
            info = info.replace(title,"").strip()

        # Extrai enunciado
        statement = card.locator(SEL["statement"]).inner_html().strip().replace("\n"," ") if card.locator(SEL["statement"]).count() else ""

        # Extrai alternativas
        alternatives_html = "".join([
            card.locator(SEL["alt"]).nth(j).inner_html().strip()
            for j in range(card.locator(SEL["alt"]).count())
        ])

        # Extrai comentários
        comments_html = "".join([
            card.locator(SEL["commentText"]).nth(j).inner_html().strip()
            for j in range(card.locator(SEL["commentText"]).count())
        ]) + alternatives_html

        comments_html = comments_html.replace(
            '<div class="question-commentary-text font-size-2">',
            '<div class="question-commentary-text font-size-2"><p>------------</p>'
        )

        # Extrai comentário principal
        comment_node = ""
        if card.locator(SEL["commentText"]).count():
            c = card.locator(SEL["commentText"]).first.inner_html().strip()
            comment_node = f'<node MAX_WIDTH="40 cm"><richcontent TYPE="NODE"><html><head></head><body>{c}</body></html></richcontent></node>'

        # Extrai badge
        badge = card.locator(SEL["badge"]).first.inner_html().strip() if card.locator(SEL["badge"]).count() else ""

        # Extrai informações extras
        extra_html = "".join([
            card.locator(SEL["extra"]).nth(j).inner_html().replace(
                '<div class="text px-3 font-size-2 svelte-1tiqrp1">',
                '<div class="text px-3 font-size-2 svelte-1tiqrp1">&#9830 '
            )
            for j in range(card.locator(SEL["extra"]).count())
        ])

        # Destaca questões com gabarito "E"
        destaque = f' style="background-color:{OUTPUT_CONFIG["highlight_color"]};"' if gab == "E" and OUTPUT_CONFIG["highlight_wrong"] else ""
        header = " | ".join(filter(None, [num, gab, title, info]))

        # Constrói o HTML do nó
        node_html = f"""
<node MAX_WIDTH="40 cm">
  <richcontent TYPE="NODE">
    <html><head></head><body>
      <span{destaque}>{header}</span><br>{statement}
    </body></html>
  </richcontent>
  <richcontent TYPE="NOTE" CONTENT-TYPE="xml/">
    <html><head></head><body>{comments_html} | {badge}</body></html>
  </richcontent>
  {f'<node><richcontent TYPE="NODE"><html><head></head><body>{extra_html}</body></html></richcontent></node>' if extra_html else ""}
  {comment_node}
</node>"""
        nodes.append({"gab": gab, "html": node_html})
    
    return nodes

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
        gabarito_map = {}  # Opcional: {"1":"C","2":"E",...}

        # Cria diretório de saída
        out_dir = Path(OUTPUT_CONFIG["output_dir"])
        out_dir.mkdir(exist_ok=True)
        
        # Cria diretório de screenshots
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(exist_ok=True)

        log_message("Iniciando scraping do QConcursos...")
        log_message(f"Total de URLs a processar: {len(urls)}")
        
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
                    log_message("✓ Login realizado com sucesso!", "SUCCESS")
                    log_message(f"URL final: {page.url}", "SUCCESS")
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
            log_message("🚀 INICIANDO PROCESSO DE RASPAGEM DE DADOS", "SUCCESS")
            for i, url in enumerate(urls, 1):
                log_message(f"📄 PROCESSANDO URL {i}/{len(urls)}", "INFO")
                log_message(f"🔗 Navegando para: {url[:80]}...", "INFO")
                update_progress(i-1, len(urls), url)
                
                try:
                    page.goto(url, wait_until="domcontentloaded")
                    log_message("✅ Página carregada com sucesso!", "SUCCESS")
                    
                    # Clica nas abas necessárias
                    log_message("🎯 Configurando abas para extração...", "INFO")
                    click_tab(page, "Estatísticas")
                    click_tab(page, "Comentários de alunos")
                    log_message("✅ Abas configuradas!", "SUCCESS")
                    
                    # Rola para carregar todo o conteúdo
                    log_message("📜 Carregando todo o conteúdo da página...", "INFO")
                    scroll_all(page)
                    log_message("✅ Conteúdo carregado completamente!", "SUCCESS")
                    
                    # Extrai os dados
                    log_message("🔍 INICIANDO EXTRAÇÃO DE DADOS...", "INFO")
                    gabarito_map = {}  # Pode ser customizado se necessário
                    nodes = extract_nodes(page, gabarito_map)
                    all_nodes.extend(nodes)
                    
                    log_message(f"✅ EXTRAÍDOS {len(nodes)} NÓDULOS DE DADOS!", "SUCCESS")
                    log_message(f"📊 Total acumulado: {len(all_nodes)} nódulos", "INFO")
                    update_progress(i, len(urls))
                    time.sleep(SCRAPING_CONFIG["url_pause"])
                    
                except Exception as e:
                    log_message(f"Erro ao processar URL: {e}", "ERROR")
                    
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

            # Gera o XML
            log_message("📋 INICIANDO FORMATAÇÃO DOS DADOS...", "INFO")
            log_message("🔄 Construindo arquivo XML do Freeplane...", "INFO")
            xml = build_freeplane(all_nodes)
            output_file = out_dir / OUTPUT_CONFIG["filename"]
            output_file.write_text(xml, encoding=OUTPUT_CONFIG["encoding"])
            
            log_message(f"💾 ARQUIVO SALVO: {output_file}", "SUCCESS")
            log_message(f"🎯 PROCESSO FINALIZADO - {len(all_nodes)} NÓDULOS PROCESSADOS!", "SUCCESS")
            log_message("🎉 RASPAGEM CONCLUÍDA COM SUCESSO!", "SUCCESS")

            browser.close()
            
    except Exception as e:
        log_message(f"💥 ERRO CRÍTICO NO PROCESSO: {e}", "ERROR")
        raise
    finally:
        # Marca o fim da execução
        set_running_status(False)

if __name__ == "__main__":
    main() 