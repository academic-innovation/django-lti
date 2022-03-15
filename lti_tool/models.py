import json
import re
from typing import List, Optional, Tuple
from urllib import parse
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.http import HttpResponse
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from jwcrypto.jwk import JWK
from pylti1p3.contrib.django.message_launch import DjangoMessageLaunch
from pylti1p3.deep_link_resource import DeepLinkResource
from pylti1p3.registration import Registration

from .constants import ContextRole


class KeyQuerySet(models.QuerySet):
    """Custom QuerySet for Key objects."""

    def active(self):
        """Excludes inactive keys from the QuerySet."""
        return self.filter(is_active=True)

    def as_jwks(self):
        """Returns active keys as a JWKS."""
        return {"keys": [key.as_jwk() for key in self.active()]}


class KeyManager(models.Manager):
    """Manager for Key objects."""

    def create_from_jwk(self, key):
        """Creates and returns a new Key object using the provided JWK.

        Args:
            key (JWK): The JWK used to create the Key.

        Returns:
            Key: A new Key object.
        """
        return self.create(
            public_key=key.export_to_pem().decode("utf-8"),
            private_key=key.export_to_pem(private_key=True, password=None).decode(
                "utf-8"
            ),
        )

    def generate(self):
        """Creates and returns a new keypair.

        Returns:
            Key: A new Key object.
        """
        return self.create_from_jwk(JWK.generate(kty="RSA", size=2048))


class Key(models.Model):
    """A keypair for use in LTI integrations.

    Attributes:
        public_key (str): Public key data.
        private_key (str): Private key data.
        is_active (bool): Indicates if the key is present in the JWKS.
        datetime_created (datetime): When the key was created.
        datetime_modified (datetime): When the key was last modified.
    """

    public_key = models.TextField(_("public key"))
    private_key = models.TextField(_("private key"))
    is_active = models.BooleanField(_("is active"), default=True)
    datetime_created = models.DateTimeField(_("created"), default=now, editable=False)
    datetime_modified = models.DateTimeField(_("modified"), auto_now=True)

    objects = KeyManager.from_queryset(KeyQuerySet)()

    class Meta:
        verbose_name = _("JWK")
        verbose_name_plural = _("JWKs")
        get_latest_by = "datetime_created"

    def __str__(self):
        return self.as_jwk()["kid"]

    def as_jwk(self):
        """Returns the key as a JWK."""
        jwk_obj = JWK.from_pem(self.public_key.encode("utf-8"))
        public_jwk = json.loads(jwk_obj.export_public())
        public_jwk["alg"] = "RS256"
        public_jwk["use"] = "sig"
        return public_jwk


class LtiRegistrationQuerySet(models.QuerySet):
    """Custom QuerySet for LtiRegistration objects."""

    def active(self):
        """Excludes inactive registrations from the QuerySet."""
        return self.filter(is_active=True)


class LtiRegistration(models.Model):
    """A LTI platform registration.

    Attributes:
        name (str): A display name for this registration
        uuid (uuid4): A unique identifier for registraitons for use in OIDC login init.
        issuer (str): The platform's issuer.
        client_id (str): The client ID assigned to the tool by the platform.
        auth_url (str): The platform's auth login URL.
        token_url (str): The platform's access token retrieval URL.
        keyset_url (str): The platform's JWKS URL.
        is_active (bool): Indicates if the registration is active within the tool.
        public_key (str): Public key data specifc to this registration. Only to be used
            when the platform cannot retrieve keys from a tool's JWKS URL.
        private_key (str): Private key data specifc to this registration. Only to be
            used when the platform cannot retrieve keys from a tool's JWKS URL.
        datetime_created (datetime): When the registration was created.
        datetime_modified (datetime): When the registration was last modified.
    """

    name = models.CharField(_("name"), max_length=255)
    uuid = models.UUIDField(_("UUID"), default=uuid4)
    issuer = models.CharField(_("issuer"), max_length=255)
    client_id = models.CharField(_("client ID"), max_length=255)
    auth_url = models.URLField(_("auth URL"))
    token_url = models.URLField(_("access token URL"))
    keyset_url = models.URLField(_("keyset URL"))
    is_active = models.BooleanField(_("is active"), default=True)
    public_key = models.TextField(_("public key"), blank=True)
    private_key = models.TextField(_("private key"), blank=True)
    datetime_created = models.DateTimeField(_("created"), default=now, editable=False)
    datetime_modified = models.DateTimeField(_("modified"), auto_now=True)

    objects = LtiRegistrationQuerySet.as_manager()

    class Meta:
        verbose_name = _("LTI registration")
        verbose_name_plural = _("LTI registrations")
        constraints = [
            models.UniqueConstraint(
                fields=["issuer", "client_id"], name="unique_client_id_per_issuer"
            )
        ]

    def __str__(self):
        return self.name

    @property
    def has_key(self):
        """bool: Indicates if the registration has an assigned keypair."""
        return self.public_key and self.private_key

    def to_registration(self) -> Registration:
        reg = Registration()
        reg.set_auth_login_url(self.auth_url)
        reg.set_auth_token_url(self.token_url)
        # reg.set_auth_audience(auth_audience)
        reg.set_client_id(self.client_id)
        # reg.set_key_set(key_set)
        reg.set_key_set_url(self.keyset_url)
        reg.set_issuer(self.issuer)
        if self.has_key:
            reg.set_tool_public_key(self.public_key)
            reg.set_tool_private_key(self.private_key)
        else:
            key = Key.objects.active().latest()
            reg.set_tool_private_key(key.private_key)
            reg.set_tool_public_key(key.public_key)
        return reg


class LtiPlatformInstance(models.Model):
    """An instance of a LTI learning platform.

    The platform instance claim is described in the LTI spec at
    https://www.imsglobal.org/spec/lti/v1p3/#platform-instance-claim
    """

    issuer = models.CharField(_("issuer"), max_length=255)
    guid = models.CharField(_("GUID"), max_length=255)
    contact_email = models.EmailField(_("contact email"), blank=True)
    description = models.TextField(_("description"), blank=True)
    name = models.CharField(_("name"), max_length=500, blank=True)
    url = models.URLField(_("URL"), blank=True)
    product_family_code = models.CharField(
        _("product family code"), max_length=500, blank=True
    )
    version = models.CharField(_("version"), max_length=500, blank=True)

    class Meta:
        verbose_name = _("LTI platform instance")
        verbose_name_plural = _("LTI platform instances")
        constraints = [
            models.UniqueConstraint(
                fields=["issuer", "guid"], name="unique_guid_per_issuer"
            )
        ]

    def __str__(self) -> str:
        return self.name if self.name else self.guid


class LtiDeploymentQuerySet(models.QuerySet):
    """Custom QuerySet for LtiDeployment objects."""

    def active(self):
        """Excludes inactive deployments from the QuerySet."""
        return self.filter(is_active=True)


class LtiDeployment(models.Model):
    """A LTI deployment.

    Deployments are described in the LTI 1.3 core specification at
    https://www.imsglobal.org/spec/lti/v1p3/#tool-deployment.

    Attributes:
        registration (LtiRegistration): The platform registration associated with
            this deployment.
        deployment_id (str): The deployment ID as provided by the platform.
        is_active (bool): Indicates if the deployment has been activated in the tool.
        platform_instance (LtiPlatformInstance): The platform instance associated with
            this deployment.
        datetime_created (datetime): When the deployment was created.
        datetime_modified (datetime): When the deployment was last modified.
    """

    registration = models.ForeignKey(
        LtiRegistration,
        related_name="deployments",
        on_delete=models.CASCADE,
        verbose_name=_("registration"),
    )
    deployment_id = models.CharField(_("deployment ID"), max_length=255)
    is_active = models.BooleanField(_("is active"), default=False)
    platform_instance = models.ForeignKey(
        LtiPlatformInstance,
        related_name="deployments",
        on_delete=models.SET_NULL,
        verbose_name=_("platform instance"),
        null=True,
        blank=True,
    )
    datetime_created = models.DateTimeField(_("created"), default=now, editable=False)
    datetime_modified = models.DateTimeField(_("modified"), auto_now=True)

    objects = LtiDeploymentQuerySet.as_manager()

    class Meta:
        verbose_name = _("LTI deployment")
        verbose_name_plural = _("LTI deployments")
        constraints = [
            models.UniqueConstraint(
                fields=["registration", "deployment_id"],
                name="unique_deployment_id_per_registration",
            )
        ]

    def __str__(self):
        return f"{self.registration}: {self.deployment_id}"


class LtiUser(models.Model):
    """A platform user as described by an LTI launch.

    The user identity claims are described in the LTI spec at
    https://www.imsglobal.org/spec/lti/v1p3/#user-identity-claims
    """

    registration = models.ForeignKey(
        LtiRegistration,
        related_name="users",
        on_delete=models.CASCADE,
        verbose_name=_("registration"),
    )
    sub = models.CharField(_("subject"), max_length=255)
    given_name = models.CharField(_("given name"), max_length=500, blank=True)
    family_name = models.CharField(_("family name"), max_length=500, blank=True)
    name = models.CharField(_("name"), max_length=500, blank=True)
    email = models.EmailField(_("email"), blank=True)
    picture_url = models.URLField(_("picture URL"), blank=True)
    auth_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="lti_users",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("auth user"),
    )
    datetime_created = models.DateTimeField(_("created"), default=now, editable=False)
    datetime_modified = models.DateTimeField(_("modified"), auto_now=True)

    class Meta:
        verbose_name = _("LTI user")
        verbose_name_plural = _("LTI users")
        constraints = [
            models.UniqueConstraint(
                fields=["registration", "sub"], name="unique_sub_per_registration"
            )
        ]

    def __str__(self):
        return self.sub


class LtiContext(models.Model):
    """Describes the context of a LTI launch.

    The context claim are described in the LTI spec at
    https://www.imsglobal.org/spec/lti/v1p3/#context-claim
    """

    deployment = models.ForeignKey(
        LtiDeployment,
        related_name="contexts",
        on_delete=models.CASCADE,
        verbose_name=_("deployment"),
    )
    id_on_platform = models.CharField(_("ID on platform"), max_length=255, blank=True)
    label = models.CharField(_("label"), max_length=255, blank=True)
    title = models.CharField(_("title"), max_length=500, blank=True)
    members = models.ManyToManyField(
        LtiUser,
        related_name="contexts",
        through="LtiMembership",
        verbose_name="members",
    )
    is_course_template = models.BooleanField(_("is course template"), default=False)
    is_course_offering = models.BooleanField(_("is course offering"), default=False)
    is_course_section = models.BooleanField(_("is course section"), default=False)
    memberships_url = models.URLField(blank=True)
    is_group = models.BooleanField(_("is group"), default=False)
    datetime_created = models.DateTimeField(_("created"), default=now, editable=False)
    datetime_modified = models.DateTimeField(_("modified"), auto_now=True)

    class Meta:
        verbose_name = _("LTI context")
        verbose_name_plural = _("LTI contexts")
        constraints = [
            models.UniqueConstraint(
                fields=["deployment", "id_on_platform"],
                name="unique_context_id_per_deployment",
            )
        ]

    def __str__(self):
        return self.title if self.title else self.id_on_platform

    def update_memberships(self, member_data: List[dict]):
        """Updates memberships for this context using NRPS data."""
        registration = self.deployment.registration
        for member in member_data:
            user_defaults = {
                "given_name": member.get("given_name"),
                "family_name": member.get("family_name"),
                "name": member.get("name"),
                "email": member.get("email"),
                "picture_url": member.get("picture"),
            }
            user, _created = LtiUser.objects.update_or_create(
                registration=registration,
                sub=member["user_id"],
                defaults={k: v for (k, v) in user_defaults.items() if v is not None},
            )
            member_roles = [
                LtiMembership.normalize_role(role) for role in member["roles"]
            ]
            LtiMembership.objects.update_or_create(
                context=self,
                user=user,
                defaults={
                    "is_administrator": ContextRole.ADMINISTRATOR in member_roles,
                    "is_content_developer": ContextRole.CONTENT_DEVELOPER
                    in member_roles,
                    "is_instructor": ContextRole.INSTRUCTOR in member_roles,
                    "is_learner": ContextRole.LEARNER in member_roles,
                    "is_mentor": ContextRole.MENTOR in member_roles,
                    "is_active": member["status"] == "Active",
                },
            )


class LtiMembership(models.Model):
    """A user's role within a learning context.

    Roles are described in the LTI spec at
    https://www.imsglobal.org/spec/lti/v1p3/#roles-claim
    """

    user = models.ForeignKey(
        LtiUser,
        related_name="memberships",
        on_delete=models.CASCADE,
        verbose_name=_("user"),
    )
    context = models.ForeignKey(
        LtiContext,
        related_name="memberships",
        on_delete=models.CASCADE,
        verbose_name=_("context"),
    )
    is_administrator = models.BooleanField(_("is administrator"), default=False)
    is_content_developer = models.BooleanField(_("is_content_developer"), default=False)
    is_instructor = models.BooleanField(_("is instructor"), default=False)
    is_learner = models.BooleanField(_("is learner"), default=False)
    is_mentor = models.BooleanField(_("is mentor"), default=False)
    is_active = models.BooleanField(_("is active"), default=True)
    datetime_created = models.DateTimeField(_("created"), default=now, editable=False)
    datetime_modified = models.DateTimeField(_("modified"), auto_now=True)

    class Meta:
        verbose_name = _("LTI membership")
        verbose_name_plural = _("LTI memberships")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "context"], name="no_duplicate_memberships"
            )
        ]

    def __str__(self):
        return f"{self.user} in {self.context}"

    @classmethod
    def normalize_role(cls, role: str) -> str:
        """Expands a simple context role to a full URI, if needed."""
        if re.match(r"^\w+$", role):
            return f"http://purl.imsglobal.org/vocab/lis/v2/membership#{role}"
        return role


class LtiResourceLink(models.Model):
    """Represents a resource link in an LTI launch.

    The resource link claim is described in the LTI spec at
    https://www.imsglobal.org/spec/lti/v1p3/#resource-link-claim
    """

    context = models.ForeignKey(
        LtiContext,
        related_name="resource_links",
        on_delete=models.CASCADE,
        verbose_name=_("context"),
    )
    id_on_platform = models.CharField(_("ID on platform"), max_length=255)
    title = models.CharField(_("title"), max_length=500, blank=True)
    description = models.TextField(_("description"), blank=True)
    datetime_created = models.DateTimeField(_("created"), default=now, editable=False)
    datetime_modified = models.DateTimeField(_("modified"), auto_now=True)

    class Meta:
        verbose_name = _("LTI resource link")
        verbose_name_plural = _("LTI resource links")
        constraints = [
            models.UniqueConstraint(
                fields=["context", "id_on_platform"],
                name="unique_resource_link_id_per_context",
            )
        ]

    def __str__(self):
        return self.title if self.title else self.id_on_platform


class LtiLaunch:
    """A LTI launch."""

    _lti1p3_message_launch: Optional[DjangoMessageLaunch] = None
    _lti1p3_launch_id: Optional[str] = None

    def __init__(self, message_launch: DjangoMessageLaunch) -> None:
        launch_id = None
        if message_launch is not None:
            launch_id = message_launch.get_launch_id()
        self._lti1p3_launch_id = launch_id
        self._lti1p3_message_launch = message_launch

    def get_launch_id(self):
        return self._lti1p3_launch_id

    def get_message_launch(self):
        return self._lti1p3_message_launch

    def get_launch_data(self):
        message_launch = self.get_message_launch()
        if message_launch is None:
            return None
        return message_launch.get_launch_data()

    def get_claim(self, claim):
        launch_data = self.get_launch_data()
        if launch_data is None:
            return None
        return launch_data.get(claim)

    @property
    def is_present(self) -> bool:
        return True

    @property
    def is_absent(self) -> bool:
        return False

    @property
    def is_resource_launch(self) -> bool:
        """Indicates if the launch is resource link launch request."""
        message_launch = self.get_message_launch()
        if message_launch is None:
            return False
        return message_launch.is_resource_launch()

    @property
    def is_deep_link_launch(self) -> bool:
        """Indicates if the launch is a deep linking request."""
        message_launch = self.get_message_launch()
        if message_launch is None:
            return False
        return message_launch.is_deep_link_launch()

    @property
    def is_submission_review_launch(self) -> bool:
        """Indicates if the launch is a submission review request."""
        message_launch = self.get_message_launch()
        if message_launch is None:
            return False
        return message_launch.is_submission_review_launch()

    @property
    def is_data_privacy_launch(self) -> bool:
        """Indicates if the launch is a data privacy launch request."""
        message_launch = self.get_message_launch()
        if message_launch is None:
            return False
        return message_launch.is_data_privacy_launch()

    @cached_property
    def registration(self) -> LtiRegistration:
        tool_conf = self.get_message_launch().get_tool_conf()
        return tool_conf.registration

    @cached_property
    def deployment(self) -> LtiDeployment:
        tool_conf = self.get_message_launch()._tool_config
        if tool_conf.deployment is not None:
            return tool_conf.deployment
        deployment_id = self.get_claim(
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
        )
        return LtiDeployment.objects.get(
            registration=self.registration, deployment_id=deployment_id
        )

    @cached_property
    def user(self) -> LtiUser:
        return LtiUser.objects.get(
            registration=self.registration, sub=self.get_claim("sub")
        )

    @property
    def nrps_claim(self):
        return self.get_claim(
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice"
        )

    @property
    def context_claim(self):
        return self.get_claim("https://purl.imsglobal.org/spec/lti/claim/context")

    @cached_property
    def context(self) -> LtiContext:
        context_id = self.context_claim["id"] if self.context_claim is not None else ""
        return LtiContext.objects.get(
            deployment=self.deployment, id_on_platform=context_id
        )

    @property
    def roles_claim(self):
        return self.get_claim("https://purl.imsglobal.org/spec/lti/claim/roles")

    @cached_property
    def membership(self) -> LtiMembership:
        issuer = self.get_claim("iss")
        client_id = self.get_claim("aud")
        sub = self.get_claim("sub")
        context_id = self.context_claim["id"] if self.context_claim is not None else ""
        return LtiMembership.objects.get(
            user__registration__issuer=issuer,
            user__registration__client_id=client_id,
            user__sub=sub,
            context__id_on_platform=context_id,
        )

    @property
    def resource_link_claim(self):
        return self.get_claim("https://purl.imsglobal.org/spec/lti/claim/resource_link")

    @cached_property
    def resource_link(self) -> LtiResourceLink:
        context_id = self.context_claim["id"] if self.context_claim is not None else ""
        return LtiResourceLink.objects.get(
            context__deployment=self.deployment,
            context__id_on_platform=context_id,
            id_on_platform=self.resource_link_claim["id"],
        )

    @property
    def platform_instance_claim(self):
        return self.get_claim("https://purl.imsglobal.org/spec/lti/claim/tool_platform")

    @cached_property
    def platform_instance(self) -> LtiPlatformInstance:
        if self.platform_instance_claim is None:
            return None
        return LtiPlatformInstance.objects.get(
            issuer=self.get_claim("iss"), guid=self.platform_instance_claim["guid"]
        )

    @property
    def launch_presentation_claim(self):
        return self.get_claim(
            "https://purl.imsglobal.org/spec/lti/claim/launch_presentation"
        )

    @property
    def document_target(self) -> Optional[str]:
        """The kind of browser window or frame in which the launch is presented.

        See https://www.imsglobal.org/spec/lti/v1p3/#launch-presentation-claim"""
        if self.launch_presentation_claim is None:
            return None
        return self.launch_presentation_claim.get("document_target")

    @property
    def dimensions(self) -> Optional[Tuple[int, int]]:
        """Width and height of the window or frame in which the launch is presented.

        See https://www.imsglobal.org/spec/lti/v1p3/#launch-presentation-claim"""
        if self.launch_presentation_claim is None:
            return None
        dimensions = (
            self.launch_presentation_claim.get("width"),
            self.launch_presentation_claim.get("height"),
        )
        return dimensions if None not in dimensions else None

    def get_return_url(
        self,
        *,
        lti_errormsg: str = "",
        lti_msg: str = "",
        lti_errorlog: str = "",
        lti_log: str = "",
    ) -> Optional[str]:
        """Constructs a return URL, when supported by the launch."""
        if self.launch_presentation_claim is None:
            return None
        return_url = self.launch_presentation_claim.get("return_url")
        if return_url is None:
            return None
        url_parts = parse.urlsplit(return_url)
        query = dict(
            parse.parse_qsl(url_parts.query)
            + [
                ("lti_errormsg", lti_errormsg),
                ("lti_msg", lti_msg),
                ("lti_errorlog", lti_errorlog),
                ("lti_log", lti_log),
            ]
        )
        return parse.urlunsplit(
            (
                url_parts.scheme,
                url_parts.netloc,
                url_parts.path,
                parse.urlencode([param for param in query.items() if param[1]]),
                url_parts.fragment,
            )
        )

    def deep_link_response(self, resources: List[DeepLinkResource]) -> HttpResponse:
        """Creates a deep linking response for this launch."""
        html = self.get_message_launch().get_deep_link().output_response_form(resources)
        return HttpResponse(html)

    def get_custom_claim(self, claim: str) -> Optional[str]:
        """Returns a custom claim value, or None if not present."""
        custom_claims = self.get_claim(
            "https://purl.imsglobal.org/spec/lti/claim/custom"
        )
        return custom_claims.get(claim) if custom_claims is not None else None


class AbsentLtiLaunch:
    """Placeholder for non-LTI launch contexts."""

    @property
    def is_present(self) -> bool:
        return False

    @property
    def is_absent(self) -> bool:
        return True
