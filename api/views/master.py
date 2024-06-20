from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from user.models import Customer
from ..serializers.master import CustomTokenPairSerializer, CustomerSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from organization.models import Terminal, Branch
from rest_framework.response import Response
from collections import defaultdict
import jwt
from organization.models import DeviceTracker
from rest_framework import status

User = get_user_model()

class Custom400Exception(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Custom error message for status code 400'

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenPairSerializer


class CustomerAPI(ModelViewSet):
    serializer_class = CustomerSerializer
    model = Customer
    queryset = Customer.objects.active()
    pagination_class = None

# class TerminalUpdateView(APIView):
#     def post(self, request, *args, **kwargs):
#         data = request.data
        
#         switched_to_terminal = data['terminal']
#         branch = data['branch']

#         try:
#             terminal_obj = Terminal.objects.get(terminal_no=int(switched_to_terminal), branch=Branch.objects.get(pk=int(branch)), status=True, is_deleted=False)
#         except Exception as e:
#             raise APIException("Terminal with that id does not exist")
        
#         if terminal_obj.is_active == True:
#             terminal_obj.is_active = False
#             terminal_obj.save()
#         else:
#             terminal_obj.is_active = True
#             terminal_obj.save()
#         data = {
#             'is_active' : terminal_obj.is_active
#         }
#         return Response(data)
        
        
class TerminalUpdateView(APIView):
    def post(self, request, *args, **kwargs):
        jwt_token = request.META.get("HTTP_AUTHORIZATION")
        jwt_token = jwt_token.split()[1]
        try:
            token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
            # You can access other claims as needed

            # Assuming "branch" is one of the claims, access it
            branch = token_data.get("branch")
            agent = token_data.get("name")
            deviceId = token_data.get("deviceId")


            # Print the branch
            print("Branch:", branch)
            print("Agent:", agent)
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.DecodeError:
            print("Token is invalid.")
        data = request.data
        
        switched_to_terminal = data['terminal']
        branch = data['branch']

        try:
            terminal_obj = Terminal.objects.get(terminal_no=int(switched_to_terminal), branch=Branch.objects.get(pk=int(branch)), status=True, is_deleted=False)
        except Exception as e:
            raise APIException("Terminal with that id does not exist")
        
        try:
            devicetracker_obj = DeviceTracker.objects.get(terminal = terminal_obj)
        except Exception as e:
            raise Custom400Exception("No device logged in with the given terminal")
        
        if devicetracker_obj.status == True:
            devicetracker_obj.status = False
            devicetracker_obj.save()
        else:
            devicetracker_obj.status = True
            devicetracker_obj.save()
        data = {
            'is_active' : devicetracker_obj.status
        }
        return Response(data)
        
        
from rest_framework import generics
from bill.models import Bill, BillPayment
from api.serializers.give_all_bills import BillSerializer,PaymentModeSerializer
from rest_framework import status
from decimal import Decimal
import jwt
from organization.models import Branch, Terminal
from django.db.models import Sum
from product.models import Product

class MasterBillDetailView(generics.ListAPIView):
    serializer_class = BillSerializer  # Assuming the URL parameter is 'id'

    def get_branch(self):
        jwt_token = self.request.META.get("HTTP_AUTHORIZATION")
        jwt_token = jwt_token.split()[1]
        try:
            token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
            user_id = token_data.get("user_id")
            username = token_data.get("username")
            role = token_data.get("role")
            # You can access other claims as needed

            # Assuming "branch" is one of the claims, access it
            branch = token_data.get("branch")

            # Print the branch
            print("Branch:", branch)
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.DecodeError:
            print("Token is invalid.")
        print(branch)
        branch = Branch.objects.get(id=branch)
        return branch

    def list(self, request, *args, **kwargs):

        branch = self.get_branch()
        terminals = Terminal.objects.filter(is_deleted=False, branch=branch)
        response_list = []
        total_bills = 0
        total_bill_items = 0
        total_beverage_items = 0
        total_food_items = 0
        total_others_items = 0

        
        total = {
                'food_total': Decimal(0.0),
                'beverage_total': Decimal(0.0),
                'others_total': Decimal(0.0),
                'discount_amount': Decimal(0.0),
                'taxable_amount': Decimal(0.0),
                'tax_amount': Decimal(0.0),
                'grand_total': Decimal(0.0),
                'service_charge': Decimal(0.0),
                'CASH': Decimal(0.0),
                'CREDIT': Decimal(0.0),
                'COMPLIMENTARY': Decimal(0.0),
                'CREDIT CARD': Decimal(0.0),
                'MOBILE PAYMENT': Decimal(0.0),
            }
            
        branch_queryset = Bill.objects.filter(is_end_day=False, branch=branch)

        bill_items_total = self.calculate_bill_items_total(branch_queryset)

        for terminal in terminals:
        # queryset, queryset1 = self.get_queryset()


            queryset = Bill.objects.filter(is_end_day=False, branch=branch, terminal=(terminal.terminal_no))
            queryset1 = Bill.objects.filter(is_end_day=False, status=True, branch=branch, terminal=str(terminal.terminal_no))

            no_of_bills = queryset1.count()

            total_bills += no_of_bills
            # Get the IDs of bills with is_end_day=False
            bill_ids = queryset1.values_list('id', flat=True)

            possible_payment_modes = ["CASH", "CREDIT", "COMPLIMENTARY", "CREDIT CARD", "MOBILE PAYMENT"]

            # Initialize a dictionary to store the payment mode totals
            payment_mode_totals = {mode: Decimal(0.0) for mode in possible_payment_modes}

            # Get the total amount for each payment mode
            bill_payments = BillPayment.objects.filter(bill_id__in=bill_ids)

            for payment in bill_payments:
                # Update the total for each payment mode
                payment_mode_totals[payment.payment_mode] += payment.amount

            # Create a list of payment mode data
            payment_mode_data = [
                {"payment_mode": mode, "total_amount": payment_mode_totals[mode]}
                for mode in possible_payment_modes
            ]


            # Calculate the invoice_number and grand_total for void bills
            # void_bills_data = queryset.filter(status=False).values('invoice_number', 'grand_total')

            # Serialize the payment_mode_data
            payment_mode_serializer = PaymentModeSerializer(payment_mode_data, many=True)
            first_bill = None
            last_bill = None

            for bill in queryset:
                if not first_bill and bill.invoice_number:
                    first_bill = bill
                if bill.invoice_number:
                    last_bill = bill

            # If no bill with a non-null invoice number is found for the last bill, use the last bill
            if last_bill is None:
                last_bill = queryset.last()

            starting_from_invoice = first_bill.invoice_number if first_bill else None
            ending_from_invoice = last_bill.invoice_number if last_bill else None

            
            sub_total_sum = Decimal(0)
            discount_amount_sum = Decimal(0)
            taxable_amount_sum = Decimal(0)
            tax_amount_sum = Decimal(0)
            grand_total_sum = Decimal(0)
            service_charge_sum = Decimal(0)

            for bill in queryset1:
                if bill.payment_mode != 'COMPLIMENTARY':
                    sub_total_sum += bill.sub_total
                    discount_amount_sum += bill.discount_amount
                    taxable_amount_sum += bill.taxable_amount
                    tax_amount_sum += bill.tax_amount
                    grand_total_sum += bill.grand_total
                    service_charge_sum += bill.service_charge
            # bill_items_total = self.calculate_bill_items_total(queryset)

            serializer = self.get_serializer(queryset, many=True)

            # Create a response dictionary with "bill_data" key
            response_data = {
                # "bill_data": serializer.data,
                'terminal': terminal.terminal_no,
                "payment_modes": payment_mode_serializer.data,
                "Starting_from":starting_from_invoice,
                "Ending_from":ending_from_invoice,
                # "bill_items_total": bill_items_total,
            }


            # Calculate and add the sales data to the response
            sales_data = {
                'discount_amount': discount_amount_sum,
                'taxable_amount': taxable_amount_sum,
                'tax_amount': tax_amount_sum,
                'grand_total': grand_total_sum,
                'service_charge': service_charge_sum,
            }
            response_data['Sales'] = sales_data

            # Add void bills data to the response
            # response_data['void_bills'] = void_bills_data
            
            food_queryset = queryset.filter(
                is_end_day=False,
                bill_items__product_title__in=Product.objects.filter(type__title="FOOD").values_list('title', flat=True)
            ) 

            # print(f"food_queryset {food_queryset}")
            food_total = food_queryset.aggregate(food_total=Sum('bill_items__amount'))['food_total'] or Decimal(0.0)
            food_quantity = food_queryset.aggregate(food_quantity=Sum('bill_items__product_quantity'))['food_quantity'] or Decimal(0.0)

            total_food_items += food_quantity

            # Get the total amount of beverage products
            beverage_queryset = queryset.filter(
                is_end_day=False,
                bill_items__product_title__in=Product.objects.filter(type__title="BEVERAGE").values_list('title', flat=True)
            )

            beverage_total = beverage_queryset.aggregate(beverage_total=Sum('bill_items__amount'))['beverage_total'] or Decimal(0.0)

            beverage_quantity = beverage_queryset.aggregate(beverage_quantity=Sum('bill_items__product_quantity'))['beverage_quantity'] or Decimal(0.0)
            total_beverage_items += beverage_quantity

            others_queryset = queryset.filter(
                is_end_day=False,
                bill_items__product_title__in=Product.objects.filter(type__title="OTHERS").values_list('title', flat=True)
            )

            others_total = others_queryset.aggregate(others_total=Sum('bill_items__amount'))['others_total'] or Decimal(0.0)

            others_quantity = others_queryset.aggregate(others_quantity=Sum('bill_items__product_quantity'))['others_quantity'] or Decimal(0.0)
            total_others_items += others_quantity


            # food_total = queryset.filter(
            #     is_end_day=False,
            #     bill_items__product_title__in=Product.objects.filter(type__title="FOOD").values_list('title', flat=True)
            # ) .aggregate(food_total=Sum('bill_items__amount'))['food_total'] or Decimal(0.0)


            # # Get the total amount of beverage products
            # beverage_total = queryset.filter(
            #     is_end_day=False,
            #     bill_items__product_title__in=Product.objects.filter(type__title="BEVERAGE").values_list('title', flat=True)
            # ).aggregate(beverage_total=Sum('bill_items__amount'))['beverage_total'] or Decimal(0.0)

            # # Get the total amount of other products
            # others_total = queryset.filter(
            #     is_end_day=False,
            #     bill_items__product_title__in=Product.objects.filter(type__title="OTHERS").values_list('title', flat=True)
            # ).aggregate(others_total=Sum('bill_items__amount'))['others_total'] or Decimal(0.0)
            
            total_items = queryset.filter(
                is_end_day=False
            ).aggregate(items_total=Sum('bill_items__product_quantity'))['items_total'] or 0

            total_bill_items += total_items

            response_data['food_total'] = food_total
            response_data['beverage_total'] = beverage_total
            response_data['others_total'] = others_total
            response_data['no_of_bills'] = no_of_bills


            total['food_total'] += food_total
            total['beverage_total'] += beverage_total
            total['others_total'] += others_total
            total['discount_amount'] += discount_amount_sum
            total['taxable_amount'] += taxable_amount_sum
            total['tax_amount'] += tax_amount_sum
            total['grand_total'] += grand_total_sum
            total['service_charge'] += service_charge_sum
            total['no_of_bills'] = total_bills

            for payment_data in payment_mode_data:
                total['CASH'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CASH' else Decimal(0.0)
                total['CREDIT'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CREDIT' else Decimal(0.0)
                total['COMPLIMENTARY'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CREDIT CARD' else Decimal(0.0)
                total['CREDIT CARD'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'COMPLIMENTARY' else Decimal(0.0)
                total['MOBILE PAYMENT'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'MOBILE PAYMENT' else Decimal(0.0)


            response_list.append(response_data)

        actual_response = {
            "data": response_list, 
            "totals": total,
            "total_items": int(total_bill_items),
            "total_food_items": int(total_food_items),
            "total_beverage_items": int(total_beverage_items),
            "total_others_items": int(total_others_items),
            "foods": bill_items_total.get('FOOD', []),
            "beverages": bill_items_total.get('BEVERAGE', []),
            "others": bill_items_total.get('OTHERS', []) ,

        }

        return Response(actual_response, status=status.HTTP_200_OK)
        
    # def calculate_bill_items_total(self, queryset):
    #     bill_items_total = defaultdict(list)

    #     # Create a dictionary to store product quantities
    #     product_quantities = defaultdict(lambda: {'quantity': 0, 'rate': 0, 'product_title': ''})

    #     for bill in queryset:
    #         for bill_item in bill.bill_items.all():
    #             product_id = bill_item.product.id
    #             quantity = bill_item.product_quantity
    #             rate = bill_item.rate
    #             product_title = bill_item.product_title
    #             product_category = bill_item.product.type.title  # Assuming 'type' is the related field to ProductCategory

    #             key = (product_id, rate)
    #             if key in product_quantities:
    #                 product_quantities[key]['quantity'] += quantity
    #             else:
    #                 product_quantities[key] = {
    #                     'quantity': quantity,
    #                     'rate': rate,
    #                     'product_title': product_title,
    #                 }

    #             # Append the bill item to the corresponding category list
    #         # for product_id, item_data in product_quantities.items():
    #             bill_items_total[product_category].append({
    #                 'product_title': product_title,
    #                 'product_quantity': quantity,
    #                 'rate': rate,
    #                 'amount': quantity * rate,
    #             })

    #     # Convert defaultdict to regular dict for JSON serialization
    #     bill_items_total = dict(bill_items_total)

    #     return bill_items_total
    
    def calculate_bill_items_total(self, queryset):
        bill_items_total = defaultdict(list)

        # Create a dictionary to store product quantities
        product_quantities = defaultdict(lambda: {'quantity': 0, 'rate': 0, 'product_title': ''})

        for bill in queryset:
            for bill_item in bill.bill_items.all():
                product_id = bill_item.product.id
                quantity = bill_item.product_quantity
                rate = bill_item.rate
                product_title = bill_item.product_title
                product_category = bill_item.product.type.title  # Assuming 'type' is the related field to ProductCategory

                key = (product_id, rate)
                if key in product_quantities:
                    product_quantities[key]['quantity'] += quantity
                else:
                    product_quantities[key] = {
                        'quantity': quantity,
                        'rate': rate,
                        'product_title': product_title,
                        'type': product_category
                    }

                # Append the bill item to the corresponding category list

        for product_id, item_data in product_quantities.items():
                bill_items_total[item_data['type']].append({
                    'product_title': item_data['product_title'],
                    'product_quantity': item_data['quantity'],
                    'rate': item_data['rate'],
                    'amount': item_data['quantity'] * item_data['rate'],
                })

        # Convert defaultdict to regular dict for JSON serialization
        bill_items_total = dict(bill_items_total)

        return bill_items_total