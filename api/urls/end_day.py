from django.urls import path

from api.views.end_day import EndDayDailyReportFilterView, MasterEndDay

urlpatterns = [
    # Other URL patterns...
    path('endday-reports/<int:branch_id>/', EndDayDailyReportFilterView.as_view(), name='endday-reports'),
    path('master-endday-mail/', MasterEndDay.as_view(), name='master-endday'),

]

