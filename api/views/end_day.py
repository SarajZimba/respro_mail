from rest_framework import generics, status
from django.utils import timezone
from datetime import date
from api.serializers.end_day import EndDayDailyReportSerializer
from organization.models import EndDayDailyReport
from django.shortcuts import get_object_or_404
from organization.models import Branch, Terminal
from django.db.models import Q
from django.db.models import Sum
from organization.models import CashDrop
from django.db.models import Sum
from itertools import groupby
from operator import itemgetter
from organization.master_end_day import end_day
from rest_framework.views import APIView
from rest_framework.response import Response
import jwt
from bill.models import Bill

class EndDayDailyReportFilterView(generics.ListAPIView):
    serializer_class = EndDayDailyReportSerializer

    def get_queryset(self):

        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, pk=branch_id)
        print(branch)
        # Get today's date
        today_date = date.today()
        today_date_str = today_date.strftime('%Y-%m-%d')

        # Filter records based on branch, terminal, and today's date
        queryset = EndDayDailyReport.objects.filter(
            Q(branch=branch)&
             Q(
            created_date__startswith=today_date_str)
        ).order_by('-date_time')  # Order by date_time in descending order to get the last entry

        return queryset
        
# from rest_framework.exceptions import APIException
# class MasterEndDay(APIView):
#     def get(self, request, *args, **kwargs):
#         jwt_token = self.request.META.get("HTTP_AUTHORIZATION")
#         jwt_token = jwt_token.split()[1]
#         try:
#             token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
#             user_id = token_data.get("user_id")
#             username = token_data.get("username")
#             role = token_data.get("role")
#             # You can access other claims as needed

#             # Assuming "branch" is one of the claims, access it
#             branch = token_data.get("branch")

#             # Print the branch
#             print("Branch:", branch)
#         except jwt.ExpiredSignatureError:
#             print("Token has expired.")
#         except jwt.DecodeError:
#             print("Token is invalid.")
#         branch = Branch.objects.get(id=branch, is_deleted=False, status=True)
#         terminals = branch.terminal_set.filter(is_deleted=False, status=True)
#         daycloseForallterminal = True
#         for terminal in terminals:
#             if terminal.dayclose == False:
#                 daycloseForallterminal = False
#                 break
#             else:
#                 daycloseForallterminal=True
        
#         if daycloseForallterminal == True:
#             try:
#                 end_day()
#                 for terminal in terminals:
#                     terminal.dayclose = False
#                     terminal.save()
#             except Exception as e:
#                 print(e)
#                 return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             terminals = branch.terminal_set.filter(is_deleted=False, status=True, dayclose=False)
#             terminal_ids = []
#             for terminal in terminals:
#                 if terminal.dayclose == False:
#                     terminal_ids.append(terminal.terminal_no)
#             return Response({"detail": f"Terminal : {terminal_ids} need to close their days"}, status=status.HTTP_400_BAD_REQUEST)

        
        
#         return Response({"detail": "Endday has been done successfully"}, status=status.HTTP_200_OK)


from rest_framework.exceptions import APIException
class MasterEndDay(APIView):
    def get(self, request, *args, **kwargs):
        jwt_token = self.request.META.get("HTTP_AUTHORIZATION")
        jwt_token = jwt_token.split()[1]
        try:
            token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
            user_id = token_data.get("user_id")
            username = token_data.get("name")
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
        branch = Branch.objects.get(id=branch, is_deleted=False, status=True)
        terminals = branch.terminal_set.filter(is_deleted=False, status=True)
        daycloseForallterminal = True
        # for terminal in terminals:
        #     if terminal.dayclose == False:
        #         daycloseForallterminal = False
        #         break
        #     else:
        #         daycloseForallterminal=True
        terminal_to_close_their_day = []
        for terminal in terminals:
            no_bill=True
            if Bill.objects.filter(is_end_day=False, status=True, terminal=terminal.terminal_no, branch=branch).exists():
                no_bill = False
            else:
                no_bill=True
            if (terminal.dayclose or no_bill) == False:
                daycloseForallterminal = False
                terminal_to_close_their_day.append(terminal.terminal_no)
                break
            else:
                daycloseForallterminal=True
        
        if daycloseForallterminal == True:
            try:
                branches = []
                branches.append(branch)
                end_day(branches, username)
                for terminal in terminals:
                    terminal.dayclose = False
                    terminal.save()
            except Exception as e:
                print(e)
                return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # terminals = branch.terminal_set.filter(is_deleted=False, status=True, dayclose=False)
            # terminal_ids = []
            # for terminal in terminal_to_close_their_day:
            #     if terminal.dayclose == False:
                    # terminal_ids.append(terminal.terminal_no)
            return Response({"detail": f"Terminal : {terminal_to_close_their_day[0]} has bill and need to close their days "}, status=status.HTTP_400_BAD_REQUEST)
                    
            # return Response({"detail": f"There exists some terminal whose day is not closed"}, status=status.HTTP_400_BAD_REQUEST)


        
        
        return Response({"detail": "Endday has been done successfully"}, status=status.HTTP_200_OK)


