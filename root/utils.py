import six

import shortuuid
from django.db import models
from django.http import JsonResponse
from django.utils.text import slugify
from root.constants import COUNTRIES


class Manger(models.Manager):
    def is_not_deleted(self):
        return self.filter(is_deleted=False)

    def active(self):
        return self.filter(is_deleted=False, status=True)


class BaseModel(models.Model):
    """
    This is the base model for all the models.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    sorting_order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    objects = Manger()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def catch_exception(self, slug_item, *args, **kwargs):
        self.slug = slugify(slug_item) + "-" + str(six.text_type(shortuuid.uuid()))
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):

        if hasattr(self, "slug"):
            if hasattr(self, "name"):
                if self.name:
                    try:
                        self.slug = slugify(self.name)
                        super().save(*args, **kwargs)
                    except Exception:
                        self.catch_exception(self, self.name, *args, **kwargs)

            elif hasattr(self, "title"):
                if self.title:
                    try:
                        self.slug = slugify(self.title)
                        # super().save(*args, **kwargs)
                    except Exception:
                        self.catch_exception(self, self.title, *args, **kwargs)

        super().save(*args, **kwargs)


class CountryField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 2)
        kwargs.setdefault("choices", COUNTRIES)
        kwargs.setdefault("default", "NP")

        super(CountryField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"


class UserMixin(BaseModel):
    GENDER_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Others"),
    )
    user = models.OneToOneField(
        "user.User",
        on_delete=models.CASCADE,
    )
    phone_number = models.CharField(max_length=255, null=False, blank=False)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    dob = models.DateField(null=True, blank=True)

    country = CountryField()
    state = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    user_image = models.ImageField(upload_to="user/images/", null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user.full_name} - {self.phone_number}"


class DeleteMixin:
    def remove_from_DB(self, request):
        try:
            object_id = request.GET.get("pk", None)
            object = self.model.objects.get(id=object_id)
            object.is_deleted = True
            object.save()

            return True
        except Exception as e:
            print(e)
            return str(e)

    def get(self, request):
        status = self.remove_from_DB(request)
        return JsonResponse({"deleted": status})


class SingletonModel:
    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        return super().save(**kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


def remove_from_DB(self, request):
    try:
        object_id = request.GET.get("pk", None)
        self.model.objects.get(id=object_id).delete()
        return True
    except:
        return False
        

def format_order_json(orders):

    details = []

    from organization.models import Organization
    from bill.models import BillItemVoid

    for order in orders:
        
        sale_dict = {
                "id": None,
                "bill_items": [ ],
                "payment_split": [],
                "order": {},
                "isCompleted": False,
                "isSaved": True,
                "organization": Organization.objects.first().org_name,
                "isVoid": False,
                "tableNo": str(order.table_no),
                "noOfGuest": order.no_of_guest,
                "is_cancelled": False,
                "startdatetime": order.start_datetime,
                "server_id": order.id,
                "is_synced": False,
                "fiscal_year": Organization.objects.first().current_fiscal_year,
                "agent_name": None,
                "terminal": str(order.terminal_no),
                "customer_name": order.customer.name if order.customer else None,
                "customer_address": order.customer.address if order.customer else None,
                "customer_tax_number": order.customer.tax_number if order.customer else None ,
                "transaction_date_time": order.start_datetime,
                "transaction_date": order.date,
                "transaction_miti": order.date,
                "sub_total": 0.0,
                "discount_amount": 0.0,
                "taxable_amount": 0.0,
                "tax_amount": 0.0,
                "grand_total": 0.0,
                "service_charge": 0.0,
                "invoice_number": None,
                "amount_in_words": None,
                "payment_mode": None,
                "print_count": 0,
                "bill_count_number": 0,
                "is_end_day": False,
                "agent": None,
                "customer": None,
                "branch": order.branch.id,
                "void_items": [],
                "order_type":order.order_type


            }
        order_dict = {
                "id": order.id,
                "tableNumber": str(order.table_no),
                "date": order.date,
                "sale_id": order.sale_id,
                "terminal": order.terminal_no,
                "start_datetime": order.start_datetime,
                "is_completed": order.is_completed,
                "no_of_guest": order.no_of_guest,
                "branch": order.branch.id,
                "employee": order.employee,
                "order_type": order.order_type,
                "is_saved": order.is_saved,
                "products": [

                ],
                "bot": None,
                "kot": 1
            }

        for order_details in order.orderdetails_set.all():
            
                    if (order_details.product and order_details.product.image):
                    
                        path = order_details.product.image.path 
                        index = path.find('/uploads')
                
                        # Check if '/uploads' is found
                        if index != -1:
                            # Extract the part after '/uploads', including '/uploads'
                            relative_path = path[index:]
                        else:
                            # If '/uploads' is not found, use the entire path
                            relative_path = path
                    
                    else:
                        relative_path =  None
                    products_dict = {
                        "id": order_details.id,
                        "title": order_details.product.title if order_details.product else None,
                        "slug": order_details.product.slug if order_details.product else None,
                        "description": order_details.product.description if (order_details.product and order_details.product.description) else None,
                        "image": relative_path,
                        "unit": order_details.product.unit if (order_details.product and order_details.product.unit) else None,
                        "price": order_details.product.price if (order_details.product and order_details.product.price) else None,
                        "isTaxable": order_details.product.is_taxable if (order_details.product and order_details.product.is_taxable) else None,
                        "discount_exempt": order_details.product.discount_exempt if (order_details.product and order_details.product.discount_exempt) else None,
                        "productId": order_details.product.id if (order_details.product) else None,
                        "saleId": order.sale_id,
                        "product_quantity": order_details.product_quantity,
                        "kotID": int(order_details.kotID) if order_details.kotID is not None else None,
                        "botID": int(order_details.botID) if order_details.botID is not None else None,
                        "modification": order_details.modification,
                        "ordertime": order_details.ordertime,
                        "employee": order_details.employee,
                        "order": order.id if order is not None else None,
                        "product": order_details.product.id if order_details.product else None,
                        "category": order_details.product.type.title if order_details.product else None,
                        "group": order_details.product.group if order_details.product else None
                    }

                    order_dict["products"].append(products_dict)
                    
        billitemvoid = BillItemVoid.objects.filter(order=order)
        for itemvoid in billitemvoid:

            itemvoid_dict = {
                "count" : itemvoid.count,
                "product" : itemvoid.product.id,
                "order" : itemvoid.order.id,
                "quantity" : itemvoid.quantity,
                "isBefore" : itemvoid.isBefore,
                "reason" : itemvoid.reason,
            }
            sale_dict['void_items'].append(itemvoid_dict)
            # saleId = models.IntegerField(null=True, blank=True)
            # count = models.IntegerField(null=True, blank=True)
            # product = models.ForeignKey(Product, on_delete=models.CASCADE)
            # bill_item = models.ForeignKey(BillItem, on_delete=models.CASCADE,null=True, blank=True)
            # order_item = models.ForeignKey(OrderDetails, on_delete=models.CASCADE,null=True, blank=True)
            # order = models.ForeignKey(Order, on_delete=models.CASCADE,null=True, blank=True)
            # quantity = models.IntegerField()
            # isBefore = models.BooleanField(default=True) #This defines if the void is done beofre the bill or after thebill

        


        sale_dict["order"] = order_dict
        details.append(sale_dict)
    print("This is the details", details)

    return details
    
import base64
def get_image_bytes(obj):
    if obj.thumbnail:
        try:
            with open(obj.thumbnail.path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
                decoded_string = encoded_string.decode('utf-8')
                return decoded_string
        except Exception as e:
            print(f"Error encoding the image for {obj}")
    return None

