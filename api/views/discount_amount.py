# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from discount.models import DiscountTable
# from api.serializers.discount import DiscountSerilizer
# from rest_framework import status


# class DiscountApiView(APIView):
#     permission_classes = [IsAuthenticated]
    

#     def get(self, request):
#         discount = DiscountTable.objects.filter(is_deleted=False)
#         serilizer = DiscountSerilizer(discount, many=True)

#         return Response(serilizer.data, status=status.HTTP_200_OK)
    
# DiscountApiView=DiscountApiView.as_view()


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from discount.models import DiscountTable
from api.serializers.discount import DiscountSerilizer
from rest_framework import status

# api to get all the discounts
class DiscountApiView(APIView):
    permission_classes = [IsAuthenticated]
    

    def get(self, request):
        discount = DiscountTable.objects.filter(is_deleted=False)
        serilizer = DiscountSerilizer(discount, many=True)

        return Response(serilizer.data, status=status.HTTP_200_OK)
    
DiscountApiView=DiscountApiView.as_view()

# dicount creating api
class DiscountCreateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data

        serializer = DiscountSerilizer(data=data)
        try:
            if serializer.is_valid():
                serializer.save()

                return Response("Discount added", status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"Error in data {e}", status=status.HTTP_400_BAD_REQUEST)

# discount updating Api   
class DiscountUpdateApiView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        discount_id = kwargs.get('pk')
        discount = DiscountTable.objects.get(pk=discount_id)

        data =request.data
        
        serializer = DiscountSerilizer(discount, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response("Discount Updated", status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Discount deleting Api
class DiscountDeleteApiView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        discount_id = kwargs.get('pk')
        discount = DiscountTable.objects.get(pk=discount_id)
        try:
            discount.is_deleted=True
            discount.status = False
            discount.save()
            return Response("Discount has been deleted", status=status.HTTP_200_OK)

        except Exception as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)




