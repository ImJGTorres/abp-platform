from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from apps.usuarios.models import Usuario
from apps.usuarios.serializers import UsuarioSerializer

class UsuarioCreateView(generics.CreateAPIView):
    queryset           = Usuario.objects.all()
    serializer_class   = UsuarioSerializer
    permission_classes = [IsAdminUser]  # solo administradores pueden crear usuarios