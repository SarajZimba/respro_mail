from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.serializers.organization import BranchSerializer, OrganizationSerializer, TableSerializer, TerminalSerialzier, BlockAccountSerializer, CashDropSerializer, CashDropLatestSerializer, OnlyTerminalSerializer

from organization.models import Branch, Organization, Table, Terminal, CashDrop, DeviceTracker
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django.conf import settings
from datetime import datetime
from django.db.models import Max
import jwt

"""  """
import os
import environ
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(settings.BASE_DIR, ".env"))

"""  """

from django.contrib.auth import get_user_model
User = get_user_model()


class CashDropViewSet(ModelViewSet):
    queryset = CashDrop.objects.all()
    serializer_class = CashDropSerializer


from organization.models import EndDayDailyReport

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from organization.models import CashDrop, EndDayDailyReport, Branch

class CashDropLatestView(APIView):
    def get(self, request, branch_id, terminal, format=None):
        try:
            branch = Branch.objects.get(id=branch_id)

            # Get the latest CashDrop object for the specified branch and terminal
            latest_cash_drop = CashDrop.objects.filter(branch_id=branch, terminal=terminal).last()
            no_cashdrop = EndDayDailyReport.objects.filter(branch=branch, terminal=terminal).last()
            if latest_cash_drop is None:
                return Response({'latest_balance': no_cashdrop.cash if no_cashdrop else 0.0})

            # Calculate the latest_balance
            latest_balance_final = latest_cash_drop.latest_balance

            # If needed, you can add other calculations here based on your requirements

            data = {'latest_balance': latest_balance_final}
            return Response(data, status=status.HTTP_200_OK)

        except Branch.DoesNotExist:
            return Response({'detail': 'Branch not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BlockAccountView(APIView):
    permission_classes = AllowAny,

    def patch(self, request):
        serializer = BlockAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account_type = serializer.validated_data.get('type')
        blocked = serializer.validated_data.get('blocked')
        key = serializer.validated_data.get('key')

        if key != env('SECRET_BACKENDS'):
            return Response({'details':"Something Went Wrong"}, 400)
        

        users = User.objects.all()
        if account_type == 'OUTLET' and blocked=='YES':
            for user in users:
                user.is_active = False
                user.save()
            return Response({"details":"Successfully Blocked"})
            
        elif account_type == 'OUTLET' and blocked=='NO':
            for user in users:
                user.is_active = True
                user.save()
            return Response({"details":"Successfully Activated"})

        return Response({"details":"Something Went Wrong"}, 400)




class OrganizationApi(ReadOnlyModelViewSet):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.active()

    def list(self, request, *args, **kwargs):
        instance = Organization.objects.last()
        serializer_data = self.get_serializer(instance).data
        serializer_data['server_date'] = datetime.now().date()
        return Response(serializer_data)


class BranchApi(ModelViewSet):
    permission_classes = IsAuthenticatedOrReadOnly,
    serializer_class = BranchSerializer
    queryset = Branch.objects.active().filter(is_central=False)

class TableApi(ReadOnlyModelViewSet):
    serializer_class = TableSerializer
    queryset = Table.objects.all()

from django.db.models import Q
class TerminalApi(ReadOnlyModelViewSet):
    serializer_class = TerminalSerialzier
    queryset = Terminal.objects.all()

    def list(self, request, *args, **kwargs):
        branch_id = self.request.query_params.get('branchId')
        terminal_no = self.request.query_params.get('terminalNo')
        if branch_id and terminal_no:
            terminal_exists = Terminal.objects.filter(branch_id=branch_id, terminal_no=terminal_no).exists()
            if terminal_exists:
                qs =  Terminal.objects.filter(branch_id=branch_id, terminal_no=terminal_no)
                serializer = self.get_serializer(qs, many=True)
                return Response(serializer.data)
            else:
                return Response({'details':"No terminal with provided branch and terminal no"}, status=404)
            

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    # def post(self, request, *args, **kwargs):
    #     data = request.data
    #     terminal_no = request.data['terminal']
    #     branch = request.data['branch']

    #     terminal = Terminal.objects.filter(branch__id = branch, is_deleted=False, is_active = False).exclude(terminal_no=terminal_no)

    #     serializer = OnlyTerminalSerializer(terminal, many=True)

    #     details = {
    #         'previous_terminal': terminal_no,
    #         'available_terminals': serializer.data
    #     }

    #     return Response(details)
    
    def post(self, request, *args, **kwargs):
        data = request.data
        terminal_no = request.data['terminal']
        branch = request.data['branch']

        # terminal = Terminal.objects.filter(branch__id = branch, is_deleted=False).exclude(terminal_no=terminal_no)

        # serializer = OnlyTerminalSerializer(terminal, many=True)
        # Fetch DeviceTracker objects with is_active=False for the specified branch
        active_device_trackers = DeviceTracker.objects.filter(
            terminal__branch_id=branch,
            status=True
        )

        # Extract unique terminal numbers from the active DeviceTracker objects
        active_terminal_numbers = [tracker.terminal.terminal_no for tracker in active_device_trackers]

        print(active_terminal_numbers)
        # Fetch terminals not in the list of active terminal numbers and excluding the provided terminal_no
        terminals = Terminal.objects.filter(branch__id=branch, status=True, is_deleted=False).exclude(terminal_no__in=active_terminal_numbers)


        print(terminals)


        serializer = OnlyTerminalSerializer(terminals, many=True)

        details = {
            'previous_terminal': terminal_no,
            'available_terminals': serializer.data
        }

        return Response(details)

class CashDropSummaryView(APIView):
    def get(self, request, branch_id, terminal, *args, **kwargs):
        # Get all CashDrop instances where is_end_day is False
        cashdrops1 = CashDrop.objects.filter(branch_id = branch_id, terminal=terminal)
        cashdrops = CashDrop.objects.filter(is_end_day=False, branch_id=branch_id, terminal=terminal)

        # Serialize the data
        if not cashdrops1.exists():
            response_data = {
            'first_object_opening_balance': 0.0,
            'last_object_remaining_balance': 0.0,
            'total_cashdrop_amount': 0.0,
            'total_expense': 0.0,
            'total_addCash': 0.0,
            }
            return Response(response_data)
        if not cashdrops.exists():
            latest_cashdrop = CashDrop.objects.filter(branch_id=branch_id, terminal=terminal).last()
            response_data = {
            'first_object_opening_balance': latest_cashdrop.latest_balance,
            'last_object_remaining_balance': latest_cashdrop.latest_balance,
            'total_cashdrop_amount': 0.0,
            'total_expense': 0.0,
            'total_addCash': 0.0,
            }
            return Response(response_data)
        serializer = CashDropSerializer(cashdrops, many=True)

        # Extract required information from the serialized data
        first_object_opening_balance = serializer.data[0]['opening_balance']
        last_object_remaining_balance = serializer.data[-1]['remaining_balance']

        # Calculate total cashdrop_amount, expense, addCash
        total_cashdrop_amount = sum(item['cashdrop_amount'] for item in serializer.data)
        total_expense = sum(item['expense'] for item in serializer.data)
        total_addCash = sum(item['addCash'] for item in serializer.data)

        # Create a response dictionary
        response_data = {
            'first_object_opening_balance': first_object_opening_balance,
            'last_object_remaining_balance': last_object_remaining_balance,
            'total_cashdrop_amount': total_cashdrop_amount,
            'total_expense': total_expense,
            'total_addCash': total_addCash,
        }

        return Response(response_data)
        
# class AllTerminalApi(ReadOnlyModelViewSet):
#     serializer_class = OnlyTerminalSerializer
#     queryset = Terminal.objects.filter(is_deleted=False)

#     def post(self, request, *args, **kwargs):
#         data = request.data
#         branch = request.data['branch']
#         # print(terminal_no)
#         # print(branch)
#         terminal = Terminal.objects.filter(branch__id = branch).exclude(is_deleted=True)#.exclude(terminal_no=terminal_no) #and ~Q(terminal_no = terminal_no)
        
#         serializer = OnlyTerminalSerializer(terminal, many=True)

#         details = {
#             # 'previous_terminal': terminal_no,
#             'available_terminals': serializer.data
#         }

#         return Response(details)

class AllTerminalApi(ReadOnlyModelViewSet):
    serializer_class = OnlyTerminalSerializer
    queryset = Terminal.objects.filter(is_deleted=False)

    def post(self, request, *args, **kwargs):
        data = request.data
        branch = request.data['branch']
        # print(terminal_no)
        # print(branch)

        active_device_trackers = DeviceTracker.objects.filter(
            terminal__branch_id=branch,
            status=True
        )

        # Extract unique terminal numbers from the active DeviceTracker objects
        active_terminal_numbers = [tracker.terminal.terminal_no for tracker in active_device_trackers]
        terminals = Terminal.objects.filter(branch__id = branch).exclude(is_deleted=True)#.exclude(terminal_no=terminal_no) #and ~Q(terminal_no = terminal_no)
        
        available_terminals = []

        for terminal in terminals:
            if terminal.terminal_no in active_terminal_numbers:
                data = {
                    "id":terminal.id,
                    "terminal_no":terminal.terminal_no,
                    "is_active": True
                }
            
            else:
                data = {
                    "id":terminal.id,
                    "terminal_no":terminal.terminal_no,
                    "is_active": False
                }

            available_terminals.append(data)

        details = {
            'available_terminals': available_terminals
        }

        return Response(details)
        
from rest_framework import generics
from organization.models import PrinterSetting
from api.serializers.organization import PrinterSettingSerializer

class PrinterSettingListView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data

        jwt_token = request.META.get("HTTP_AUTHORIZATION")
        jwt_token = jwt_token.split()[1]
        try:
            token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
            # You can access other claims as needed

            # Assuming "branch" is one of the claims, access it
            branch = token_data.get("branch")
            terminal_no = token_data.get("terminal")
            # token_type = token_data.get("token_type")


            # Print the branch
            print("Branch:", branch)
            print("Terminal:", terminal_no)
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.DecodeError:
            print("Token is invalid.")
        ip = data['ip']
        port = data['port']
        url = data ['url']
        type = data['type']
        print_status = data['print_status']
        try:
            terminal_obj = Terminal.objects.get(terminal_no = int(terminal_no), status=True, is_deleted=False, branch=Branch.objects.get(id=branch, status=True, is_deleted=False))
        except Terminal.DoesNotExist:
            return Response({"detail":"Terminal does not exists"}, status=status.HTTP_400_BAD_REQUEST)
        print(terminal_obj)
        try:
            PrinterSetting.objects.filter(terminal=terminal_obj, printer_location=type, is_deleted=False, status=True).delete()
            PrinterSetting.objects.create(ip=ip, port=port, url=url, terminal=terminal_obj, printer_location=type,print_status=print_status)
        except Exception as e:
            print(e)
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail":"PrinterSetting created successfully"}, status=status.HTTP_200_OK)

from rest_framework.exceptions import APIException
class Custom400Exception(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Custom error message for status code 400'
class TerminalDayClose(APIView):
    def get(self, request, *args, **kwargs):
        jwt_token = request.META.get('HTTP_AUTHORIZATION')
        token = jwt_token.split()[1]
        try:
            token_data = jwt.decode(token, options={'verify_signature':False} )
            branch = token_data.get('branch')
            terminal = token_data.get('terminal')
            deviceId = token_data.get('deviceId')
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.DecodeError:
            print("Token is invalid.")
        print(terminal)
        try:
            terminal_obj = Terminal.objects.get(terminal_no = int(terminal), status=True, is_deleted=False, branch=Branch.objects.get(id=branch, status=True, is_deleted=False))
        except Terminal.DoesNotExist:
            return Response({"detail":"Terminal does not exists"}, status=status.HTTP_400_BAD_REQUEST)
        terminal_obj.dayclose = True
        terminal_obj.save()
        
        try:
            devicetracker_obj = DeviceTracker.objects.get(deviceId=deviceId, terminal = terminal_obj, status=True)
        except Exception as e:
            raise Custom400Exception("No device logged in with the given terminal")
        
        devicetracker_obj.status = False
        # terminal_obj.active_count -= 1
        devicetracker_obj.save()

        return Response({"detail":"DayClose Flag updated"}, status=status.HTTP_200_OK)

class AutoEndDay(APIView):
    def get(self, request, *args, **kwargs):
        org = Organization.objects.first()
        try:
            if org.auto_end_day == True:
                org.auto_end_day = False
                org.save()
            else:
                org.auto_end_day = True
                org.save()
        except Exception as e:
            return Response("Something went wrong", 400)
            
        data = { "auto_end_day": org.auto_end_day}

        return Response(data, 200)
