MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'oboeware.django.OboeDjangoMiddleware',
]

from django import wrap_middleware_classes
wrap_middleware_classes(MIDDLEWARE_CLASSES)

#import oboeware
from oboeware.django import OboeDjangoMiddleware

o = OboeDjangoMiddleware()
import oboe

print oboe.__file__
print o.process_request("hey")
