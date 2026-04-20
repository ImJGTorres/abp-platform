from config.settings import *  # noqa: F401, F403

# Hasher rápido para tests — MD5 no es seguro en producción pero
# evita las 720k iteraciones de PBKDF2 que enlentecen la suite.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]