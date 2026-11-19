from collections.abc import Awaitable, Callable, Iterable
from inspect import iscoroutinefunction
from typing import Any

import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse

from asgiref.sync import markcoroutinefunction, sync_to_async
from pylti1p3.exception import LtiException

from .constants import SESSION_KEY
from .models import AbsentLtiLaunch
from .types import LtiHttpRequest
from .utils import (
    get_embed_cache,
    get_embed_cache_key,
    get_embed_cache_timeout,
    get_launch_from_request,
)


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


def _merge_frame_ancestors(config: dict[str, Any], domains: set[str]) -> dict[str, Any]:
    """Returns a copy of a CSP config with domains added to frame-ancestors."""
    sources = config.get("frame-ancestors")
    if isinstance(sources, str):
        sources = [sources]
    elif not isinstance(sources, Iterable):
        sources = []
    return {
        **config,
        "frame-ancestors": {source for source in sources if source.lower() != "'none'"}
        | domains,
    }


class LtiEmbedMiddleware:
    """Allow LTI sessions to be embedded in the appropriate platform."""

    sync_capable = True
    async_capable = True

    def __init__(
        self,
        get_response: Callable[[LtiHttpRequest], Any],
    ) -> None:
        if django.VERSION < (6, 0):
            raise ImproperlyConfigured(
                "LtiEmbedMiddleware requires Django 6.0 or later."
            )
        self.get_response = get_response
        self.async_mode = iscoroutinefunction(self.get_response)
        if self.async_mode:
            markcoroutinefunction(self)

    def check_launch_middleware(self, request: LtiHttpRequest) -> None:
        """Raises if LtiLaunchMiddleware hasn't run before this middleware."""
        if not hasattr(request, "lti_launch"):
            raise ImproperlyConfigured(
                "LtiEmbedMiddleware requires LtiLaunchMiddleware to be listed "
                "before it in MIDDLEWARE."
            )

    def get_domains(self, request: LtiHttpRequest) -> set[str]:
        """Returns the embed domains that apply to the request, if any."""
        registration = getattr(request, "lti_registration", None)  # OIDC init
        if registration is None:
            if isinstance(request.lti_launch, AbsentLtiLaunch):
                return set()
            registration = request.lti_launch.registration  # launch requests
        domains: set[str] | None = get_embed_cache().get_or_set(
            get_embed_cache_key(registration.id),
            lambda: set(registration.embed_domains.values_list("domain", flat=True)),
            timeout=get_embed_cache_timeout(),
        )
        return domains or set()

    def add_frame_ancestors(
        self, response: HttpResponse, domains: set[str]
    ) -> HttpResponse:
        """Adds domains to frame-ancestors in the enforced and report-only policies.

        A policy is left alone if a view overrode it with ``csp_override`` or
        ``csp_report_only_override``. The report-only policy is only changed if
        it already restricts frame-ancestors, so new violation reports aren't
        introduced.
        """
        if not domains:
            return response
        # (response attribute set by Django's CSP decorators, setting name,
        #  whether to add frame-ancestors when the policy doesn't already have it)
        targets = (
            ("_csp_config", "SECURE_CSP", True),
            ("_csp_ro_config", "SECURE_CSP_REPORT_ONLY", False),
        )
        for attr, setting_name, add_if_missing in targets:
            if hasattr(response, attr):
                continue
            config = getattr(settings, setting_name)
            if not add_if_missing and not config.get("frame-ancestors"):
                continue
            setattr(response, attr, _merge_frame_ancestors(config, domains))
        return response

    def __call__(
        self, request: LtiHttpRequest
    ) -> HttpResponse | Awaitable[HttpResponse]:
        if self.async_mode:
            return self.__acall__(request)
        self.check_launch_middleware(request)
        response = self.get_response(request)
        return self.add_frame_ancestors(response, self.get_domains(request))

    async def __acall__(self, request: LtiHttpRequest) -> HttpResponse:
        self.check_launch_middleware(request)
        response = await self.get_response(request)
        domains = await sync_to_async(self.get_domains)(request)
        return self.add_frame_ancestors(response, domains)
