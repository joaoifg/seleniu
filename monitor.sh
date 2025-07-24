#!/bin/bash

echo "=== MONITORAMENTO QCONCURSOS SCRAPER ==="
echo "========================================"

echo ""
echo "🔍 1. STATUS DOS CONTAINERS:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "📝 2. ÚLTIMOS LOGS DO SCRAPER (Login e Progresso):"
docker logs qc-scraper --tail 50

echo ""
echo "📁 3. ARQUIVOS GERADOS:"
echo "Output:"
docker exec qc-scraper ls -la /app/output/ 2>/dev/null || echo "Pasta output vazia ou não acessível"

echo ""
echo "Screenshots:"
docker exec qc-scraper ls -la /app/screenshots/ 2>/dev/null || echo "Pasta screenshots vazia ou não acessível"

echo ""
echo "Logs:"
docker exec qc-scraper ls -la /app/logs/ 2>/dev/null || echo "Pasta logs vazia ou não acessível"

echo ""
echo "🌐 4. ACESSE A INTERFACE WEB:"
echo "   👉 http://localhost:5000"
echo ""
echo "🔄 5. PARA LOGS EM TEMPO REAL:"
echo "   docker logs qc-scraper -f"
echo ""
echo "🔄 6. PARA REINICIAR O SCRAPER:"
echo "   docker compose restart scraper" 