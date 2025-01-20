from django.contrib.admin.apps import AdminConfig


class CommonologyAdminConfig(AdminConfig):
    default_site = "project.admin.CommonologyAdmin"
