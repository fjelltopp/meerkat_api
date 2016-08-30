"""
config.py

Configuration and settings
"""


class Config(object):
    DEBUG = True
    TESTING = False
    # Global stuff
    SQLALCHEMY_DATABASE_URI = (
        'postgresql+psycopg2://postgres:postgres@db/meerkat_db')
    API_KEY = "test-api"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APPLICATION_ROOT = "/api"
    PROPAGATE_EXCEPTIONS = True
class Production(Config):
    DEBUG = False
    TESTING = False

class Development(Config):
    DEBUG = True
    TESTING = True


class Testing(Config):
    DEBUG = False
    TESTING = True
