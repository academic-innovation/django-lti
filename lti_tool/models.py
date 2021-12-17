import json
from uuid import uuid4

from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from jwcrypto.jwk import JWK


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
