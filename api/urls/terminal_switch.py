from django.urls import path

from api.views.terminal_switch import BillListView, CheckTerminalStatus, LogoutTerminalStatus, BillListFetchTerminalView

urlpatterns = [
    path('terminalswitch-bills/', BillListView.as_view(), name='terminalswitch-bills'),
    path('terminaldata-fetch/', BillListFetchTerminalView.as_view(), name='terminaldata-fetch'),
    path('check-terminalstatus/', CheckTerminalStatus.as_view(), name='check-terminal-status' ),
    path('logout-terminal/', LogoutTerminalStatus.as_view(), name='check-terminal-status' )

    # Add other URL patterns as needed
]