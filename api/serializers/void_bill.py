from rest_framework import serializers
from bill.models import VoidBillTracker, Bill

class VoidBillSerializer(serializers.ModelSerializer):
    fromOrder = serializers.SerializerMethodField()
    toOrder = serializers.SerializerMethodField()
    fromBill = serializers.SerializerMethodField()
    toBill = serializers.SerializerMethodField()
    class Meta:
        model = VoidBillTracker
        exclude = ["created_at", "updated_at", "status", "is_deleted", "sorting_order", "is_featured", "prev_bill", "new_bill", "prev_bill_id", "new_bill_id"]
        
    def get_fromOrder(self, obj):
        if obj.prev_bill_id:
            bill = Bill.objects.get(id=obj.prev_bill_id)
            return bill.order.sale_id
        else:
            return None
        
    def get_toOrder(self, obj):
        if obj.new_bill_id:
            bill = Bill.objects.get(id=obj.new_bill_id)
            return bill.order.sale_id
        else:
            return None
            
    def get_fromBill(self, obj):
        return obj.prev_bill
        # if obj.prev_bill_id:
        #     bill = Bill.objects.get(id=obj.prev_bill_id)
        #     return bill.invoice_number
        # else:
        #     return None
        
    def get_toBill(self, obj):
        return obj.new_bill
        # if obj.new_bill_id:
        #     bill = Bill.objects.get(id=obj.new_bill_id)
        #     return bill.invoice_number
        # else:
        #     return None
