import pytest

from lti_tool import factories, models


@pytest.mark.django_db
class TestLtiRegistrationQuerySet:
    """Tests for LtiRegistrationQuerySet."""

    def test_active(self):
        factories.LtiRegistrationFactory.create_batch(2)
        inactive_registration = factories.LtiRegistrationFactory(is_active=False)
        active_registrations = models.LtiRegistration.objects.active()
        assert inactive_registration not in active_registrations
        assert len(active_registrations) == 2


@pytest.mark.django_db
class TestLtiRegistration:
    """Tests for the LtiRegistration model."""

    def test_str(self):
        registration = factories.LtiRegistrationFactory(name="LTI Registration")
        assert str(registration) == "LTI Registration"


@pytest.mark.django_db
class TestLtiDeploymentQuerySet:
    """Tests for LtiDeploymentQuerySet."""

    def test_active(self):
        factories.LtiDeploymentFactory.create_batch(2, is_active=True)
        inactive_deployment = factories.LtiDeploymentFactory()
        active_deployments = models.LtiDeployment.objects.active()
        assert inactive_deployment not in active_deployments
        assert len(active_deployments) == 2


@pytest.mark.django_db
class TestLtiDeployment:
    """Tests for the LtiDeployment model."""

    def test_str(self):
        deployment = factories.LtiDeploymentFactory(
            registration__name="Registration", deployment_id="a-deployment-id"
        )
        assert str(deployment) == "Registration: a-deployment-id"
