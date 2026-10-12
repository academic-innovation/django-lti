from django.http import HttpRequest

from .models import AbsentLtiLaunch, LtiLaunch


class LtiHttpRequest(HttpRequest):
    lti_launch: LtiLaunch | AbsentLtiLaunch
