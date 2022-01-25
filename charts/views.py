from django.shortcuts import render

from charts.charts import CHARTS


def htmx_chart_view(request, chart_name, *args, **kwargs):
    chart = CHARTS[chart_name]
    return render(request, "charts/simple_chart.html", {"chart": chart})
