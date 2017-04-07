"""
config.py

Configuration and settings
"""

import os


def from_env(env_var, default):
    """ Gets value from envrionment variable or uses default

    Args:
        env_var: name of envrionment variable
        default: the default value
    """
    new = os.environ.get(env_var)
    if new:
        return new
    else:
        return default

class Config(object):
    DEBUG = True
    TESTING = False
    # Global stuff
    SQLALCHEMY_DATABASE_URI = (
        'postgresql+psycopg2://postgres:postgres@db/meerkat_db')
    API_KEY = "test-api"
    AUTH = {
        'default': [['registered'],['demo']]
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APPLICATION_ROOT = "/api"
    PROPAGATE_EXCEPTIONS = True
    BROKER_URL = 'amqp://guest@dev_rabbit_1//'
    CELERY_RESULT_BACKEND = 'rpc://guest@dev_rabbit_1//'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    SENTRY_DNS = from_env('SENTRY_DNS', '')
    INTERNAL_DEVICE_API_ROOT = from_env("INTERNAL_API_ROOT", 'http://dev_nginx_1/mob')
    EXTERNAL_DEVICE_API_ROOT = '/mob'

    LOGGING_URL = os.getenv("LOGGING_URL", None)
    LOGGING_SOURCE = os.getenv("LOGGING_SOURCE", "frontend")
    LOGGING_SOUCRE_TYPE = "api"
    LOGGING_IMPLEMENTAION = os.getenv("LOGGING_IMPLEMENTAION", "demo")
    
class Production(Config):
    DEBUG = False
    TESTING = False

class Development(Config):
    DEBUG = True
    TESTING = True


class Testing(Config):
    DEBUG = False
    TESTING = True
