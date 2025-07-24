import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 1  # SocketIO funciona melhor com um único worker
worker_class = "eventlet"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help control memory usage
max_requests = 1000
max_requests_jitter = 100

# Logging
errorlog = "/app/logs/gunicorn_error.log"
loglevel = "info"
accesslog = "/app/logs/gunicorn_access.log"
access_log_format = '%h %l %u %t "%r" %s %b "%{Referer}i" "%{User-Agent}i"'

# Process naming
proc_name = 'qc_web_interface'

# Server mechanics
preload_app = True
daemon = False
pidfile = '/tmp/gunicorn.pid'
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None 