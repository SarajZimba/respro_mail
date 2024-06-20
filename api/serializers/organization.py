from importlib.metadata import MetadataPathFinder
from rest_framework.serializers import ModelSerializer
from organization.models import Branch, Organization, Table, Terminal, PrinterSetting, CashDrop
from rest_framework import serializers


class CashDropSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashDrop
        exclude =['latest_balance']


class CashDropLatestSerializer(serializers.Serializer):
    latest_balance = serializers.FloatField()
    
class BlockAccountSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=7)
    blocked = serializers.CharField(max_length=4)
    key = serializers.CharField(max_length=255)
    device_id = serializers.CharField(max_length=100, required=False)


class OrganizationSerializer(ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "org_name",
            "org_logo",
            "tax_number",
            "website",
            "company_contact_number",
            "company_contact_email",
            "contact_person_number",
            "company_address",
            "company_bank_qr",
            "current_fiscal_year",
            "auto_end_day"
        ]

class TableSerializer(ModelSerializer):
    class Meta:
        model = Table
        fields = 'table_number', 'is_occupied','id'


class PrinterSettingSerializer(ModelSerializer):
    
    type = serializers.SerializerMethodField()

    class Meta:
        model = PrinterSetting
        fields = "url", "port", "ip", "type", "print_status"
    
    def get_type(self, obj):
        return obj.printer_location


class TerminalSerialzier(ModelSerializer):
    tables = TableSerializer(many=True, read_only=True, source="table_set")
    printers = PrinterSettingSerializer(many=True, read_only=True, source="printersetting_set")
    class Meta:
        model = Terminal
        fields = "id", "terminal_no", "tables", "printers"
        
class OnlyTerminalSerializer(ModelSerializer):
    class Meta:
        model = Terminal
        fields = "id", "terminal_no"

class BranchSerializer(ModelSerializer):
    class Meta:
        model = Branch
        fields = [
            "id",
            "name",
            "address",
            "contact_number",
            "branch_manager",
            "organization",
            "branch_code",
        ]

