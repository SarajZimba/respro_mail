# from ..views.discount_amount import  DiscountApiView
# from django.urls import path

# urlpatterns = [
#     path("getdiscountlist/",DiscountApiView,name="disount-type")
# ]

from ..views.discount_amount import  DiscountApiView, DiscountCreateApiView, DiscountUpdateApiView ,DiscountDeleteApiView
from django.urls import path

urlpatterns = [
    path("getdiscountlist/",DiscountApiView,name="disount-type"),
    path("postdiscount/",DiscountCreateApiView.as_view(),name="post-disount-type"),
    path("updatediscount/<int:pk>",DiscountUpdateApiView.as_view(),name="update-disount-type"),
    path("deletediscount/<int:pk>",DiscountDeleteApiView.as_view(),name="update-disount-type"),
]