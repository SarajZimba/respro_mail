from datetime import datetime
from api.serializers.bill import (
    BillDetailSerializer,
    BillItemSerializer,
    PaymentTypeSerializer,
    BillSerializer,
    TablReturnEntrySerializer,
    TblSalesEntrySerializer,
    TblTaxEntrySerializer,
    TblTaxEntryVoidSerializer,
    BillCheckSumSerializer
)
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response


from bill.models import Bill, PaymentType, TablReturnEntry, TblSalesEntry, TblTaxEntry, ConflictBillNumber, Order, OrderDetails
from organization.models import Branch, Organization, Terminal, Table
from product.models import BranchStockTracking, Product
from django.shortcuts import get_object_or_404
from django.db import transaction



class PaymentTypeList(ListAPIView):
    serializer_class = PaymentTypeSerializer
    queryset = PaymentType.objects.active()


class BillInfo(APIView):
    def get(self, request):
        branch_code = self.request.query_params.get("branch_code")
        terminal = self.request.query_params.get("terminal")
        branch_and_terminal = f"{branch_code}-{terminal}"
        if not branch_code or not terminal:
            return Response({"result": "Please enter branch code and terminal"},400)
        branch = get_object_or_404(Branch, branch_code=branch_code)
        current_fiscal_year = Organization.objects.last().current_fiscal_year
        last_bill_number = Bill.objects.filter(terminal=terminal, fiscal_year = current_fiscal_year, branch=branch).order_by('-bill_count_number').first()
        if last_bill_number:
            return Response({"result": last_bill_number.invoice_number})
        return Response({"result": 0})


class BillAPI(ModelViewSet):
    serializer_class = BillSerializer
    queryset = Bill.objects.active()

    def get_queryset(self, *args, **kwargs):
        queryset = Bill.objects.filter(
            is_deleted=False, status=True, agent=self.request.user
        )
        return queryset

    def get_serializer_class(self):
        detail_actions = ["retrieve", "list"]
        if self.action in detail_actions:
            return BillDetailSerializer
        return super().get_serializer_class()


class TblTaxEntryAPI(ModelViewSet):
    pagination_class = None
    serializer_class = TblTaxEntrySerializer
    queryset = TblTaxEntry.objects.all()

class TblTaxEntryUpdateView(APIView):
    
    def patch(self, request, bill_no):
        serializer = TblTaxEntryVoidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trans_date = serializer.validated_data.get('trans_date')
        org = Organization.objects.first()
        fiscal_year = org.current_fiscal_year

        try:
            bill_date = trans_date[:10]
            bill_date = datetime.strptime(bill_date, "%Y-%m-%d").date()
        except Exception:
            return Response({'message':'Date time format incorrect'}, status=400)
            

        instance = TblTaxEntry.objects.filter(bill_no=bill_no, bill_date=bill_date)

        if not instance:
            return Response({'message':'No data available with provided details'}, status=404)
        instance = instance.first()

        is_active_data = serializer.validated_data.get("is_active")
        reason = serializer.validated_data.get("reason")


        if is_active_data == "no":
            miti = ""
            quantity = 1
            try:
                print("TRY VITRA XU MA\n\n")
                obj = TblSalesEntry.objects.get(
                    bill_no=instance.bill_no, customer_pan=instance.customer_pan
                )
                print(obj)

                obj = Bill.objects.get(
                    invoice_number=instance.bill_no,
                    customer_tax_number=instance.customer_pan,
                    fiscal_year=fiscal_year
                )
                obj.status = False
                obj.save()
                # obj.save()

                print(obj)
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

            except:
                print("exception")
        instance.save()


        return Response({'message':'Successful'})


class TblSalesEntryAPI(ModelViewSet):
    serializer_class = TblSalesEntrySerializer
    queryset = TblSalesEntry.objects.all()


class TablReturnEntryAPI(ModelViewSet):
    serializer_class = TablReturnEntrySerializer
    queryset = TablReturnEntry.objects.all()


# class BulkBillCreateView(APIView):

#     def post(self, request):
#         bills = request.data.get('bills', [])
#         print("bills", bills)
#         if not bills:
#             return Response({'details':"Bills is required"}, status=400)
#         conflict_invoices = []
#         for bill in bills:
#             serializer = BillSerializer(data=bill, context={'request':request})
#             if serializer.is_valid():
#                 print("serializer_data are ", serializer.data)
#                 serializer.save()
#             else:
#                 print("These are the serializers errors:", serializer.errors)
#                 conflict_invoices.append(bill['invoice_number'])
#                 ConflictBillNumber.objects.create(invoice_number=bill['invoice_number'])
#         if conflict_invoices:
#             return Response({'details': conflict_invoices}, status=409)

#         return Response({'details': 'Bills Created'}, status=201)
        
class BulkBillCreateView(APIView):

    @transaction.atomic()
    def post(self, request):
        bills = request.data.get('bills', [])
        print("bills", bills)
        if not bills:
            return Response({'details':"Bills is required"}, status=400)
        conflict_invoices = []
        orders_list = []
        orderdetails_list = []
        for bill in bills:
            is_saved = bill['orders']['is_saved'] #is_saved true denotes that the bill is not saved in the database. 

            if is_saved is not True:
                serializer = BillSerializer(data=bill, context={'request':request})
                if serializer.is_valid():
                    print("serializer_data are ", serializer.validated_data)
                    serializer.save()
                else:
                    print("These are the serializers errors:", serializer.errors)
                    conflict_invoices.append(bill['invoice_number'])
                    ConflictBillNumber.objects.create(invoice_number=bill['invoice_number'])
            else:
                order = bill["orders"]

                if order.get('id') is None:
                    print(f"The order is null")
                    table_no = order['table_no']
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
                    terminal_no = order['terminal_no']

                    order_obj = Order.objects.create(table_no=table_no, date=date, sale_id=sale_id, terminal=Terminal.objects.get(terminal_no=terminal_no), start_datetime=start_datetime, is_completed=is_completed, no_of_guest=no_of_guest, branch=Branch.objects.get(pk=branch), employee=employee, order_type=order_type, is_saved=is_saved, terminal_no=terminal_no)

                    for order_detail_data in order.get('order_details'):
                        product = order_detail_data['product']
                        product_quantity = order_detail_data['product_quantity']
                        kotID = order_detail_data['kotID']
                        botID = order_detail_data['botID']
                        modification = order_detail_data['modification']
                        ordertime = order_detail_data['ordertime']
                        employee = order_detail_data['employee']
                        OrderDetails.objects.create(order=order_obj, product=Product.objects.get(pk=product), product_quantity=product_quantity, kotID=kotID, ordertime=ordertime, employee=employee, botID=botID, modification=modification)
                        # orderdetails_dict = {
                        #     'orderdetails'
                        # }
                    details = {
                        "order_id": order_obj.id,
                        "sale_id": order_obj.sale_id,
                        "is_saved": "false"
                    }

                    orders_list.append(details)

                else:
                    id = order.get('id')
                    print(f"The order is not None . It is {id}")
                    # print("This is the order is", order)
                    order_obj = Order.objects.get(id=id)
                    OrderDetails.objects.filter(order=order_obj).delete()

                    # OrderDetails.objects.filter(order=order).delete()
                    
                if order.get('order_details') == []:
                    type = order_obj.order_type
                    table_no = order_obj.table_no
                    terminal_no = order_obj.terminal_no
                    branch = order_obj.branch
                    # table = Table.objects.get(terminal=Terminal.objects.get(terminal_no=terminal_no, branch=branch, is_deleted=False, status=True), table_number=table_no)
                    # table.is_estimated = False
                    # table.is_occupied = False
                    if type == "Dine In":
                        table = Table.objects.get(terminal=Terminal.objects.get(terminal_no=terminal_no, branch=branch, is_deleted=False, status=True), table_number=table_no, status=True, is_deleted=False)
                        table.is_estimated = False
                        table.is_occupied = False
                        table.save()
                    # table.save()
                    order_obj.status=False
                    order_obj.save()

                else:                  
    
                    # for order_detail_data in order.get('order_details'):
                    #     product = order_detail_data['product']
                    #     product_quantity = order_detail_data['product_quantity']
                    #     kotID = order_detail_data['kotID']
                    #     ordertime = order_detail_data['ordertime']
                    #     employee = order_detail_data['employee']
                    #     modification = order_detail_data['modification']
                    #     OrderDetails.objects.create(order=order_obj, product=product, product_quantity=product_quantity, kotID=kotID, ordertime=ordertime, employee=employee, modification=modification)
        

                    for order_detail_data in order.get('order_details'):
                        product = order_detail_data['product']
                        product_quantity = order_detail_data['product_quantity']
                        kotID = order_detail_data['kotID']
                        botID = order_detail_data['botID']
                        modification = order_detail_data['modification']
                        ordertime = order_detail_data['ordertime']
                        employee = order_detail_data['employee']
                        OrderDetails.objects.create(order=order_obj, product=Product.objects.get(pk=product), product_quantity=product_quantity, kotID=kotID, ordertime=ordertime, employee=employee, botID=botID, modification=modification)

                    
                    

        if conflict_invoices:
            return Response({'details': conflict_invoices}, status=409)

        # return Response({'details': 'Bills Created'}, status=201)
        return Response(orders_list, status=201)


from datetime import date
class BillCheckSumView(APIView):

    def post(self, request):
        print(request.data)
        fiscal_year = Organization.objects.last().current_fiscal_year

        bills = request.data.get('bills', [])
        if not bills:
            return Response({'details':"Bills is required"}, status=400)
        print('After bill check')
        new_invoice_list:list = []
        for bill in bills:
            invoice_num = bill.get('invoice_number', None)
            fiscal_year = bill.get('fiscal_year', fiscal_year)
            print(bill)
            if not Bill.objects.filter(invoice_number=invoice_num, fiscal_year=fiscal_year).exists():
                if bill.get('payment_mode').lower() == "complimentary":
                    if Bill.objects.filter(fiscal_year=fiscal_year, transaction_date_time=bill.get('transaction_date_time')).exists():
                        continue
                new_invoice_list.append(invoice_num)
                serializer = BillSerializer(data=bill, context={'request':request})
                print('******')
                print(bill)
                try:
                    print(serializer.errors)
                except Exception:
                    pass
                serializer.is_valid(raise_exception=True)
                try:
                    serializer.save()
                except Exception as e:
                    pass
        return Response({'details': 'ok', 'created_invoices':new_invoice_list})