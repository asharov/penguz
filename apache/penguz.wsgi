import os, sys

# Change this to wherever you've installed Penguz.
# Everything else in this file can stay as is.
django_root = os.path.join('/', 'var', 'django')

sys.path.append(django_root)
sys.path.append(os.path.join(django_root, 'penguz')

os.environ['DJANGO_SETTINGS_MODULE'] = 'penguz.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
