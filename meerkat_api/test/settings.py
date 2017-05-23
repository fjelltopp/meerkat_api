from passlib.hash import pbkdf2_sha256
import calendar
import time
import jwt
import os

# Need this module to be importable without the whole of meerkat_auth config
# Directly load secret settings file from which to import required variables
# File must include JWT_COOKIE_NAME, JWT_ALGORITHM and JWT_PUBLIC_KEY variables
filename = os.environ.get('MEERKAT_AUTH_SETTINGS')
exec(compile(open(filename, "rb").read(), filename, 'exec'))

# We need to authenticate our tests using the dev/testing rsa keys
token_payload = {
    u'acc': {
        u'demo': [u'manager', u'registered'],
        u'jordan': [u'manager', u'registered'],
        u'madagascar': [u'manager', u'registered']
    },
    u'data': {u'name': u'Testy McTestface'},
    u'usr': u'testUser',
    u'exp': calendar.timegm(time.gmtime()) + 1000,  # Lasts for 1000 seconds
    u'email': u'test@test.org.uk'
}
token = jwt.encode(token_payload,
                   JWT_SECRET_KEY,
                   algorithm=JWT_ALGORITHM).decode("utf-8")

header = {'Authorization': JWT_HEADER_PREFIX + token}
header_non_authorised = {'Authorization': ''}
