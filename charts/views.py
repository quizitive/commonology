from django.shortcuts import render

from project.htmx import HTMXProtectedView

from charts.charts import Charts


class HTMXChartView(HTMXProtectedView):

    # e.g. /charts/htmx/your_chart_name/?query=params&passed=as&kwargs=tochart
    def get(self, request, *args, **kwargs):
        chart_name = kwargs.get("chart_name")
        chart = Charts.get_chart(chart_name)(**{k: v for k, v in request.GET.items()})
        return render(request, "charts/simple_chart.html", {"chart": chart})

