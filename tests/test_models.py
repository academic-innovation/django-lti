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


@pytest.mark.django_db
class TestLtiPlatformInstance:
    """Tests for the LtiPlatformInstance model."""

    @pytest.mark.parametrize(
        ("guid", "name", "result"), [("guid", "Name", "Name"), ("guid", "", "guid")]
    )
    def test_str(self, guid, name, result):
        platform_instance = factories.LtiPlatformInstanceFactory(name=name, guid=guid)
        assert str(platform_instance) == result


@pytest.mark.django_db
class TestLtiUser:
    """Tests for the LtiUser model."""

    def test_str(self):
        user = factories.LtiUserFactory(sub="abc123")
        assert str(user) == "abc123"


@pytest.mark.django_db
class TestLtiContext:
    """Tests for the LtiContext model."""

    @pytest.mark.parametrize(
        ("id", "title", "result"),
        [("abc123", "Title", "Title"), ("abc123", "", "abc123")],
    )
    def test_str(self, id, title, result):
        context = factories.LtiContextFactory(id_on_platform=id, title=title)
        assert str(context) == result


@pytest.mark.django_db
class TestLtiMembership:
    """Tests for the LtiMembership model."""

    def test_str(self):
        membership = factories.LtiMembershipFactory(
            user__sub="user1234", context__title="Math"
        )
        assert str(membership) == "user1234 in Math"


@pytest.mark.django_db
class TestLtiResourceLink:
    """Tests for the LtiResourceLink model."""

    @pytest.mark.parametrize(
        ("id", "title", "result"),
        [("abc123", "Title", "Title"), ("abc123", "", "abc123")],
    )
    def test_str(self, id, title, result):
        resource_link = factories.LtiResourceLinkFactory(id_on_platform=id, title=title)
        assert str(resource_link) == result
