from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from mail import views

app_name = 'mail'

urlpatterns = [
    path('mailtest/', views.mailtest, name='mailtest'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('massmail/', views.MassMail.as_view(), name='massmail'),
    path('mailchimp_hook/', views.MailchimpWebhook.as_view(), name='mailchimp_hook_get'),
    path('mailchimp_hook/<uuid>', views.MailchimpWebhook.as_view(), name='mailchimp_hook')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)