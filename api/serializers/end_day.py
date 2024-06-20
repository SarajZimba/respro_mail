from rest_framework import serializers
from organization.models import EndDayDailyReport

# class EndDayDailyReportSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EndDayDailyReport
#         exclude = ('created_at', 'updated_at', 'status', 'is_deleted', 'sorting_order', 'is_featured', 'total_discounts', 'total_void_count', 'no_of_guest', 'created_date', 'others_sale', 'date_time', 'food_sale', 'beverage_sale')

from rest_framework import serializers

class EndDayDailyReportSerializer(serializers.ModelSerializer):
    food = serializers.FloatField(source='food_sale')
    beverage = serializers.FloatField(source='beverage_sale')
    totalVoid = serializers.IntegerField(source='total_void_count')
    noOfGuest = serializers.IntegerField(source='no_of_guest')
    totalDiscount = serializers.FloatField(source='total_discounts')

    class Meta:
        model = EndDayDailyReport
        fields = (
            'employee_name',
            'net_sales',
            'vat',
            'cash',
            'credit',
            'credit_card',
            'mobile_payment',
            'complimentary',
            'start_bill',
            'end_bill',
            'total_sale',
            'food',
            'beverage',
            'totalVoid',
            'noOfGuest',
            'totalDiscount',
            'branch',
            'terminal',
        )