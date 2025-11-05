import os
from pathlib import Path
import environ
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env()

ENVIROMENT =env 

SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# settings.py
SITE_URL = "http://127.0.0.1:8000"


#ALLOWED_HOSTS = ['192.168.0.231']
ALLOWED_HOSTS = []

# Application definition
SITE_ID = 1
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

PROJECT_APPS = [
    'apps.dasboard',
    'apps.perfil',
    'apps.shops',
    'apps.user',
    'apps.api',

    
]

THIRD_PARTY_APPS = [
  
   
]
INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
   
)


MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
     'core.middleware.RastrearVisitasMiddleware',
   
]





ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.shops.cart_context.cart_item_count',
                'apps.perfil.context_processors.perfiles_pendientes_count',
                'apps.perfil.context_processors.ordenes_pendientes_count',
                'apps.dasboard.context_processors.reclamos_pendientes_count',
                "apps.perfil.context_processors.unread_notifications",
            ],
        },
    },
]

                
WSGI_APPLICATION = 'core.wsgi.application'



# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASES['default']['ATOMIC_REQUESTS'] =True

#CORS_ORIGIN_WHITELIST = ['https:/localhost:3000','https:/localhost:8000',]
#CORS_TRUSTED_ORIGINS = ['https:/localhost:3000','https:/localhost:8000',]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/


LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True
# settings.py







LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_SAVE_EVERY_REQUEST = True  # Renovar la sesión con cada solicitud



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/



MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Carpeta donde colocas tus archivos estáticos en desarrollo
STATIC_ROOT = BASE_DIR / 'staticfiles' 



# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'user.UserAccount'






FILE_UPLOAD_PERMISSIONS = 0o640

#EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'hugor8819@gmail.com'
EMAIL_HOST_PASSWORD = 'ioqompxdqsikhwcm'

DEFAULT_FROM_EMAIL = 'Velix <hugor8819@gmail.com>'  # nombre visible
SERVER_EMAIL = DEFAULT_FROM_EMAIL  


SITE_NAME = "Velix"                # o el nombre de tu producto
SUPPORT_EMAIL = "soporte@tu-dominio.com"
