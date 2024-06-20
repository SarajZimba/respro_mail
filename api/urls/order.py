from django.urls import path

from api.views.order import OrderCreateAPIView, SplitBillAPIView, UpdateCustomerOrder

urlpatterns = [
    path('create-order/', OrderCreateAPIView.as_view(), name='create-order'),
    path('split-order/', SplitBillAPIView.as_view(), name='split-order'),
    path('update-customer-order', UpdateCustomerOrder.as_view(), name='update-customer-order')


]