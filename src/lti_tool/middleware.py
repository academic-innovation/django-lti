from pylti1p3.exception import LtiException

from .constants import SESSION_KEY
from .models import AbsentLtiLaunch
from .utils import get_launch_from_request


class LtiLaunchMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        launch_id = request.session.get(SESSION_KEY)
        try:
            request.lti_launch = get_launch_from_request(request, launch_id)
        except LtiException:
            request.lti_launch = AbsentLtiLaunch()
        return self.get_response(request)
