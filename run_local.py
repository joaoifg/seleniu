#!/usr/bin/env python3
"""
Script para executar o scraper localmente sem Docker.
Útil para desenvolvimento e testes.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    try:
        import playwright
        import dotenv
        print("✓ Dependências Python encontradas")
    except ImportError as e:
        print(f"✗ Dependência não encontrada: {e}")
        print("Execute: pip install -r requirements.txt")
        return False
    
    # Verifica se o browser está instalado
    try:
        result = subprocess.run(
            ["python", "-m", "playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True
        )
        if "chromium" not in result.stdout:
            print("Instalando browsers do Playwright...")
            subprocess.run(["python", "-m", "playwright", "install", "--with-deps", "chromium"])
        print("✓ Browsers do Playwright prontos")
    except Exception as e:
        print(f"✗ Erro ao verificar browsers: {e}")
        return False
    
    return True

def check_env_file():
    """Verifica se o arquivo .env existe."""
    if not Path(".env").exists():
        print("⚠ Arquivo .env não encontrado!")
        print("Copiando env.example para .env...")
        try:
            import shutil
            shutil.copy("env.example", ".env")
            print("✓ Arquivo .env criado. Edite-o com suas credenciais!")
            return False
        except Exception as e:
            print(f"✗ Erro ao criar .env: {e}")
            return False
    return True

def main():
    """Função principal."""
    print("🚀 QConcursos Scraper - Execução Local")
    print("=" * 50)
    
    # Verifica dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Verifica arquivo .env
    if not check_env_file():
        print("\n📝 Configure suas credenciais no arquivo .env antes de continuar!")
        sys.exit(1)
    
    # Verifica se urls.txt existe
    if not Path("urls.txt").exists():
        print("✗ Arquivo urls.txt não encontrado!")
        sys.exit(1)
    
    print("\n✅ Tudo pronto! Executando scraper...")
    print("=" * 50)
    
    # Executa o scraper
    try:
        subprocess.run([sys.executable, "scraper.py"])
    except KeyboardInterrupt:
        print("\n⚠ Interrompido pelo usuário")
    except Exception as e:
        print(f"\n✗ Erro ao executar scraper: {e}")

if __name__ == "__main__":
    main() 