from django.urls import path
from api.views.end_day_check import TerminalCheckAPI

urlpatterns = [
    path('terminal-check/<int:branch_id>/', TerminalCheckAPI.as_view(), name='terminal-check'),
    # Add other URLs as needed
]