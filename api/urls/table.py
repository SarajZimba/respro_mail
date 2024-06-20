from django.urls import path
from api.views.table import SaveTableLayout, GetTableLayoutByBranchView, ChangeEstimateAPIView

urlpatterns = [
    # Your other URL patterns
    path('save_table_layout/<int:branch_id>/<int:terminal_no>', SaveTableLayout.as_view(), name='save-table-layout'),
    path('get_table_layout/<int:branch_id>/<int:terminal_no>', GetTableLayoutByBranchView.as_view(), name='get-table-layout-by-branch'), 
    path('change-table-estimate/<int:order>', ChangeEstimateAPIView.as_view(), name='change-table-estimate'), 

]