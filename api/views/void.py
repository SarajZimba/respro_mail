from rest_framework.views import APIView
from bill.models import BillItemVoid
from rest_framework.response import Response
from django.db.models import Sum
import jwt
class VoidBillAPIView(APIView):
    def get(self, request, *args, **kwargs):
        jwt_token = request.META.get("HTTP_AUTHORIZATION")
        jwt_token = jwt_token.split()[1]
        try:
            token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
            # You can access other claims as needed

            # Assuming "branch" is one of the claims, access it
            branch = token_data.get("branch")
            agent = token_data.get("name")

            # Print the branch
            print("Branch:", branch)
            print("Agent:", agent)
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.DecodeError:
            print("Token is invalid.")

        # billitemvoids = BillItemVoid.objects.filter(status=True, is_deleted=False, order__branch=branch).values('product__title').annotate(total_quantity=Sum('quantity'))
        billitemvoids = BillItemVoid.objects.filter(status=True, is_deleted=False, order__branch=branch)
        void_list = []
        for itemvoids in billitemvoids:
            void_dict = {
                "product__title":itemvoids.product.title,
                "quantity": itemvoids.quantity,
                "start_time": itemvoids.order.created_at.strftime("%Y-%m-%d %I:%M %p"),
                "table_no": itemvoids.order.table_no,
                "reason": itemvoids.reason,
                "employee": itemvoids.order.employee

            }
            void_list.append(void_dict)
        # print(billitemvoids)

        
        return Response(void_list, 200)

