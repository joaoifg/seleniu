#!/usr/bin/env python3
"""
Script de teste para verificar se a configuração está correta.
"""

import sys
from pathlib import Path

def test_imports():
    """Testa se todas as importações funcionam."""
    print("🔍 Testando importações...")
    
    try:
        import playwright
        print("  ✓ playwright")
    except ImportError:
        print("  ✗ playwright - Execute: pip install playwright")
        return False
    
    try:
        import dotenv
        print("  ✓ python-dotenv")
    except ImportError:
        print("  ✗ python-dotenv - Execute: pip install python-dotenv")
        return False
    
    try:
        from config import SEL, SCRAPING_CONFIG, OUTPUT_CONFIG
        print("  ✓ config.py")
    except ImportError as e:
        print(f"  ✗ config.py - {e}")
        return False
    
    try:
        from freeplane import build_freeplane
        print("  ✓ freeplane.py")
    except ImportError as e:
        print(f"  ✗ freeplane.py - {e}")
        return False
    
    return True

def test_files():
    """Testa se os arquivos necessários existem."""
    print("\n📁 Testando arquivos...")
    
    required_files = [
        "scraper.py",
        "config.py", 
        "freeplane.py",
        "urls.txt",
        "env.example"
    ]
    
    all_good = True
    for file in required_files:
        if Path(file).exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - Arquivo não encontrado")
            all_good = False
    
    return all_good

def test_config():
    """Testa se as configurações estão válidas."""
    print("\n⚙️ Testando configurações...")
    
    try:
        from config import SEL, SCRAPING_CONFIG, OUTPUT_CONFIG
        
        # Testa seletores
        required_selectors = ["email", "password", "submit", "card"]
        for selector in required_selectors:
            if selector in SEL:
                print(f"  ✓ Seletor '{selector}'")
            else:
                print(f"  ✗ Seletor '{selector}' não encontrado")
                return False
        
        # Testa configurações de scraping
        if SCRAPING_CONFIG["timeout"] > 0:
            print(f"  ✓ Timeout: {SCRAPING_CONFIG['timeout']}ms")
        else:
            print("  ✗ Timeout inválido")
            return False
        
        # Testa configurações de output
        if OUTPUT_CONFIG["output_dir"]:
            print(f"  ✓ Diretório de saída: {OUTPUT_CONFIG['output_dir']}")
        else:
            print("  ✗ Diretório de saída não definido")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Erro ao testar configurações: {e}")
        return False

def test_urls():
    """Testa se as URLs estão válidas."""
    print("\n🌐 Testando URLs...")
    
    try:
        urls = [u.strip() for u in Path("urls.txt").read_text().splitlines() if u.strip()]
        
        if not urls:
            print("  ✗ Nenhuma URL encontrada em urls.txt")
            return False
        
        for i, url in enumerate(urls, 1):
            if url.startswith("https://app.qconcursos.com/"):
                print(f"  ✓ URL {i}: {url[:50]}...")
            else:
                print(f"  ✗ URL {i} inválida: {url}")
                return False
        
        print(f"  ✓ Total de URLs: {len(urls)}")
        return True
        
    except Exception as e:
        print(f"  ✗ Erro ao ler URLs: {e}")
        return False

def main():
    """Função principal."""
    print("🧪 QConcursos Scraper - Teste de Configuração")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_files,
        test_config,
        test_urls
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ Todos os testes passaram! O scraper está pronto para uso.")
        print("\n📝 Próximos passos:")
        print("1. Copie env.example para .env")
        print("2. Edite .env com suas credenciais do QConcursos")
        print("3. Execute: python run_local.py")
    else:
        print("❌ Alguns testes falharam. Corrija os problemas antes de continuar.")
        sys.exit(1)

if __name__ == "__main__":
    main() 