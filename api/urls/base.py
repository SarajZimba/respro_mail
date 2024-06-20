from .user import urlpatterns as user_urlpatterns
from .product import urlpatterns as product_urlpatterns
from .bill import urlpatterns as bill_urlpatterns
from .organization import urlpatterns as org_urlpatterns
from .discount_urls import urlpatterns as discount_urlspatterns
from .accounting_urls import urlpatterns as accounting_urlpatterns
from .purchase import urlpatterns as purchase_urlpatterns
from .end_day import urlpatterns as end_day_urls
from .end_day_check import urlpatterns as end_day_check_urls
from .table import urlpatterns as table_urlpatterns
from .branch import urlpatterns as branch_urlpatterns
from .order import urlpatterns as order_urlpatterns 
from .terminal_switch import urlpatterns as terminal_switch_urlpatterns
from .master import urlpatterns as master_urlpatterns
from .give_all_bills import urlpatterns as today_transaction_urlpatterns
from .void_bill import urlpatterns as void_bill_urlpatterns
from .overview import urlpatterns as overview_urlpatterns
from .mail import urlpatterns as mail_urlpatterns
from  .void import urlpatterns as void_urlpatterns
from .mobilepayment_type import urlpatterns as mobile_urlpatterns



urlpatterns = (
    [] + user_urlpatterns + product_urlpatterns + bill_urlpatterns + org_urlpatterns+discount_urlspatterns+ accounting_urlpatterns + purchase_urlpatterns + end_day_urls + end_day_check_urls + table_urlpatterns+ branch_urlpatterns + order_urlpatterns + terminal_switch_urlpatterns  + master_urlpatterns + today_transaction_urlpatterns + void_bill_urlpatterns+ overview_urlpatterns+ mail_urlpatterns+ void_urlpatterns+mobile_urlpatterns
)
