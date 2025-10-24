import pytest

from lti_tool import factories, models, utils
from lti_tool.lti_core.utils import compute_oauth_consumer_key_sign


@pytest.mark.django_db
class TestSyncUserFromLaunch:
    """Tests for utils.sync_user_from_launch."""

    def test_sync_new_user(self, monkeypatch):
        launch_data = {
            "sub": "abc123",
            "given_name": "First",
            "family_name": "Last",
            "name": "First Last",
            "email": "first.last@example.com",
            "picture": "https://example.com/picture.jpg",
        }
        registration = factories.LtiRegistrationFactory()
        monkeypatch.setattr(
            models.LtiLaunch, "get_launch_data", lambda self: launch_data
        )
        monkeypatch.setattr(models.LtiLaunch, "registration", registration)
        lti_launch = models.LtiLaunch(None)
        user = utils.sync_user_from_launch(lti_launch)
        assert user.sub == "abc123"
        assert user.given_name == "First"
        assert user.family_name == "Last"
        assert user.name == "First Last"
        assert user.email == "first.last@example.com"
        assert user.picture_url == "https://example.com/picture.jpg"

    def test_sync_existing_user(self, monkeypatch):
        registration = factories.LtiRegistrationFactory()
        factories.LtiUserFactory(registration=registration, sub="abc123")
        launch_data = {
            "sub": "abc123",
            "given_name": "First",
            "family_name": "Last",
            "name": "First Last",
            "email": "first.last@example.com",
            "picture": "https://example.com/picture.jpg",
        }
        monkeypatch.setattr(
            models.LtiLaunch, "get_launch_data", lambda self: launch_data
        )
        monkeypatch.setattr(models.LtiLaunch, "registration", registration)
        lti_launch = models.LtiLaunch(None)
        user = utils.sync_user_from_launch(lti_launch)
        assert models.LtiUser.objects.count() == 1
        assert user.sub == "abc123"
        assert user.given_name == "First"
        assert user.family_name == "Last"
        assert user.name == "First Last"
        assert user.email == "first.last@example.com"
        assert user.picture_url == "https://example.com/picture.jpg"

    @pytest.mark.parametrize("user_id_present", [True, False])
    def test_sync_user_with_migration(self, monkeypatch, user_id_present):
        migration_claim = {"oauth_consumer_key": "179248902"}
        if user_id_present:
            migration_claim["user_id"] = "lti1p1"
        migration_claim["oauth_consumer_key_sign"] = compute_oauth_consumer_key_sign(
            "179248902",
            "689302",
            "https://lmsvendor.com",
            "PM48OJSfGDTAzAo",
            1551290856,
            "172we8671fd8z",
            "oauth_secret",
        )
        launch_data = {
            "nonce": "172we8671fd8z",
            "iat": 1551290796,
            "exp": 1551290856,
            "iss": "https://lmsvendor.com",
            "aud": "PM48OJSfGDTAzAo",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "689302",
            "sub": "abc123",
            "https://purl.imsglobal.org/spec/lti/claim/lti1p1": migration_claim,
        }
        registration = factories.LtiRegistrationFactory()
        monkeypatch.setattr(
            models.LtiLaunch, "get_launch_data", lambda self: launch_data
        )
        monkeypatch.setattr(models.LtiLaunch, "registration", registration)
        lti_launch = models.LtiLaunch(None)
        user = utils.sync_user_from_launch(lti_launch, "oauth_secret")
        assert user.sub == "abc123"
        assert user.lti1p1_id_on_platform == "lti1p1" if user_id_present else "abc123"


@pytest.mark.django_db
class TestSyncContextFromLaunch:
    """Tests for utils.sync_context_from_launch."""

    def test_sync_empty_context(self, monkeypatch):
        context_claim = None
        deployment = factories.LtiDeploymentFactory()
        monkeypatch.setattr(models.LtiLaunch, "context_claim", context_claim)
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        context = utils.sync_context_from_launch(lti_launch)
        assert context.id_on_platform == ""

    def test_sync_new_context(self, monkeypatch):
        context_claim = {
            "id": "a-context-id",
            "title": "A Context Title",
            "label": "CTX101",
            "type": ["http://purl.imsglobal.org/vocab/lis/v2/course#CourseOffering"],
        }
        deployment = factories.LtiDeploymentFactory()
        monkeypatch.setattr(models.LtiLaunch, "context_claim", context_claim)
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        context = utils.sync_context_from_launch(lti_launch)
        assert context.id_on_platform == "a-context-id"
        assert context.label == "CTX101"
        assert context.title == "A Context Title"
        assert context.is_course_offering

    def test_sync_new_context_with_ags(self, monkeypatch):
        context_claim = {"id": "a-context-id"}
        ags_claim = {
            "scope": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            ],
            "lineitems": "https://www.example.com/2344/lineitems/",
            "lineitem": "https://www.example.com/2344/lineitems/1234/lineitem",
        }
        deployment = factories.LtiDeploymentFactory()
        monkeypatch.setattr(models.LtiLaunch, "context_claim", context_claim)
        monkeypatch.setattr(models.LtiLaunch, "ags_claim", ags_claim)
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        context = utils.sync_context_from_launch(lti_launch)
        assert context.id_on_platform == "a-context-id"
        assert context.lineitems_url == "https://www.example.com/2344/lineitems/"
        assert not context.can_query_lineitems
        assert context.can_manage_lineitems
        assert context.can_publish_scores
        assert context.can_access_results

    def test_sync_existing_context(self, monkeypatch):
        deployment = factories.LtiDeploymentFactory()
        factories.LtiContextFactory(
            deployment=deployment, id_on_platform="ctx-1", is_group=True
        )
        new_context_claim = {
            "id": "ctx-1",
            "title": "New Context Title",
            "label": "CTX101",
            "type": ["http://purl.imsglobal.org/vocab/lis/v2/course#CourseOffering"],
        }
        monkeypatch.setattr(models.LtiLaunch, "context_claim", new_context_claim)
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        updated_context = utils.sync_context_from_launch(lti_launch)
        assert models.LtiContext.objects.count() == 1
        assert updated_context.title == "New Context Title"
        assert updated_context.label == "CTX101"
        assert not updated_context.is_group
        assert updated_context.is_course_offering

    @pytest.mark.parametrize("context_id_present", [True, False])
    def test_sync_context_with_migration(self, monkeypatch, context_id_present):
        context_claim = {"id": "c1p3"}
        deployment = factories.LtiDeploymentFactory()
        migration_claim = {"oauth_consumer_key": "179248902"}
        if context_id_present:
            migration_claim["context_id"] = "c1p1"
        migration_claim["oauth_consumer_key_sign"] = compute_oauth_consumer_key_sign(
            "179248902",
            deployment.deployment_id,
            "https://lmsvendor.com",
            "PM48OJSfGDTAzAo",
            1551290856,
            "172we8671fd8z",
            "oauth_secret",
        )
        launch_data = {
            "nonce": "172we8671fd8z",
            "iat": 1551290796,
            "exp": 1551290856,
            "iss": "https://lmsvendor.com",
            "aud": "PM48OJSfGDTAzAo",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": (
                deployment.deployment_id
            ),
            "https://purl.imsglobal.org/spec/lti/claim/context": context_claim,
            "sub": "abc123",
            "https://purl.imsglobal.org/spec/lti/claim/lti1p1": migration_claim,
        }
        monkeypatch.setattr(
            models.LtiLaunch, "get_launch_data", lambda self: launch_data
        )
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        context = utils.sync_context_from_launch(lti_launch, "oauth_secret")
        assert context.id_on_platform == "c1p3"
        assert context.lti1p1_id_on_platform == "c1p1" if context_id_present else "c1p3"


@pytest.mark.django_db
class TestSyncMembershipFromLaunch:
    """Tests for utils.sync_membership_from_launch."""

    def test_sync_new_membership(self, monkeypatch):
        user = factories.LtiUserFactory()
        context = factories.LtiContextFactory(
            deployment__registration=user.registration
        )
        roles_claim = ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"]
        monkeypatch.setattr(models.LtiLaunch, "roles_claim", roles_claim)
        lti_launch = models.LtiLaunch(None)
        membership = utils.sync_membership_from_launch(lti_launch, user, context)
        assert membership.user == user
        assert membership.context == context
        assert membership.is_learner
        assert not membership.is_administrator
        assert not membership.is_content_developer
        assert not membership.is_instructor
        assert not membership.is_mentor

    def test_sync_existing_membership(self, monkeypatch):
        membership = factories.LtiMembershipFactory(is_content_developer=True)
        roles_claim = ["http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"]
        monkeypatch.setattr(models.LtiLaunch, "roles_claim", roles_claim)
        lti_launch = models.LtiLaunch(None)
        updated_membership = utils.sync_membership_from_launch(
            lti_launch, membership.user, membership.context
        )
        assert models.LtiMembership.objects.count() == 1
        assert updated_membership.is_content_developer
        assert updated_membership.is_instructor


@pytest.mark.django_db
class TestSyncResourceLinkFromLaunch:
    """Tests for utils.sync_resource_link_from_launch."""

    @pytest.mark.parametrize(
        ["claim_title", "claim_description", "title", "description"],
        [("Title", "Description", "Title", "Description"), (None, None, "", "")],
    )
    def test_sync_new_resource_link(
        self, monkeypatch, claim_title, claim_description, title, description
    ):
        context = factories.LtiContextFactory()
        resource_link_claim = {
            "id": "resource-link-id",
            "title": claim_title,
            "description": claim_description,
        }
        monkeypatch.setattr(
            models.LtiLaunch, "resource_link_claim", resource_link_claim
        )
        lti_launch = models.LtiLaunch(None)
        resource_link = utils.sync_resource_link_from_launch(lti_launch, context)
        assert resource_link.id_on_platform == "resource-link-id"
        assert resource_link.title == title
        assert resource_link.description == description

    @pytest.mark.parametrize(
        ["claim_title", "claim_description", "title", "description"],
        [("Title", "Description", "Title", "Description"), (None, None, "", "")],
    )
    def test_sync_existing_resource_link(
        self, monkeypatch, claim_title, claim_description, title, description
    ):
        context = factories.LtiContextFactory()
        resource_link = factories.LtiResourceLinkFactory(context=context)
        resource_link_claim = {
            "id": resource_link.id_on_platform,
            "title": claim_title,
            "description": claim_description,
        }
        monkeypatch.setattr(
            models.LtiLaunch, "resource_link_claim", resource_link_claim
        )
        lti_launch = models.LtiLaunch(None)
        resource_link = utils.sync_resource_link_from_launch(lti_launch, context)
        assert models.LtiResourceLink.objects.count() == 1
        assert resource_link.title == title
        assert resource_link.description == description

    @pytest.mark.parametrize("resource_link_id_present", (True, False))
    def test_sync_resource_link_with_migration(
        self, monkeypatch, resource_link_id_present
    ):
        context = factories.LtiContextFactory()
        resource_link_claim = {
            "id": "rl1p3",
        }
        migration_claim = {"oauth_consumer_key": "179248902"}
        if resource_link_id_present:
            migration_claim["resource_link_id"] = "rl1p1"
        migration_claim["oauth_consumer_key_sign"] = compute_oauth_consumer_key_sign(
            "179248902",
            "deployment",
            "https://lmsvendor.com",
            "PM48OJSfGDTAzAo",
            1551290856,
            "172we8671fd8z",
            "oauth_secret",
        )
        launch_data = {
            "nonce": "172we8671fd8z",
            "iat": 1551290796,
            "exp": 1551290856,
            "iss": "https://lmsvendor.com",
            "aud": "PM48OJSfGDTAzAo",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "deployment",
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": (
                resource_link_claim
            ),
            "sub": "abc123",
            "https://purl.imsglobal.org/spec/lti/claim/lti1p1": migration_claim,
        }
        monkeypatch.setattr(
            models.LtiLaunch, "get_launch_data", lambda self: launch_data
        )
        lti_launch = models.LtiLaunch(None)
        resource_link = utils.sync_resource_link_from_launch(
            lti_launch, context, "oauth_secret"
        )
        assert resource_link.id_on_platform == "rl1p3"
        assert (
            resource_link.lti1p1_id_on_platform == "rl1p1"
            if resource_link_id_present
            else "rl1p3"
        )


@pytest.mark.django_db
class TestSyncPlatformInstanceFromLaunch:
    """Tests for utils.sync_platform_instance_from_launch."""

    def test_no_platform_claim(self, monkeypatch):
        deployment = factories.LtiDeploymentFactory()
        issuer = deployment.registration.issuer
        launch_data = {
            "iss": issuer,
        }
        monkeypatch.setattr(models.LtiLaunch, "get_launch_data", lambda s: launch_data)
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        platform_instance = utils.sync_platform_instance_from_launch(lti_launch)
        assert platform_instance is None

    def test_sync_new_platform_instance(self, monkeypatch):
        deployment = factories.LtiDeploymentFactory(platform_instance=None)
        issuer = deployment.registration.issuer
        launch_data = {
            "iss": issuer,
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform": {
                "guid": "guid",
                "contact_email": "email@example.com",
                "description": "Description",
                "name": "Name",
                "url": "https://www.example.com",
                "product_family_code": "example",
                "version": "1.0",
            },
        }
        monkeypatch.setattr(models.LtiLaunch, "get_launch_data", lambda s: launch_data)
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        platform_instance = utils.sync_platform_instance_from_launch(lti_launch)
        assert platform_instance.issuer == issuer
        assert platform_instance.guid == "guid"
        assert platform_instance.contact_email == "email@example.com"
        assert platform_instance.description == "Description"
        assert platform_instance.name == "Name"
        assert platform_instance.url == "https://www.example.com"
        assert platform_instance.product_family_code == "example"
        assert platform_instance.version == "1.0"
        assert platform_instance.deployments.first() == deployment

    def test_sync_existing_platform_instance(self, monkeypatch):
        deployment = factories.LtiDeploymentFactory()
        platform_instance = deployment.platform_instance
        launch_data = {
            "iss": platform_instance.issuer,
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform": {
                "guid": platform_instance.guid,
                "contact_email": "email@example.com",
                "description": "Description",
                "name": "Name",
                "url": "https://www.example.com",
                "product_family_code": "example",
                "version": "1.0",
            },
        }
        monkeypatch.setattr(models.LtiLaunch, "get_launch_data", lambda s: launch_data)
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        updated_platform_instance = utils.sync_platform_instance_from_launch(lti_launch)
        assert models.LtiPlatformInstance.objects.count() == 1
        assert updated_platform_instance.guid == platform_instance.guid
        assert updated_platform_instance.contact_email == "email@example.com"
        assert updated_platform_instance.description == "Description"
        assert updated_platform_instance.name == "Name"
        assert updated_platform_instance.url == "https://www.example.com"
        assert updated_platform_instance.product_family_code == "example"
        assert updated_platform_instance.version == "1.0"
        assert updated_platform_instance.deployments.first() == deployment

    @pytest.mark.parametrize("platform_instance_id_present", (True, False))
    def test_sync_platform_instance_with_migration(
        self, monkeypatch, platform_instance_id_present
    ):
        deployment = factories.LtiDeploymentFactory(platform_instance=None)
        issuer = deployment.registration.issuer
        migration_claim = {"oauth_consumer_key": "179248902"}
        if platform_instance_id_present:
            migration_claim["tool_consumer_instance_guid"] = "pi1p1"
        migration_claim["oauth_consumer_key_sign"] = compute_oauth_consumer_key_sign(
            "179248902",
            deployment.deployment_id,
            issuer,
            "PM48OJSfGDTAzAo",
            1551290856,
            "172we8671fd8z",
            "oauth_secret",
        )
        launch_data = {
            "iss": issuer,
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform": {
                "guid": "pi1p3"
            },
            "nonce": "172we8671fd8z",
            "iat": 1551290796,
            "exp": 1551290856,
            "aud": "PM48OJSfGDTAzAo",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": (
                deployment.deployment_id
            ),
            "sub": "abc123",
            "https://purl.imsglobal.org/spec/lti/claim/lti1p1": migration_claim,
        }
        monkeypatch.setattr(models.LtiLaunch, "get_launch_data", lambda s: launch_data)
        monkeypatch.setattr(models.LtiLaunch, "deployment", deployment)
        lti_launch = models.LtiLaunch(None)
        platform_instance = utils.sync_platform_instance_from_launch(
            lti_launch, "oauth_secret"
        )
        assert platform_instance.guid == "pi1p3"
        assert (
            platform_instance.lti1p1_id_on_platform == "pi1p1"
            if platform_instance_id_present
            else "pi1p3"
        )


@pytest.mark.django_db
class TestDjangoToolConfig:
    """Tests for utils.DjangoToolConfig."""

    @pytest.mark.parametrize("is_known_deployment", (True, False))
    def test_find_deployment(self, is_known_deployment):
        models.Key.objects.generate()
        registration = factories.LtiRegistrationFactory()
        deployment_id = "a-deployment"
        if is_known_deployment:
            factories.LtiDeploymentFactory(
                registration=registration, deployment_id=deployment_id, is_active=True
            )

        tool_config = utils.DjangoToolConfig(registration_uuid=registration.uuid)
        tool_config.find_registration_by_issuer(registration.issuer)
        deployment = tool_config.find_deployment(registration.issuer, deployment_id)

        assert deployment.get_deployment_id() == deployment_id
        assert tool_config.deployment.deployment_id == deployment_id
        assert tool_config.deployment.is_active == is_known_deployment
        assert models.LtiDeployment.objects.count() == 1

    @pytest.mark.parametrize("is_known_deployment", (True, False))
    def test_find_deployment_by_params(self, is_known_deployment):
        models.Key.objects.generate()
        registration = factories.LtiRegistrationFactory()
        deployment_id = "a-deployment"
        if is_known_deployment:
            factories.LtiDeploymentFactory(
                registration=registration, deployment_id=deployment_id, is_active=True
            )

        tool_config = utils.DjangoToolConfig()
        tool_config.find_registration_by_params(
            registration.issuer, registration.client_id
        )
        deployment = tool_config.find_deployment_by_params(
            registration.issuer, deployment_id, registration.client_id
        )

        assert deployment.get_deployment_id() == deployment_id
        assert tool_config.deployment.deployment_id == deployment_id
        assert tool_config.deployment.is_active == is_known_deployment
        assert models.LtiDeployment.objects.count() == 1
