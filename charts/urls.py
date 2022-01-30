from django.urls import path, re_path

from charts import views

urlpatterns = [
    path('htmx/<str:chart_name>', views.HTMXChartView.as_view(), name='htmx-chart'),
]
