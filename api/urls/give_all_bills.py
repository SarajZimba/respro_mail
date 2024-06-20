# urls.py
from django.urls import path
from api.views.give_all_bills import BillDetailView

urlpatterns = [
    # Other URL patterns
    path('bill-endday/<str:terminal_id>', BillDetailView.as_view(), name='bill-detail'),
]
