from rest_framework import generics
from bill.models import Bill, BillPayment
from api.serializers.give_all_bills import BillSerializer,PaymentModeSerializer
from rest_framework import status
from decimal import Decimal
import jwt
from organization.models import Branch, Terminal
from django.db.models import Sum
from product.models import Product
from rest_framework.response import Response
from datetime import datetime
from rest_framework.views import APIView
import calendar



class SalesBranchView(generics.ListAPIView):
    serializer_class = BillSerializer  # Assuming the URL parameter is 'id'

    def list(self, request, *args, **kwargs):

        branches = Branch.objects.filter(is_deleted=False, status=True)

        current_date_now = datetime.now()

        current_date_str = current_date_now.strftime('%Y-%m-%d')

        from_date_str = request.GET.get('fromDate')

        to_date_str = request.GET.get('toDate')

        # Convert the fromDate parameter to a datetime object
        # if from_date_str:
        #     current_date = from_date_str
        # else:
        #     current_date=current_date_str
        if from_date_str and to_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            except ValueError:
                # Handle the error if the date format is incorrect
                return Response("Invalid date format, should be YYYY-MM-DD", status=status.HTTP_400_BAD_REQUEST)

        else:
            # current_date=current_date_str
            from_date = current_date_now
            to_date =current_date_now


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
                'Sales': {
                    'discount_amount': Decimal(0.0),
                    'taxable_amount': Decimal(0.0),
                    'tax_amount': Decimal(0.0),
                    'grand_total': Decimal(0.0),
                    'service_charge': Decimal(0.0),
                    'net_sales': Decimal(0.0),
                },
                'payment_modes' : [
                {
                    "payment_mode": "CASH",
                    "total_amount": Decimal(0.0)
                },
                {
                    "payment_mode": "CREDIT",
                    "total_amount": Decimal(0.0)
                },
                {
                    "payment_mode": "COMPLIMENTARY",
                    "total_amount": Decimal(0.0)
                },
                {
                    "payment_mode": "CREDIT CARD",
                    "total_amount": Decimal(0.0)
                },
                {
                    "payment_mode": "MOBILE PAYMENT",
                    "total_amount": Decimal(0.0)
                }
                ]
            }
        


        for branch in branches:
        # queryset, queryset1 = self.get_queryset()


            # queryset = Bill.objects.filter(transaction_date=current_date, branch=branch)
            # queryset1 = Bill.objects.filter(transaction_date=current_date, status=True, branch=branch)
            queryset = Bill.objects.filter(transaction_date__range=(from_date, to_date), branch=branch, is_end_day=False)
            queryset1 = Bill.objects.filter(transaction_date__range=(from_date, to_date), status=True, branch=branch, is_end_day=False)

            no_of_bills = queryset1.count()

            total_bills += no_of_bills
            # Get the IDs of bills with transaction_date=current_date
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
            net_sales = sub_total_sum-discount_amount_sum
            bill_items_total_branch = self.calculate_bill_items_total_branch(queryset)

            serializer = self.get_serializer(queryset, many=True)

            # Create a response dictionary with "bill_data" key
            response_data = {
                # "bill_data": serializer.data,
                'branch': branch.name,
                "payment_modes": payment_mode_serializer.data,
                # "Starting_from":starting_from_invoice,
                # "Ending_from":ending_from_invoice,
                "bill_items_total": bill_items_total_branch,
            }


            # Calculate and add the sales data to the response
            sales_data = {
                'discount_amount': discount_amount_sum,
                'taxable_amount': taxable_amount_sum,
                'tax_amount': tax_amount_sum,
                'grand_total': grand_total_sum,
                'service_charge': service_charge_sum,
                'net_sales': net_sales
            }
            response_data['Sales'] = sales_data

            # Add void bills data to the response
            # response_data['void_bills'] = void_bills_data
            
            food_queryset = queryset1.filter(
                bill_items__product_title__in=Product.objects.filter(type__title="FOOD").values_list('title', flat=True)
            ) 

            # print(f"food_queryset {food_queryset}")
            food_total = food_queryset.aggregate(food_total=Sum('bill_items__amount'))['food_total'] or Decimal(0.0)
            food_quantity = food_queryset.aggregate(food_quantity=Sum('bill_items__product_quantity'))['food_quantity'] or Decimal(0.0)

            total_food_items += food_quantity

            # Get the total amount of beverage products
            beverage_queryset = queryset1.filter(
                bill_items__product_title__in=Product.objects.filter(type__title="BEVERAGE").values_list('title', flat=True)
            )

            beverage_total = beverage_queryset.aggregate(beverage_total=Sum('bill_items__amount'))['beverage_total'] or Decimal(0.0)

            beverage_quantity = beverage_queryset.aggregate(beverage_quantity=Sum('bill_items__product_quantity'))['beverage_quantity'] or Decimal(0.0)
            total_beverage_items += beverage_quantity

            others_queryset = queryset1.filter(
                bill_items__product_title__in=Product.objects.filter(type__title="OTHERS").values_list('title', flat=True)
            )

            others_total = others_queryset.aggregate(others_total=Sum('bill_items__amount'))['others_total'] or Decimal(0.0)

            others_quantity = others_queryset.aggregate(others_quantity=Sum('bill_items__product_quantity'))['others_quantity'] or Decimal(0.0)
            total_others_items += others_quantity
            
            total_items = queryset1.filter(
            ).aggregate(items_total=Sum('bill_items__product_quantity'))['items_total'] or 0

            total_bill_items += total_items

            response_data['food_total'] = food_total
            response_data['beverage_total'] = beverage_total
            response_data['others_total'] = others_total
            # response_data['no_of_bills'] = no_of_bills    


            total['food_total'] += food_total
            total['beverage_total'] += beverage_total
            total['others_total'] += others_total
            total['Sales']['discount_amount'] += discount_amount_sum
            total['Sales']['taxable_amount'] += taxable_amount_sum
            total['Sales']['tax_amount'] += tax_amount_sum
            total['Sales']['grand_total'] += grand_total_sum
            total['Sales']['service_charge'] += service_charge_sum
            total['Sales']['net_sales'] += net_sales
            # total['no_of_bills'] = total_bills

            # for payment_data in payment_mode_data:
            #     total['CASH'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CASH' else Decimal(0.0)
            #     total['CREDIT'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CREDIT' else Decimal(0.0)
            #     total['COMPLIMENTARY'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CREDIT CARD' else Decimal(0.0)
            #     total['CREDIT CARD'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'COMPLIMENTARY' else Decimal(0.0)
            #     total['MOBILE PAYMENT'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'MOBILE PAYMENT' else Decimal(0.0)
            for payment_data in payment_mode_data:
                total['payment_modes'][0]['total_amount'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CASH' else Decimal(0.0)
                total['payment_modes'][1]['total_amount'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CREDIT' else Decimal(0.0)
                total['payment_modes'][2]['total_amount'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'COMPLIMENTARY' else Decimal(0.0)
                total['payment_modes'][3]['total_amount'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'CREDIT CARD' else Decimal(0.0)
                total['payment_modes'][4]['total_amount'] += payment_data['total_amount'] if payment_data['payment_mode'] == 'MOBILE PAYMENT' else Decimal(0.0)


            response_list.append(response_data)

        actual_response = {
            "data": response_list, 
            "totals": total,
            # "total_items": int(total_bill_items),
            # "total_food_items": int(total_food_items),
            # "total_beverage_items": int(total_beverage_items),
            # "total_others_items": int(total_others_items),
            # "foods": bill_items_total.get('FOOD', []),
            # "beverages": bill_items_total.get('BEVERAGE', []),
            # "others": bill_items_total.get('OTHERS', []) ,

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
    #                     'type': product_category
    #                 }

    #             # Append the bill item to the corresponding category list

    #     for product_id, item_data in product_quantities.items():
    #             bill_items_total[item_data['type']].append({
    #                 'product_title': item_data['product_title'],
    #                 'product_quantity': item_data['quantity'],
    #                 'rate': item_data['rate'],
    #                 'amount': item_data['quantity'] * item_data['rate'],
    #             })

    #     # Convert defaultdict to regular dict for JSON serialization
    #     bill_items_total = dict(bill_items_total)

    #     return bill_items_total
    
    def calculate_bill_items_total_branch(self, queryset):
        bill_items_total_branch = defaultdict(list)

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


        for product_id, item_data in product_quantities.items():
                bill_items_total_branch[item_data['type']].append({
                    'product_title': item_data['product_title'],
                    'product_quantity': item_data['quantity'],
                    'rate': item_data['rate'],
                    'amount': item_data['quantity'] * item_data['rate'],
                })

        # Convert defaultdict to regular dict for JSON serialization
        bill_items_total_branch = dict(bill_items_total_branch)

        return bill_items_total_branch
    
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
    
from collections import defaultdict

class BranchWiseMonthSale(APIView):
    def get(self, request, *args, **kwargs):
        from_date_str = request.GET.get('CurrentYear')
        current_year = datetime.strptime(from_date_str, '%Y').year

        print(current_year)
        
        branches = Branch.objects.filter(is_deleted=False, status=True)
        
        current_date = datetime.now()
        branch_data_sent = []
        for branch in branches:
            branch_data = {
                "slug": branch.name,
                "month_list" : []
            }

            queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year=current_year, is_end_day=False)

            # print(branch.name)
            # print(queryset1)
            # print(f'current month is {current_date.month}')
            # for queryset in queryset1:
            #     print(queryset.invoice_number)    
            #     print(queryset.transaction_date_time.month)

            bills_monthly = defaultdict(list)

            for month in range(1, 13):
                month_name = calendar.month_name[month]
                bills = queryset1.filter(transaction_date__month=month)
                bills_monthly[month_name] = list(bills)


            # print(bills_monthly)



            for month, bills in bills_monthly.items():
            # print(f"Bills for month {month}:")
                month_sales = Decimal(0.0)

                # response_data = {}
                for bill in bills:
                    month_sales += bill.grand_total 

                month_dict = {
                    "month":month,
                    'grand_total': month_sales
                }

                branch_data['month_list'].append(month_dict)
            branch_data_sent.append(branch_data)

        return Response(branch_data_sent, status=status.HTTP_200_OK)
        
# from collections import defaultdict

# class BranchWiseMonthSale(APIView):
#     def get(self, request, *args, **kwargs):
#         data = request.data
#         type = data['type']

#         if type == 'branch': 
#             from_date_str = request.GET.get('CurrentYear')
#             current_year = datetime.strptime(from_date_str, '%Y').year

#             print(current_year)
            
#             branches = Branch.objects.filter(is_deleted=False, status=True)
            
#             current_date = datetime.now()
#             branch_data_sent = []
#             for branch in branches:
#                 branch_data = {
#                     "slug": branch.name,
#                     "month_list" : []
#                 }

#                 queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year=current_year, is_end_day=False)

#                 # print(branch.name)
#                 # print(queryset1)
#                 # print(f'current month is {current_date.month}')
#                 # for queryset in queryset1:
#                 #     print(queryset.invoice_number)    
#                 #     print(queryset.transaction_date_time.month)

#                 bills_monthly = defaultdict(list)

#                 for month in range(1, 13):
#                     month_name = calendar.month_name[month]
#                     bills = queryset1.filter(transaction_date__month=month)
#                     bills_monthly[month_name] = list(bills)


#                 # print(bills_monthly)



#                 for month, bills in bills_monthly.items():
#                 # print(f"Bills for month {month}:")
#                     month_sales = Decimal(0.0)

#                     # response_data = {}
#                     for bill in bills:
#                         month_sales += bill.grand_total 

#                     month_dict = {
#                         "month":month,
#                         'grand_total': month_sales
#                     }

#                     branch_data['month_list'].append(month_dict)
#                 branch_data_sent.append(branch_data)

            
            

#             return Response(branch_data_sent, status=status.HTTP_200_OK)
        
        # else:
        #     from_date_str = request.GET.get('CurrentYear')
        #     current_year = datetime.strptime(from_date_str, '%Y').year

        #     print(current_year)
            
        #     branches = Branch.objects.filter(is_deleted=False, status=True)
            
        #     current_date = datetime.now()
        #     branch_data_sent = []
        #     for branch in branches:
        #         branch_data = {
        #             "slug": branch.name,
        #             "month_list" : []
        #         }

        #         queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year=current_year, is_end_day=False)

        #         # print(branch.name)
        #         # print(queryset1)
        #         # print(f'current month is {current_date.month}')
        #         # for queryset in queryset1:
        #         #     print(queryset.invoice_number)    
        #         #     print(queryset.transaction_date_time.month)

        #         bills_monthly = defaultdict(list)

        #         for month in range(1, 13):
        #             month_name = calendar.month_name[month]
        #             bills = queryset1.filter(transaction_date__month=month)
        #             bills_monthly[month_name] = list(bills)


        #         # print(bills_monthly)



        #         for month, bills in bills_monthly.items():
        #         # print(f"Bills for month {month}:")
        #             month_sales = Decimal(0.0)

        #             # response_data = {}
        #             for bill in bills:
        #                 month_sales += bill.grand_total 

        #             month_dict = {
        #                 "month":month,
        #                 'grand_total': month_sales
        #             }

        #             branch_data['month_list'].append(month_dict)
        #         branch_data_sent.append(branch_data)

        #     total_monthly_sales = defaultdict(Decimal)

        #     for branch_data in branch_data_sent:
        #         for month_data in branch_data['month_list']:
        #             month_name = month_data['month']
        #             total_monthly_sales[month_name] += month_data['grand_total']

        #     total_data = []

        #     for month_name, total_sales in total_monthly_sales.items():
        #         month_data = {
        #             "month": month_name,
        #             "grand_total": total_sales
        #         }
        #         total_data.append(month_data)

        #     data_to_be_sent = {
        #         'slug': type,
        #         'data' : total_data
        #     }
            

        #     return Response(data_to_be_sent, status=status.HTTP_200_OK)

class BranchAndTerminalWiseMonthSale(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        branch_id = data.get('branch', None)

        if branch_id:
            from_date_str = request.GET.get('CurrentYear')
            current_year = datetime.strptime(from_date_str, '%Y').year

            print(current_year)
            
            branch = Branch.objects.get(is_deleted=False, status=True, id=branch_id)

            terminals = branch.terminal_set.filter(is_deleted=False, status=True)
            month_abbr = {
                1: 'Jan',
                2: 'Feb',
                3: 'Mar',
                4: 'Apr',
                5: 'May',
                6: 'Jun',
                7: 'Jul',
                8: 'Aug',
                9: 'Sep',
                10: 'Oct',
                11: 'Nov',
                12: 'Dec'
            }
            branch_data_sent = []
            for terminal in terminals:
                terminal_data = {
                    "branch": str(terminal.terminal_no),
                    "month_list" : []
                }

                queryset1 = Bill.objects.filter(status=True, branch=branch, terminal=terminal.terminal_no, transaction_date__year=current_year, is_end_day=False)

                # print(branch.name)
                # print(queryset1)
                # print(f'current month is {current_date.month}')
                # for queryset in queryset1:
                #     print(queryset.invoice_number)    
                #     print(queryset.transaction_date_time.month)

                bills_monthly = defaultdict(list)

                for month in range(1, 13):
                    month_name = month_abbr[month]
                    bills = queryset1.filter(transaction_date__month=month)
                    bills_monthly[month_name] = list(bills)


                # print(bills_monthly)



                for month, bills in bills_monthly.items():
                # print(f"Bills for month {month}:")
                    month_sales = Decimal(0.0)

                    # response_data = {}
                    for bill in bills:
                        month_sales += bill.grand_total 

                    month_dict = {
                        "month":month,
                        'grand_total': month_sales
                    }

                    terminal_data['month_list'].append(month_dict)
                branch_data_sent.append(terminal_data)

            response_data = {
                'slug': 'terminal',
                'data': branch_data_sent
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            from_date_str = request.GET.get('CurrentYear')
            current_year = datetime.strptime(from_date_str, '%Y').year

            print(current_year)
            
            branches = Branch.objects.filter(is_deleted=False, status=True)
            
            current_date = datetime.now()
            month_abbr = {
                1: 'Jan',
                2: 'Feb',
                3: 'Mar',
                4: 'Apr',
                5: 'May',
                6: 'Jun',
                7: 'Jul',
                8: 'Aug',
                9: 'Sep',
                10: 'Oct',
                11: 'Nov',
                12: 'Dec'
            }
            branch_data_sent = []
            for branch in branches:
                branch_data = {
                    "branch": branch.name,
                    "month_list" : []
                }

                queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year=current_year, is_end_day=False)

                # print(branch.name)
                # print(queryset1)
                # print(f'current month is {current_date.month}')
                # for queryset in queryset1:
                #     print(queryset.invoice_number)    
                #     print(queryset.transaction_date_time.month)

                bills_monthly = defaultdict(list)

                for month in range(1, 13):
                    month_name = month_abbr[month]
                    bills = queryset1.filter(transaction_date__month=month)
                    bills_monthly[month_name] = list(bills)


                # print(bills_monthly)



                for month, bills in bills_monthly.items():
                # print(f"Bills for month {month}:")
                    month_sales = Decimal(0.0)

                    # response_data = {}
                    for bill in bills:
                        month_sales += bill.grand_total 

                    month_dict = {
                        "month":month,
                        'grand_total': month_sales
                    }

                    branch_data['month_list'].append(month_dict)
                branch_data_sent.append(branch_data)
            response_data = {
                'slug': 'branch',
                'data': branch_data_sent
            }
            
            

            return Response(response_data, status=status.HTTP_200_OK)
            

class BranchAndTerminalWiseMonthAndFoodTypeSale(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        branch_id = data.get('branch', None)
        from_date_str = request.GET.get('CurrentYear')
        current_year = datetime.strptime(from_date_str, '%Y').year
        to_date_str = request.GET.get('ToYear')
        to_year = datetime.strptime(to_date_str, '%Y').year
        if branch_id:
            bill_items_total = self.calculate_bill_items_total(Bill.objects.filter(status=True, is_end_day=False, branch__id=branch_id, transaction_date__year__range=(current_year, to_year)))
            print(current_year)
            
            branch = Branch.objects.get(is_deleted=False, status=True, id=branch_id)

            terminals = branch.terminal_set.filter(is_deleted=False, status=True)
            month_abbr = {
                1: 'Jan',
                2: 'Feb',
                3: 'Mar',
                4: 'Apr',
                5: 'May',
                6: 'Jun',
                7: 'Jul',
                8: 'Aug',
                9: 'Sep',
                10: 'Oct',
                11: 'Nov',
                12: 'Dec'
            }
            
            branch_data_sent = []
            for terminal in terminals:
                terminal_data = {
                    "branch": str(terminal.terminal_no),
                    "month_list" : []
                }

                queryset1 = Bill.objects.filter(status=True, branch=branch, terminal=terminal.terminal_no, transaction_date__year__range=(current_year, to_year), is_end_day=False)

                bills_monthly = defaultdict(list)

                for month in range(1, 13):
                    month_name = month_abbr[month]
                    bills = queryset1.filter(transaction_date__month=month)
                    food_queryset = bills.filter(
                            bill_items__product_title__in=Product.objects.filter(type__title="FOOD").values_list('title', flat=True)
                        ) 
                    food_total = food_queryset.aggregate(food_total=Sum('bill_items__amount'))['food_total'] or Decimal(0.0)
                    bills_monthly[month_name] = food_total

                # print(bills_monthly.items())
                for month, total in bills_monthly.items():
                    # print(f'{month}-{bills}')
                # print(f"Bills for month {month}:")
                    month_sales = Decimal(0.0)


                    month_dict = {
                        "month":month,
                        'grand_total': total
                    }

                    terminal_data['month_list'].append(month_dict)
                branch_data_sent.append(terminal_data)

            response_data = {
                'slug': 'branch',
                'data': branch_data_sent,
                'bill_items_total': bill_items_total
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            from_date_str = request.GET.get('CurrentYear')
            current_year = datetime.strptime(from_date_str, '%Y').year
            to_date_str = request.GET.get('ToYear')
            to_year = datetime.strptime(to_date_str, '%Y').year
            
            bill_items_total = self.calculate_bill_items_total(Bill.objects.filter(status=True,is_end_day=False, transaction_date__year__range=(current_year, to_year)))

            print(current_year)
            
            branches = Branch.objects.filter(is_deleted=False, status=True)
            
            current_date = datetime.now()
            month_abbr = {
                1: 'Jan',
                2: 'Feb',
                3: 'Mar',
                4: 'Apr',
                5: 'May',
                6: 'Jun',
                7: 'Jul',
                8: 'Aug',
                9: 'Sep',
                10: 'Oct',
                11: 'Nov',
                12: 'Dec'
            }
            branch_data_sent = []
            for branch in branches:
                branch_data = {
                    "branch": branch.name,
                    "month_list" : []
                }

                queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year__range=(current_year, to_year), is_end_day=False)

                bills_monthly = defaultdict(list)

                for month in range(1, 13):
                    month_name = month_abbr[month]
                    bills = queryset1.filter(transaction_date__month=month)
                    food_queryset = bills.filter(
                            bill_items__product_title__in=Product.objects.filter(type__title="FOOD").values_list('title', flat=True)
                        ) 
                    food_total = food_queryset.aggregate(food_total=Sum('bill_items__amount'))['food_total'] or Decimal(0.0)
                    bills_monthly[month_name] = food_total



                for month, total in bills_monthly.items():
                    month_sales = Decimal(0.0)

                    month_dict = {
                        "month":month,
                        'grand_total': total
                    }

                    branch_data['month_list'].append(month_dict)
                branch_data_sent.append(branch_data)
            response_data = {
                'slug': 'terminal',
                'data': branch_data_sent,   
                'bill_items_total': bill_items_total
                
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    def calculate_bill_items_total(self, queryset):
        bill_items_total = []

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


        for product_id, item_data in product_quantities.items():
                if item_data['type'] not in ['BEVERAGE', 'OTHERS']:
                    bill_items_total.append({
                        'product_title': item_data['product_title'],
                        'product_quantity': item_data['quantity'],
                        'rate': item_data['rate'],
                        'amount': item_data['quantity'] * item_data['rate'],
                    })

        # # Convert defaultdict to regular dict for JSON serialization
        # bill_items_total = dict(bill_items_total)

        return bill_items_total
        
class BranchAndTerminalWiseMonthAndOthersTypeSale(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        branch_id = data.get('branch', None)
        from_date_str = request.GET.get('CurrentYear')
        current_year = datetime.strptime(from_date_str, '%Y').year
        to_date_str = request.GET.get('ToYear')
        to_year = datetime.strptime(to_date_str, '%Y').year

        if branch_id:
            bill_items_total = self.calculate_bill_items_total(Bill.objects.filter(status=True, is_end_day=False, branch__id=branch_id, transaction_date__year__range=(current_year, to_year)))
            print(current_year)
            
            branch = Branch.objects.get(is_deleted=False, status=True, id=branch_id)

            terminals = branch.terminal_set.filter(is_deleted=False, status=True)
            
            month_abbr = {
                1: 'Jan',
                2: 'Feb',
                3: 'Mar',
                4: 'Apr',
                5: 'May',
                6: 'Jun',
                7: 'Jul',
                8: 'Aug',
                9: 'Sep',
                10: 'Oct',
                11: 'Nov',
                12: 'Dec'
            }
            branch_data_sent = []
            for terminal in terminals:
                terminal_data = {
                    "branch": str(terminal.terminal_no),
                    "month_list" : []
                }

                queryset1 = Bill.objects.filter(status=True, branch=branch, terminal=terminal.terminal_no, transaction_date__year__range=(current_year, to_year), is_end_day=False)

                bills_monthly = defaultdict(list)

                for month in range(1, 13):
                    month_name = month_abbr[month]
                    bills = queryset1.filter(transaction_date__month=month)
                    others_queryset = bills.filter(
                            bill_items__product_title__in=Product.objects.filter(type__title="OTHERS").values_list('title', flat=True)
                        ) 
                    others_total = others_queryset.aggregate(others_total=Sum('bill_items__amount'))['others_total'] or Decimal(0.0)
                    bills_monthly[month_name] = others_total

                # print(bills_monthly.items())
                for month, total in bills_monthly.items():
                    # print(f'{month}-{bills}')
                # print(f"Bills for month {month}:")
                    month_sales = Decimal(0.0)


                    month_dict = {
                        "month":month,
                        'grand_total': total
                    }

                    terminal_data['month_list'].append(month_dict)
                branch_data_sent.append(terminal_data)

            response_data = {
                'slug': 'branch',
                'data': branch_data_sent,
                'bill_items_total': bill_items_total
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            from_date_str = request.GET.get('CurrentYear')
            current_year = datetime.strptime(from_date_str, '%Y').year
            to_date_str = request.GET.get('ToYear')
            to_year = datetime.strptime(to_date_str, '%Y').year
            
            bill_items_total = self.calculate_bill_items_total(Bill.objects.filter(status=True, is_end_day=False, transaction_date__year__range=(current_year, to_year)))

            print(current_year)
            
            branches = Branch.objects.filter(is_deleted=False, status=True)
            
            current_date = datetime.now()
            month_abbr = {
                1: 'Jan',
                2: 'Feb',
                3: 'Mar',
                4: 'Apr',
                5: 'May',
                6: 'Jun',
                7: 'Jul',
                8: 'Aug',
                9: 'Sep',
                10: 'Oct',
                11: 'Nov',
                12: 'Dec'
            }
            branch_data_sent = []
            for branch in branches:
                branch_data = {
                    "branch": branch.name,
                    "month_list" : []
                }

                queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year__range=(current_year, to_year), is_end_day=False)

                bills_monthly = defaultdict(list)

                for month in range(1, 13):
                    month_name = month_abbr[month]
                    bills = queryset1.filter(transaction_date__month=month)
                    others_queryset = bills.filter(
                            bill_items__product_title__in=Product.objects.filter(type__title="OTHERS").values_list('title', flat=True)
                        ) 
                    others_total = others_queryset.aggregate(others_total=Sum('bill_items__amount'))['others_total'] or Decimal(0.0)
                    bills_monthly[month_name] = others_total



                for month, total in bills_monthly.items():
                    month_sales = Decimal(0.0)

                    month_dict = {
                        "month":month,
                        'grand_total': total
                    }

                    branch_data['month_list'].append(month_dict)
                branch_data_sent.append(branch_data)
            response_data = {
                'slug': 'terminal',
                'data': branch_data_sent,   
                'bill_items_total': bill_items_total
                
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    def calculate_bill_items_total(self, queryset):
        bill_items_total = []

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


        for product_id, item_data in product_quantities.items():
                if item_data['type'] not in ['BEVERAGE', 'FOOD']:
                    bill_items_total.append({
                        'product_title': item_data['product_title'],
                        'product_quantity': item_data['quantity'],
                        'rate': item_data['rate'],
                        'amount': item_data['quantity'] * item_data['rate'],
                    })

        # # Convert defaultdict to regular dict for JSON serialization
        # bill_items_total = dict(bill_items_total)

        return bill_items_total
        

class BranchAndTerminalWiseMonthAndBeverageTypeSale(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        branch_id = data.get('branch', None)
        from_date_str = request.GET.get('CurrentYear')
        current_year = datetime.strptime(from_date_str, '%Y').year
        to_date_str = request.GET.get('ToYear')
        to_year = datetime.strptime(to_date_str, '%Y').year
        if branch_id:
            bill_items_total = self.calculate_bill_items_total(Bill.objects.filter(status=True, is_end_day=False, branch__id=branch_id, transaction_date__year__range=(current_year, to_year)))
            print(current_year)
            
            branch = Branch.objects.get(is_deleted=False, status=True, id=branch_id)

            terminals = branch.terminal_set.filter(is_deleted=False, status=True)
            
            month_abbr = {
                1: 'Jan',
                2: 'Feb',
                3: 'Mar',
                4: 'Apr',
                5: 'May',
                6: 'Jun',
                7: 'Jul',
                8: 'Aug',
                9: 'Sep',
                10: 'Oct',
                11: 'Nov',
                12: 'Dec'
            }
            branch_data_sent = []
            for terminal in terminals:
                terminal_data = {
                    "branch": str(terminal.terminal_no),
                    "month_list" : []
                }

                queryset1 = Bill.objects.filter(status=True, branch=branch, terminal=terminal.terminal_no, transaction_date__year__range=(current_year, to_year), is_end_day=False)

                bills_monthly = defaultdict(list)

                for month in range(1, 13):
                    month_name = month_abbr[month]
                    bills = queryset1.filter(transaction_date__month=month)
                    beverage_queryset = bills.filter(
                            bill_items__product_title__in=Product.objects.filter(type__title="BEVERAGE").values_list('title', flat=True)
                        ) 
                    beverage_total = beverage_queryset.aggregate(beverage_total=Sum('bill_items__amount'))['beverage_total'] or Decimal(0.0)
                    bills_monthly[month_name] = beverage_total

                # print(bills_monthly.items())
                for month, total in bills_monthly.items():
                    # print(f'{month}-{bills}')
                # print(f"Bills for month {month}:")
                    month_sales = Decimal(0.0)


                    month_dict = {
                        "month":month,
                        'grand_total': total
                    }

                    terminal_data['month_list'].append(month_dict)
                branch_data_sent.append(terminal_data)

            response_data = {
                'slug': 'branch',
                'data': branch_data_sent,
                'bill_items_total': bill_items_total
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            from_date_str = request.GET.get('CurrentYear')
            current_year = datetime.strptime(from_date_str, '%Y').year
            to_date_str = request.GET.get('ToYear')
            to_year = datetime.strptime(to_date_str, '%Y').year
            
            bill_items_total = self.calculate_bill_items_total(Bill.objects.filter(status=True, is_end_day=False, transaction_date__year__range=(current_year, to_year)))

            print(current_year)
            
            branches = Branch.objects.filter(is_deleted=False, status=True)
            
            current_date = datetime.now()
            month_abbr = {
                1: 'Jan',
                2: 'Feb',
                3: 'Mar',
                4: 'Apr',
                5: 'May',
                6: 'Jun',
                7: 'Jul',
                8: 'Aug',
                9: 'Sep',
                10: 'Oct',
                11: 'Nov',
                12: 'Dec'
            }
            branch_data_sent = []
            for branch in branches:
                branch_data = {
                    "branch": branch.name,
                    "month_list" : []
                }

                queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year__range=(current_year, to_year), is_end_day=False)

                bills_monthly = defaultdict(list)

                for month in range(1, 13):
                    month_name = month_abbr[month]
                    bills = queryset1.filter(transaction_date__month=month)
                    beverage_queryset = bills.filter(
                            bill_items__product_title__in=Product.objects.filter(type__title="BEVERAGE").values_list('title', flat=True)
                        ) 
                    beverage_total = beverage_queryset.aggregate(beverage_total=Sum('bill_items__amount'))['beverage_total'] or Decimal(0.0)
                    bills_monthly[month_name] = beverage_total



                for month, total in bills_monthly.items():
                    month_sales = Decimal(0.0)

                    month_dict = {
                        "month":month,
                        'grand_total': total
                    }

                    branch_data['month_list'].append(month_dict)
                branch_data_sent.append(branch_data)
            response_data = {
                'slug': 'terminal',
                'data': branch_data_sent,   
                'bill_items_total': bill_items_total
                
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    def calculate_bill_items_total(self, queryset):
        bill_items_total = []

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


        for product_id, item_data in product_quantities.items():
                if item_data['type'] not in ['FOOD', 'OTHERS']:
                    bill_items_total.append({
                        'product_title': item_data['product_title'],
                        'product_quantity': item_data['quantity'],
                        'rate': item_data['rate'],
                        'amount': item_data['quantity'] * item_data['rate'],
                    })

        # # Convert defaultdict to regular dict for JSON serialization
        # bill_items_total = dict(bill_items_total)

        return bill_items_total

        
# class BranchAndTerminalWiseMonthAndOthersTypeSale(APIView):
#     def post(self, request, *args, **kwargs):
#         data = request.data
#         branch_id = data.get('branch', None)

#         if branch_id:
#             from_date_str = request.GET.get('CurrentYear')
#             current_year = datetime.strptime(from_date_str, '%Y').year
#             to_date_str = request.GET.get('ToYear')
#             to_year = datetime.strptime(to_date_str, '%Y').year

#             print(current_year)
            
#             branch = Branch.objects.get(is_deleted=False, status=True, id=branch_id)

#             terminals = branch.terminal_set.filter(is_deleted=False, status=True)
            
#             branch_data_sent = []
#             for terminal in terminals:
#                 terminal_data = {
#                     "branch": str(terminal.terminal_no),
#                     "month_list" : []
#                 }

#                 queryset1 = Bill.objects.filter(status=True, branch=branch, terminal=terminal.terminal_no, transaction_date__year__range=(current_year, to_year), is_end_day=False)

#                 bills_monthly = defaultdict(list)

#                 for month in range(1, 13):
#                     month_name = calendar.month_name[month]
#                     bills = queryset1.filter(transaction_date__month=month)
#                     others_queryset = bills.filter(
#                             bill_items__product_title__in=Product.objects.filter(type__title="OTHERS").values_list('title', flat=True)
#                         ) 
#                     others_total = others_queryset.aggregate(others_total=Sum('bill_items__amount'))['others_total'] or Decimal(0.0)
#                     bills_monthly[month_name] = others_total

#                 # print(bills_monthly.items())
#                 for month, total in bills_monthly.items():
#                     # print(f'{month}-{bills}')
#                 # print(f"Bills for month {month}:")
#                     # month_sales = Decimal(0.0)


#                     month_dict = {
#                         "month":month,
#                         'grand_total': total
#                     }

#                     terminal_data['month_list'].append(month_dict)
#                 branch_data_sent.append(terminal_data)

#             response_data = {
#                 'slug': 'branch',
#                 'data': branch_data_sent
#             }

#             return Response(response_data, status=status.HTTP_200_OK)
#         else:
#             from_date_str = request.GET.get('CurrentYear')
#             current_year = datetime.strptime(from_date_str, '%Y').year
#             to_date_str = request.GET.get('ToYear')
#             to_year = datetime.strptime(to_date_str, '%Y').year

#             print(current_year)
            
#             branches = Branch.objects.filter(is_deleted=False, status=True)
            
#             current_date = datetime.now()
#             branch_data_sent = []
#             for branch in branches:
#                 branch_data = {
#                     "branch": branch.name,
#                     "month_list" : []
#                 }

#                 queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year__range=(current_year, to_year), is_end_day=False)

#                 bills_monthly = defaultdict(list)

#                 for month in range(1, 13):
#                     month_name = calendar.month_name[month]
#                     bills = queryset1.filter(transaction_date__month=month)
#                     others_queryset = bills.filter(
#                             bill_items__product_title__in=Product.objects.filter(type__title="OTHERS").values_list('title', flat=True)
#                         ) 
#                     others_total = others_queryset.aggregate(others_total=Sum('bill_items__amount'))['others_total'] or Decimal(0.0)
#                     bills_monthly[month_name] = others_total



#                 for month, total in bills_monthly.items():
#                     month_sales = Decimal(0.0)

#                     month_dict = {
#                         "month":month,
#                         'grand_total': total
#                     }

#                     branch_data['month_list'].append(month_dict)
#                 branch_data_sent.append(branch_data)
#             response_data = {
#                 'slug': 'terminal',
#                 'data': branch_data_sent
#             }
            
#             return Response(response_data, status=status.HTTP_200_OK)
        
# class BranchAndTerminalWiseMonthAndBeverageTypeSale(APIView):
#     def post(self, request, *args, **kwargs):
#         data = request.data
#         branch_id = data.get('branch', None)

#         if branch_id:
#             from_date_str = request.GET.get('CurrentYear')
#             current_year = datetime.strptime(from_date_str, '%Y').year
#             to_date_str = request.GET.get('ToYear')
#             to_year = datetime.strptime(to_date_str, '%Y').year

#             print(current_year)
            
#             branch = Branch.objects.get(is_deleted=False, status=True, id=branch_id)

#             terminals = branch.terminal_set.filter(is_deleted=False, status=True)
            
#             branch_data_sent = []
#             for terminal in terminals:
#                 terminal_data = {
#                     "branch": str(terminal.terminal_no),
#                     "month_list" : []
#                 }

#                 queryset1 = Bill.objects.filter(status=True, branch=branch, terminal=terminal.terminal_no, transaction_date__year__range=(current_year, to_year), is_end_day=False)

#                 bills_monthly = defaultdict(list)

#                 for month in range(1, 13):
#                     month_name = calendar.month_name[month]
#                     bills = queryset1.filter(transaction_date__month=month)
#                     beverage_queryset = bills.filter(
#                             bill_items__product_title__in=Product.objects.filter(type__title="BEVERAGE").values_list('title', flat=True)
#                         ) 
#                     beverage_total = beverage_queryset.aggregate(beverage_total=Sum('bill_items__amount'))['beverage_total'] or Decimal(0.0)
#                     bills_monthly[month_name] = beverage_total

#                 # print(bills_monthly.items())
#                 for month, total in bills_monthly.items():
#                     # print(f'{month}-{bills}')
#                 # print(f"Bills for month {month}:")
#                     # month_sales = Decimal(0.0)


#                     month_dict = {
#                         "month":month,
#                         'grand_total': total
#                     }

#                     terminal_data['month_list'].append(month_dict)
#                 branch_data_sent.append(terminal_data)

#             response_data = {
#                 'slug': 'branch',
#                 'data': branch_data_sent
#             }

#             return Response(response_data, status=status.HTTP_200_OK)
#         else:
#             from_date_str = request.GET.get('CurrentYear')
#             current_year = datetime.strptime(from_date_str, '%Y').year
#             to_date_str = request.GET.get('ToYear')
#             to_year = datetime.strptime(to_date_str, '%Y').year

#             print(current_year)
            
#             branches = Branch.objects.filter(is_deleted=False, status=True)
            
#             current_date = datetime.now()
#             branch_data_sent = []
#             for branch in branches:
#                 branch_data = {
#                     "branch": branch.name,
#                     "month_list" : []
#                 }

#                 queryset1 = Bill.objects.filter(status=True, branch=branch, transaction_date__year__range=(current_year, to_year), is_end_day=False)

#                 bills_monthly = defaultdict(list)

#                 for month in range(1, 13):
#                     month_name = calendar.month_name[month]
#                     bills = queryset1.filter(transaction_date__month=month)
#                     beverage_queryset = bills.filter(
#                             bill_items__product_title__in=Product.objects.filter(type__title="BEVERAGE").values_list('title', flat=True)
#                         ) 
#                     beverage_total = beverage_queryset.aggregate(beverage_total=Sum('bill_items__amount'))['beverage_total'] or Decimal(0.0)
#                     bills_monthly[month_name] = beverage_total



#                 for month, total in bills_monthly.items():
#                     month_sales = Decimal(0.0)

#                     month_dict = {
#                         "month":month,
#                         'grand_total': total
#                     }

#                     branch_data['month_list'].append(month_dict)
#                 branch_data_sent.append(branch_data)
#             response_data = {
#                 'slug': 'terminal',
#                 'data': branch_data_sent
#             }
            
#             return Response(response_data, status=status.HTTP_200_OK)