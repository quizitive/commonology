from urllib.parse import urlparse, parse_qs, urlencode

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import View

from project.utils import REDIS


class HTMXProtectedView(UserPassesTestMixin, View):
    """This view requires a user to have the url path in their session, and each query parameter
    is validated against the possible values stored in the session. Use htmx_call function below
    in your view to use classes of this type.

    If you don't want to protect on all query params (e.g. 'q' in: /leaderboard/htmx/?slug=rambus&q=ted)
    override protected_args to return only the args you DO want. In a case like this, we want to validate
    that this session can make calls to the rambus leaderboard, but we don't care what the search query is.
    """

    def test_func(self):
        validation_dict = self.request.session.get(self.request.path)
        if validation_dict is None:
            return False
        for arg in self.protected_args:
            for val in self.request.GET.getlist(arg):
                if val not in validation_dict.get(arg, {}):
                    return False
        return True

    @property
    def protected_args(self):
        return self.request.GET.keys()


def htmx_call(request, path):
    """
    This will put the request path with the corresponding query params into the session to authorize
    a subsequent ajax call from the browser.
    """
    parsed_path = urlparse(path)
    query_args = parse_qs(parsed_path.query)
    request.session[parsed_path.path] = query_args
    return path
