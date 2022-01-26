from django.shortcuts import render

from charts.charts import Charts


def htmx_chart_view(request, chart_name):
    chart = Charts.get_chart_class(chart_name)(**{k: v for k, v in request.GET.items()})
    return render(request, "charts/simple_chart.html", {"chart": chart})
