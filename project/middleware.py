

class ParametersMiddleware():
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        for key, value in request.GET.items():
            parameter = key.strip('?')
            request.session[parameter] = value
        return self.get_response(request)
