from datetime import datetime
from django.contrib.auth import get_user_model

from django.db import models
from django.dispatch import receiver
from organization.models import Organization, Branch, Terminal, Table
from product.models import Product, ProductRecipie, RecipieItemSale
from root.utils import BaseModel
from django.db.models.signals import post_save
from .utils import create_journal_for_bill, update_terminal_amount, create_journal_for_complimentary, reverse_accounting
from decimal import Decimal
User = get_user_model()


class TblTaxEntry(models.Model):
    idtbltaxEntry = models.AutoField(primary_key=True)
    fiscal_year = models.CharField(max_length=20)
    bill_no = models.CharField(null=True, max_length=20)
    customer_name = models.CharField(max_length=200, null=True)
    customer_pan = models.CharField(max_length=200, null=True)
    bill_date = models.DateField(null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_printed = models.CharField(max_length=20, default="Yes")
    is_active = models.CharField(max_length=20, default="Yes")
    printed_time = models.CharField(null=True, max_length=20)
    entered_by = models.CharField(null=True, max_length=20)
    printed_by = models.CharField(null=True, max_length=20)
    is_realtime = models.CharField(max_length=20, default="Yes")
    sync_with_ird = models.CharField(max_length=20, default="Yes")
    payment_method = models.CharField(null=True, max_length=20, default="Cash")
    vat_refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_id = models.CharField(null=True, max_length=20)
    unit = models.CharField(default="-", max_length=20)

    class Meta:
        db_table = "tbltaxentry"

    def __str__(self):
        return f"{self.idtbltaxEntry}- {self.fiscal_year} - {self.bill_no}"


class TblSalesEntry(models.Model):
    tblSalesEntry = models.AutoField(primary_key=True)
    bill_date = models.CharField(null=True, max_length=20)
    bill_no = models.CharField(null=True, max_length=20)
    customer_name = models.CharField(max_length=200, null=True)
    customer_pan = models.CharField(max_length=200, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    NoTaxSales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ZeroTaxSales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    miti = models.CharField(null=True, max_length=20)
    ServicedItem = models.CharField(max_length=20, default="Goods")
    quantity = models.PositiveIntegerField(default=1)
    exemptedSales = models.CharField(default="0", max_length=20)
    export = models.CharField(default="0", max_length=20)
    exportCountry = models.CharField(default="0", max_length=20)
    exportNumber = models.CharField(default="0", max_length=20)
    exportDate = models.CharField(default="0", max_length=20)
    unit = models.CharField(default="-", max_length=20)

    class Meta:
        db_table = "tblSalesEntry"

    def __str__(self):
        return f"{self.tblSalesEntry}- {self.bill_date} - {self.bill_no}"


class TablReturnEntry(models.Model):
    idtblreturnEntry = models.AutoField(primary_key=True)
    bill_date = models.CharField(null=True, max_length=20)
    bill_no = models.CharField(null=True, max_length=20)
    customer_name = models.CharField(max_length=200, null=True)
    customer_pan = models.CharField(max_length=200, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    NoTaxSales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ZeroTaxSales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    miti = models.CharField(null=True, max_length=20)
    ServicedItem = models.CharField(max_length=20, default="Goods")
    quantity = models.PositiveIntegerField(default=1)
    reason = models.TextField(null=True, blank=True)
    exemptedSales = models.CharField(default="0", max_length=20)
    export = models.CharField(default="0", max_length=20)
    exportCountry = models.CharField(default="0", max_length=20)
    exportNumber = models.CharField(default="0", max_length=20)
    exportDate = models.CharField(default="0", max_length=20)
    unit = models.CharField(default="-", max_length=20)
    fiscal_year = models.CharField(max_length=10, null=True)

    class Meta:
        db_table = "tblreturnentry"
        unique_together = 'bill_no', 'fiscal_year'

    def __str__(self):
        return f"{self.idtblreturnEntry}- {self.bill_date} - {self.bill_no}"
    

@receiver(post_save, sender=TablReturnEntry)
def reverse_accounting_after_void(sender, instance, created, **kwargs):
    if created:
        reverse_accounting(instance)



class PaymentType(BaseModel):
    title = models.CharField(max_length=255, verbose_name="Payment Type Title")
    description = models.TextField(null=True, verbose_name="Payment Type Description")
    icon = models.ImageField(upload_to="payment-type/icons/", null=True, blank=True)
    slug = models.SlugField(unique=True, verbose_name="Payment Type Slug")

    def __str__(self):
        return self.title
    
class Order(BaseModel):
    table_no = models.IntegerField(null=True, blank=True)
    date = models.CharField(max_length= 100, null=True, blank=True)
    sale_id = models.IntegerField(null=True, blank=True)
    terminal = models.ForeignKey(Terminal, models.CASCADE, null=True, blank=True)
    start_datetime = models.CharField(max_length=255, null=True, blank=True)
    is_completed = models.BooleanField(null=True, blank=True, default=False)
    no_of_guest = models.IntegerField(null=True, blank=True)
    branch = models.ForeignKey(Branch, models.CASCADE, null=True, blank=True)
    employee = models.CharField(max_length= 255, null=True, blank=True)
    order_type = models.CharField(max_length = 255, null=True, blank=True)
    is_saved = models.BooleanField(null=True, blank=True, default=True)
    terminal_no = models.PositiveIntegerField(null=True, blank=True)
    customer = models.ForeignKey("user.Customer", on_delete=models.CASCADE, null=True, blank=True)

    
@receiver(post_save, sender=Order)
def change_table_status(sender, instance, created, **kwargs):
    if created:
        # from organization.models import Table, Terminal
        # terminal_obj = Terminal.objects.get(branch=instance.branch, terminal_no=instance.terminal_no, is_deleted=False, status=True)
        # table = Table.objects.get(table_number=instance.table_no, terminal__branch=instance.branch, terminal=terminal_obj) #This is because the terminal was expexted here but the instance of the terminal is being sent from the frontend
        # table.is_occupied = True
        # table.save()
        if instance.order_type == "Dine In":
            from organization.models import Table, Terminal
            terminal_obj = Terminal.objects.get(branch=instance.branch, terminal_no=instance.terminal_no, is_deleted=False, status=True)
            table = Table.objects.get(table_number=instance.table_no, terminal__branch=instance.branch, terminal=terminal_obj, status=True, is_deleted=False) #This is because the terminal was expexted here but the instance of the terminal is being sent from the frontend
            table.is_occupied = True
            table.save()

class OrderDetails(BaseModel):
    order = models.ForeignKey(Order, models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, models.CASCADE, null=True, blank=True)
    product_quantity = models.PositiveBigIntegerField(default=1)
    kotID = models.CharField(max_length=255, null=True, blank=True)
    botID = models.CharField(max_length=255, null=True, blank=True)
    modification = models.CharField(max_length=255, null=True, blank=True)
    ordertime = models.CharField(max_length = 255, null=True, blank=True)
    employee = models.CharField(max_length=255, null=True , blank=True)
     



class BillItem(BaseModel):
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product_title = models.CharField(
        max_length=255, verbose_name="Product Title", null=True
    )
    product_quantity = models.PositiveBigIntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_title = models.CharField(max_length=50, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_taxable = models.BooleanField(default=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    kot_id = models.IntegerField(null=True, blank=True)
    bot_id = models.IntegerField(null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)


    def __str__(self):
        return f"{self.product_title}"


@receiver(post_save, sender=BillItem)
def create_invoice_number(sender, instance, created, **kwargs):
    if created:
        sold_product = instance.product
        if ProductRecipie.objects.filter(product=sold_product).exists():
            product_recipie = ProductRecipie.objects.get(product=sold_product)
            for i in product_recipie.items:
                qty = int(i['quantity'])
                sold_qty = qty * int(instance.product_quantity)
                RecipieItemSale.objects.create(product_id=i['id'], quantity=sold_qty, branch=instance.branch)

''' Signal for Decresing Product Stock after Sold '''
# from product.models import BranchStockTracking
# from datetime import date
# def reconcile_product(sender, instance, **kwargs):
#     import pdb
#     pdb.set_trace()
    # try:
    #     branch = instance.bill_set.first().branch
    #     bst = BranchStockTracking.objects.get(product=instance.product,branch=branch, date=date.today())
    #     bst.sold +=instance.product_quantity
    #     bst.save()
    # except BranchStockTracking.DoesNotExist:
    #     BranchStockTracking.objects.create(product=instance.product,branch=branch, date=date.today(), sold=instance.product_quantity)
    

# m2m_changed.connect(reconcile_product, sender=BillItem.bill_set)

""" **************************************** """

class ConflictBillNumber(BaseModel):
    invoice_number = models.CharField(max_length=50)

    def __str__(self):
        return self.invoice_number


class Bill(BaseModel):
    fiscal_year = models.CharField(max_length=20)
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    agent_name = models.CharField(max_length=255, null=True)
    terminal = models.CharField(max_length=10, default="1")
    customer_name = models.CharField(max_length=255, null=True, blank=True)
    customer_address = models.CharField(max_length=255, null=True, blank=True)
    customer_tax_number = models.CharField(max_length=255, null=True, blank=True)
    customer = models.ForeignKey("user.Customer", on_delete=models.SET_NULL, null=True)
    transaction_date_time = models.DateTimeField(auto_now_add=True)
    transaction_date = models.DateField(auto_now_add=True)

    transaction_miti = models.CharField(max_length=255, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    invoice_number = models.CharField(max_length=50, null=True, blank=True)
    amount_in_words = models.TextField(null=True, blank=True)
    payment_mode = models.CharField(
        max_length=255, default="Cash", blank=True, null=True
    )

    bill_items = models.ManyToManyField(BillItem, blank=False)
    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.SET_NULL, null=True
    )
    branch = models.ForeignKey(
        "organization.Branch", on_delete=models.SET_NULL, null=True
    )
    print_count = models.PositiveIntegerField(default=1)
    bill_count_number = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    order = models.OneToOneField(Order, models.CASCADE, null=True, blank=True)
    is_end_day= models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.customer_name}-{self.transaction_date}- {self.grand_total}"
    
    class Meta:
        unique_together = 'invoice_number', 'fiscal_year', 'branch'


@receiver(post_save, sender=Bill)
def create_invoice_number(sender, instance, created, **kwargs):
    current_fiscal_year = Organization.objects.last().current_fiscal_year

    if created and instance.payment_mode.lower().strip() == "complimentary":
        instance.tax_amount = 0
        instance.taxable_amount = 0
        instance.discount_amount = 0
        instance.save()
        try:
            create_journal_for_complimentary(instance)
        except Exception as e:
            pass

    if created and not instance.payment_mode.lower().strip() == "complimentary":
        if not instance.payment_mode.lower().strip() == "split":
            try:
                create_journal_for_bill(instance)
            except Exception as e:
                print(e)

        branch = instance.branch.branch_code
        terminal = instance.terminal

        update_terminal_amount(terminal=terminal, branch=branch, total=instance.grand_total-Decimal(instance.tax_amount))

        bill_number = 0
        invoice_number = ""
        instance.fiscal_year = current_fiscal_year
        if terminal == 1:
            last_bill = Bill.objects.filter(terminal=terminal, fiscal_year = current_fiscal_year, branch=instance.branch).order_by('-bill_count_number').first()
            if not last_bill:
                bill_number = 1
            else:
                bill_number = last_bill.bill_count_number + 1

            if branch is not None:
                invoice_number = f"{branch}-{terminal}-{bill_number}"
            else:
                invoice_number = f"{terminal}-{bill_number}"
            
            instance.invoice_number = invoice_number
            instance.bill_count_number=bill_number
        else:
            invoice_number = instance.invoice_number
        a = TblTaxEntry(
            fiscal_year=current_fiscal_year,
            bill_no=invoice_number,
            customer_name=instance.customer_name,
            customer_pan=instance.customer_tax_number,
            bill_date=instance.transaction_date,
            amount=instance.grand_total,
            taxable_amount=instance.taxable_amount,
            tax_amount=instance.tax_amount,
            is_printed="Yes",
            printed_time=str(datetime.now().time().strftime(("%I:%M %p"))),
            entered_by=instance.agent_name,
            printed_by=instance.agent_name,
            is_realtime="Yes",
            sync_with_ird="Yes",
            payment_method=instance.payment_mode,
            vat_refund_amount=0.0,
            transaction_id="-",
        )

        b = TblSalesEntry(
            bill_date=instance.transaction_date,
            customer_name=instance.customer_name,
            customer_pan=instance.customer_tax_number,
            amount=instance.grand_total,
            NoTaxSales=0.0,
            ZeroTaxSales=0.0,
            taxable_amount=instance.taxable_amount,
            tax_amount=instance.tax_amount,
            miti=instance.transaction_miti,
            ServicedItem="Goods",
            quantity=1.0,
            bill_no=invoice_number,
        )

        if instance.tax_amount == 0:
            a.exemptedSales = instance.sub_total
            b.exemptedSales = instance.sub_total

        b.save()

        a.save()
        instance.save()


class BillItemVoid(BaseModel):
    count = models.IntegerField(null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE,null=True, blank=True)
    isBefore = models.BooleanField(default=True) #This defines if the void is done beofre the bill or after thebill
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    bill_item = models.ForeignKey(BillItem, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    reason = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return f'{self.product.title} void by quantity -> {self.quantity}'


class BillPayment(BaseModel):
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT)
    payment_mode = models.CharField(max_length=100)
    rrn = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    def __str__(self):
        return self.payment_mode
        
class VoidBillTracker(BaseModel):
    prev_bill = models.CharField(max_length=255, null=True, blank=True)
    new_bill = models.CharField(max_length=255, null=True, blank=True)
    prev_bill_id = models.IntegerField(null=True, blank=True)
    new_bill_id = models.IntegerField(null=True, blank=True)
    bill_new = models.ForeignKey(Bill, models.CASCADE, null=True, blank=True, related_name='bill_new_trackers')
    bill_prev= models.ForeignKey(Bill, models.CASCADE, null=True, blank=True, related_name='bill_prev_trackers')
    
    
class MobilePaymentType(BaseModel):
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    icon = models.ImageField(upload_to="mobile-payment-type/icons/", null=True, blank=True)
    qr = models.ImageField(upload_to="mobile-payment-type/qr/", null=True, blank=True)

    def __str__(self):
        return self.name 
    
    def get_qr(self):
        if self.qr :
            return self.qr.url
        else:
            return None
        
    def get_icon(self):
        if self.icon :
            return self.icon.url
        else:
            return None
        
class MobilePaymentSummary(BaseModel):
     type = models.ForeignKey(MobilePaymentType, models.CASCADE)
     value = models.DecimalField(max_digits=9, decimal_places=2, default=0)
     bill = models.ForeignKey(Bill, models.CASCADE, null=True, blank=True)


