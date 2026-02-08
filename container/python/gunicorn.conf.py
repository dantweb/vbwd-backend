import os

bind = "0.0.0.0:5000"
workers = int(os.getenv("GUNICORN_WORKERS", 4))
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = os.getenv("LOG_LEVEL", "info")

# For development with reload
reload = os.getenv("FLASK_ENV") == "development"
