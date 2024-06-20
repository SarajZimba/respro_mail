from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from api.serializers.order import OrderDetailsSerializer,OrderSerializer
from bill.models import Order, OrderDetails
from django.db import transaction
from organization.models import Terminal, Branch
from product.models import Product

class OrderCreateAPIView(APIView):
    def post(self, request, format=None):
        order_serializer = OrderSerializer(data=request.data)
        if order_serializer.is_valid():
            order = order_serializer.save()
            order_details_data = request.data.get('order_details', [])

            for order_detail_data in order_details_data:
                order_detail_data['order'] = order.id
            order_details_serializer = OrderDetailsSerializer(data=order_details_data, many=True)
            if order_details_serializer.is_valid():
                order_details_serializer.save()

                return Response(order_serializer.data, status=status.HTTP_201_CREATED)
            
            else:
                order.delete()
                return Response(order_details_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


    def patch(self, request, format=None):
        order_details_data = request.data
        # if not order_id:
        #     return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        for order_detail_data in order_details_data:
            order_id = order_detail_data.get('order')
            if not order_id:
                return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        order_details_serializer = OrderDetailsSerializer(data=request.data, many=True)
        if order_details_serializer.is_valid():
            with transaction.atomic():
                # Delete existing OrderDetails associated with the specified Order ID
                for order_detail_data in order_details_data:
                    OrderDetails.objects.filter(order=order_detail_data['order']).delete()

                # Save new OrderDetails
                order_details_serializer.save()

            return Response(order_details_serializer.data, status=status.HTTP_201_CREATED)
            
        else:
            return Response(order_details_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            
class SplitBillAPIView(APIView):
    
    @transaction.atomic()
    def post(self, request, format=None):
        try:
            data = request.data
            splitted_order_id = data['splitted_order_id']
            remaining_order = data.get("remaining_orders", [])
            split_order = data.get("split_order", {})

            # Delete the original orderdetails
            original_order = Order.objects.get(id=splitted_order_id)
            original_order_details = OrderDetails.objects.filter(order=splitted_order_id)
            original_order_details.delete()

            for order_detail_data in remaining_order:
                order_detail_data.pop("order")
                product_id = order_detail_data.pop("product")
                product = Product.objects.get(pk=product_id)
                order_detail_data["product"] = product

                OrderDetails.objects.create(order=original_order, **order_detail_data)



            branch_id = split_order.pop("branch")
            branch = Branch.objects.get(pk=branch_id)
            
            terminal_id = split_order.pop("terminal_no")
            terminal = Terminal.objects.get(terminal_no=terminal_id, branch=branch, is_deleted=False, status=True)

            # Create order with related objects
            split_order["terminal"] = terminal   
            split_order["branch"] = branch
            split_order["terminal_no"] = terminal_id

            order_details_data = split_order.pop("order_details", [])

            order = Order.objects.create(**split_order)

    
            for order_detail_data in order_details_data:
                order_detail_data.pop("order")
                product_id = order_detail_data.pop("product")
                product = Product.objects.get(pk=product_id)
                order_detail_data["product"] = product

                OrderDetails.objects.create(order=order, **order_detail_data)

            details = {
                        "order_id": order.id,
                        "sale_id": order.sale_id,
                        "is_saved":order.is_saved
                    }
            return Response(details, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
from user.models import Customer
class UpdateCustomerOrder(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data

        customer = data['customer']
        order = data['order']
        try:

            order_obj = Order.objects.get(pk=int(order))
        except Exception as e:
            return Response("No order found with such id", 400)
        try:
            customer_obj = Customer.objects.get(pk=int(customer))
        except Exception:
            return Response("No customer found with that id", 400)
        
        order_obj.customer = customer_obj
        order_obj.save()

        return Response("Customer has been updated successfully", 200)


    