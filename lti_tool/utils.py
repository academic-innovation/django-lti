from typing import Optional

from django.http.request import HttpRequest

from pylti1p3.contrib.django.launch_data_storage.cache import DjangoCacheDataStorage
from pylti1p3.contrib.django.message_launch import DjangoMessageLaunch
from pylti1p3.deployment import Deployment
from pylti1p3.registration import Registration
from pylti1p3.tool_config.abstract import ToolConfAbstract

from .models import Key, LtiDeployment, LtiLaunch, LtiRegistration


def _prepare_registraion(lti_registration):
    reg = Registration()
    reg.set_auth_login_url(lti_registration.auth_url)
    reg.set_auth_token_url(lti_registration.token_url)
    # reg.set_auth_audience(auth_audience)
    reg.set_client_id(lti_registration.client_id)
    # reg.set_key_set(key_set)
    reg.set_key_set_url(lti_registration.keyset_url)
    reg.set_issuer(lti_registration.issuer)
    if lti_registration.has_key:
        reg.set_tool_public_key(lti_registration.public_key)
        reg.set_tool_private_key(lti_registration.private_key)
    else:
        key = Key.objects.active().latest()
        reg.set_tool_private_key(key.private_key)
        reg.set_tool_public_key(key.public_key)
    return reg


def _prepare_deployment(lti_deployment):
    return Deployment().set_deployment_id(lti_deployment.deployment_id)


class DjangoToolConfig(ToolConfAbstract):
    """LTI tool configuration class.

    A registration UUID may be specified on init to address situations
    where client_id isn't included in OIDC initiation params.
    """

    registration_uuid = None
    registration = None
    deployment = None

    def __init__(self, registration_uuid=None):
        super().__init__()
        self.registration_uuid = registration_uuid

    def check_iss_has_one_client(self, iss):
        return False

    def check_iss_has_many_clients(self, iss):
        return True

    def find_registration_by_issuer(self, iss, *args, **kwargs):
        try:
            self.registration = LtiRegistration.objects.active().get(
                uuid=self.registration_uuid, issuer=iss
            )
            return _prepare_registraion(self.registration)
        except LtiRegistration.DoesNotExist:
            return None

    def find_registration_by_params(self, iss, client_id, *args, **kwargs):
        lookups = {"issuer": iss, "client_id": client_id}
        if self.registration_uuid is not None:
            lookups.update(uuid=self.registration_uuid)
        try:
            self.registration = LtiRegistration.objects.active().get(**lookups)
            return _prepare_registraion(self.registration)
        except LtiRegistration.DoesNotExist:
            return None

    def find_deployment(self, iss, deployment_id):
        try:
            self.deployment = LtiDeployment.objects.active().get(
                registration__uuid=self.registration_uuid,
                registration__issuer=iss,
                registration__is_active=True,
                deployment_id=deployment_id,
            )
            return _prepare_deployment(self.deployment)
        except LtiDeployment.DoesNotExist:
            return None

    def find_deployment_by_params(self, iss, deployment_id, client_id, *args, **kwargs):
        lookups = {
            "registration__issuer": iss,
            "registration__client_id": client_id,
            "registration__is_active": True,
            "deployment_id": deployment_id,
        }
        if self.registration_uuid is not None:
            lookups.update(registration__uuid=self.registration_uuid)
        try:
            self.deployment = LtiDeployment.objects.active().get(**lookups)
            return _prepare_deployment(self.deployment)
        except LtiDeployment.DoesNotExist:
            return None


def get_launch_from_request(
    request: HttpRequest, launch_id: Optional[str] = None
) -> LtiLaunch:
    """
    Returns the DjangoMessageLaunch associated with a request.

    Optionally, a launch_id may be specified to retrieve the launch from the cache.
    """

    tool_conf = DjangoToolConfig()
    launch_data_storage = DjangoCacheDataStorage()
    if launch_id is not None:
        message_launch = DjangoMessageLaunch.from_cache(
            launch_id, request, tool_conf, launch_data_storage=launch_data_storage
        )
    else:
        message_launch = DjangoMessageLaunch(
            request, tool_conf, launch_data_storage=launch_data_storage
        )
        message_launch.validate()
    return LtiLaunch(message_launch)
