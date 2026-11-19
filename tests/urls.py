from types import SimpleNamespace

from django.http import HttpResponse
from django.urls import path
from django.views.decorators.csp import csp_override, csp_report_only_override

from lti_tool.models import LtiRegistration
from lti_tool.views import OIDCLoginInitView


def empty_view(request, *args, **kwargs):
    return HttpResponse()


async def empty_view_async(request, *args, **kwargs):
    return HttpResponse()


@csp_override({"default-src": ["'self'", "cdn.example.com"]})
def csp_override_view(request, *args, **kwargs):
    return HttpResponse()


@csp_override({"default-src": ["'self'", "cdn.example.com"]})
async def csp_override_view_async(request, *args, **kwargs):
    return HttpResponse()


@csp_report_only_override({"default-src": ["'self'", "cdn.example.com"]})
def csp_report_only_override_view(request, *args, **kwargs):
    return HttpResponse()


@csp_report_only_override({"default-src": ["'self'", "cdn.example.com"]})
async def csp_report_only_override_view_async(request, *args, **kwargs):
    return HttpResponse()


def launch_view(request, *args, **kwargs):
    """Sets a stand-in launch during the view, like LtiLaunchBaseView.post does."""
    registration = LtiRegistration.objects.get(pk=request.GET["registration_id"])
    request.lti_launch = SimpleNamespace(registration=registration)
    return HttpResponse()


async def launch_view_async(request, *args, **kwargs):
    """Sets a stand-in launch during the view, like LtiLaunchBaseView.post does."""
    registration = await LtiRegistration.objects.aget(pk=request.GET["registration_id"])
    request.lti_launch = SimpleNamespace(registration=registration)
    return HttpResponse()


urlpatterns = [
    path("page/", empty_view),
    path("async_page/", empty_view_async),
    path("csp_override/", csp_override_view),
    path("async_csp_override/", csp_override_view_async),
    path("csp_report_only_override/", csp_report_only_override_view),
    path("async_csp_report_only_override/", csp_report_only_override_view_async),
    path("launch_page/", launch_view),
    path("async_launch_page/", launch_view_async),
    path("init/", OIDCLoginInitView.as_view()),
    path("init/<uuid:registration_uuid>/", OIDCLoginInitView.as_view()),
]
