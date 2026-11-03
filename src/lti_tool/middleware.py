from inspect import iscoroutinefunction

from asgiref.sync import markcoroutinefunction, sync_to_async
from pylti1p3.exception import LtiException

from .constants import SESSION_KEY
from .models import AbsentLtiLaunch
from .utils import get_launch_from_request


class LtiLaunchMiddleware:
    """Resolve the current LTI launch from the session and attach it to the request."""

    sync_capable = True
    async_capable = True

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)
        if self.async_mode:
            markcoroutinefunction(self)

    def __call__(self, request):
        if self.async_mode:
            return self.__acall__(request)
        launch_id = request.session.get(SESSION_KEY)
        try:
            request.lti_launch = get_launch_from_request(request, launch_id)
        except LtiException:
            request.lti_launch = AbsentLtiLaunch()
        return self.get_response(request)

    async def __acall__(self, request):
        launch_id = await request.session.aget(SESSION_KEY)
        try:
            request.lti_launch = await sync_to_async(get_launch_from_request)(
                request, launch_id
            )
        except LtiException:
            request.lti_launch = AbsentLtiLaunch()
        return await self.get_response(request)
