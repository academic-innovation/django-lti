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


class LtiDeploymentFactory(factory.django.DjangoModelFactory):
    """Factory for LtiDeployment objects."""

    registration = factory.SubFactory(LtiRegistrationFactory)
    deployment_id = factory.Faker("pystr")

    class Meta:
        model = models.LtiDeployment
