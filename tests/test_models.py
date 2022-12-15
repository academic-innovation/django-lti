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
        [("ctx-4444", "", "ctx-4444"), ("ctx-4444", "Title", "Title")],
    )
    def test_str(self, id, title, result):
        context = factories.LtiContextFactory(id_on_platform=id, title=title)
        assert str(context) == result

    def test_update_memberships(self):
        context = factories.LtiContextFactory()
        member_data = [
            {
                "status": "Active",
                "name": "Jane Q. Public",
                "picture": "https://platform.example.edu/jane.jpg",
                "given_name": "Jane",
                "family_name": "Doe",
                "email": "jane@platform.example.edu",
                "user_id": "user_1",
                "roles": ["Instructor"],
            },
            {
                "status": "Inactive",
                "user_id": "user_2",
                "roles": ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"],
            },
        ]
        context.update_memberships(member_data)

        member_1 = models.LtiMembership.objects.get(context=context, user__sub="user_1")
        member_2 = models.LtiMembership.objects.get(context=context, user__sub="user_2")

        assert context.members.count() == 2

        assert not member_1.is_administrator
        assert not member_1.is_content_developer
        assert member_1.is_instructor
        assert not member_1.is_learner
        assert not member_1.is_mentor
        assert member_1.is_active
        assert member_1.user.name == "Jane Q. Public"
        assert member_1.user.given_name == "Jane"
        assert member_1.user.family_name == "Doe"
        assert member_1.user.picture_url == "https://platform.example.edu/jane.jpg"
        assert member_1.user.email == "jane@platform.example.edu"

        assert not member_2.is_administrator
        assert not member_2.is_content_developer
        assert not member_2.is_instructor
        assert member_2.is_learner
        assert not member_2.is_mentor
        assert not member_2.is_active


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


@pytest.mark.django_db
class TestLtiLaunch:
    """Tests for the LtiLaunch object."""

    def test_membership_with_duplicate_context_ids(self, monkeypatch):
        previous_membership = factories.LtiMembershipFactory()
        registration = previous_membership.user.registration
        new_membership = factories.LtiMembershipFactory(
            context__deployment__registration=registration,
            context__id_on_platform=previous_membership.context.id_on_platform,
            user=previous_membership.user,
        )
        new_deployment = new_membership.context.deployment
        launch_data = {
            "iss": registration.issuer,
            "aud": registration.client_id,
            "sub": new_membership.user.sub,
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": (
                new_deployment.deployment_id
            ),
            "https://purl.imsglobal.org/spec/lti/claim/context": {
                "id": new_membership.context.id_on_platform,
            },
        }
        monkeypatch.setattr(
            models.LtiLaunch, "get_launch_data", lambda self: launch_data
        )
        monkeypatch.setattr(models.LtiLaunch, "deployment", new_deployment)
        lti_launch = models.LtiLaunch(None)
        assert lti_launch.membership == new_membership
