from django.urls import path

from api.views.void_bill import MakeVoidBill, VoidBillItemView


urlpatterns = [
    # Your other URL patterns
    # path('make-void-bill/<str:invoice_number>', MakeVoidBill.as_view(), name='make-void-bill'),
    path('make-void-bill/<int:order_id>', MakeVoidBill.as_view(), name='make-void-bill'),
    path('store-void-items/', VoidBillItemView.as_view(), name='store-void-items'),

]