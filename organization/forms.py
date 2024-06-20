from django import forms
from root.forms import BaseForm

from .models import Organization, StaticPage


class OrganizationForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Organization
        fields = "__all__"
        exclude = [
            "is_deleted",
            "status",
            "is_featured",
            "sorting_order",
        ]


class StaticPageForm(BaseForm, forms.ModelForm):
    class Meta:
        model = StaticPage
        fields = "__all__"
        exclude = [
            "is_deleted",
            "status",
            "slug",
            "sorting_order",
            "is_featured",
        ]


from .models import Branch


class BranchForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Branch
        fields = "__all__"
        exclude = [
            "is_deleted",
            "status",
            "deleted_at",
            "sorting_order",
            "is_featured",
            "organization",
        ]

from .models import Terminal

class TerminalForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Terminal
        fields = '__all__'
        exclude = ['is_deleted', 'status', 'deleted_at','sorting_order', 'is_featured']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add a placeholder for the table_number field
        self.fields['terminal_no'].widget.attrs['placeholder'] = 'Enter terminal number'

from .models import Table
class TableForm(BaseForm, forms.ModelForm):
    class Meta:
        model = Table
        fields = '__all__'
        exclude = ['is_deleted', 'status', 'deleted_at', "sorting_order",  "is_featured" , 'is_occupied' ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add a placeholder for the table_number field
        self.fields['table_number'].widget.attrs['placeholder'] = 'Enter table number'

    def clean(self):
        cleaned_data = super().clean()
        terminal = cleaned_data.get("terminal")
        table_number = cleaned_data.get("table_number")

        # Check for duplicate entries
        if Table.objects.filter(terminal=terminal, table_number=table_number).exists():
            raise forms.ValidationError(f"This table {table_number} entry already exists in  {terminal}")

        return cleaned_data

from .models import PrinterSetting
class PrinterSettingForm(BaseForm, forms.ModelForm):
    class Meta:
        model = PrinterSetting
        fields = '__all__'
        exclude = ['is_deleted', 'status', 'deleted_at', "sorting_order",  "is_featured" ]
                        

from .models import MailRecipient

class MailRecipientForm(BaseForm, forms.ModelForm):
    class Meta:
        model = MailRecipient
        fields = '__all__'
  