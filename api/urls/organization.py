from django.urls import path
from api.views.organization import OrganizationApi, BranchApi, TableApi, TerminalApi, BlockAccountView, CashDropViewSet, CashDropLatestView, CashDropSummaryView, AllTerminalApi, PrinterSettingListView, TerminalDayClose, AutoEndDay
from rest_framework import routers

router = routers.DefaultRouter()

router.register("organization", OrganizationApi)
router.register("branch", BranchApi)
router.register("table", TableApi)
router.register("terminal", TerminalApi)
router.register("cashdrops", CashDropViewSet)
router.register("all-terminals", AllTerminalApi)
# router.register("latest", CashDropViewSet)


urlpatterns = [
    path("block-account/", BlockAccountView.as_view()),
    path('latest/<int:branch_id>/<str:terminal>/', CashDropLatestView.as_view(), name='cashdrop-latest'),  
    path('cashdrop-summary/<int:branch_id>/<str:terminal>/', CashDropSummaryView.as_view(), name='cashdrop-summary'),
    path('printer-setting/', PrinterSettingListView.as_view(), name='printer-setting'),
    path('day-close/', TerminalDayClose.as_view(), name='day-close'),
    path('auto-end/', AutoEndDay.as_view(), name='auto-end'),




] + router.urls
