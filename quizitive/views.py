from django.shortcuts import render
from django.views import View


class HomeView(View):
    template = "quizitive/index.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)
