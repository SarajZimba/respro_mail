from django.db import models
from root.utils import BaseModel, SingletonModel
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import datetime
import environ
env = environ.Env(DEBUG=(bool, False))


class StaticPage(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    published_date = models.DateField(null=True, blank=True)
    keywords = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Organization(SingletonModel, BaseModel):
    # basic company details
    org_name = models.CharField(max_length=255)
    org_logo = models.ImageField(
        upload_to="organization/images/", null=True, blank=True
    )
    tax_number = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="PAN/VAT Number"
    )
    website = models.URLField(null=True, blank=True)
    current_fiscal_year = models.CharField(max_length=20)
    start_year = models.IntegerField()
    end_year = models.IntegerField()

    # contact details
    company_contact_number = models.CharField(max_length=255, null=True, blank=True)
    company_contact_email = models.EmailField(null=True, blank=True)
    contact_person_name = models.CharField(max_length=255, null=True, blank=True)
    contact_person_number = models.CharField(max_length=255, null=True, blank=True)
    company_address = models.CharField(max_length=255, null=True, blank=True)
    company_bank_qr = models.ImageField(
        upload_to="organization/images/", null=True, blank=True
    )
    auto_end_day = models.BooleanField(default=True)
    loyalty_percentage =models.DecimalField(max_digits=10, decimal_places=2, default=0)



    def __str__(self):
        return self.org_name
    
    def get_fiscal_year(self):
        return f'{self.start_year}-{self.end_year}'


from uuid import uuid4


def get_default_uuid():
    return uuid4().hex


class Branch(BaseModel):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, null=True, blank=True)
    contact_number = models.CharField(max_length=50, null=True, blank=True)
    branch_manager = models.CharField(max_length=255, null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch_code = models.CharField(
        max_length=255, null=False, blank=False, unique=True, default=get_default_uuid
    )
    is_central = models.BooleanField(default=False, verbose_name='For Central Billing (Web)')
    branch_image = models.ImageField(upload_to='branch_images/', null=True, blank=True)


    def __str__(self):
        return f"{self.organization.org_name} - {self.name}"



class Terminal(BaseModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    terminal_no = models.PositiveIntegerField()
    # is_active = models.BooleanField(default=False)
    # active_count = models.IntegerField(default = 0)
    dayclose = models.BooleanField(default=False)


    def __str__(self):
        return f'Terminal {self.terminal_no} of branch {self.branch.name}'
        
# @receiver(pre_save, sender=Terminal)
# def ensure_non_negative_active_count(sender, instance, **kwargs):
#     if instance.active_count < 0:
#         instance.active_count = 0  # Set active_count to zero if it's negative
    

@receiver(post_save, sender=Terminal)
def create_profile(sender, instance, created, **kwargs):
    if created:
        pass
        # create_terminal_sub_ledgers(branch_code=instance.branch.branch_code, terminal_no=instance.terminal_no)

class PrinterSetting(BaseModel):

    PRINTER_LOCATION = (
        ('KITCHEN', "KITCHEN"),
        ("BAR", "BAR")
    )

    terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE)
    url = models.CharField(max_length=100, null=True, blank=True)
    port = models.IntegerField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    printer_location = models.CharField(max_length=10, choices=PRINTER_LOCATION)
    print_status = models.BooleanField(default=False)

    def __str__(self):
        return f'Printer for terminal {self.terminal.terminal_no}'
    
    class Meta:
        unique_together = 'printer_location', 'terminal',



class Table(BaseModel):
    terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE)
    table_number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)
    is_estimated = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.table_number} table from Terminal {self.terminal.terminal_no}'
        
    class Meta:
        # Add a unique constraint for table_number within each terminal
        unique_together = ('terminal', 'table_number')


class EndDayRecord(BaseModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    terminal = models.CharField(max_length=10)
    date = models.DateField()

    def __str__(self):
        return self.branch.name



class MailRecipient(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class MailSendRecord(models.Model):
    mail_recipient = models.ForeignKey(MailRecipient, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mail_recipient.name


class EndDayDailyReport(BaseModel):
    employee_name = models.CharField(max_length=50)
    net_sales = models.FloatField()
    vat = models.FloatField()
    total_discounts = models.FloatField()
    cash = models.FloatField()
    credit = models.FloatField()
    credit_card = models.FloatField()
    mobile_payment = models.FloatField()
    complimentary = models.FloatField()
    start_bill = models.CharField(max_length=20)
    end_bill = models.CharField(max_length=20)
    total_void_count = models.IntegerField()
    date_time = models.CharField(max_length=100, null=True)
    food_sale = models.FloatField()
    beverage_sale = models.FloatField()
    others_sale = models.FloatField()
    no_of_guest = models.IntegerField()
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    terminal = models.CharField(max_length=10, null=True)
    total_sale = models.FloatField(default=0)
    created_date = models.DateField(default=datetime.date.today)
    dine_grandtotal = models.FloatField(default=0)
    delivery_grandtotal = models.FloatField(default=0)
    takeaway_grandtotal = models.FloatField(default=0)
    dine_nettotal = models.FloatField(default=0)
    delivery_nettotal = models.FloatField(default=0)
    takeaway_nettotal = models.FloatField(default=0)
    dine_vattotal = models.FloatField(default=0)
    delivery_vattotal = models.FloatField(default=0)
    takeaway_vattotal = models.FloatField(default=0)

    class Meta:
        unique_together = 'created_date', 'start_bill', 'end_bill'

    def __str__(self):
        return 'Report'
    
    def save(self, *args, **kwargs):
        self.total_sale = self.net_sales + self.vat
        return super().save()

# class CashDrop(models.Model):
#     branch_id = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
#     branch = models.CharField(max_length=200, null=True, blank=True)
#     opening_balance = models.FloatField(default=0.0)
#     datetime = models.CharField(max_length=200)
#     cashdrop_amount = models.FloatField(default=0.0)
#     employee = models.CharField(max_length=100)
#     expense = models.FloatField(default=0.0, null=True, blank=True)
#     remaining_balance = models.FloatField(default=0.0, null=True, blank=True)  

class CashDrop(models.Model):
    branch_id = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    branch = models.CharField(max_length=200, null=True, blank=True)
    opening_balance = models.FloatField(default=0.0)
    datetime = models.CharField(max_length=200)
    # cashdrop_amount = models.FloatField(default=0.0)
    cashdrop_amount = models.FloatField(default=0.0)
    employee = models.CharField(max_length=100)
    expense = models.FloatField(default=0.0)
    remaining_balance = models.FloatField(default=0.0)
    terminal = models.CharField(max_length=200, null=True, blank=True)
    addCash = models.FloatField(default=0.0)
    narration = models.CharField(max_length=400, null=True, blank=True)
    is_end_day = models.BooleanField(default=False)
    latest_balance = models.FloatField(default=0.0)


    def save(self, *args, **kwargs):
        # Round the cash value to 2 decimal places before saving
        self.opening_balance = round(self.opening_balance, 2)
        self.cashdrop_amount = round(self.cashdrop_amount, 2)
        self.expense = round(self.expense, 2)
        self.remaining_balance = round(self.remaining_balance, 2)
        self.addCash = round(self.addCash, 2)
        self.latest_balance = self.opening_balance - self.cashdrop_amount - self.expense + self.addCash
        super().save(*args, **kwargs)

    def save1(self, *args, **kwargs):
        # Round the cash value to 2 decimal places before saving
        self.opening_balance = round(self.opening_balance, 2)
        self.cashdrop_amount = round(self.cashdrop_amount, 2)
        self.expense = round(self.expense, 2)
        self.remaining_balance = round(self.remaining_balance, 2)
        self.addCash = round(self.addCash, 2)
        self.latest_balance = self.latest_balance
        super().save(*args, **kwargs)
    
    

# from .utils import send_mail_to_receipients
# from threading import Thread
# from datetime import datetime
# from django.db.models import Sum
# from itertools import groupby
# from operator import itemgetter

# @receiver(post_save, sender=EndDayDailyReport)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         sender = env('EMAIL_HOST_USER')
#         mail_list = []
#         recipients = MailRecipient.objects.filter(status=True)
#         for r in recipients:
#             mail_list.append(r.email)
#             MailSendRecord.objects.create(mail_recipient=r)
#         if mail_list:
#             dt_now = datetime.now()
#             date_now = dt_now.strftime('%Y-%m-%d')  # Extract the date part only
#             time_now = dt_now.time().strftime('%I:%M %p')
#             org = Organization.objects.first().org_name
#             branch = instance.branch.name
#             # branch_id = instance.branch.id
            
#             # Retrieve all CashDrop objects for the branch and date
#             cashdrops = CashDrop.objects.filter(branch=branch, datetime__startswith=date_now)
            
#             # Calculate the total expense and total cashdrop
#             total_expense = cashdrops.aggregate(Sum('expense'))['expense__sum'] or 0.0
#             total_cashdrop = cashdrops.aggregate(Sum('cashdrop_amount'))['cashdrop_amount__sum'] or 0.0
            
#             latest_balance=0
#             total_expense_cashdrop = 0
#             total_expense_cashdrop = total_expense + total_cashdrop
#             latest_cash_drop = cashdrops.last()
#             if latest_cash_drop is not None:
#                 # Calculate the latest_balance
#                 latest_balance = latest_cash_drop.opening_balance - latest_cash_drop.cashdrop_amount
#                 # opening_balance = latest_cash_drop.opening_balance
#                 # cashdrop = latest_cash_drop.cashdrop_amount
#                 if latest_cash_drop.expense is not None:
#                     latest_balance -= latest_cash_drop.expense
#                     # expense = latest_cash_drop.expense
#                 if latest_cash_drop.addCash is not None:
#                     latest_balance += latest_cash_drop.addCash
#                 else:
#                     expense = 0.0
            
#             opening_balance = latest_balance + total_expense_cashdrop
            
#             # from bill.models import Bill
#             # bills = Bill.objects.filter(payment_mode="CREDIT").values('invoice_number', 'customer_name', 'grand_total')
            
#             # grouped_bills = {}
#             # for key, group in groupby(bills, key=itemgetter('customer_name')):
#             #     # Each group is a list of dictionaries
#             #     grouped_bills[key] = list(group)
#             report_data = {
#                 'org_name': org,
#                 'date_now': date_now,
#                 'time_now': time_now,
#                 'total_sale': instance.total_sale,
#                 'date_time': instance.date_time,
#                 'employee_name': instance.employee_name,
#                 'net_sales': instance.net_sales,
#                 'vat': instance.vat,
#                 'total_discounts': instance.total_discounts,
#                 'cash': instance.cash,
#                 'credit': instance.credit,
#                 'credit_card': instance.credit_card,
#                 'mobile_payment': instance.mobile_payment,
#                 'complimentary': instance.complimentary,
#                 'start_bill': instance.start_bill,
#                 'end_bill': instance.end_bill,
#                 'total_void_count': instance.total_void_count,
#                 'food_sale': instance.food_sale,
#                 'beverage_sale': instance.beverage_sale,
#                 'others_sale': instance.others_sale,
#                 'no_of_guest': instance.no_of_guest,
#                 'branch': branch,
#                 'terminal': instance.terminal,
#                 'latest_balance': latest_balance,
#                 'opening_balance': opening_balance,
#                 'total_expense': total_expense,
#                 # 'grouped_bills': grouped_bills,
#                 'total_cashdrop': total_cashdrop  # Include the total expense and cashdrop in report_data
#             }
#             Thread(target=send_mail_to_receipients, args=(report_data, mail_list, sender)).start()

from .utils import send_mail_to_receipients
from threading import Thread
from datetime import datetime
from django.db.models import Sum
from itertools import groupby
from operator import itemgetter

# @receiver(post_save, sender=EndDayDailyReport)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         sender = env('EMAIL_HOST_USER')
#         mail_list = []
#         recipients = MailRecipient.objects.filter(status=True)
#         for r in recipients:
#             mail_list.append(r.email)
#             MailSendRecord.objects.create(mail_recipient=r)
#         if mail_list:
#             dt_now = datetime.now()
#             date_now = dt_now.strftime('%Y-%m-%d')  # Extract the date part only
#             time_now = dt_now.time().strftime('%I:%M %p')
#             org = Organization.objects.first().org_name
#             branch = instance.branch.name
#             # branch_id = instance.branch.id
            
#             # Retrieve all CashDrop objects for the branch and date
#             cashdrops = CashDrop.objects.filter(branch=branch, datetime__startswith=date_now)
            
#             # Calculate the total expense and total cashdrop
#             total_expense = cashdrops.aggregate(Sum('expense'))['expense__sum'] or 0.0
#             total_cashdrop = cashdrops.aggregate(Sum('cashdrop_amount'))['cashdrop_amount__sum'] or 0.0
            
#             latest_balance=0
#             total_expense_cashdrop = 0
#             total_expense_cashdrop = total_expense + total_cashdrop
#             latest_cash_drop = cashdrops.last()
#             if latest_cash_drop is not None:
#                 # Calculate the latest_balance
#                 latest_balance = latest_cash_drop.opening_balance - latest_cash_drop.cashdrop_amount
#                 # opening_balance = latest_cash_drop.opening_balance
#                 # cashdrop = latest_cash_drop.cashdrop_amount
#                 if latest_cash_drop.expense is not None:
#                     latest_balance -= latest_cash_drop.expense
#                     # expense = latest_cash_drop.expense
#                 if latest_cash_drop.addCash is not None:
#                     latest_balance += latest_cash_drop.addCash
#                 else:
#                     expense = 0.0
            
#             opening_balance = latest_balance + total_expense_cashdrop
#             cash_to_be_added= float(instance.cash)
#             cash_total= latest_balance + cash_to_be_added
#             start_bill_number = int(instance.start_bill.split('-')[-1])
#             end_bill_number = int(instance.end_bill.split('-')[-1])
#             print(start_bill_number)
#             print(end_bill_number)
#             # bills = Bill.objects.filter(payment_mode="CREDIT")
#             from bill.models import Bill
#             # bills = Bill.objects.filter(payment_mode="CREDIT", invoice_number__gte=f'{instance.branch.branch_code}-{instance.terminal}-{start_bill_number}',
#             #     invoice_number__lte=f'{instance.branch.branch_code}-{instance.terminal}-{end_bill_number}', branch=instance.branch).values('invoice_number', 'customer_name', 'grand_total')
#             bills = Bill.objects.filter(
#                 payment_mode="CREDIT",
#                 invoice_number__range=[
#                     f'{instance.branch.branch_code}-{instance.terminal}-{start_bill_number}',
#                     f'{instance.branch.branch_code}-{instance.terminal}-{end_bill_number}'
#                 ],
#                 branch=instance.branch
#             ).values('invoice_number', 'customer_name', 'grand_total')
#             # print("Before looping", bills)
#             # Group bills by customer_name
#             # grouped_bills = {}
#             # for key, group in groupby(bills, key=itemgetter('customer_name')):
#             #     # Each group is a list of dictionaries
#             #     bills_data = list(group)

#             #     total_amount = sum(bill_data['grand_total'] for bill_data in bills_data)

#             #     grouped_bills[key] = {
#             #         'bills_data': bills_data,
#             #         'total_amount': total_amount,
#             #     }
#             print("before sorting", bills)
#             sorted_bills = sorted(bills, key=itemgetter('customer_name'))
            
#             print("after sorting", sorted_bills)
#             # Group bills by customer_name
#             grouped_bills = {}
#             for key, group in groupby(sorted_bills, key=itemgetter('customer_name')):
#                 # Convert the group iterator to a list of dictionaries
#                 bills_data = list(group)
            
#                 # Calculate the total amount for each customer's bills
#                 total_amount = sum(bill_data['grand_total'] for bill_data in bills_data)
            
#                 # Store the grouped data in a dictionary
#                 grouped_bills[key] = {
#                     'bills_data': bills_data,
#                     'total_amount': total_amount
#                 }
            
#             # Print or further process the grouped bills
#             print(grouped_bills)
            
#             report_data = {
#                 'org_name': org,
#                 'date_now': date_now,
#                 'time_now': time_now,
#                 'total_sale': instance.total_sale,
#                 'date_time': instance.date_time,
#                 'employee_name': instance.employee_name,
#                 'net_sales': instance.net_sales,
#                 'vat': instance.vat,
#                 'total_discounts': instance.total_discounts,
#                 'cash': instance.cash,
#                 'credit': instance.credit,
#                 'credit_card': instance.credit_card,
#                 'mobile_payment': instance.mobile_payment,
#                 'complimentary': instance.complimentary,
#                 'start_bill': instance.start_bill,
#                 'end_bill': instance.end_bill,
#                 'total_void_count': instance.total_void_count,
#                 'food_sale': instance.food_sale,
#                 'beverage_sale': instance.beverage_sale,
#                 'others_sale': instance.others_sale,
#                 'no_of_guest': instance.no_of_guest,
#                 'branch': branch,
#                 'terminal': instance.terminal,
#                 'latest_balance': latest_balance,
#                 'opening_balance': opening_balance,
#                 'total_expense': total_expense,
#                 'grouped_bills': grouped_bills,
#                 'cash_total': cash_total,
#                 'total_cashdrop': total_cashdrop  # Include the total expense and cashdrop in report_data
#             }
#             Thread(target=send_mail_to_receipients, args=(report_data, mail_list, sender)).start()


# @receiver(post_save, sender=EndDayDailyReport)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         if instance.employee_name != 'system':
#             sender = env('EMAIL_HOST_USER')
#             mail_list = []
#             recipients = MailRecipient.objects.filter(status=True)
#             for r in recipients:
#                 mail_list.append(r.email)
#                 MailSendRecord.objects.create(mail_recipient=r)
#             if mail_list:
#                 dt_now = datetime.now()
#                 date_now = dt_now.strftime('%Y-%m-%d')  # Extract the date part only
#                 time_now = dt_now.time().strftime('%I:%M %p')
#                 org = Organization.objects.first().org_name
#                 branch = instance.branch.name
#                 # branch_id = instance.branch.id
                
#                 # Retrieve all CashDrop objects for the branch and date
#                 cashdrops = CashDrop.objects.filter(branch=branch, datetime__startswith=date_now)
                
#                 # Calculate the total expense and total cashdrop
#                 total_expense = cashdrops.aggregate(Sum('expense'))['expense__sum'] or 0.0
#                 total_cashdrop = cashdrops.aggregate(Sum('cashdrop_amount'))['cashdrop_amount__sum'] or 0.0
                
#                 latest_balance=0
#                 total_expense_cashdrop = 0
#                 total_expense_cashdrop = total_expense + total_cashdrop
#                 latest_cash_drop = cashdrops.last()
#                 if latest_cash_drop is not None:
#                     # Calculate the latest_balance
#                     latest_balance = latest_cash_drop.opening_balance - latest_cash_drop.cashdrop_amount
#                     # opening_balance = latest_cash_drop.opening_balance
#                     # cashdrop = latest_cash_drop.cashdrop_amount
#                     if latest_cash_drop.expense is not None:
#                         latest_balance -= latest_cash_drop.expense
#                         # expense = latest_cash_drop.expense
#                     if latest_cash_drop.addCash is not None:
#                         latest_balance += latest_cash_drop.addCash
#                     else:
#                         expense = 0.0
                
#                 opening_balance = latest_balance + total_expense_cashdrop
#                 cash_to_be_added= float(instance.cash)
#                 cash_total= latest_balance + cash_to_be_added
#                 start_bill_number = int(instance.start_bill.split('-')[-1])
#                 end_bill_number = int(instance.end_bill.split('-')[-1])
#                 print(start_bill_number)
#                 print(end_bill_number)
#                 # bills = Bill.objects.filter(payment_mode="CREDIT")
#                 from bill.models import Bill
#                 # bills = Bill.objects.filter(payment_mode="CREDIT", invoice_number__gte=f'{instance.branch.branch_code}-{instance.terminal}-{start_bill_number}',
#                 #     invoice_number__lte=f'{instance.branch.branch_code}-{instance.terminal}-{end_bill_number}', branch=instance.branch).values('invoice_number', 'customer_name', 'grand_total')
#                 bills = Bill.objects.filter(
#                     payment_mode="CREDIT",
#                     invoice_number__range=[
#                         f'{instance.branch.branch_code}-{instance.terminal}-{start_bill_number}',
#                         f'{instance.branch.branch_code}-{instance.terminal}-{end_bill_number}'
#                     ],
#                     branch=instance.branch
#                 ).values('invoice_number', 'customer_name', 'grand_total')
#                 # print("Before looping", bills)
#                 # Group bills by customer_name
#                 # grouped_bills = {}
#                 # for key, group in groupby(bills, key=itemgetter('customer_name')):
#                 #     # Each group is a list of dictionaries
#                 #     bills_data = list(group)

#                 #     total_amount = sum(bill_data['grand_total'] for bill_data in bills_data)

#                 #     grouped_bills[key] = {
#                 #         'bills_data': bills_data,
#                 #         'total_amount': total_amount,
#                 #     }
#                 print("before sorting", bills)
#                 sorted_bills = sorted(bills, key=itemgetter('customer_name'))
                
#                 print("after sorting", sorted_bills)
#                 # Group bills by customer_name
#                 grouped_bills = {}
#                 for key, group in groupby(sorted_bills, key=itemgetter('customer_name')):
#                     # Convert the group iterator to a list of dictionaries
#                     bills_data = list(group)
                
#                     # Calculate the total amount for each customer's bills
#                     total_amount = sum(bill_data['grand_total'] for bill_data in bills_data)
                
#                     # Store the grouped data in a dictionary
#                     grouped_bills[key] = {
#                         'bills_data': bills_data,
#                         'total_amount': total_amount
#                     }
                
#                 # Print or further process the grouped bills
#                 print(grouped_bills)
                
#                 report_data = {
#                     'org_name': org,
#                     'date_now': date_now,
#                     'time_now': time_now,
#                     'total_sale': instance.total_sale,
#                     'date_time': instance.date_time,
#                     'employee_name': instance.employee_name,
#                     'net_sales': instance.net_sales,
#                     'vat': instance.vat,
#                     'total_discounts': instance.total_discounts,
#                     'cash': instance.cash,
#                     'credit': instance.credit,
#                     'credit_card': instance.credit_card,
#                     'mobile_payment': instance.mobile_payment,
#                     'complimentary': instance.complimentary,
#                     'start_bill': instance.start_bill,
#                     'end_bill': instance.end_bill,
#                     'total_void_count': instance.total_void_count,
#                     'food_sale': instance.food_sale,
#                     'beverage_sale': instance.beverage_sale,
#                     'others_sale': instance.others_sale,
#                     'no_of_guest': instance.no_of_guest,
#                     'branch': branch,
#                     'terminal': instance.terminal,
#                     'latest_balance': latest_balance,
#                     'opening_balance': opening_balance,
#                     'total_expense': total_expense,
#                     'grouped_bills': grouped_bills,
#                     'cash_total': cash_total,
#                     'total_cashdrop': total_cashdrop  # Include the total expense and cashdrop in report_data
#                 }
#                 Thread(target=send_mail_to_receipients, args=(report_data, mail_list, sender)).start()

#         else:
#             print("The endday was created by the system")
 
            
class Table_Layout(BaseModel):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    dx = models.FloatField(default=0.0)
    dy = models.FloatField(default=0.0)
    desiredWidth = models.FloatField(default=0.0)
    desiredHeight = models.FloatField(default=0.0)
    table_id = models.OneToOneField(Table, on_delete=models.CASCADE, null=True, blank=True)
    orientation = models.CharField(max_length=200, null=True, blank=True)
    terminal = models.ForeignKey(Terminal, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'table from Terminal {self.branch.name}'
        
class DeviceTracker(BaseModel):
    deviceId = models.CharField(max_length=255, null=True, blank=True)
    terminal = models.ForeignKey(Terminal , on_delete=models.CASCADE,null=True, blank=True)

            

