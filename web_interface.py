#!/usr/bin/env python3
"""
Interface web para monitorar o scraping do QConcursos em tempo real.
"""

# Monkey patch do eventlet deve ser feito antes de qualquer outra importação
import eventlet
eventlet.monkey_patch()

import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import redis

app = Flask(__name__)
app.config['SECRET_KEY'] = 'qconcursos_scraper_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Configuração do Redis para comunicação entre processos
try:
    redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    USE_REDIS = True
    print("✅ Redis conectado - logs em tempo real habilitados")
except:
    USE_REDIS = False
    print("⚠️ Redis não disponível - usando logs de arquivo")

class ScrapingMonitor:
    def __init__(self):
        self.status = {
            'running': False,
            'current_url': '',
            'total_urls': 0,
            'processed_urls': 0,
            'total_nodes': 0,
            'start_time': None,
            'last_update': datetime.now(),
            'logs': [],
            'errors': [],
            'screenshots': []
        }
        self.logs_file = Path("logs/scraper.log")
        self.logs_file.parent.mkdir(exist_ok=True)
        
    def add_log(self, message, level="INFO"):
        log_entry = {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'level': level,
            'message': message
        }
        self.status['logs'].append(log_entry)
        self.status['last_update'] = datetime.now()
        
        # Manter apenas os últimos 100 logs
        if len(self.status['logs']) > 100:
            self.status['logs'] = self.status['logs'][-100:]
            
        # Salvar em arquivo
        with open(self.logs_file, "a", encoding="utf-8") as f:
            f.write(f"[{log_entry['timestamp']}] {level}: {message}\n")
            
        # Emitir via WebSocket
        socketio.emit('new_log', log_entry)
        
    def update_progress(self, processed, total, current_url=""):
        self.status['processed_urls'] = processed
        self.status['total_urls'] = total
        self.status['current_url'] = current_url
        self.status['last_update'] = datetime.now()
        
        socketio.emit('progress_update', {
            'processed': processed,
            'total': total,
            'current_url': current_url,
            'percentage': round((processed / total) * 100, 1) if total > 0 else 0
        })
        
    def add_screenshot(self, filename):
        screenshot_info = {
            'filename': filename,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'path': f"/screenshots/{filename}"
        }
        self.status['screenshots'].append(screenshot_info)
        socketio.emit('new_screenshot', screenshot_info)
        
    def set_running(self, running):
        self.status['running'] = running
        if running:
            self.status['start_time'] = datetime.now()
        socketio.emit('status_change', {'running': running})

monitor = ScrapingMonitor()

@app.route('/')
def index():
    """Página principal da interface."""
    return render_template('monitor.html')

@app.route('/api/status')
def get_status():
    """API para obter status atual do scraping."""
    status = monitor.status.copy()
    if status['start_time']:
        elapsed = datetime.now() - status['start_time']
        status['elapsed_time'] = str(elapsed).split('.')[0]  # Remove microseconds
    else:
        status['elapsed_time'] = "00:00:00"
    
    return jsonify(status)

@app.route('/api/logs')
def get_logs():
    """API para obter logs mais recentes."""
    return jsonify(monitor.status['logs'][-50:])  # Últimos 50 logs

@app.route('/screenshots/<filename>')
def serve_screenshot(filename):
    """Serve screenshots gerados durante o scraping."""
    from flask import send_from_directory
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    return send_from_directory(screenshots_dir, filename)

@app.route('/api/test_login', methods=['POST'])
def api_test_login():
    data = request.get_json()
    url = data.get('url', '')
    import subprocess

    # Passa a URL como argumento se fornecida
    cmd = ['python', 'test_login.py']
    if url:
        cmd.append(url)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=60
        )
        return jsonify({'result': result.stdout})
    except Exception as e:
        return jsonify({'result': f'Erro: {str(e)}'})

@socketio.on('connect')
def handle_connect():
    """Quando um cliente se conecta via WebSocket."""
    print(f"Cliente conectado: {request.sid}")
    emit('status_change', {'running': monitor.status['running']})
    emit('progress_update', {
        'processed': monitor.status['processed_urls'],
        'total': monitor.status['total_urls'],
        'current_url': monitor.status['current_url'],
        'percentage': round((monitor.status['processed_urls'] / monitor.status['total_urls']) * 100, 1) if monitor.status['total_urls'] > 0 else 0
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Quando um cliente se desconecta."""
    print(f"Cliente desconectado: {request.sid}")

def monitor_redis_logs():
    """Monitor Redis para logs em tempo real."""
    if not USE_REDIS:
        return
        
    pubsub = redis_client.pubsub()
    pubsub.subscribe('scraper_logs')
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                log_data = json.loads(message['data'])
                monitor.add_log(log_data['message'], log_data.get('level', 'INFO'))
            except:
                continue

def monitor_file_logs():
    """Monitor arquivo de logs quando Redis não está disponível."""
    last_size = 0
    while True:
        try:
            if monitor.logs_file.exists():
                current_size = monitor.logs_file.stat().st_size
                if current_size > last_size:
                    with open(monitor.logs_file, 'r', encoding='utf-8') as f:
                        f.seek(last_size)
                        new_lines = f.readlines()
                        for line in new_lines:
                            if line.strip():
                                # Parse log line: [timestamp] LEVEL: message
                                try:
                                    parts = line.strip().split('] ', 1)
                                    if len(parts) == 2:
                                        timestamp = parts[0][1:]  # Remove [
                                        level_msg = parts[1].split(': ', 1)
                                        if len(level_msg) == 2:
                                            level, message = level_msg
                                            socketio.emit('new_log', {
                                                'timestamp': timestamp,
                                                'level': level,
                                                'message': message
                                            })
                                except:
                                    continue
                    last_size = current_size
            time.sleep(1)
        except:
            time.sleep(5)

# Classe para interceptar logs do scraper
class WebSocketLogHandler:
    """Handler customizado para enviar logs via WebSocket."""
    
    @staticmethod
    def log(message, level="INFO"):
        monitor.add_log(message, level)
        
        # Também envia para Redis se disponível
        if USE_REDIS:
            try:
                redis_client.publish('scraper_logs', json.dumps({
                    'message': message,
                    'level': level,
                    'timestamp': datetime.now().isoformat()
                }))
            except:
                pass
    
    @staticmethod
    def update_progress(processed, total, current_url=""):
        monitor.update_progress(processed, total, current_url)
        
        # Também envia para Redis se disponível
        if USE_REDIS:
            try:
                redis_client.set('scraper_progress', json.dumps({
                    'processed': processed,
                    'total': total,
                    'current_url': current_url
                }))
            except:
                pass
    
    @staticmethod
    def add_screenshot(filename):
        monitor.add_screenshot(filename)
        
    @staticmethod
    def set_running(running):
        monitor.set_running(running)

# Torna o handler disponível globalmente
app.websocket_handler = WebSocketLogHandler

def start_monitoring_threads():
    """Inicia threads de monitoramento de logs."""
    # Criar diretório de logs se não existir
    Path("logs").mkdir(exist_ok=True)
    
    if USE_REDIS:
        log_thread = threading.Thread(target=monitor_redis_logs, daemon=True)
    else:
        log_thread = threading.Thread(target=monitor_file_logs, daemon=True)
    log_thread.start()

if __name__ == '__main__':
    start_monitoring_threads()
    
    # Inicia a aplicação
    print("🚀 Interface web iniciada!")
    print("📊 Acesse: http://localhost:5000")
    
    # Para desenvolvimento local
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
else:
    # Para produção com gunicorn
    start_monitoring_threads() 