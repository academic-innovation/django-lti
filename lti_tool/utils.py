import re
from typing import Optional

from django.http.request import HttpRequest

from pylti1p3.contrib.django.launch_data_storage.cache import DjangoCacheDataStorage
from pylti1p3.contrib.django.message_launch import DjangoMessageLaunch
from pylti1p3.deployment import Deployment
from pylti1p3.tool_config.abstract import ToolConfAbstract

from .constants import AgsScope, ContextRole, ContextType
from .models import (
    LtiContext,
    LtiDeployment,
    LtiLaunch,
    LtiMembership,
    LtiPlatformInstance,
    LtiRegistration,
    LtiResourceLink,
    LtiUser,
)


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
            return self.registration.to_registration()
        except LtiRegistration.DoesNotExist:
            return None

    def find_registration_by_params(self, iss, client_id, *args, **kwargs):
        lookups = {"issuer": iss, "client_id": client_id}
        if self.registration_uuid is not None:
            lookups.update(uuid=self.registration_uuid)
        try:
            self.registration = LtiRegistration.objects.active().get(**lookups)
            return self.registration.to_registration()
        except LtiRegistration.DoesNotExist:
            return None

    def find_deployment(self, iss, deployment_id):
        try:
            self.deployment = LtiDeployment.objects.get(
                registration__uuid=self.registration_uuid,
                registration__issuer=iss,
                registration__is_active=True,
                deployment_id=deployment_id,
            )
        except LtiDeployment.DoesNotExist:
            self.deployment = LtiDeployment.objects.create(
                registration=self.registration, deployment_id=deployment_id
            )
        return _prepare_deployment(self.deployment)

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
            self.deployment = LtiDeployment.objects.get(**lookups)
        except LtiDeployment.DoesNotExist:
            self.deployment = LtiDeployment.objects.create(
                registration=self.registration, deployment_id=deployment_id
            )
        return _prepare_deployment(self.deployment)


def normalize_role(role: str) -> str:
    """Expands a simple context role to a full URI, if needed."""
    if re.match(r"^\w+$", role):
        return f"http://purl.imsglobal.org/vocab/lis/v2/membership#{role}"
    return role


def get_launch_from_request(
    request: HttpRequest, launch_id: Optional[str] = None
) -> LtiLaunch:
    """Returns the DjangoMessageLaunch associated with a request.

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


def sync_user_from_launch(lti_launch: LtiLaunch) -> LtiUser:
    sub = lti_launch.get_claim("sub")
    user_claims = {
        "given_name": lti_launch.get_claim("given_name"),
        "family_name": lti_launch.get_claim("family_name"),
        "name": lti_launch.get_claim("name"),
        "email": lti_launch.get_claim("email"),
        "picture_url": lti_launch.get_claim("picture"),
    }
    lti_user, _created = LtiUser.objects.update_or_create(
        registration=lti_launch.registration,
        sub=sub,
        defaults={k: v for k, v in user_claims.items() if v is not None},
    )
    return lti_user


def _get_ags_props(lti_launch: LtiLaunch) -> dict:
    ags_claim = lti_launch.ags_claim
    if ags_claim is None:
        return {}
    ags_scope = ags_claim.get("scope", [])
    return {
        "lineitems_url": ags_claim.get("lineitems", ""),
        "can_query_lineitems": AgsScope.QUERY_LINEITEMS in ags_scope,
        "can_manage_lineitems": AgsScope.MANAGE_LINEITEMS in ags_scope,
        "can_publish_scores": AgsScope.PUBLISH_SCORES in ags_scope,
        "can_access_results": AgsScope.ACCESS_RESULTS in ags_scope,
    }


def sync_context_from_launch(lti_launch: LtiLaunch) -> LtiContext:
    context_claim = {} if lti_launch.context_claim is None else lti_launch.context_claim
    nrps_claim = lti_launch.nrps_claim
    nrps_endpoint = "" if nrps_claim is None else nrps_claim["context_memberships_url"]
    context_types = context_claim.get("type", [])
    defaults = {
        "title": context_claim.get("title", ""),
        "label": context_claim.get("label", ""),
        "is_course_template": (ContextType.COURSE_TEMPLATE in context_types),
        "is_course_offering": (ContextType.COURSE_OFFERING in context_types),
        "is_course_section": (ContextType.COURSE_SECTION in context_types),
        "is_group": (ContextType.GROUP in context_types),
    }
    if nrps_endpoint:
        defaults["memberships_url"] = nrps_endpoint
    defaults.update(_get_ags_props(lti_launch))
    context, _created = LtiContext.objects.update_or_create(
        deployment=lti_launch.deployment,
        id_on_platform=context_claim.get("id", ""),
        defaults=defaults,
    )
    return context


def sync_membership_from_launch(
    lti_launch: LtiLaunch, user: LtiUser, context: LtiContext
) -> LtiMembership:
    roles = [normalize_role(role) for role in lti_launch.roles_claim]
    defaults = {}
    if ContextRole.ADMINISTRATOR in roles:
        defaults["is_administrator"] = True
    if ContextRole.CONTENT_DEVELOPER in roles:
        defaults["is_content_developer"] = True
    if ContextRole.INSTRUCTOR in roles:
        defaults["is_instructor"] = True
    if ContextRole.LEARNER in roles:
        defaults["is_learner"] = True
    if ContextRole.MENTOR in roles:
        defaults["is_mentor"] = True
    membership, _created = LtiMembership.objects.update_or_create(
        user=user, context=context, defaults=defaults
    )
    return membership


def sync_resource_link_from_launch(
    lti_launch: LtiLaunch, context: LtiContext
) -> LtiResourceLink:
    resource_link_claim = {
        k: v for k, v in lti_launch.resource_link_claim.items() if v is not None
    }
    resource_link, _created = LtiResourceLink.objects.update_or_create(
        context=context,
        id_on_platform=resource_link_claim["id"],
        defaults={
            "title": resource_link_claim.get("title", ""),
            "description": resource_link_claim.get("description", ""),
        },
    )
    return resource_link


def sync_platform_instance_from_launch(
    lti_launch: LtiLaunch,
) -> Optional[LtiPlatformInstance]:
    platform_instance_claim = lti_launch.platform_instance_claim
    if platform_instance_claim is None:
        return None
    platform_instance, _created = LtiPlatformInstance.objects.update_or_create(
        issuer=lti_launch.get_claim("iss"),
        guid=platform_instance_claim["guid"],
        defaults={
            "contact_email": platform_instance_claim.get("contact_email", ""),
            "description": platform_instance_claim.get("description", ""),
            "name": platform_instance_claim.get("name", ""),
            "url": platform_instance_claim.get("url", ""),
            "product_family_code": platform_instance_claim.get(
                "product_family_code", ""
            ),
            "version": platform_instance_claim.get("version", ""),
        },
    )
    deployment = lti_launch.deployment
    deployment.platform_instance = platform_instance
    deployment.save(update_fields=["platform_instance"])
    return platform_instance


def sync_data_from_launch(lti_launch: LtiLaunch) -> None:
    user = sync_user_from_launch(lti_launch)
    if not lti_launch.is_data_privacy_launch:
        context = sync_context_from_launch(lti_launch)
        sync_membership_from_launch(lti_launch, user, context)
        if not lti_launch.is_deep_link_launch:
            sync_resource_link_from_launch(lti_launch, context)
    sync_platform_instance_from_launch(lti_launch)
