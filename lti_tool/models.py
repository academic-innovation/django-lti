import json
from typing import Optional, Tuple
from urllib import parse
from uuid import uuid4

from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from jwcrypto.jwk import JWK
from pylti1p3.contrib.django.message_launch import DjangoMessageLaunch


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


class AbsentLtiLaunch:
    """Placeholder for non-LTI launch contexts."""

    @property
    def is_present(self) -> bool:
        return False

    @property
    def is_absent(self) -> bool:
        return True
