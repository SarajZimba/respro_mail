from rest_framework.response import Response
from rest_framework.views import APIView
from bill.models import VoidBillTracker, Bill, TablReturnEntry, Order, OrderDetails, BillItemVoid
from rest_framework import status
from product.models import Product
from organization.models import Table, Terminal


class MakeVoidBill(APIView):

    def post(self, request, order_id, format=None):
        data = request.data

        reason = data.get("voidReason")
        bill = Bill.objects.get(order__id=order_id)
        bill_id = bill.id
        voidbillobj = VoidBillTracker.objects.create(prev_bill=bill.invoice_number, prev_bill_id=bill_id, bill_prev=bill)

        # bill = Bill.objects.get(invoice_number=biinvoice_number, fiscal_year=fiscal_year)
        bill.status = False
        bill.save()

        miti = bill.transaction_miti
        quantity = bill.bill_items.count()
        return_entry = TablReturnEntry(
            bill_date=bill.transaction_date,
            bill_no=bill.invoice_number,
            customer_name=bill.customer_name,
            customer_pan=bill.customer_tax_number,
            amount=bill.grand_total,
            NoTaxSales=0,
            ZeroTaxSales=0,
            taxable_amount=bill.taxable_amount,
            tax_amount=bill.tax_amount,
            miti=miti,
            ServicedItem="Goods",
            quantity=quantity,
            reason=reason,
            fiscal_year=bill.fiscal_year
        )
        try:
            return_entry.save()
        except Exception as e:
            print(e)

        voidbillobj_id = voidbillobj.id
        return Response({"voidbillobj_id": voidbillobj_id}, status=status.HTTP_201_CREATED)
        
class VoidBillItemView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data

        void_item = data.get('void_item')
        orderdetails_items = data.get('orderdetails_items')
        order = data.get('order')
        try:
            order_obj = Order.objects.get(id=order)
        except Order.DoesNotExist:
            return Response({"error": f"Order with ID {order} does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        OrderDetails.objects.filter(order=order_obj).delete()
        if orderdetails_items == []:
            # order = Order.objects.get(id=order)
            table_no = order_obj.table_no
            terminal_no = order_obj.terminal_no
            branch = order_obj.branch
            table = Table.objects.get(terminal=Terminal.objects.get(terminal_no=terminal_no, branch=branch, is_deleted=False, status=True), table_number=table_no)
            table.is_estimated = False
            table.is_occupied = False
            table.save()
            order_obj.status=False
            order_obj.save()
        else:

            for item in orderdetails_items:
    
                product = item['product']
                product_quantity = item['product_quantity']
                kotID = item['kotID']
                botID = item['botID']
                modification = item['modification']
                ordertime = item['ordertime']
                employee = item['employee']
    
    
                order_item = OrderDetails.objects.create(order=order_obj, product=Product.objects.get(id=product), product_quantity=product_quantity, kotID=kotID, botID=botID, modification=modification, ordertime=ordertime, employee=employee)


        # for void_item in void_items:

        qty = void_item['quantity']
        product = void_item['product']
        count = void_item['count']
        isBefore = void_item['isBefore']
        reason = void_item['reason']
        BillItemVoid.objects.create(quantity=qty, product=Product.objects.get(id=product), count=count, isBefore=isBefore, order=order_obj, reason=reason)

        return Response("VoidItems Created Successfully", status=status.HTTP_200_OK)


