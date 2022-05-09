from typing import Union

from django.http import HttpRequest

from .models import AbsentLtiLaunch, LtiLaunch


class LtiHttpRequest(HttpRequest):
    lti_launch: Union[LtiLaunch, AbsentLtiLaunch]
