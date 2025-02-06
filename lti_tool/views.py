from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import urljoin

from pylti1p3.contrib.django import DjangoCacheDataStorage, DjangoOIDCLogin

from lti_tool.utils import DjangoToolConfig, get_launch_from_request

from .constants import SESSION_KEY
from .models import Key, LtiLaunch
from .types import LtiHttpRequest
from .utils import sync_data_from_launch


def jwks(request):
    """Makes a JWKS available to LTI platforms."""
    return JsonResponse(Key.objects.as_jwks())


@method_decorator(csrf_exempt, name="dispatch")
class OIDCLoginInitView(View):
    """Handles OIDC 3rd-party login initiation for an LTI launch."""

    main_msg = (
        "Your browser prevents embedded content from using cookies.  To work "
        "around this, the content must be opened in a new tab or window.  "
    )
    click_msg = "Open a new tab or window now."
    loading_msg = "Loading..."

    def get(self, request, *args, **kwargs):
        registration_uuid = kwargs.get("registration_uuid")
        return self.get_oidc_response(request, registration_uuid, request.GET)

    def post(self, request, *args, **kwargs):
        registration_uuid = kwargs.get("registration_uuid")
        return self.get_oidc_response(request, registration_uuid, request.POST)

    def get_redirect_url(self, target_link_uri: str) -> str:
        """Returns the redirect_uri to use for the OIDC initiation response."""
        return target_link_uri

    def get_oidc_response(self, request, registration_uuid, params):
        tool_conf = DjangoToolConfig(registration_uuid)
        launch_data_storage = DjangoCacheDataStorage()
        oidc_login = DjangoOIDCLogin(
            request, tool_conf, launch_data_storage=launch_data_storage
        )
        target_link_uri = params.get("target_link_uri")
        if target_link_uri is None:
            return HttpResponseBadRequest("Missing target_link_uri parameter.")
        redirect_url = self.get_redirect_url(target_link_uri)
        return oidc_login.enable_check_cookies(
            self.main_msg, self.click_msg, self.loading_msg
        ).redirect(redirect_url)


@method_decorator(csrf_exempt, name="dispatch")
class LtiLaunchBaseView(View):
    """Base view for handling LTI 1.3 launches.

    Inherit from this view and implement the `handle_resource_launch` method. Other
    message types can be handled as well by overriding the appropriate method.
    """

    def post(self, request: LtiHttpRequest, *args, **kwargs):
        request.session.clear()
        lti_launch = get_launch_from_request(request)
        sync_data_from_launch(lti_launch)
        self.launch_setup(request, lti_launch)
        if not lti_launch.deployment.is_active:
            return self.handle_inactive_deployment(request, lti_launch)
        request.session[SESSION_KEY] = lti_launch.get_launch_id()
        request.lti_launch = lti_launch
        if request.lti_launch.is_resource_launch:
            return self.handle_resource_launch(request, lti_launch)
        if request.lti_launch.is_deep_link_launch:
            return self.handle_deep_linking_launch(request, lti_launch)
        if request.lti_launch.is_submission_review_launch:
            return self.handle_submission_review_launch(request, lti_launch)
        if request.lti_launch.is_data_privacy_launch:
            return self.handle_data_privacy_launch(request, lti_launch)

    def launch_setup(self, request: HttpRequest, lti_launch: LtiLaunch) -> None:
        pass

    def handle_inactive_deployment(
        self, request: HttpRequest, lti_launch: LtiLaunch
    ) -> HttpResponse:
        """Handles LTI launches with inactive deployments."""
        error_msg = _("This deployment is not active.")
        return_url = lti_launch.get_return_url(lti_errormsg=error_msg)
        if return_url is None:
            return HttpResponseForbidden(error_msg)
        return HttpResponseRedirect(return_url)

    def handle_resource_launch(
        self, request: HttpRequest, lti_launch: LtiLaunch
    ) -> HttpResponse:
        """Handles an LTI resource launch.

        Implement this method to handle LTI resource link launch requests,
        as described in the LTI 1.3 core spec at
        https://www.imsglobal.org/spec/lti/v1p3/#resource-link-launch-request-message
        """
        raise NotImplementedError(
            "Subclasses of LtiLaunchBaseView must implement handle_resource_launch"
        )

    def handle_deep_linking_launch(
        self, request: HttpRequest, lti_launch: LtiLaunch
    ) -> HttpResponse:
        error_msg = _("Deep linking is not supported.")
        # TODO: Update once pylti1p3 supports error_msg claim.
        return HttpResponseForbidden(error_msg)

    def handle_submission_review_launch(
        self, request: HttpRequest, lti_launch: LtiLaunch
    ) -> HttpResponse:
        error_msg = _("Submission review launch is not supported.")
        return_url = lti_launch.get_return_url(lti_errormsg=error_msg)
        if return_url is None:
            return HttpResponseForbidden(error_msg)
        return HttpResponseRedirect(return_url)

    def handle_data_privacy_launch(
        self, request: HttpRequest, lti_launch: LtiLaunch
    ) -> HttpResponse:
        error_msg = _("Data privacy launch is not supported.")
        return_url = lti_launch.get_return_url(lti_errormsg=error_msg)
        if return_url is None:
            return HttpResponseForbidden(error_msg)
        return HttpResponseRedirect(return_url)


class LtiConfigView(View):
    """
    JSON configuration endpoint for LTI 1.3.

    In Canvas LMS, an LTI Developer Key can be created via Manual
    Entry, or by URL. This view provides the JSON necessary for URL
    configuration in Canvas.

    https://canvas.instructure.com/doc/api/file.lti_dev_key_config.html
    """
    @staticmethod
    def get_config_json(domain: str, uuid: str) -> dict:
        oidc_init_uri = urljoin(
            "https://{}".format(domain),
            reverse("init", kwargs={"registration_uuid": uuid}))

        title = ""
        description = ""
        if hasattr(settings, "LTI_TOOL_CONFIGURATION"):
            if settings.LTI_TOOL_CONFIGURATION["title"]:
                title = settings.LTI_TOOL_CONFIGURATION["title"]

            if settings.LTI_TOOL_CONFIGURATION["description"]:
                description = settings.LTI_TOOL_CONFIGURATION["description"]

        return {
            "title": title,
            "description": description,
            "oidc_initiation_url": oidc_init_uri,
            "scopes": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
            ],
            "public_jwk_url": urljoin(
                "https://{}".format(domain), reverse("jwks")),
        }

    def config_hook(self, config: dict) -> dict:
        """
        Override this method at the application level to customize the
        configuration object. At the very least, `target_link_uri`
        must be added to the config dictionary.

        You can configure placements for the LTI application within
        the LMS tool via options in the returned dictionary.

        See reference documentation:
        https://canvas.instructure.com/doc/api/file.lti_dev_key_config.html
        """
        return config

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        domain = request.get_host()
        registration_uuid = kwargs.get("registration_uuid")
        config_obj = LtiConfigView.get_config_json(domain, registration_uuid)

        config_obj = self.config_hook(config_obj)

        return JsonResponse(config_obj)
