from rest_framework import serializers
from bill.models import Bill, BillItem, BillPayment, BillItemVoid
from api.serializers.order import CustomOrderWithOrderDetailsSerializer
# from api.serializers.organization import PrinterSettingSerializer
from organization.models import Table_Layout, Table
from api.serializers.bill import BillItemVoidSerializerTerminalSwitch


class TableLayoutSerializer(serializers.ModelSerializer):
    tableNo = serializers.SerializerMethodField()
    class Meta:
        model = Table_Layout
        exclude = [
            "created_at",
            "updated_at",
            "status",
            "is_deleted",
            "sorting_order",
            "is_featured",
        ]     

    def get_tableNo(self, obj):
        return obj.table_id.table_number
        
class TableSerializer(serializers.ModelSerializer):
    tablelayouts = TableLayoutSerializer(source='table_layout', allow_null=True)
    class Meta:
        model = Table
        exclude = [
            "created_at",
            "updated_at",
            "status",
            "is_deleted",
            "sorting_order",
            "is_featured",
        ]  


class BillItemSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    class Meta:
        model = BillItem
        fields = [
            "product_quantity",
            "product",
            "rate",
            "amount",
            "kot_id",
            "bot_id",
            "type"
        ]
        
    def get_type(self, obj):
        return obj.product.type.title

class PaymentModeSerializer(serializers.ModelSerializer):
    saleId = serializers.SerializerMethodField()
    class Meta:
        model = BillPayment
        exclude = [
            "created_at",
            "updated_at",
            "status",
            "is_deleted",
            "sorting_order",
            "is_featured",
            "bill"
        ]

    def get_saleId(self, obj):
        return obj.bill.order.sale_id if obj.bill.order else None
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['amount'] = round(float(data['amount']), 2) if data['amount'] else 0.0
        
        return data  

class BillSerializer(serializers.ModelSerializer):
    bill_items = BillItemSerializer(many=True, read_only=True)

    payment_split = PaymentModeSerializer(source='billpayment_set', many=True, read_only=True)

    order = CustomOrderWithOrderDetailsSerializer()

    isCompleted = serializers.SerializerMethodField()
    isSaved = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    isVoid = serializers.SerializerMethodField()

    tableNo = serializers.SerializerMethodField()
    noOfGuest = serializers.SerializerMethodField()
    
    is_cancelled = serializers.SerializerMethodField()
    startdatetime = serializers.SerializerMethodField()
    server_id = serializers.SerializerMethodField()
    is_synced = serializers.SerializerMethodField()
    void_items = serializers.SerializerMethodField()
    order_type = serializers.SerializerMethodField()
    
    transaction_date_time = serializers.SerializerMethodField()


    class Meta:
        model = Bill
        exclude = [
            "created_at",
            "updated_at",
            "is_deleted",
            "sorting_order",
            "is_featured",
            "status"
        ]
        
    def get_transaction_date_time(self, obj):
        return str(obj.transaction_date_time).split('+')[0]
        
    def get_void_items(self, obj):
        # Check if the bill has an associated order
        if obj.order:
            # Get the related BillItemVoid instances for the order
            bill_item_voids = BillItemVoid.objects.filter(order=obj.order)
            # Serialize the related BillItemVoid instances
            serializer = BillItemVoidSerializerTerminalSwitch(instance=bill_item_voids, many=True)
            return serializer.data
        return None
        
    def get_is_cancelled(self, obj):
        return False if (obj.order is not None and obj.order.orderdetails_set.first() is not None) else True
        
    def get_is_synced(self, obj):
        return True 
    
    def get_startdatetime(self, obj):
        return obj.order.start_datetime if obj.order else None
    
    def get_server_id(self, obj):
        return obj.order.id if obj.order else None

    def get_isCompleted(self, obj):
        return obj.order.is_completed if obj.order else None
    
    def get_isSaved(self, obj):
        return obj.order.is_saved if obj.order else None
    
    def get_organization(self, obj):
        return obj.organization.org_name if obj.organization else None
    
    def get_isVoid(self, obj):
        return False if obj.status else True
    
    def get_tableNo(self, obj):
        return str(obj.order.table_no) if (obj.order and obj.order.table_no) else None 
    
    def get_noOfGuest(self, obj):
        return obj.order.no_of_guest if obj.order else None
        
    def get_order_type(self, obj):
        return obj.order.order_type if obj.order else None
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sub_total'] = round(float(data['sub_total']), 2)
        data['discount_amount'] = round(float(data['discount_amount']), 2)
        data['taxable_amount'] = round(float(data['taxable_amount']), 2)
        data['tax_amount'] = round(float(data['tax_amount']), 2)
        data['grand_total'] = round(float(data['grand_total']), 2)
        data['service_charge'] = round(float(data['service_charge']), 2)
        
        return data