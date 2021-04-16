from django.urls import path
from mail import views

urlpatterns = [
    path('mailtest/', views.mailtest, name='mailtest'),
    path('massmail/', views.MassMail.as_view(), name='massmail'),
    path('mailchimp_hook/', views.MailchimpWebhook.as_view(), name='mailchimp_hook_get'),
    path('mailchimp_hook/<uuid>', views.MailchimpWebhook.as_view(), name='mailchimp_hook')
]
