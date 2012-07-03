# Copy this file to local_settings.py and add any necessary local
# settings here. You will want to set at least the DATABASES and
# SECRET_KEY settings, and probably some others too.

# Add only the settings you want to change from the defaults in
# settings.py. Anything in this file will override any setting from
# settings.py.

# Admin name and email address
ADMINS = (
#    ('Admin', 'admin@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/django/penguz/app/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/django/penguz/app/static/"
STATIC_ROOT = ''

# URL prefix for static files.
STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# Make bcrypt the default password hasher. In local settings because
# bcrypt doesn't come by default with Python or Django, so not
# everyone will have it installed. If you don't, just delete this part.
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)
