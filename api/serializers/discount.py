from discount.models import DiscountTable
from rest_framework.serializers import ModelSerializer


class DiscountSerilizer(ModelSerializer):
    class Meta:
        model = DiscountTable
        fields = 'id', 'discount_name', 'discount_type', 'discount_amount'

# update function in discount serializer
    def update(self, instance, validated_data):
        print(validated_data.items())
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
