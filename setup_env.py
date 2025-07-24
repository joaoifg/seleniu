#!/usr/bin/env python3
"""
Script para configurar facilmente as credenciais do QConcursos.
"""

import os
from pathlib import Path

def setup_env():
    """
    Configura o arquivo .env com as credenciais do QConcursos.
    """
    print("=== CONFIGURAÇÃO DAS CREDENCIAIS DO QCONCURSOS ===")
    print()
    
    # Verifica se já existe um .env
    env_file = Path(".env")
    if env_file.exists():
        print("❗ Arquivo .env já existe!")
        choice = input("Deseja sobrescrever? (s/N): ").lower().strip()
        if choice not in ['s', 'sim', 'y', 'yes']:
            print("Cancelado.")
            return
    
    print("Por favor, insira suas credenciais do QConcursos:")
    print("(As credenciais serão salvas no arquivo .env)")
    print()
    
    # Solicita email
    while True:
        email = input("Email: ").strip()
        if email and "@" in email:
            break
        print("❌ Email inválido. Digite um email válido.")
    
    # Solicita senha
    while True:
        password = input("Senha: ").strip()
        if len(password) >= 8:
            break
        print("❌ Senha deve ter pelo menos 8 caracteres.")
    
    # Cria o arquivo .env
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"QC_EMAIL={email}\n")
            f.write(f"QC_PASSWORD={password}\n")
        
        print()
        print("✅ Arquivo .env criado com sucesso!")
        print()
        print("Agora você pode executar:")
        print("  python test_login.py    # Para testar apenas o login")
        print("  python scraper.py       # Para executar o scraping completo")
        
    except Exception as e:
        print(f"❌ Erro ao criar arquivo .env: {e}")

def check_env():
    """
    Verifica se as credenciais estão configuradas corretamente.
    """
    from dotenv import load_dotenv
    
    load_dotenv()
    email = os.getenv("QC_EMAIL")
    password = os.getenv("QC_PASSWORD")
    
    print("=== VERIFICAÇÃO DAS CREDENCIAIS ===")
    
    if not email:
        print("❌ QC_EMAIL não encontrado no .env")
        return False
    
    if not password:
        print("❌ QC_PASSWORD não encontrado no .env")
        return False
    
    print(f"✅ Email: {email}")
    print(f"✅ Senha: {'*' * len(password)} ({len(password)} caracteres)")
    print()
    print("✅ Credenciais configuradas corretamente!")
    return True

if __name__ == "__main__":
    print("1. Configurar credenciais")
    print("2. Verificar credenciais existentes")
    print()
    
    choice = input("Escolha uma opção (1 ou 2): ").strip()
    
    if choice == "1":
        setup_env()
    elif choice == "2":
        if not check_env():
            print()
            choice = input("Deseja configurar agora? (s/N): ").lower().strip()
            if choice in ['s', 'sim', 'y', 'yes']:
                setup_env()
    else:
        print("Opção inválida.") 