from rest_framework import serializers
from organization.models import EndDayDailyReport

class EndDayDailyRecordSerializer(serializers.ModelSerializer):
    # terminal_no = serializers.IntegerField(source='terminal')  # Convert charfield to integer

    class Meta:
        model = EndDayDailyReport
        # fields = ('terminal_no', 'created_at')
