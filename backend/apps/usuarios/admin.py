from django.contrib import admin
from apps.usuarios.models import Usuario

# Esto permite entrar a http://localhost:8000/admin 
# y ver la tabla de usuarios visualmente.
admin.site.register(Usuario)