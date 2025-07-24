FROM python:3.11-slim

# 1) Atualiza e instala deps do Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2) Instala Playwright browsers (Chromium) depois de copiar requirements
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install --with-deps chromium

# 3) Copia o restante
COPY . .

# 4) Pasta de saída
RUN mkdir -p /app/output

CMD ["python", "scraper.py"] 