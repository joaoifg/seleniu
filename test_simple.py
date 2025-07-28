from playwright.sync_api import sync_playwright
import time

def test_simple_login():
    print("=== TESTE SIMPLES DE LOGIN ===")
    
    with sync_playwright() as p:
        print("1. Iniciando navegador...")
        browser = p.chromium.launch(headless=False)  # headless=False para ver o que está acontecendo
        context = browser.new_context()
        page = context.new_page()
        
        print("2. Navegando para login...")
        page.goto("https://www.qconcursos.com/conta/entrar?return_url=https%3A%2F%2Fapp.qconcursos.com%2F")
        page.wait_for_timeout(3000)
        
        print("3. Preenchendo credenciais...")
        page.fill('#login_email', 'joaohenriqueoci@gmail.com')
        page.fill('#login_password', 'sua_senha_aqui')  # Substitua pela sua senha
        
        print("4. Clicando no login...")
        page.click('#btnLogin')
        page.wait_for_timeout(5000)
        
        print(f"5. URL atual: {page.url}")
        
        if "entrar" not in page.url:
            print("✅ Login realizado com sucesso!")
            
            print("6. Testando navegação para uma URL...")
            test_url = "https://app.qconcursos.com/playground/questoes?discipline_ids[]=100&examining_board_ids[]=2&per_page=50&subject_ids[]=315"
            page.goto(test_url)
            page.wait_for_timeout(5000)
            print(f"7. URL da questão: {page.url}")
            
            print("8. Aguardando 10 segundos para inspeção...")
            page.wait_for_timeout(10000)
            
        else:
            print("❌ Falha no login")
        
        browser.close()

if __name__ == "__main__":
    test_simple_login() 