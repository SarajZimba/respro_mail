from ..views.mail import  MailApiView, MailCreateApiView, MailUpdateApiView ,MailDeleteApiView
from django.urls import path

urlpatterns = [
    path("getmaillist/",MailApiView,name="mail-type"),
    path("postmail/",MailCreateApiView.as_view(),name="post-mail-type"),
    path("updatemail/<int:pk>",MailUpdateApiView.as_view(),name="update-mail-type"),
    path("deletemail/<int:pk>",MailDeleteApiView.as_view(),name="delete-mail-type"),
]