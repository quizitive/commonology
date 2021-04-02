from django.urls import path
from mail import views

urlpatterns = [
    path('mailtest/', views.mailtest, name='mailtest'),
    path('mailchimp_hook/', views.MailchimpWebhook.as_view(), name='mailchimp_hook'),
    path('mailchimp_hook/<uuid>', views.MailchimpWebhook.as_view(), name='mailchimp_hook')
]
