import factory

from . import models


class LtiRegistrationFactory(factory.django.DjangoModelFactory):
    """Factory for LtiRegistration objects."""

    name = factory.Faker("company")
    issuer = factory.Faker("url")
    client_id = factory.Faker("pystr")
    auth_url = factory.Faker("uri")
    token_url = factory.Faker("uri")
    keyset_url = factory.Faker("uri")

    class Meta:
        model = models.LtiRegistration


class LtiPlatformInstanceFactory(factory.django.DjangoModelFactory):
    """Factory for LtiPlatformInstance objects."""

    issuer = factory.Faker("url")
    guid = factory.Faker("pystr")
    contact_email = factory.Faker("email")
    description = factory.Faker("text")
    name = factory.Faker("company")
    url = factory.Faker("uri")
    product_family_code = factory.Faker("word")
    version = factory.Faker("word")

    class Meta:
        model = models.LtiPlatformInstance


class LtiDeploymentFactory(factory.django.DjangoModelFactory):
    """Factory for LtiDeployment objects."""

    registration = factory.SubFactory(LtiRegistrationFactory)
    deployment_id = factory.Faker("pystr")
    platform_instance = factory.SubFactory(
        LtiPlatformInstanceFactory,
        issuer=factory.SelfAttribute("..registration.issuer"),
    )

    class Meta:
        model = models.LtiDeployment


class LtiUserFactory(factory.django.DjangoModelFactory):
    """Factory for LtiUser objects."""

    registration = factory.SubFactory(LtiRegistrationFactory)
    sub = factory.Faker("pystr")
    given_name = factory.Faker("first_name")
    family_name = factory.Faker("last_name")
    name = factory.LazyAttribute(lambda o: f"{o.given_name} {o.family_name}")
    email = factory.Faker("email")
    picture_url = factory.Faker("uri")

    class Meta:
        model = models.LtiUser


class LtiContextFactory(factory.django.DjangoModelFactory):
    """Factory for LtiContext objects."""

    deployment = factory.SubFactory(LtiDeploymentFactory)
    id_on_platform = factory.Faker("pystr")
    label = factory.Faker("word")
    title = factory.Faker("catch_phrase")
    memberships_url = factory.Faker("uri")

    class Meta:
        model = models.LtiContext


class LtiMembershipFactory(factory.django.DjangoModelFactory):
    """Factory for LtiMembership objects."""

    context = factory.SubFactory(LtiContextFactory)
    user = factory.SubFactory(
        LtiUserFactory,
        registration=factory.SelfAttribute("..context.deployment.registration"),
    )

    class Meta:
        model = models.LtiMembership


class LtiResourceLinkFactory(factory.django.DjangoModelFactory):
    """Factory for LtiResourceLink objects."""

    context = factory.SubFactory(LtiContextFactory)
    id_on_platform = factory.Faker("pystr")
    title = factory.Faker("catch_phrase")
    description = factory.Faker("sentence")

    class Meta:
        model = models.LtiResourceLink
