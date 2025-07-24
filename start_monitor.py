#!/usr/bin/env python3
"""
Script para iniciar o monitor web e opcionalmente o scraper.
"""

import os
import sys
import time
import argparse
import subprocess
import threading
from pathlib import Path

def run_web_interface():
    """Executa a interface web."""
    print("🌐 Iniciando interface web...")
    subprocess.run([sys.executable, "web_interface.py"])

def run_scraper():
    """Executa o scraper."""
    print("🔍 Iniciando scraper...")
    time.sleep(3)  # Aguarda interface web subir
    subprocess.run([sys.executable, "scraper.py"])

def check_credentials():
    """Verifica se as credenciais estão configuradas."""
    from dotenv import load_dotenv
    
    load_dotenv()
    email = os.getenv("QC_EMAIL")
    password = os.getenv("QC_PASSWORD")
    
    if not email or not password:
        print("❌ Credenciais não configuradas!")
        print("Execute: python setup_env.py")
        return False
    
    return True

def check_urls_file():
    """Verifica se o arquivo urls.txt existe."""
    if not Path("urls.txt").exists():
        print("❌ Arquivo urls.txt não encontrado!")
        print("Crie o arquivo urls.txt com as URLs a serem processadas.")
        return False
    
    urls = [u.strip() for u in Path("urls.txt").read_text().splitlines() if u.strip()]
    if not urls:
        print("❌ Arquivo urls.txt está vazio!")
        return False
    
    print(f"✅ Encontradas {len(urls)} URLs para processar")
    return True

def main():
    parser = argparse.ArgumentParser(description="Monitor do QConcursos Scraper")
    parser.add_argument("--mode", choices=["web", "scraper", "both"], default="both",
                      help="Modo de execução: apenas web, apenas scraper, ou ambos")
    parser.add_argument("--no-check", action="store_true",
                      help="Pula verificações de pré-requisitos")
    
    args = parser.parse_args()
    
    print("🚀 QConcursos Scraper Monitor")
    print("=" * 40)
    
    # Verificações de pré-requisitos
    if not args.no_check:
        print("🔍 Verificando pré-requisitos...")
        
        if args.mode in ["scraper", "both"]:
            if not check_credentials():
                return 1
            
            if not check_urls_file():
                return 1
        
        print("✅ Verificações concluídas!")
        print()
    
    # Cria diretórios necessários
    for dir_name in ["logs", "screenshots", "output"]:
        Path(dir_name).mkdir(exist_ok=True)
    
    if args.mode == "web":
        print("🌐 Executando apenas a interface web...")
        print("📊 Acesse: http://localhost:5000")
        run_web_interface()
        
    elif args.mode == "scraper":
        print("🔍 Executando apenas o scraper...")
        run_scraper()
        
    elif args.mode == "both":
        print("🚀 Executando interface web e scraper...")
        print("📊 Acesse: http://localhost:5000")
        print()
        
        # Inicia interface web em thread separada
        web_thread = threading.Thread(target=run_web_interface, daemon=True)
        web_thread.start()
        
        # Aguarda um pouco e depois inicia o scraper
        time.sleep(3)
        
        try:
            run_scraper()
        except KeyboardInterrupt:
            print("\n⛔ Interrompido pelo usuário")
            return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 