from django.urls import path
from mail import views

#app_name = 'mail'

urlpatterns = [
    path('mailtest/', views.mailtest, name='mailtest'),
    path('mailchimp_hook/', views.MailchimpWebhook.as_view(), name='mailchimp_hook_get'),
    path('mailchimp_hook/<uuid>', views.MailchimpWebhook.as_view(), name='mailchimp_hook'),
]
