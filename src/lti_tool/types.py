from django.http import HttpRequest

from .models import AbsentLtiLaunch, LtiLaunch, LtiRegistration


class LtiHttpRequest(HttpRequest):
    lti_launch: LtiLaunch | AbsentLtiLaunch
    lti_registration: LtiRegistration | None
