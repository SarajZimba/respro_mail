from datetime import date

from django.forms.models import model_to_dict
from rest_framework.response import Response
from api.serializers.product import (
    CustomerProductDetailSerializer,
    CustomerProductSerializer,
    ProductSerializer,
    ProductCategorySerializer,
    ProductReconcileSerializer,
    BulkItemReconcilationApiItemSerializer,
    ProductSerializerCreate,
    ProductMasterSerializer,


)
from rest_framework.views import APIView

from rest_framework.generics import ListAPIView, RetrieveAPIView

from product.models import CustomerProduct, Product,ProductMultiprice, BranchStockTracking, BranchStock, ItemReconcilationApiItem, ProductCategory
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import json
from django.shortcuts import get_object_or_404
from organization.models import Branch

class ProductMultipriceapi(ListAPIView):
    def get(self, request):
        try:
            products_list = Product.objects.all().values(
        "id",
        "title",
        "slug",
        "description",
        "image",
        "price",
        "is_taxable",
        "product_id",
        "unit",
        "category",
        "barcode"
        )
            temp_data = products_list
            for index,item in enumerate(products_list):
                print(item["id"])
                queryset = ProductMultiprice.objects.filter(product_id=item["id"]).values()
                temp_data[index]["multiprice"]=queryset
            return Response(temp_data,200)

        except Exception as error:
            return Response({"message":str(error)})

from root.utils import get_image_bytes

class ProductTypeListView(ListAPIView):
    serializer_class = ProductCategorySerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
       
        products = Product.objects.active().all()

        item_type ={
            "FOOD":{
                "title":"FOOD",
                "group": []
            },
            "BEVERAGE":{
                "title":"BEVERAGE",
                "group": []
            },
            "OTHERS": {
                "title":"OTHERS",
                "group": []
            }
        }
        type_group = {"FOOD": [],"BEVERAGE": [],"OTHERS": []}

        product_list = []

        for product in products:
            product_dict =  model_to_dict(product)
            del product_dict['image']
            product_dict['thumbnail'] = get_image_bytes(product)
            product_dict['type'] = product.type.title
            product_list.append(product_dict)


        for product in product_list:
            if  product['group'] not in type_group[product['type']]:
                type_group[product['type']].append(product['group'])
                item_type[product['type']]['group'].append({"title":product['group'], "items":[]})
        
        for product in product_list:
            group_list = item_type[product['type']]['group']
            for i in group_list:
                if i['title'] == product['group']:
                    i['items'].append(product)



            
        return Response(item_type)

        


class ProductList(ListAPIView):
    serializer_class = ProductSerializer
    pagination_class = None

    def get_queryset(self):
        return Product.objects.active().filter(is_billing_item=True)
     
        
    
    


class ProductDetail(RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return Product.objects.active()


class CustomerProductAPI(ModelViewSet):
    serializer_class = CustomerProductSerializer
    queryset = CustomerProduct.objects.active()

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):

        is_added = CustomerProduct.objects.filter(
            is_deleted=False,
            status=True,
            customer=request.data["customer"],
            product=request.data["product"],
        )

        if not is_added:
            return super().create(request, *args, **kwargs)
        else:
            return Response(
                {"message": "This product is already added to the customer"},
            )

    def get_queryset(self, *args, **kwargs):
        customer_id = self.request.query_params.get("customerId")
        if customer_id:
            queryset = CustomerProduct.objects.filter(
                is_deleted=False, status=True, customer=customer_id
            )

            return queryset
        else:
            return super().get_queryset()

    def get_serializer_class(self):
        detail_actions = ["retrieve", "list"]
        if self.action in detail_actions:
            return CustomerProductDetailSerializer
        return super().get_serializer_class()




class BranchStockTrackingView(APIView):
    """
    Useless view
    """
    def post(self, request):
        serializer = ProductReconcileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        products = serializer.validated_data.get('products', [])

        for p in products:
            date = p.get('date')
            branch = p.get('branch')
            product = p.get('product')
            wastage = p.get('wastage', 0)
            returned = p.get('returned', 0)
            physical = p.get('physical', 0)
            latest_entry = BranchStockTracking.objects.filter(branch=branch, product=product, date__lt=date).order_by('-date').first()
            if latest_entry:
                """ Goes everytime in if ** INCOMPLETE ** """
                new_opening = latest_entry.physical

                try:
                    branch_stock = BranchStockTracking.objects.get(branch=branch, product=product, date=date)
                    closing = new_opening-wastage-returned-branch_stock.sold+branch_stock.received
                    discrepancy = physical - closing
                    branch_stock.opening = new_opening
                    branch_stock.wastage =  wastage
                    branch_stock.returned = returned
                    branch_stock.physical = physical
                    branch_stock.closing = closing
                    branch_stock.discrepancy = discrepancy
                    branch_stock.save()
                except BranchStockTracking.DoesNotExist:
                    closing = new_opening-wastage
                    discrepancy = physical - closing
                    BranchStockTracking.objects.create(
                        branch=branch, product=product,
                        opening=new_opening, date=date,
                        wastage=wastage, returned=returned,
                        physical=physical, closing=closing, discrepancy=discrepancy
                    )
                
        return Response({'details':'success'}, 201)



# from organization.models import EndDayRecord, EndDayDailyReport, CashDrop
# class ApiItemReconcilationView(APIView):

#     def post(self, request):
#         serializer = BulkItemReconcilationApiItemSerializer(data=request.data)
        
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         print("data:",serializer.validated_data)
#         EndDayRecord.objects.create(branch_id = serializer.validated_data.get('branch'),
#                                      terminal=serializer.validated_data.get('terminal'),
#                                      date = serializer.validated_data.get('date')
#                                      )
#         report_total = serializer.validated_data.get("report_total")
#         new_data = {'branch_id':serializer.validated_data.get('branch'),'terminal':serializer.validated_data.get('terminal'), **report_total}
#         try:
#             EndDayDailyReport.objects.create(**new_data)
#         except Exception as e:
#             print(e)
#         cashdrops = CashDrop.objects.filter(is_end_day=False)
#         cashdrops.update(is_end_day=True)
#         return Response({'details':'success'}, 201)

from organization.models import EndDayRecord, EndDayDailyReport, CashDrop, Terminal
from bill.models import Bill
class ApiItemReconcilationView(APIView):

    def post(self, request):
        serializer = BulkItemReconcilationApiItemSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()

        print("data:",serializer.validated_data)
        EndDayRecord.objects.create(branch_id = serializer.validated_data.get('branch'),
                                     terminal=serializer.validated_data.get('terminal'),
                                     date = serializer.validated_data.get('date')
                                     )
        report_total = serializer.validated_data.get("report_total")
        print(report_total)
        new_data = {'branch_id':serializer.validated_data.get('branch'),'terminal':serializer.validated_data.get('terminal'), **report_total}
        try:
            EndDayDailyReport.objects.create(**new_data)
            cashdrops = CashDrop.objects.filter(is_end_day=False)
            cashdrops.update(is_end_day=True)
            latest_cash_drop = CashDrop.objects.filter(branch_id=serializer.validated_data.get('branch'), terminal=serializer.validated_data.get('terminal')).last()
            print("I am getting the cash", report_total.get('cash', 0))
            print("before", latest_cash_drop.latest_balance)
            latest_cash_drop.latest_balance += report_total.get('cash', 0)
            print("after", latest_cash_drop.latest_balance)
            latest_cash_drop.save1()
        except Exception as e:
            print(e)
            
        Bill.objects.filter(branch=serializer.validated_data.get('branch'), terminal=serializer.validated_data.get('terminal'), is_end_day=False).update(is_end_day=True)


        return Response({'details':'success'}, 201)


class CheckAllowReconcilationView(APIView):

    def get(self, request):
        today_date = date.today()
        branch_id = request.GET.get('branch_id', None)
        terminal_id = request.GET.get('terminal_id', None)
        if not branch_id:
            return Response({'detail':'Please provide branch_id in url params'}, 400)
        if not terminal_id:
            return Response({'detail':'Please provide terminal_id in url params'}, 400)
        branch = get_object_or_404(Branch, pk=branch_id)
        if ItemReconcilationApiItem.objects.filter(date=today_date, branch = branch, terminal=terminal_id).exists():
            return Response({'detail':'Items already reconciled for today!! Please Contact Admin'}, 400)
        return Response({'details':'ok'}, 200)


@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_product_requisition(request):
    data = request.data.get('data', None)
    if data:
        data = json.loads(data)
        for d in data:
            quantity = int(d['quantity'])
            BranchStock.objects.create(branch_id=d['branch_id'], product_id=d['product_id'], quantity=quantity)
        return Response({'detail':'ok'}, 201)
    return Response({'detail':'Invalid data'}, 400)

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

class ProductCreateAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()  # Create a mutable copy of the request data
        type_id = data.pop('type', None)
        
        # Extract other fields from the request data
        title = data.pop('title', [None])[0]
        slug = data.pop('slug', [None])[0]
        description = data.pop('description', [None])[0]
        price = float(data.pop('price', [0.0])[0])
        unit = data.pop('unit', [None])[0]
        barcode = data.pop('barcode', [None])[0]
        group = data.pop('group', [None])[0]
        image = data.get('image', None)  # Get the image from the request data
        is_taxable = data.pop('is_taxable', None)[0] 
        reconcile = data.pop('reconcile', None)[0] 
        is_produced = data.pop('is_produced', None)[0] 
        is_billing_item = data.pop('is_billing_item', None)[0] 
        cost_price = float(data.pop('cost_price', [0.0])[0])  
        discount_exempt = data.pop('discount_exempt', None)[0] 

        # Convert type_id to a ProductCategory instance
        try:
            product_type = ProductCategory.objects.get(title=type_id[0]) if isinstance(type_id, list) else ProductCategory.objects.get(title=type_id)
        except ProductCategory.DoesNotExist:
            return Response({'error': 'Invalid type ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare the data for the serializer
        product_data = {
            'title': title,
            'is_taxable':is_taxable,
            'reconcile': reconcile,
            'is_produced': is_produced,
            'description': description,
            'price': price,
            'cost_price': cost_price,
            'unit': unit,
            'barcode': barcode,
            'group': group,
            'type': product_type.id,  # Using ID to pass to the serializer
            'image': image,  # Add the image to the product data
            'is_billing_item':is_billing_item,
            'discount_exempt':discount_exempt

        }
        
        print(f"This is the product data {product_data} ")

        serializer = ProductSerializerCreate(data=product_data)
        if serializer.is_valid():
            product = serializer.save()
            return Response("Product Created", status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

class ProductUpdateAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def put(self, request, *args, **kwargs):
        product_id = kwargs.get('pk')
        product = get_object_or_404(Product, pk=product_id)
        
        data = request.data.copy()  # Create a mutable copy of the request data
        print(data)
        type_id = data.pop('type', None)
        
        # Check if 'image' field is provided in the request data
        if 'image' in data:
            if data['image'] != '':
            # If image is provided, use the provided value
                image_data = data['image']
            else :
                image_data = None
        else:
            if product.image != '':
                image_data = product.image
            else:
                image_data= None
            

        # Prepare the data for the serializer
        product_data = {
            'title': data.get('title', product.title),
            'slug': data.get('slug', product.slug),
            'description': data.get('description', product.description),
            'price': float(data.get('price', product.price)),
            'cost_price': float(data.get('cost_price', product.cost_price)),
            'unit': data.get('unit', product.unit),
            'barcode': data.get('barcode', product.barcode),
            'group': data.get('group', product.group),
            'image': image_data,
            'is_taxable': data.get('is_taxable', product.is_taxable),
            'reconcile': data.get('reconcile', product.reconcile),
            'is_produced': data.get('is_produced', product.is_produced),
            'is_billing_item': data.get('is_billing_item', product.is_billing_item),
            'discount_exempt': data.get('discount_exempt', product.discount_exempt),
        }

        if type_id:
            try:
                product_type = ProductCategory.objects.get(title=type_id[0])
                product_data['type'] = product_type.id
            except ProductCategory.DoesNotExist:
                return Response({'error': 'Invalid type ID'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductSerializerCreate(product, data=product_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response("Product Updated", status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ProductDeleteAPIView(APIView):

    def patch(self, request, *args, **kwargs):
        product_id = kwargs.get('pk')
        product = get_object_or_404(Product, pk=product_id)
        product.is_deleted = True
        product.status = False
        product.save()
        return Response("Product Deleted", status=status.HTTP_200_OK)
        
class ProductMasterList(ListAPIView):
    serializer_class = ProductMasterSerializer
    pagination_class = None

    def get_queryset(self):
        return Product.objects.active()
        
class ProductGroupAPIView(APIView):
    def get(self, request, *args, **kwargs):
        products =Product.objects.filter(status=True, is_deleted=False)
        product_groups = []
        for product in products:
            if product.group not in product_groups:
                product_groups.append(product.group)
        return Response(product_groups, 200)


