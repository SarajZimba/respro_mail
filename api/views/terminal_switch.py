from rest_framework.views import APIView
from rest_framework.response import Response
from bill.models import Bill, Order, VoidBillTracker
from api.serializers.terminal_switch import BillSerializer, TableLayoutSerializer, TableSerializer
import jwt
from organization.models import PrinterSetting, Terminal, Branch, Table_Layout, Table
from api.serializers.organization import PrinterSettingSerializer
from root.utils import format_order_json
from rest_framework.exceptions import APIException
from api.serializers.void_bill import VoidBillSerializer
from rest_framework import status

from datetime import timedelta
from django.utils import timezone as djtz
import secrets

from pathlib import Path

import os

import environ
from organization.models import DeviceTracker



BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

from rest_framework import status

class Custom306Exception(APIException):
    status_code = status.HTTP_306_RESERVED
    default_detail = 'Custom error message for status code 306'
    
class Custom400Exception(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Custom error message for status code 400'


class BillListView(APIView):
    def post(self, request, *args, **kwargs):
        # print(request)
        data = request.data

        jwt_token = request.META.get("HTTP_AUTHORIZATION")
        jwt_token = jwt_token.split()[1]
        try:
            token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
            # You can access other claims as needed

            # Assuming "branch" is one of the claims, access it
            branch = token_data.get("branch")
            agent = token_data.get("name")
            
            token_type = token_data.get("token_type")
            user_id = token_data.get("user_id")
            deviceId = token_data.get("deviceId")
            terminal = data['switched_to']
            jti = token_data['jti']

            role = token_data.get("role")

            token_expiry = djtz.now() + timedelta(hours=1)
            token_created = djtz.now()

            token_payload = {
                "token_type": token_type,
                "exp": token_expiry,
                "iat": token_created,
                "jti":jti,
                "user_id": user_id,
                "name": agent,
                "role": role,  # Note: List should be directly included in payload, not as a string
                "branch": branch,
                "terminal": terminal,
                "deviceId": deviceId
            }
            # token_type = token_data.get("token_type")
            SECRET_KEY = env("SECRET_KEY")

            jwt_token_encoded = jwt.encode(token_payload, key=SECRET_KEY, algorithm='HS256')


            print("encoded JWT token", jwt_token_encoded)

            # Print the branch
            print("Branch:", branch)
            print("Agent:", agent)
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.DecodeError:
            print("Token is invalid.")
        branch_id = request.query_params.get('branch')
        terminal_id = request.query_params.get('terminal')
        
        switched_to_terminal = int(data['switched_to'])
        switched_from_terminal = int(data['switched_from'])


        if DeviceTracker.objects.filter(terminal = Terminal.objects.get(terminal_no=switched_to_terminal, branch=Branch.objects.get(pk=int(branch_id)), is_deleted=False, status=True), status=True).exists():
            raise Custom400Exception("Terminal is already active in another device")
        
        # elif Terminal.objects.get(terminal_no=switched_to_terminal, branch=Branch.objects.get(pk=int(branch_id)), is_deleted=False, status=True).active_count >=1:
        #     raise Custom400Exception("Terminal is already active in another device")
        else:

        
            bills = Bill.objects.filter(branch__id=branch_id, terminal=terminal_id, is_end_day=False)
            all_bills = Bill.objects.filter(branch__id=branch_id, terminal=terminal_id)
            bills_without_complimentary = all_bills.exclude(payment_mode='COMPLIMENTARY')
            ordered_bills_without_complimentary = bills_without_complimentary.order_by('id')
            serializer = BillSerializer(bills, many=True)
            printers = PrinterSetting.objects.filter(terminal__terminal_no=terminal_id)
            # table_layouts = Table_Layout.objects.filter(branch = Branch.objects.get(pk=branch_id))
            table_layouts = Table.objects.filter(terminal__terminal_no = terminal_id, terminal__branch__id=branch_id)
            tablelayoutserializer = TableSerializer(table_layouts, many=True)
    
            # tablelayoutserializer = TableLayoutSerializer(table_layouts, many=True)
            printer_serializer = PrinterSettingSerializer(printers,many=True)
    
            # orders_without_bill = Order.objects.filter(is_completed=False, is_saved=True, branch__id=branch_id, terminal_no = int(terminal_id))
            orders_without_bill = Order.objects.filter(
                is_completed=False, 
                is_saved=True, 
                branch__id=branch_id, 
                terminal_no=int(terminal_id),
                status=True
            )
                
            print(f'This is the orders {orders_without_bill}')
    
            formatted_json = format_order_json(orders_without_bill)
            
            filtered_trackers = VoidBillTracker.objects.filter(prev_bill__contains=f"-{switched_to_terminal}-", bill_new__is_end_day=False, bill_prev__is_end_day=False)
    
            voidbilltracker = VoidBillSerializer(filtered_trackers, many=True)
    
            details = {
                "switched_from" : switched_from_terminal,
                "switched_to": switched_to_terminal,
                "branch": branch_id,
                "terminal": terminal_id,
                "agent": agent,
                "last_bill_no": ordered_bills_without_complimentary.last().bill_count_number if ordered_bills_without_complimentary.last()  else 0,
                "printer": printer_serializer.data,
                "table_layout": tablelayoutserializer.data,
                "sale" : serializer.data,
                "remaining_orders" : formatted_json, 
                "void_bill_trackers" : voidbilltracker.data,
                "jwttoken": jwt_token_encoded
            }
            switched_to_terminal_obj = Terminal.objects.get(terminal_no=switched_to_terminal, branch=Branch.objects.get(pk=int(branch_id)), is_deleted=False, status=True)
            DeviceTracker.objects.filter(terminal=switched_to_terminal_obj).delete()
            devicetrackerbefore_obj = DeviceTracker.objects.create(deviceId=deviceId, terminal=switched_to_terminal_obj)
            switched_from_terminal_obj = Terminal.objects.get(terminal_no=switched_from_terminal, branch=Branch.objects.get(pk=int(branch_id)), is_deleted=False, status=True)

            devicetrackerafter_obj = DeviceTracker.objects.get(deviceId=deviceId, terminal=switched_from_terminal_obj)
            devicetrackerafter_obj.status = False
            devicetrackerafter_obj.save()
            return Response(details)
        
class CheckTerminalStatus(APIView):
    def get(self, request, *args, **kwargs):
        switched_to_terminal = request.query_params.get('terminal')
        branch = request.query_params.get('branch')

        

        # if Terminal.objects.get(terminal_no=terminal, branch=branch_obj).is_active == True:
        #     raise serializers.ValidationError("Terminal is already active")

        terminal_obj = Terminal.objects.get(terminal_no=int(switched_to_terminal), branch=Branch.objects.get(pk=int(branch)), status=True, is_deleted=False)

        data = {
            'is_active' : terminal_obj.is_active
        }
        return Response(data)
    
    def post(self, request, *args, **kwargs):
        data = request.data
        switched_to_terminal = data['terminal']
        branch = data['branch']

        


        # if Terminal.objects.get(terminal_no=terminal, branch=branch_obj).is_active == True:
        #     raise serializers.ValidationError("Terminal is already active")

        terminal_obj = Terminal.objects.get(terminal_no=int(switched_to_terminal), branch=Branch.objects.get(pk=int(branch)), status=True, is_deleted=False)

        data = {
            'is_active' : terminal_obj.is_active
        }
        return Response(data)
        
        
# class LogoutTerminalStatus(APIView):
#     # def get(self, request, *args, **kwargs):
#     #     switched_to_terminal = request.query_params.get('terminal')
#     #     branch = request.query_params.get('branch')

        

#     #     # if Terminal.objects.get(terminal_no=terminal, branch=branch_obj).is_active == True:
#     #     #     raise serializers.ValidationError("Terminal is already active")

#     #     terminal_obj = Terminal.objects.get(terminal_no=int(switched_to_terminal), branch=Branch.objects.get(pk=int(branch)), status=True, is_deleted=False)

#     #     data = {
#     #         'is_active' : terminal_obj.is_active
#     #     }
#     #     return Response(data)
    
#     def post(self, request, *args, **kwargs):
#         data = request.data
#         switched_to_terminal = data['terminal']
#         branch = data['branch']

        


#         # if Terminal.objects.get(terminal_no=terminal, branch=branch_obj).is_active == True:
#         #     raise serializers.ValidationError("Terminal is already active")
#         try:
#             terminal_obj = Terminal.objects.get(terminal_no=int(switched_to_terminal), branch=Branch.objects.get(pk=int(branch)), status=True, is_deleted=False)
#         except Exception as e:
#             raise APIException("Terminal with that id does not exist")
#         terminal_obj.is_active = False
#         terminal_obj.active_count -= 1
#         terminal_obj.save()
#         data = {
#             'is_active' : terminal_obj.is_active
#         }
#         return Response(data)
        
class LogoutTerminalStatus(APIView):
    
    def post(self, request, *args, **kwargs):
        jwt_token = request.META.get("HTTP_AUTHORIZATION")
        jwt_token = jwt_token.split()[1]
        try:
            token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
            # You can access other claims as needed

            # Assuming "branch" is one of the claims, access it
            branch = token_data.get("branch")
            agent = token_data.get("name")
            deviceId = token_data.get("deviceId")


            # Print the branch
            print("Branch:", branch)
            print("Agent:", agent)
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
        except jwt.DecodeError:
            print("Token is invalid.")
        data = request.data
        switched_to_terminal = data['terminal']
        # branch = data['branch']

        


        # if Terminal.objects.get(terminal_no=terminal, branch=branch_obj).is_active == True:
        #     raise serializers.ValidationError("Terminal is already active")
        try:
            terminal_obj = Terminal.objects.get(terminal_no=int(switched_to_terminal), branch=Branch.objects.get(pk=int(branch)), status=True, is_deleted=False)
        except Exception as e:
            raise APIException("Terminal with that id does not exist")
        
        try:
            devicetracker_obj = DeviceTracker.objects.get(deviceId=deviceId, terminal = terminal_obj, status=True)
        except Exception as e:
            raise APIException("No device logged in with the given terminal")
        
        devicetracker_obj.status = False
        # terminal_obj.active_count -= 1
        devicetracker_obj.save()
        data = {
            'is_active' : devicetracker_obj.status
        }
        return Response(data)
        
class BillListFetchTerminalView(APIView):
    def post(self, request, *args, **kwargs):
        # print(request)
        data = request.data

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
        branch_id = request.query_params.get('branch')
        terminal_id = request.query_params.get('terminal')
        
        switched_to_terminal = int(data['switched_to'])
        switched_from_terminal = int(data['switched_from'])


        # if Terminal.objects.get(terminal_no=switched_to_terminal, branch=Branch.objects.get(pk=int(branch_id))).is_active == True:
        #     raise APIException("Terminal is already active")
        # else:
        #     terminal_obj = Terminal.objects.get(terminal_no=switched_to_terminal, branch=Branch.objects.get(pk=int(branch_id)))
        #     terminal_obj.is_active = True
        #     terminal_obj.save()
        #     terminal_prev_obj = Terminal.objects.get(terminal_no=switched_from_terminal, branch=Branch.objects.get(pk=int(branch_id)))
        #     terminal_prev_obj.is_active = False
        #     terminal_prev_obj.save()
        
        bills = Bill.objects.filter(branch__id=branch_id, terminal=terminal_id, is_end_day=False)
        all_bills = Bill.objects.filter(branch__id=branch_id, terminal=terminal_id)
        serializer = BillSerializer(bills, many=True)
        printers = PrinterSetting.objects.filter(terminal__terminal_no=terminal_id)
        # table_layouts = Table_Layout.objects.filter(branch = Branch.objects.get(pk=branch_id))
        table_layouts = Table.objects.filter(terminal__terminal_no = terminal_id, terminal__branch__id=branch_id)
        tablelayoutserializer = TableSerializer(table_layouts, many=True)

        # tablelayoutserializer = TableLayoutSerializer(table_layouts, many=True)
        printer_serializer = PrinterSettingSerializer(printers,many=True)

        # orders_without_bill = Order.objects.filter(is_completed=False, is_saved=True, branch__id=branch_id, terminal_no = int(terminal_id))
        orders_without_bill = Order.objects.filter(
            is_completed=False, 
            is_saved=True, 
            branch__id=branch_id, 
            terminal_no=int(terminal_id),
            status = True
        )
            
        print(f'This is the orders {orders_without_bill}')

        formatted_json = format_order_json(orders_without_bill)
        
        filtered_trackers = VoidBillTracker.objects.filter(prev_bill__contains=f"-{switched_to_terminal}-", bill_new__is_end_day=False, bill_prev__is_end_day=False)

        voidbilltracker = VoidBillSerializer(filtered_trackers, many=True)

        details = {
            "switched_from" : switched_from_terminal,
            "switched_to": switched_to_terminal,
            "branch": branch_id,
            "terminal": terminal_id,
            "agent": agent,
            "last_bill_no": all_bills.last().bill_count_number if all_bills.last() else 0,
            "printer": printer_serializer.data,
            "table_layout": tablelayoutserializer.data,
            "sale" : serializer.data,
            "remaining_orders" : formatted_json,
            "void_bill_trackers" : voidbilltracker.data

        }
        return Response(details)
