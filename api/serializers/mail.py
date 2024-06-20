from rest_framework import serializers

from organization.models import MailRecipient

class MailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=MailRecipient
        fields = '__all__'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance