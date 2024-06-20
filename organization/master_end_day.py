from rest_framework import generics, status
from django.utils import timezone
from datetime import date
from api.serializers.end_day import EndDayDailyReportSerializer
from organization.models import EndDayDailyReport
from django.shortcuts import get_object_or_404
from organization.models import Branch, Terminal
from django.db.models import Q
from organization.models import CashDrop
from django.db.models import Sum
from itertools import groupby
from operator import itemgetter
import pytz
from django.core.management.base import BaseCommand
from django.utils import timezone
from organization.models import Branch, Organization, EndDayDailyReport, EndDayRecord, MailRecipient, MailSendRecord
from bill.models import Bill, BillPayment
from decimal import Decimal
from product.models import Product
from django.db import transaction


@transaction.atomic()
def end_day(branches,username):
    print(f"timezone {timezone.now()}")
    ny_timezone = pytz.timezone('Asia/Kathmandu')
    current_datetime_ny = timezone.now().astimezone(ny_timezone)

    organization = Organization.objects.first()

    # entered_time = organization.end_day_times



    formatted_date = current_datetime_ny.strftime("%Y-%m-%d")
    formatted_datetime = current_datetime_ny.strftime("%Y-%m-%d %I:%M %p")

    # if current_time_formatted == entered_time_formatted:

    print(f"The formatted time is {formatted_datetime}")
    branches = Branch.objects.filter(is_deleted=False, status=True)

    bill_terminals = Bill.objects.filter(is_end_day=False)

    terminal_ids = []

    for terminals in bill_terminals:
        if terminals.terminal not in terminal_ids:
            terminal_ids.append(terminals.terminal)

    print(f"terminals {terminal_ids}")


    for branch in branches:
        for terminal_id in terminal_ids:

            try:
                queryset = Bill.objects.filter(
                        is_end_day=False, branch=branch, terminal=terminal_id
                    )
            except Exception as e:
                print(f"The error occured in queryset {e}")

            try:
                queryset1 = Bill.objects.filter(
                        is_end_day=False, status=True, branch=branch, terminal=terminal_id
                    )
            except:
                print(f"The error occured in the queryset1 {e}")
                # def list(self, request, *args, **kwargs):
                #     queryset, queryset1 = self.get_queryset()

                # Get the IDs of bills with is_end_day=False

            if (
                    queryset is not None
                    and queryset1 is not None
                    and queryset.exists()
                    and queryset1.exists()
            ):
                bill_ids = queryset1.values_list("id", flat=True)

                possible_payment_modes = [
                        "CASH",
                        "CREDIT",
                        "COMPLIMENTARY",
                        "CREDIT CARD",
                        "MOBILE PAYMENT",
                    ]

                    # Initialize a dictionary to store the payment mode totals
                payment_mode_totals = {
                        mode: Decimal(0.0) for mode in possible_payment_modes
                    }

                    # Get the total amount for each payment mode
                try:
                        bill_payments = BillPayment.objects.filter(bill_id__in=bill_ids)
                        print(bill_payments)
                except Exception as e:
                        print(f"The error occured in the bill_payments {e}")
                        print(f"These are the bill ids", bill_ids)

                if bill_payments is not None:
                    for payment in bill_payments:
                            # Update the total for each payment mode
                        payment_mode_totals[payment.payment_mode] += payment.amount

                        # Create a list of payment mode data
                    payment_mode_data = [
                            {
                                "payment_mode": mode,
                                "total_amount": payment_mode_totals[mode],
                            }
                            for mode in possible_payment_modes
                        ]

                    # Calculate the invoice_number and grand_total for void bills
                void_bills_data = queryset.filter(status=False).values(
                        "invoice_number", "grand_total"
                    )
                
                void_bills_count = void_bills_data.count()

                    # Serialize the payment_mode_data
                    # payment_mode_serializer = PaymentModeSerializer(payment_mode_data, many=True)
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

                starting_from_invoice = (
                        first_bill.invoice_number if first_bill else None
                    )
                ending_from_invoice = last_bill.invoice_number if last_bill else None

                    # Serialize the queryset for bill data
                    # serializer = self.get_serializer(queryset, many=True)

                    # Calculate sums
                sub_total_sum = Decimal(0)
                discount_amount_sum = Decimal(0)
                taxable_amount_sum = Decimal(0)
                tax_amount_sum = Decimal(0)
                grand_total_sum = Decimal(0)
                service_charge_sum = Decimal(0)
                print(queryset1)
                for bill in queryset1:
                    if bill.payment_mode != "COMPLIMENTARY":
                        sub_total_sum += bill.sub_total
                        discount_amount_sum += bill.discount_amount
                        taxable_amount_sum += bill.taxable_amount
                        tax_amount_sum += bill.tax_amount
                        grand_total_sum += bill.grand_total
                        service_charge_sum += bill.service_charge
                net_sales = sub_total_sum-discount_amount_sum

                bill_items_total = calculate_bill_items_total(queryset)

                response_data = {
                        "bill_data": queryset,
                        "payment_modes": payment_mode_data,
                        "Starting_from": starting_from_invoice,
                        "Ending_from": ending_from_invoice,
                        "bill_items_total": bill_items_total,
                    }

                print("I have got the response_data", response_data)

                sales_data = {
                        "discount_amount": discount_amount_sum,
                        "taxable_amount": taxable_amount_sum,
                        "tax_amount": tax_amount_sum,
                        "grand_total": grand_total_sum,
                        "service_charge": service_charge_sum,
                    }
                response_data["Sales"] = sales_data
                
                dine_in_bills_sub_total = queryset1.filter(order__order_type="Dine In").aggregate(sub_total_sum=Sum('sub_total'))['sub_total_sum']
                takeaway_bills_sub_total = queryset1.filter(order__order_type="Takeaway").aggregate(sub_total_sum=Sum('sub_total'))['sub_total_sum']
                delivery_bills_sub_total = queryset1.filter(order__order_type="Delivery").aggregate(sub_total_sum=Sum('sub_total'))['sub_total_sum']
                dine_in_bills_vat_total = queryset1.filter(order__order_type="Dine In").aggregate(tax_amount_sum=Sum('tax_amount'))['tax_amount_sum']
                takeaway_bills_vat_total = queryset1.filter(order__order_type="Takeaway").aggregate(tax_amount_sum=Sum('tax_amount'))['tax_amount_sum']
                delivery_bills_vat_total = queryset1.filter(order__order_type="Delivery").aggregate(tax_amount_sum=Sum('tax_amount'))['tax_amount_sum']
                dine_in_bills_discount_total = queryset1.filter(order__order_type="Dine In").aggregate(discount_amount_sum=Sum('discount_amount'))['discount_amount_sum']
                takeaway_bills_discount_total = queryset1.filter(order__order_type="Takeaway").aggregate(discount_amount_sum=Sum('discount_amount'))['discount_amount_sum']
                delivery_bills_discount_total = queryset1.filter(order__order_type="Delivery").aggregate(discount_amount_sum=Sum('discount_amount'))['discount_amount_sum']

                dine_in_bills_netsale = (dine_in_bills_sub_total if dine_in_bills_sub_total else Decimal(0.0)) - (dine_in_bills_discount_total if dine_in_bills_discount_total else Decimal(0.0))
                takeaway_bills_netsale = (takeaway_bills_sub_total if takeaway_bills_sub_total else Decimal(0.0)) - (takeaway_bills_discount_total if takeaway_bills_discount_total else Decimal(0.0))
                delivery_bills_netsale = (delivery_bills_sub_total if delivery_bills_sub_total else Decimal(0.0)) - (delivery_bills_discount_total if delivery_bills_discount_total else Decimal(0.0))


                dine_in_bills_totalsale = Decimal(dine_in_bills_netsale) + (dine_in_bills_vat_total if dine_in_bills_vat_total else Decimal(0.0))
                delivery_bills_totalsale = Decimal(delivery_bills_netsale) + (delivery_bills_vat_total if delivery_bills_vat_total else Decimal(0.0))
                takeaway_bills_totalsale = Decimal(takeaway_bills_netsale) + (takeaway_bills_vat_total if takeaway_bills_vat_total else Decimal(0.0))

                print(dine_in_bills_totalsale)

                food_total = queryset1.filter(
                    is_end_day=False,
                    bill_items__product_title__in=Product.objects.filter(type__title="FOOD").values_list('title', flat=True)
                ) .aggregate(food_total=Sum('bill_items__amount'))['food_total'] or Decimal(0)
                # print(food_total)
                print(food_total)

                # print(food_total)

                # Get the total amount of beverage products
                beverage_total = queryset1.filter(
                    is_end_day=False,
                    bill_items__product_title__in=Product.objects.filter(type__title="BEVERAGE").values_list('title', flat=True)
                ).aggregate(beverage_total=Sum('bill_items__amount'))['beverage_total'] or Decimal(0)

                # Get the total amount of other products
                others_total = queryset1.filter(
                    is_end_day=False,
                    bill_items__product_title__in=Product.objects.filter(type__title="OTHERS").values_list('title', flat=True)
                ).aggregate(others_total=Sum('bill_items__amount'))['others_total'] or Decimal(0)

                    # Add void bills data to the response
                response_data["void_bills"] = void_bills_data

                organization = Organization.objects.first()

                organization = {
                        "org_name": organization.org_name,
                        "tax_number": organization.tax_number,
                        # contact details
                        "company_contact_number": organization.company_contact_number,
                        # company_contact_email = models.EmailField(null=True, blank=True)
                        "company_address": organization.company_address,
                }

                response_data["organization"] = organization

                print("Cronjob activated successfully")

                cash_total = 0.0
                credit_total = 0.0
                credit_card_total = 0.0
                mobile_payment_total = 0.0
                complimentary_total = 0.0

                for mode in payment_mode_data:
                    if mode["payment_mode"] == "CASH":
                        cash_total = mode["total_amount"]
                    if mode["payment_mode"] == "CREDIT":
                        credit_total = mode["total_amount"]
                    if mode["payment_mode"] == "CREDIT CARD":
                        credit_card_total = mode["total_amount"]
                    if mode["payment_mode"] == "MOBILE PAYMENT":
                        mobile_payment_total = mode["total_amount"]
                    if mode["payment_mode"] == "COMPLIMENTARY":
                        complimentary_total = mode["total_amount"]

                try:
                    EndDayRecord.objects.create(
                            branch_id=branch.id, terminal=terminal_id, date=formatted_date
                        )

                except Exception as e:
                    print("Error creating the Endday Record Object", e)
                no_of_guest = 0

                for bill in queryset1:
                    order = bill.order
                    if order is not None:
                        no_of_guest += order.no_of_guest
                        

                try:

                    EndDayDailyReport.objects.create(
                            employee_name=username,
                            net_sales=net_sales,
                            vat=tax_amount_sum,
                            total_discounts=discount_amount_sum,
                            cash=cash_total,
                            credit=credit_total,
                            credit_card=credit_card_total,
                            mobile_payment=mobile_payment_total,
                            complimentary=complimentary_total,
                            start_bill=starting_from_invoice,
                            end_bill=ending_from_invoice,
                            date_time=formatted_datetime,
                            terminal=terminal_id,
                            # total_sale=grand_total_sum,
                            branch_id=branch.id,
                            food_sale=food_total, 
                            beverage_sale=beverage_total,
                            others_sale=others_total,
                            total_void_count = void_bills_count,
                            no_of_guest=no_of_guest,
                            dine_grandtotal = dine_in_bills_totalsale if dine_in_bills_totalsale else 0.0,
                            delivery_grandtotal = delivery_bills_totalsale if delivery_bills_totalsale else 0.0,
                            takeaway_grandtotal = takeaway_bills_totalsale if takeaway_bills_totalsale else 0.0,
                            dine_nettotal = dine_in_bills_netsale if dine_in_bills_netsale else 0.0,
                            delivery_nettotal = delivery_bills_netsale if delivery_bills_netsale else 0.0,
                            takeaway_nettotal = takeaway_bills_netsale if takeaway_bills_netsale else 0.0,
                            dine_vattotal = dine_in_bills_vat_total if dine_in_bills_vat_total else 0.0,
                            delivery_vattotal = delivery_bills_vat_total if delivery_bills_vat_total else 0.0,
                            takeaway_vattotal = takeaway_bills_vat_total if takeaway_bills_vat_total else 0.0

                        )
                    print("The End Day object has been created")
                except Exception as e:
                    print("Error creating the Endday Object", e)

                try:
                    Bill.objects.filter(
                            branch_id=branch, terminal=terminal_id, is_end_day=False
                    ).update(is_end_day=True)

                except Exception as e:
                    print("Error in updating the bills")
                    
            else:
                print("No bills found having end day false") 
                    # self.stdout.write(self.style.SUCCESS('Bills are not created %s' % timezone.now()))

    try:
        fetch_details()
    except Exception as e:
        print(e)
        print("Error sending the mails")
    # else:
      


def calculate_bill_items_total(queryset):
    bill_items_total = []

    # Create a dictionary to store product quantities
    product_quantities = {}
    for bill in queryset:
        for bill_item in bill.bill_items.all():
            product_id = bill_item.product.id
            quantity = bill_item.product_quantity
            rate = bill_item.rate

            product_title = bill_item.product_title

            key = (product_id, rate)
            if key in product_quantities:
                product_quantities[key]["quantity"] += quantity
            else:
                product_quantities[key] = {
                    "quantity": quantity,
                    "rate": rate,
                    "product_title": product_title,
                }

    # Convert the product quantities back to a list of dictionaries
    for product_id, item_data in product_quantities.items():
        # Find the associated product
        # product = Product.objects.get(id=product_id)
        # Create a dictionary for the bill item total
        bill_items_total.append(
            {
                "product_title": item_data["product_title"],
                "product_quantity": item_data["quantity"],
                "rate": item_data["rate"],
                "amount": item_data["quantity"] * item_data["rate"],
            }
        )

    return bill_items_total


from datetime import datetime
from django.dispatch import receiver
import environ
env = environ.Env(DEBUG=(bool, False))
from organization.utils import send_combined_mail_to_receipients
from threading import Thread

def fetch_details():
    print("I am in")
    # current_date = datetime.now().date().strftime('%Y-%m-%d')
    # current_date = '2024-03-31'
    # print(f"timezone {timezone.now()}")
    ny_timezone = pytz.timezone('Asia/Kathmandu')
    current_datetime_ny = timezone.now().astimezone(ny_timezone)

    formatted_date = current_datetime_ny.strftime("%Y-%m-%d")
    transaction_date = current_datetime_ny.date()

    enddays = EndDayDailyReport.objects.filter(date_time__startswith=formatted_date)
    print(enddays)
    enddays_terminal = []

    combine_data = {}
    total_sale_holder = 0.0
    net_sales_holder = 0.0
    discount_holder = 0.0
    tax_holder = 0.0
    
    if enddays:

        for endday in enddays:
    
            sender = env('EMAIL_HOST_USER')
            mail_list = []
            recipients = MailRecipient.objects.filter(status=True)
            for r in recipients:
                mail_list.append(r.email)
                MailSendRecord.objects.create(mail_recipient=r)
            if mail_list:
    
                dt_now = datetime.now()
                date_now = dt_now.date()
                time_now = dt_now.time().strftime('%I:%M %p')
                org = Organization.objects.first().org_name
                from bill.models import Bill
                # bills = Bill.objects.filter(is_end_day=False, branch=endday.branch, terminal=endday.terminal)
                bills = Bill.objects.filter(transaction_date=transaction_date, branch=endday.branch, terminal=endday.terminal)
                total_transactions = bills.count()
                total_grand_total_by_category = {}
    
                for bill in bills:
                    for bill_item in bill.bill_items.all():
                        product_category = bill_item.product.type.title
    
                        total_grand_total_by_category[product_category] = (
                            total_grand_total_by_category.get(product_category, 0) + bill_item.amount 
                        )
    
                print(total_grand_total_by_category)
    
                # changes
    
                cashdrops = CashDrop.objects.filter(branch_id=endday.branch, datetime__startswith=formatted_date)
                print(f"CashDrops: {cashdrops}")  
                    # Calculate the total expense and total cashdrop
                total_expense = cashdrops.aggregate(Sum('expense'))['expense__sum'] or 0.0
                total_cashdrop = cashdrops.aggregate(Sum('cashdrop_amount'))['cashdrop_amount__sum'] or 0.0
                    
                latest_balance=0
                total_expense_cashdrop = 0
                total_expense_cashdrop = total_expense + total_cashdrop
                latest_cash_drop = cashdrops.last()
                if latest_cash_drop is not None:
                        # Calculate the latest_balance
                    latest_balance = latest_cash_drop.opening_balance - latest_cash_drop.cashdrop_amount
                        # opening_balance = latest_cash_drop.opening_balance
                        # cashdrop = latest_cash_drop.cashdrop_amount
                    if latest_cash_drop.expense is not None:
                        latest_balance -= latest_cash_drop.expense
                            # expense = latest_cash_drop.expense
                    if latest_cash_drop.addCash is not None:
                        latest_balance += latest_cash_drop.addCash
                    else:
                        expense = 0.0
                    
                opening_balance = latest_balance + total_expense_cashdrop
                cash_to_be_added= float(endday.cash)
                cash_total= latest_balance + cash_to_be_added
                start_bill_number = int(endday.start_bill.split('-')[-1])
                end_bill_number = int(endday.end_bill.split('-')[-1])
                print(start_bill_number)
                print(end_bill_number)
                    # bills = Bill.objects.filter(payment_mode="CREDIT")
                from bill.models import Bill
                    # bills = Bill.objects.filter(payment_mode="CREDIT", invoice_number__gte=f'{instance.branch.branch_code}-{instance.terminal}-{start_bill_number}',
                    #     invoice_number__lte=f'{instance.branch.branch_code}-{instance.terminal}-{end_bill_number}', branch=instance.branch).values('invoice_number', 'customer_name', 'grand_total')
                bills = Bill.objects.filter(
                    payment_mode="CREDIT",
                    invoice_number__range=[
                        f'{endday.branch.branch_code}-{endday.terminal}-{start_bill_number}',
                        f'{endday.branch.branch_code}-{endday.terminal}-{end_bill_number}'
                    ],
                    branch=endday.branch
                ).values('invoice_number', 'customer_name', 'grand_total')
                print("before sorting", bills)
                sorted_bills = sorted(bills, key=itemgetter('customer_name'))
                    
                print("after sorting", sorted_bills)
                    # Group bills by customer_name
                grouped_bills = {}
                for key, group in groupby(sorted_bills, key=itemgetter('customer_name')):
                        # Convert the group iterator to a list of dictionaries
                    bills_data = list(group)
                    
                        # Calculate the total amount for each customer's bills
                    total_amount = sum(bill_data['grand_total'] for bill_data in bills_data)
                    
                        # Store the grouped data in a dictionary
                    grouped_bills[key] = {
                        'bills_data': bills_data,
                        'total_amount': total_amount
                    }
    
    #until here
    
                report_data = {
                    'dine_totalsale': endday.dine_grandtotal,
                    'delivery_totalsale': endday.delivery_grandtotal,
                    'takeaway_totalsale': endday.takeaway_grandtotal,
                    'dine_netsale': endday.dine_nettotal, 
                    'delivery_netsale': endday.delivery_nettotal, 
                    'takeaway_netsale': endday.takeaway_nettotal, 
                    'dine_vat': endday.dine_vattotal,
                    'delivery_vat': endday.delivery_vattotal,
                    'takeaway_vat': endday.takeaway_vattotal,   
                    'total_sale': endday.total_sale,
                    'date_time':endday.date_time,
                    'employee_name': endday.employee_name,
                    'net_sales': endday.net_sales,
                    'tax': endday.vat,  
                    'total_discounts': endday.total_discounts,
                    'cash': endday.cash,
                    'credit': endday.credit,
                    'credit_card': endday.credit_card,
                    'mobile_payment': endday.mobile_payment,
                    'complimentary': endday.complimentary,
                    'start_bill': endday.start_bill,
                    'end_bill': endday.end_bill,
                    'branch': endday.branch.name,
                    'terminal': endday.terminal,
                    'total_transactions': total_transactions,
                    'total_grand_total_by_category':total_grand_total_by_category,
                    'grouped_bills': grouped_bills,
                    'food_sale': endday.food_sale,
                    'beverage_sale': endday.beverage_sale,
                    'others_sale': endday.others_sale,
                    'cash_total': cash_total,
                    'latest_balance': latest_balance,
                    'opening_balance': opening_balance,
                    'total_expense': total_expense,
                    'no_of_guest': endday.no_of_guest,
                    'total_cashdrop': total_cashdrop  # Include the total expense and cashdrop in report_data
    
                }
    
    
    
                enddays_terminal.append(report_data)
                total_sale_holder += endday.total_sale
                net_sales_holder += endday.net_sales
                discount_holder += endday.total_discounts
                tax_holder += endday.vat
    
                combine_data = {
                    'org_name':org,
                    'date_now': date_now,
                    'time_now': time_now,
                    "total_sale": total_sale_holder,
                    "net_sales": net_sales_holder,
                    "tax": tax_holder,
                    "total_discounts": discount_holder
    
                }
    
                # print()
    
    
                # Inside the create_profile function
          
                # Thread(target=send_combined_mail_to_receipients, args=(combine_data, enddays_terminal, mail_list, sender)).start()
            print(f"mail_list {mail_list}")
    
        print(f"enddays_terminal {enddays_terminal}")
        try:
            Thread(target=send_combined_mail_to_receipients, args=(combine_data, enddays_terminal, mail_list, sender)).start()
            print("Mail Sent")
        except Exception as e:
            print(f"Error in sending combined mail: {e}")
    else:
        print("Endday has not been created")