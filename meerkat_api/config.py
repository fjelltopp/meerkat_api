"""
config.py

Configuration and settings
"""

from os import getenv


class Config(object):
    DEBUG = True
    TESTING = False
    # Global stuff
    SQLALCHEMY_DATABASE_URI = (
        'postgresql+psycopg2://postgres:postgres@db/meerkat_db')
    API_KEY = "test-api"
    AUTH = {
        'default': [['registered'], ['demo']]
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APPLICATION_ROOT = "/api"
    PROPAGATE_EXCEPTIONS = True
    BROKER_URL = 'amqp://guest@dev_rabbit_1//'
    CELERY_RESULT_BACKEND = 'rpc://guest@dev_rabbit_1//'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    SENTRY_DNS = getenv('SENTRY_DNS', '')
    INTERNAL_DEVICE_API_ROOT = getenv("MOB_API_ROOT", 'http://dev_nginx_1/mob')
    EXTERNAL_DEVICE_API_ROOT = '/mob'
    SEND_LOGG_EVENTS = getenv("SEND_LOGG_EVENTS", False)
    LOGGING_URL = getenv("LOGGING_URL", None)
    LOGGING_SOURCE = getenv("LOGGING_SOURCE", "dev")
    LOGGING_SOURCE_TYPE = "api"
    LOGGING_IMPLEMENTATION = getenv("LOGGING_IMPLEMENTAION", "demo")

class Production(Config):
    DEBUG = False
    TESTING = False


class Development(Config):
    DEBUG = True
    TESTING = True


class Testing(Config):
    DEBUG = False
    TESTING = True
