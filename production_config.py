"""
Production configuration for POSIFIT website
Optimized for 25-30 concurrent users
"""
import os

# Environment detection
PRODUCTION = os.environ.get('PRODUCTION', 'false').lower() == 'true'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8050')
DASH_URL = os.environ.get('DASH_URL', 'http://localhost:8051')

# Production URLs
if PRODUCTION:
    # In production, both servers run on the same domain
    FLASK_URL = BASE_URL
    DASH_URL = BASE_URL  # Same domain, different paths handled by Nginx
else:
    # Development URLs
    FLASK_URL = "http://localhost:8050"
    DASH_URL = "http://localhost:8051"

# Server configuration for concurrent users
SERVER_CONFIG = {
    'host': '0.0.0.0',
    'port': int(os.environ.get('PORT', 8050)),
    'debug': not PRODUCTION,
    'threaded': True,  # Enable threading for concurrent users
}

# Dash server configuration
DASH_CONFIG = {
    'host': '0.0.0.0',
    'port': int(os.environ.get('DASH_PORT', 8051)),
    'debug': not PRODUCTION,
    'threaded': True,
}

# Gunicorn configuration for production
GUNICORN_CONFIG = {
    'bind': '0.0.0.0:8050',
    'workers': 3,  # 3 workers for 25-30 concurrent users
    'worker_class': 'sync',
    'worker_connections': 1000,
    'timeout': 120,  # 2 minutes timeout for Dash operations
    'keepalive': 5,
    'max_requests': 1000,
    'max_requests_jitter': 50,
    'preload_app': True,
}

# Database configuration (if you add database later)
DATABASE_CONFIG = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 3600,
}

# Caching configuration for performance
CACHE_CONFIG = {
    'CACHE_TYPE': 'simple',  # Use Redis in production
    'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes
}

# Security settings
SECURITY_CONFIG = {
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production'),
    'SESSION_COOKIE_SECURE': PRODUCTION,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/legofit.log',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'] if PRODUCTION else ['default'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
