from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from organization.models import Table_Layout
from api.serializers.table import TableLayoutSerializer
from django.shortcuts import get_object_or_404
from organization.models import Branch, Table_Layout, Terminal, Table
from bill.models import Order

# class SaveTableLayout(APIView):
#     def post(self, request, format=None):
#         serializer = TableLayoutSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class SaveTableLayout(APIView):
#     def post(self, request, format=None):
#         # Check if the request data is a list
#         if isinstance(request.data, list):
#             # Serialize the list of data using the ListSerializer
#             serializer = TableLayoutSerializer(data=request.data, many=True)
#         else:
#             # Serialize a single dictionary data
#             serializer = TableLayoutSerializer(data=request.data)

#         # print(request.data)

#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SaveTableLayout(APIView):
    def post(self, request, branch_id, terminal_no, format=None):
        try:
            # Get the Branch instance using the branch_id from the URL
            branch = Branch.objects.get(id=branch_id, is_deleted=False, status=True)
        except Branch.DoesNotExist:
            return Response({"error": "Branch not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            # Get the Branch instance using the branch_id from the URL
            terminal = Terminal.objects.get(branch=branch, terminal_no=terminal_no, is_deleted=False, status=True)
        except Branch.DoesNotExist:
            return Response({"error": "Terminal not found"}, status=status.HTTP_404_NOT_FOUND)

        # Delete existing objects with the same branch_id
        Table_Layout.objects.filter(branch=branch, terminal=terminal).delete()

        # Add the branch to the request data
        for data in request.data:
            data['branch'] = branch.id
            data['terminal'] = terminal.id

        # Check if the request data is a list
        if isinstance(request.data, list):
            # Serialize the list of data using the ListSerializer
            serializer = TableLayoutSerializer(data=request.data, many=True)
        else:
            # Serialize a single dictionary data
            serializer = TableLayoutSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetTableLayoutByBranchView(APIView):
    def get(self, request, branch_id, terminal_no, format=None):
        # Get the branch object by name (you can adjust this based on your actual data)
        branch = get_object_or_404(Branch, id=branch_id, is_deleted=False, status=True)
        
        terminal = get_object_or_404(Terminal, terminal_no=terminal_no, is_deleted=False, branch=branch, status=True)
        # Retrieve all Table_Layout objects related to the branch
        table_layouts = Table_Layout.objects.filter(branch=branch, terminal=terminal)

        # Serialize the data
        serializer = TableLayoutSerializer(table_layouts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
        
class ChangeEstimateAPIView(APIView):
    def get(self, request, order):
        order = Order.objects.get(id=order)
        table_no = order.table_no
        terminal_no = order.terminal_no
        branch = order.branch
        table = Table.objects.get(terminal=Terminal.objects.get(terminal_no=terminal_no, branch=branch, is_deleted=False, status=True), table_number=table_no, is_deleted=False, status=True)
        table.is_estimated = True
        table.save()

        return Response({"is_estimate": table.is_estimated}, status=status.HTTP_200_OK)