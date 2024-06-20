from django.urls import path

from ..views.overview import SalesBranchView, BranchWiseMonthSale, BranchAndTerminalWiseMonthSale, BranchAndTerminalWiseMonthAndOthersTypeSale, BranchAndTerminalWiseMonthAndBeverageTypeSale, BranchAndTerminalWiseMonthAndFoodTypeSale



urlpatterns = [
    path('master-sales-overview/', SalesBranchView.as_view(), name='bill-detail'),
    # path('monthwise-sale-branch/', BranchWiseMonthSale.as_view(), name='bill-detail'),
    path('monthwise-sale/', BranchAndTerminalWiseMonthSale.as_view(), name='bill-detail'),
    path('monthwise-sale-food/', BranchAndTerminalWiseMonthAndFoodTypeSale.as_view(), name='bill-detail-food'),
    path('monthwise-sale-beverage/', BranchAndTerminalWiseMonthAndBeverageTypeSale.as_view(), name='bill-detail-beverage'),
    path('monthwise-sale-others/', BranchAndTerminalWiseMonthAndOthersTypeSale.as_view(), name='bill-detail-others'),

] 
