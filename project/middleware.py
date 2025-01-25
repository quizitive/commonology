from django.middleware.common import CommonMiddleware
from django.http import HttpRequest, HttpResponse
import logging
import uuid

from project.log_context import log_context

logger = logging.getLogger(__name__)


class ParametersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for key, value in request.GET.items():
            parameter = key.strip("?")
            request.session[parameter] = value
        return self.get_response(request)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = str(uuid.uuid4())
        request.META["REQUEST_ID"] = request_id
        user_id = request.user.id

        with log_context(request_id=request_id, user_id=user_id):
            logger.info(f"Received request: {request.method} {request.path}")
            response = self.get_response(request)
            logger.info(f"Sending response: {request.method} {request.path} | " f"Status: {response.status_code}")
            return response
