import sys

sys.path.insert(0, '../oboeware')

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'oboeware.django.OboeDjangoMiddleware',
]

from oboeware.djangoware import OboeDjangoMiddleware
o = OboeDjangoMiddleware()

class FakeRequest(object):
    def __init__(self):
        self.META = dict()

print o.process_request(FakeRequest())
