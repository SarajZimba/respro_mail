from rest_framework import serializers
from organization.models import Table_Layout
from organization.models import Branch

class TableLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table_Layout
        fields = '__all__'

  