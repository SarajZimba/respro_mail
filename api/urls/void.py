from django.urls import path
from api.views.void import VoidBillAPIView

urlpatterns = [
    path("void-items", VoidBillAPIView.as_view(), name='void-items' )
]