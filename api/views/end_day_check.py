from rest_framework import generics
from rest_framework.response import Response
from organization.models import Terminal, EndDayDailyReport, Branch
from api.serializers.end_day_check import EndDayDailyRecordSerializer
from datetime import date
from django.db.models import Q
from rest_framework import status
from bill.models import Bill
from django.utils import timezone
from datetime import datetime, timedelta




class TerminalCheckAPI(generics.RetrieveAPIView):
    def get(self, request, branch_id):
        # Get the branch
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return Response({"error": "Branch not found"}, status=404)

        # Get all terminals for the branch
        terminals = Terminal.objects.filter(branch=branch)
        # print(terminals)

        # Check if each terminal's terminal_no exists in the EndDayDailyRecord table
        non_terminals = []
        today_date = date.today()
        today_date_str = today_date.strftime('%Y-%m-%d')
        start_datetime = datetime.combine(today_date, datetime.min.time())
        end_datetime = datetime.combine(today_date, datetime.max.time())

        start_datetime1 = timezone.make_aware(start_datetime)
        end_datetime1 = timezone.make_aware(end_datetime)
        # print(start_datetime)
        # print(end_datetime)
        
        c= 1
        for terminal in terminals:
            terminal_no = terminal.terminal_no
            print(str(terminal_no))
            end_day_record_exists = EndDayDailyReport.objects.filter(Q(branch = branch) & Q(terminal=str(terminal_no))&Q(
                created_date__startswith=today_date_str)).exists()               
            if not end_day_record_exists:
                non_terminals.append(str(terminal_no))
                c = 0
        # print(c)
        print(non_terminals)
        # Q(created_at__range=(start_datetime, end_datetime))
        if c==1:
             return Response({"detail": "OK from endday"}, status=status.HTTP_200_OK)
        elif c==0:
            for terminal in non_terminals:
                # terminal_no = terminal.terminal_no
                bill_record_exists = Bill.objects.filter(Q(branch = branch) & Q(terminal=terminal) &Q(created_at__range=(start_datetime1, end_datetime1))).exists()

                if  bill_record_exists:
                    return Response({"detail": " Not OK from Bill"}, status=status.HTTP_400_BAD_REQUEST)
            # if bill_record_exists:
            #     return Response({'detail': 'Not Ok'}, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({"detail": "OK from bill"}, status=status.HTTP_200_OK)
        # else:
        #     return Response({'detail': "Not Ok from Endday"})

        return Response
