from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from bill.forms import TblTaxEntryForm
from bill.models import (
    Bill,
    BillItem,
    BillItemVoid,
    PaymentType,
    TablReturnEntry,
    TblSalesEntry,
    TblTaxEntry,
    BillPayment,
    Order,
    OrderDetails,
    VoidBillTracker

)
from bill.utils import create_split_payment_accounting
from product.models import BranchStockTracking, BranchStock
from organization.models import Organization, Terminal, Table
from datetime import date
from django.db.utils import IntegrityError
from api.serializers.order import CustomOrderSerializer

class PaymentTypeSerializer(ModelSerializer):
    class Meta:
        model = PaymentType
        fields = ["id", "title"]


class BillItemSerializer(ModelSerializer):
    item_void_key = serializers.IntegerField(required=False)
    class Meta:
        model = BillItem
        fields = [
            "product_quantity",
            "product",
            "rate",
            "amount",
            "kot_id",
            "bot_id",
            "item_void_key"
        ]

class BillItemVoidSerializer(ModelSerializer):
    item_void_key = serializers.IntegerField()
    class Meta:
        model = BillItemVoid
        fields = ["product", "quantity", "bill_item", "item_void_key", "count", "isBefore", "reason"]
        
class BillItemVoidSerializerTerminalSwitch(ModelSerializer):
    class Meta:
        model = BillItemVoid
        fields = ["product", "quantity", "bill_item", "count", "isBefore", "reason"]
        
# new lines added
        
from bill.models import MobilePaymentSummary
class MobilePaymentSummarySerializer(ModelSerializer):
    class Meta:
        model = MobilePaymentSummary
        fields = [
            "type",
            "value"
        ]



class BillPaymentSerializer(ModelSerializer):
    class Meta:
        model = BillPayment
        fields = ['payment_mode', 'rrn', 'amount']

from django.db import transaction
from user.models import Customer
from product.models import ProductPoints, CustomerProductPointsTrack
class BillSerializer(ModelSerializer):
    bill_items = BillItemSerializer(many=True)
    agent = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )
    items_void = BillItemVoidSerializer(many=True, required=False)
    split_payment = BillPaymentSerializer(many=True, write_only=True)
    orders = CustomOrderSerializer(required=False)
    voidBillTrackerid = serializers.IntegerField(required=False)

    #new line 
    mobile_payments = MobilePaymentSummarySerializer(many=True, write_only=True, required=False)


    class Meta:
        model = Bill
        exclude = [
            "created_at",
            "updated_at",
            "status",
            "is_deleted",
            "sorting_order",
            "is_featured",
            "organization",
            "order",
        ]
    @transaction.atomic
    def create(self, validated_data):
        try:
            print(f"This is the validated_data {validated_data}")
            bill_items = []
            # new line
            payment_data = []
            mobile_payments = validated_data.pop("mobile_payments", [])
            items_data = validated_data.pop("bill_items")
            items_void = validated_data.pop("items_void")
            split_payment = validated_data.pop("split_payment")
            payment_mode = validated_data.get('payment_mode') 
            invoice_no = validated_data.get('invoice_number')
            order = validated_data.pop("orders")
            loyalty_id = validated_data.pop('loyalty_id', None)
            voidBillTrackerid = validated_data.pop("voidBillTrackerid", None)
            table_no = order['table_no'] 
            branch = order['branch']
            terminal = order['terminal']
            terminal_no = order['terminal_no']
            print(f"voidBillTrackerid is {voidBillTrackerid}")
    
    
            print("This is the order", order)
    
    
            if order.get('id') is None:
                date = order['date']
                sale_id = order['sale_id']
                terminal = order['terminal']
                start_datetime = order['start_datetime']
                is_completed = order['is_completed']
                no_of_guest = order['no_of_guest']
                branch = order['branch']
                employee = order['employee']
                order_type = order['order_type']
                is_saved = order['is_saved']
                customer = order['customer']
    
                order_obj = Order.objects.create(table_no=table_no, date=date, sale_id=sale_id, terminal=terminal, start_datetime=start_datetime, is_completed=is_completed, no_of_guest=no_of_guest, branch=branch, employee=employee, order_type=order_type, is_saved=is_saved, terminal_no=terminal_no, customer=customer)
    
                for order_detail_data in order.get('order_details'):
                    product = order_detail_data['product']
                    product_quantity = order_detail_data['product_quantity']
                    kotID = order_detail_data['kotID']
                    ordertime = order_detail_data['ordertime']
                    employee = order_detail_data['employee']
                    modification = order_detail_data['modification']
                    OrderDetails.objects.create(order=order_obj, product=product, product_quantity=product_quantity, kotID=kotID, ordertime=ordertime, employee=employee, modification=modification)
    
            else:
                id = order.get('id')
                # print("This is the order is", order)
                order_obj = Order.objects.get(id=id)
                OrderDetails.objects.filter(order=order_obj).delete()
    
                # OrderDetails.objects.filter(order=order).delete()
                
                if order.get('order_details') == []:
                    table_no = order_obj.table_no
                    terminal_no = order_obj.terminal_no
                    branch = order_obj.branch
                    type = order_obj.order_type
                    if type == "Dine In":
                        table = Table.objects.get(terminal=Terminal.objects.get(terminal_no=terminal_no, branch=branch, is_deleted=False, status=True), table_number=table_no)
                        table.is_estimated = False
                        table.is_occupied = False
                        table.save()
                    # table = Table.objects.get(terminal=Terminal.objects.get(terminal_no=terminal_no, branch=branch, is_deleted=False, status=True), table_number=table_no)
                    # table.is_estimated = False
                    # table.is_occupied = False
                    # table.save()
                    order_obj.status = False
                    order_obj.save()

                else:                  
    
                    for order_detail_data in order.get('order_details'):
                        product = order_detail_data['product']
                        product_quantity = order_detail_data['product_quantity']
                        kotID = order_detail_data['kotID']
                        ordertime = order_detail_data['ordertime']
                        employee = order_detail_data['employee']
                        modification = order_detail_data['modification']
                        OrderDetails.objects.create(order=order_obj, product=product, product_quantity=product_quantity, kotID=kotID, ordertime=ordertime, employee=employee, modification=modification)
        
    
                # for order_detail_data in order.get('order_details'):
                #     product = order_detail_data['product']
                #     product_quantity = order_detail_data['product_quantity']
                #     kotID = order_detail_data['kotID']
                #     ordertime = order_detail_data['ordertime']
                #     employee = order_detail_data['employee']
                #     modification = order_detail_data['modification']
                #     OrderDetails.objects.create(order=order_obj, product=product, product_quantity=product_quantity, kotID=kotID, ordertime=ordertime, employee=employee, modification=modification)
    
    
            if not payment_mode.lower() == "complimentary":
                bill_count_no = int(validated_data.get('invoice_number').split('-')[-1])
                branch_name=branch.branch_code if branch else None
                invoice_number1 = f"{branch_name}-{terminal}-{bill_count_no}"
                customer_id = validated_data.get('customer')
                if customer_id is not None:
                    customer = Customer.objects.get(pk=customer_id.id)
        
                    if loyalty_id is not None:
                        product_for_points = ProductPoints.objects.get(pk=loyalty_id)
                        loyaltypoints_tobe_sub = product_for_points.points
                        starting_points_redeem = customer.loyalty_points
                        if starting_points_redeem < loyaltypoints_tobe_sub:
                            raise serializers.ValidationError({"detail":"You do not have sufficient points to claim the reward"})
                        customer.loyalty_points -= loyaltypoints_tobe_sub
                        customer.save()
                        product_redeemed = product_for_points.product
                        branchstock_entries = BranchStock.objects.filter(branch=branch, product=product_redeemed, is_deleted=False).order_by('quantity')

                        quantity_decreased = False
                        for branchstock in branchstock_entries:
                                available_quantity = branchstock.quantity
                                if available_quantity > 0 and not quantity_decreased:
                                    branchstock.quantity -= 1
                                    branchstock.save()
                                    quantity_decreased=True

                        if quantity_decreased == False:
                            raise serializers.ValidationError({"detail":"The product redeemed has no stock quantities"})
                        CustomerProductPointsTrack.objects.create(customer=customer, starting_points=starting_points_redeem, points=loyaltypoints_tobe_sub, action="Redeem", bill_no=invoice_number1, remaining_points=customer.loyalty_points)
        
                    grand_total = validated_data.get('grand_total')
                    loyalty_percentage = Organization.objects.last().loyalty_percentage
                    loyalty_points = (loyalty_percentage/100) * grand_total
                    starting_points_reward = customer.loyalty_points
                    customer.loyalty_points += loyalty_points
                    customer.save()
                    CustomerProductPointsTrack.objects.create(customer=customer, starting_points=starting_points_reward, points=loyalty_points, action="Reward", bill_no=invoice_number1, remaining_points=customer.loyalty_points)

            else:
                bill_count_no = None
    
            
            bill = Bill.objects.create(
                **validated_data, organization=Organization.objects.last(), bill_count_number=bill_count_no, print_count=3, order=order_obj
            )
            
            order_obj.is_saved = False
            order_obj.is_completed = True
            order_obj.save()
            
            # from organization.models import Table, Terminal
            # terminal_obj = Terminal.objects.get(branch=branch, terminal_no=terminal_no, is_deleted=False, status=True)
    
            # table = Table.objects.get(terminal__branch = branch, terminal=terminal_obj, table_number=table_no)
    
            # table.is_occupied = False
            # table.is_estimated = False
            # table.save()
            
            if order_obj.order_type == "Dine In":
                from organization.models import Table, Terminal
                terminal_obj = Terminal.objects.get(branch=branch, terminal_no=terminal_no, is_deleted=False, status=True)
        
                table = Table.objects.get(terminal__branch = branch, terminal=terminal_obj, table_number=table_no, status=True, is_deleted=False)
        
                table.is_occupied = False
                table.is_estimated = False
                table.save()

            if split_payment and payment_mode.lower() == "split":
                branch = invoice_no.split('-')[0]
                terminal = validated_data.get('terminal')
                tax_amount = validated_data.get('tax_amount')
                customer = validated_data.get('customer')
                discount_amount = validated_data.get('discount_amount')
                create_split_payment_accounting(split_payment, validated_data.get('grand_total'), branch, terminal, tax_amount, customer, discount_amount)
            for payment in split_payment:
                BillPayment.objects.create(bill=bill, payment_mode=payment['payment_mode'], rrn=payment['rrn'], amount=payment['amount'])
    
    
            for item in items_data:
                bill_item = BillItem.objects.create(
                    product=item['product'],
                    product_quantity=item["product_quantity"],
                    rate=item["rate"],
                    product_title=item["product"].title,
                    unit_title=item["product"].unit,
                    amount=item["product_quantity"] * item["rate"],
                    kot_id = item.get('kot_id', 0),
                    bot_id = item.get('bot_id', 0),
                )
                item_void_key = item.get('item_void_key')
                for void_item in items_void:
                    if void_item['item_void_key'] == item_void_key:
                        # BillItemVoid.objects.create(product=void_item['product'], bill_item=bill_item, quantity=void_item['quantity'] )
                        BillItemVoid.objects.create(product=void_item['product'], bill_item=bill_item, quantity=void_item['quantity'], count=void_item['count'], isBefore=void_item['isBefore'], reason=void_item['reason'],order=order_obj)

    
                bill_items.append(bill_item)
            bill.bill_items.add(*bill_items)
            
            if voidBillTrackerid is not None:
                voidbilltracker_obj = VoidBillTracker.objects.get(id=voidBillTrackerid, is_deleted=False, status=True)
                print(f"The invoice number is {bill.invoice_number}")
                voidbilltracker_obj.new_bill = bill.invoice_number
                voidbilltracker_obj.new_bill_id = bill.id
                voidbilltracker_obj.bill_new = bill          
                voidbilltracker_obj.save()
            # new line
            if payment_mode.lower() == "mobile payment" or payment_mode.lower() == "split":
                for item in mobile_payments:
                    mobile_payment = MobilePaymentSummary.objects.create(
                            type = item["type"],
                            value = item["value"],
                            bill= bill
                            # ,
                            # branch=validated_data.get('branch'),
                            # terminal = validated_data.get('terminal')
                        )
    
                    payment_data.append(mobile_payment)
            return bill
        except Exception as e:
            print("Error occured while creating bill for validated data", validated_data)
            raise e


class BillDetailSerializer(ModelSerializer):
    bill_items = BillItemSerializer(many=True)
    agent = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Bill
        fields = "__all__"


class TblTaxEntrySerializer(ModelSerializer):
    reason = serializers.CharField(required=False)

    class Meta:
        model = TblTaxEntry
        fields = "__all__"

    def update(self, instance, validated_data):
        is_active_data = validated_data.get("is_active")
        reason = validated_data.get("reason")
        if is_active_data == "no":
            miti = ""
            quantity = 1
            try:
                obj = TblSalesEntry.objects.get(
                    bill_no=instance.bill_no, customer_pan=instance.customer_pan
                )
                print(obj)

                obj = Bill.objects.get(
                    invoice_number=instance.bill_no,
                    customer_tax_number=instance.customer_pan,
                )
                obj.status = False
                obj.save()
                miti = obj.transaction_miti
                quantity = obj.bill_items.count()

                return_entry = TablReturnEntry(
                    bill_date=instance.bill_date,
                    bill_no=instance.bill_no,
                    customer_name=instance.customer_name,
                    customer_pan=instance.customer_pan,
                    amount=instance.amount,
                    NoTaxSales=0,
                    ZeroTaxSales=0,
                    taxable_amount=instance.taxable_amount,
                    tax_amount=instance.tax_amount,
                    miti=miti,
                    ServicedItem="Goods",
                    quantity=quantity,
                    reason=reason,
                )
                print(return_entry)
                return_entry.save()

            except Exception as e:
                print(e)
        instance.save()

        return super().update(instance, validated_data)


class TblTaxEntryVoidSerializer(ModelSerializer):
    reason = serializers.CharField(required=False)
    trans_date = serializers.CharField(required=True)
    class Meta:
        model = TblTaxEntry
        exclude = 'fiscal_year',

class TblSalesEntrySerializer(ModelSerializer):
    class Meta:
        model = TblSalesEntry
        fields = "__all__"


class TablReturnEntrySerializer(ModelSerializer):
    class Meta:
        model = TablReturnEntry
        fields = "__all__"


class BillCheckSumSerializer(serializers.Serializer):
    bills = BillSerializer(many=True)