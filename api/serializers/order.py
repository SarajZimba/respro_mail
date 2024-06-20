from bill.models import Order, OrderDetails
from rest_framework import serializers
from api.serializers.product import ProductSerializer

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'table_no', 'date', 'sale_id', 'terminal', 'start_datetime', 'is_completed', 'no_of_guest', 'branch', 'employee', 'order_type', 'is_saved', 'terminal_no',  'customer']

    def create(self, validated_data):
        return Order.objects.create(**validated_data)

class OrderDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderDetails
        fields = ['order', 'product', 'product_quantity', 'botID', 'kotID', 'ordertime', 'employee', 'modification']

    def create(self, validated_data):
        return OrderDetails.objects.create(**validated_data)
    
class CustomOrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailsSerializer(many=True)
    id = serializers.IntegerField(required=False, allow_null=True)
    class Meta:
        model = Order
        fields = ['id', 'table_no', 'date', 'sale_id', 'terminal', 'start_datetime', 'is_completed', 'no_of_guest', 'branch', 'employee', 'order_type', 'is_saved', 'order_details', 'terminal_no', 'customer']

    # def create(self, validated_data):
    #     return Order.objects.create(**validated_data)

class CustomOrderDetailsSerializer(serializers.ModelSerializer):
    # product = ProductSerializer()
    title = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    isTaxable = serializers.SerializerMethodField()
    productId = serializers.SerializerMethodField()
    saleId = serializers.SerializerMethodField()
    # type = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    discount_exempt = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    class Meta:
        model = OrderDetails
        exclude = [
            "created_at",
            "updated_at",
            "status",
            "is_deleted",
            "sorting_order",
            "is_featured",
        ]  
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['kotID'] = int(data['kotID']) if data['kotID'] is not None else None
        data['botID'] = int(data['botID']) if data['botID'] is not None else None
        
        return data  

    def get_title(self,obj):
        return obj.product.title if (obj.product and obj.product.title) else None
        
    def get_category(self,obj):
        return obj.product.type.title if (obj.product and obj.product.type) else None
        
    def get_group(self,obj):
        return obj.product.group if obj.product else None
    
    def get_slug(self,obj):
        return obj.product.slug if (obj.product and obj.product.slug) else None
    
    def get_description(self,obj):
        return obj.product.description if (obj.product and obj.product.description) else None
    
    def get_image(self,obj):
        
        if (obj.product and obj.product.image):
        
            path = obj.product.image.path 
            index = path.find('/uploads')
    
            # Check if '/uploads' is found
            if index != -1:
                # Extract the part after '/uploads', including '/uploads'
                relative_path = path[index:]
            else:
                # If '/uploads' is not found, use the entire path
                relative_path = path
            return relative_path  
        
        else:
            return None
    
    def get_isTaxable(self,obj):
        return obj.product.is_taxable if obj.product else None
    
    def get_type(self,obj):
        return obj.product.type if (obj.product and obj.product.type) else None
    
    def get_unit(self,obj):
        return obj.product.unit if (obj.product and obj.product.unit) else None
    
    def get_price(self,obj):
        return obj.product.price if (obj.product and obj.product.price) else None
    
    def get_productId(self,obj):
        return obj.product.id if obj.product else None
    
    def get_saleId(self, obj):
        return obj.order.sale_id if (obj.order and obj.order.sale_id) else None
        
    def get_discount_exempt(self,obj):
        return obj.product.discount_exempt if (obj.product and obj.product.discount_exempt) else None


    def create(self, validated_data):
        return OrderDetails.objects.create(**validated_data)

class CustomOrderWithOrderDetailsSerializer(serializers.ModelSerializer):
    products = CustomOrderDetailsSerializer(source='orderdetails_set', many=True, read_only=True)
    bot = serializers.SerializerMethodField()
    kot = serializers.SerializerMethodField()
    tableNumber = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = ['id', 'tableNumber', 'date', 'sale_id', 'terminal', 'start_datetime', 'is_completed', 'no_of_guest', 'branch', 'employee', 'order_type', 'is_saved', 'products', 'bot', 'kot', 'terminal_no', 'customer']

    def get_bot(self, obj):
        return int(obj.orderdetails_set.first().botID) if (obj.orderdetails_set.first() is not None and obj.orderdetails_set.first().botID is not None)else None
    
    def get_kot(self, obj):
        return int(obj.orderdetails_set.first().kotID) if (obj.orderdetails_set.first() is not None and obj.orderdetails_set.first().kotID is not None) else None
    
    def get_tableNumber(self, obj):
        return str(obj.table_no) if (obj.orderdetails_set.first() is not None and obj.table_no is not None) else None