# Automação QConcursos - Web Scraping

Sistema automatizado para fazer web scraping do QConcursos e gerar arquivos Freeplane (.mm) com questões, respostas e comentários.

## 🚀 Como Usar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Executar a Interface Web

```bash
python web_interface.py
```

Acesse: http://localhost:5000

### 3. Fluxo de Automação

1. **Login**: Digite seu email e senha do QConcursos
2. **URLs**: Cole as URLs das questões (uma por linha)
3. **Iniciar**: Clique em "Login e Iniciar Scraping"
4. **Download**: Após finalizar, clique em "Baixar Freeplane (.mm)"

## 📋 Exemplo de URLs

```
https://app.qconcursos.com/playground/questoes?discipline_ids[]=100&examining_board_ids[]=2&per_page=50&subject_ids[]=315
https://app.qconcursos.com/playground/questoes?discipline_ids%5B%5D=96&per_page=50&examining_board_ids%5B%5D=2&subject_ids%5B%5D=26271
```

## 🔧 Funcionalidades

- **Login Automático**: Autenticação no QConcursos
- **Captura de Respostas**: Extrai gabarito das estatísticas
- **Comentários**: Coleta comentários de alunos e professores
- **Scroll Automático**: Carrega todo o conteúdo da página
- **Arquivo Freeplane**: Gera arquivo .mm pronto para uso

## 📁 Estrutura de Arquivos

```
seleniu/
├── web_interface.py      # Servidor Flask
├── templates/
│   └── monitor.html      # Interface web
├── output/
│   └── resultado.mm      # Arquivo gerado
├── logs/
│   └── scraper.log       # Logs da automação
└── requirements.txt      # Dependências
```

## ⚠️ Observações

- Use apenas para fins educacionais
- Respeite os termos de uso do QConcursos
- O sistema funciona em modo headless (sem interface gráfica)
- Os logs são salvos em tempo real

## 🐛 Troubleshooting

Se houver problemas:

1. Verifique suas credenciais de login
2. Confirme se as URLs estão corretas
3. Verifique os logs em `logs/scraper.log`
4. Certifique-se de que o Chromium foi instalado: `python -m playwright install chromium` 