#!/usr/bin/env python3
"""
Script simples para testar apenas o processo de login do QConcursos.
Útil para debug sem executar todo o scraping.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from config import LOGIN_URL, SEL, SCRAPING_CONFIG, DEBUG_CONFIG

def debug_page_elements(page, description=""):
    """
    Debug helper para inspecionar elementos da página.
    """
    print(f"\n=== DEBUG: {description} ===")
    print(f"URL atual: {page.url}")
    print(f"Título da página: {page.title()}")
    
    # Verifica se elementos de login existem
    email_exists = page.locator("#login_email").count() > 0
    password_exists = page.locator("#login_password").count() > 0
    submit_exists = page.locator("#btnLogin").count() > 0
    
    print(f"Email field exists: {email_exists}")
    print(f"Password field exists: {password_exists}")
    print(f"Submit button exists: {submit_exists}")
    
    # Procura por campos de input alternativos
    all_inputs = page.locator("input").count()
    print(f"Total input fields found: {all_inputs}")
    
    for i in range(min(all_inputs, 10)):  # Máximo 10 inputs
        input_elem = page.locator("input").nth(i)
        try:
            input_type = input_elem.get_attribute("type") or "text"
            input_id = input_elem.get_attribute("id") or "no-id"
            input_name = input_elem.get_attribute("name") or "no-name"
            input_class = input_elem.get_attribute("class") or "no-class"
            input_placeholder = input_elem.get_attribute("placeholder") or "no-placeholder"
            print(f"  Input {i}: type='{input_type}', id='{input_id}', name='{input_name}', placeholder='{input_placeholder}'")
        except Exception as e:
            print(f"  Input {i}: Error reading attributes - {e}")
    
    # Procura por buttons alternativos
    all_buttons = page.locator("button").count()
    print(f"Total buttons found: {all_buttons}")
    
    for i in range(min(all_buttons, 5)):  # Máximo 5 buttons
        button_elem = page.locator("button").nth(i)
        try:
            button_id = button_elem.get_attribute("id") or "no-id"
            button_text = button_elem.inner_text().strip()[:50] or "no-text"
            button_class = button_elem.get_attribute("class") or "no-class"
            button_type = button_elem.get_attribute("type") or "no-type"
            print(f"  Button {i}: id='{button_id}', type='{button_type}', text='{button_text}'")
        except Exception as e:
            print(f"  Button {i}: Error reading attributes - {e}")
    
    print("=" * 50)

def test_login():
    """
    Testa apenas o processo de login.
    """
    # Carrega variáveis de ambiente
    load_dotenv()
    email = os.getenv("QC_EMAIL")
    password = os.getenv("QC_PASSWORD")
    
    if not email or not password:
        print("ERRO: Defina QC_EMAIL e QC_PASSWORD no arquivo .env")
        return False

    print("=== TESTE DE LOGIN DO QCONCURSOS ===")
    print(f"Email: {email}")
    print(f"URL de login: {LOGIN_URL}")
    print("=" * 50)
    
    with sync_playwright() as p:
        # Inicia o navegador
        browser = p.chromium.launch(
            headless=False,  # Sempre não-headless para debug
            args=['--disable-blink-features=AutomationControlled']  # Reduz detecção de automação
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print("1. Navegando para a página de login...")
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)  # Aguarda DOM carregado
            
            print("2. Aguardando formulário de login...")
            try:
                page.wait_for_selector("#login_form", state="visible", timeout=15000)
                print("✓ Formulário de login encontrado!")
            except Exception as form_error:
                print(f"✗ Erro ao aguardar formulário: {form_error}")
            
            print("3. Aguardando JavaScript carregar completamente...")
            time.sleep(3)
            
            # Debug: inspeciona a página inicial
            debug_page_elements(page, "Página de login carregada")
            
            print("4. Tentando aguardar pelo campo de email...")
            try:
                page.wait_for_selector(SEL["email"], state="visible", timeout=10000)
                email_element = page.locator(SEL["email"])
                if email_element.is_enabled():
                    print("✓ Campo de email encontrado e habilitado!")
                else:
                    print("⚠ Campo de email encontrado mas não está habilitado")
                    time.sleep(2)
            except Exception as wait_error:
                print(f"✗ Erro ao aguardar campo de email: {wait_error}")
                debug_page_elements(page, "Após timeout aguardando campo de email")
            
            print("5. Tentando preencher email...")
            try:
                # Clica primeiro para focar o elemento
                page.click(SEL["email"], timeout=10000)
                time.sleep(0.5)  # Pausa humana
                page.fill(SEL["email"], email, timeout=15000)
                print("✓ Email preenchido com sucesso!")
            except Exception as email_error:
                print(f"✗ Erro ao preencher email: {email_error}")
                
                # Tenta seletores alternativos
                alternative_selectors = [
                    'input[name="user[email]"]',  # Baseado no HTML fornecido
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
                            print(f"✓ Email preenchido usando seletor alternativo: {alt_selector}")
                            email_filled = True
                            break
                    except Exception:
                        continue
                
                if not email_filled:
                    print("✗ Não foi possível preencher o campo de email")
                    return False
            
            print("6. Tentando preencher senha...")
            try:
                # Clica primeiro para focar o elemento
                page.click(SEL["password"], timeout=10000)
                time.sleep(0.5)  # Pausa humana
                page.fill(SEL["password"], password, timeout=15000)
                print("✓ Senha preenchida com sucesso!")
            except Exception as password_error:
                print(f"✗ Erro ao preencher senha: {password_error}")
                
                # Tenta seletores alternativos
                alternative_selectors = [
                    'input[name="user[password]"]',  # Baseado no HTML fornecido
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
                            print(f"✓ Senha preenchida usando seletor alternativo: {alt_selector}")
                            password_filled = True
                            break
                    except Exception:
                        continue
                
                if not password_filled:
                    print("✗ Não foi possível preencher o campo de senha")
                    return False
            
            # Debug após preencher os campos
            debug_page_elements(page, "Após preencher credenciais")
            
            print("7. Aguardando um momento antes de submeter...")
            time.sleep(2)
            
            print("8. Tentando clicar no botão de login...")
            try:
                page.click(SEL["submit"], timeout=10000)
                print("✓ Botão de login clicado!")
            except Exception as submit_error:
                print(f"✗ Erro ao clicar no botão: {submit_error}")
                
                # Tenta seletores alternativos
                alternative_selectors = [
                    'input[type="submit"][value="Entrar"]',  # Baseado no HTML fornecido
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
                            print(f"✓ Botão clicado usando seletor alternativo: {alt_selector}")
                            submit_clicked = True
                            break
                    except Exception:
                        continue
                
                if not submit_clicked:
                    try:
                        page.keyboard.press("Enter")
                        print("✓ Pressionado Enter como alternativa")
                    except Exception:
                        print("✗ Não foi possível submeter o formulário")
                        return False
            
            print("9. Aguardando redirecionamento...")
            try:
                page.wait_for_url("**/app.qconcursos.com/**", timeout=60000)
                print("✓ Login realizado com sucesso!")
                print(f"URL final: {page.url}")
                return True
            except Exception as redirect_error:
                print(f"✗ Erro no redirecionamento: {redirect_error}")
                print(f"URL atual: {page.url}")
                
                # Verifica se há mensagens de erro na página
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
                            print(f"Mensagem de erro encontrada: {error_text}")
                    except Exception:
                        pass
                
                return False
                
        except Exception as e:
            print(f"Erro geral durante o teste: {e}")
            return False
            
        finally:
            print("10. Aguardando 10 segundos para inspeção manual...")
            time.sleep(10)
            browser.close()

if __name__ == "__main__":
    success = test_login()
    if success:
        print("\n✓ TESTE DE LOGIN PASSOU!")
    else:
        print("\n✗ TESTE DE LOGIN FALHOU!") 