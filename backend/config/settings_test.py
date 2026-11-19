from config.settings import *  # noqa: F401, F403

# Hasher rápido para tests — MD5 no es seguro en producción pero
# evita las 720k iteraciones de PBKDF2 que enlentecen la suite.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# El cliente de pruebas usa http: no se fuerza HTTPS en la suite.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# CORS_ALLOW_ALL_ORIGINS se calcula al importar settings con el DEBUG del .env; pytest-django
# apaga DEBUG después. Se fija aquí para que la suite no dependa del .env de cada máquina.
CORS_ALLOW_ALL_ORIGINS = False
