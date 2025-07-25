# config.py
"""
Configurações centralizadas para o QConcursos Scraper.
"""

# URLs
LOGIN_URL = "https://www.qconcursos.com/conta/entrar?return_url=https%3A%2F%2Fapp.qconcursos.com%2F"

# Seletores CSS - Atualize se o site mudar
SEL = {
    "email": "#login_email",
    "password": "#login_password", 
    "submit": "#btnLogin",
    "tab": ".tab",
    "card": ".mb-4",
    "statsAttr": "[data-question-statistics-alternatives-statistics]",
    "num": ".index.text-center.font-weight-bold.border-right.pr-2.svelte-1i1uol",
    "title": ".title",
    "info": ".info.d-flex.flex-wrap.align-items-center.svelte-1i1uol",
    "statement": ".font-size-2.statement-container.svelte-18f2a5m",
    "alt": ".d-block.font-size-1",
    "commentText": ".question-commentary-text.font-size-2",
    "badge": ".badge.badge-secondary.text-light.py-1.px-1.ml-2.font-size-1",
    "extra": ".text.px-3.font-size-2.svelte-1tiqrp1"
}

# Configurações de scraping
import os

# Detecta se está rodando em Docker e configura headless automaticamente
IS_DOCKER = os.path.exists('/.dockerenv') or os.environ.get('container') == 'docker'

SCRAPING_CONFIG = {
    "headless": IS_DOCKER,      # True para Docker, False para debug local
    "timeout": 30000,           # Timeout de login em ms - aumentado para debug
    "scroll_step": 1200,        # Pixels por rolagem - reduzido para ser mais suave
    "scroll_pause": 0.8,        # Pausa entre rolagens - aumentado para dar mais tempo
    "scroll_max_iter": 60,      # Máximo de iterações de rolagem - aumentado para carregar tudo
    "url_pause": 3,             # Pausa entre URLs - aumentado para estabilidade
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # User agent realista
}

# Configurações de output
OUTPUT_CONFIG = {
    "output_dir": "output",
    "filename": "qc_freeplane.mm",
    "encoding": "utf-8",
    "highlight_wrong": True,    # Destacar questões erradas
    "highlight_color": "#ffcccc"  # Cor para questões erradas
}

# Configurações de debug
DEBUG_CONFIG = {
    "screenshot_on_error": True,
    "screenshot_path": "debug.png",
    "verbose_logging": True,    # Habilitado para debug detalhado
    "save_raw_html": True,      # Salvar HTML bruto para debug - habilitado
    "raw_html_path": "debug_raw.html"
} 