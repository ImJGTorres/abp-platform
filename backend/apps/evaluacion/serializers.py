from rest_framework import serializers

from .models import CriterioRubrica


class RapBasicoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    descripcion = serializers.CharField()
    competencia_asociada = serializers.CharField()


class CriterioRubricaSerializer(serializers.ModelSerializer):
    rap_detalle = serializers.SerializerMethodField()

    class Meta:
        model = CriterioRubrica
        fields = ['id', 'id_rubrica', 'nombre', 'descripcion', 'peso', 'rap', 'rap_detalle']
        extra_kwargs = {
            'rap': {'write_only': True},
        }

    def get_rap_detalle(self, obj):
        if obj.rap is None:
            return None
        return RapBasicoSerializer(obj.rap).data
