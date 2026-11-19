from types import SimpleNamespace
from unittest import mock

from django.core.cache import caches
from django.db import connection
from django.test.utils import CaptureQueriesContext

import pytest

from lti_tool.factories import EmbedDomainFactory, LtiRegistrationFactory
from lti_tool.models import Key

csp = pytest.importorskip("django.utils.csp")
CSP = csp.CSP
build_policy = csp.build_policy

PATCH_TARGET = "lti_tool.middleware.get_launch_from_request"
DOMAIN = "lms.example.edu"
OTHER_DOMAIN = "other.example.edu"


@pytest.fixture(autouse=True)
def clear_caches():
    """Clears caches so cached domains don't leak between tests.

    Registration ids repeat across tests, so stale cache entries would otherwise
    be served to a different registration.
    """
    for cache in caches.all(initialized_only=True):
        cache.clear()
    yield
    for cache in caches.all(initialized_only=True):
        cache.clear()


@pytest.fixture
def registration():
    """A registration that may be embedded in DOMAIN."""
    return EmbedDomainFactory(domain=DOMAIN).registration


@pytest.fixture
def bare_registration():
    """A registration with no embed domains."""
    return LtiRegistrationFactory()


@pytest.fixture
def extra_domain(registration):
    """A second embed domain for the registration."""
    return EmbedDomainFactory(registration=registration, domain=OTHER_DOMAIN)


@pytest.fixture
def key():
    """An LTI tool key, needed to build a registration for OIDC initiation."""
    return Key.objects.generate()


@pytest.fixture
def launch_for():
    """Makes LtiLaunchMiddleware resolve a launch for the given registration.

    The embed middleware only reads `lti_launch.registration`, so a stand-in
    launch is enough.
    """
    with mock.patch(PATCH_TARGET) as get_launch_from_request:

        def _launch_for(registration):
            get_launch_from_request.return_value = SimpleNamespace(
                registration=registration
            )

        yield _launch_for


def get_frame_ancestors(response, header=CSP.HEADER_ENFORCE):
    """Returns the sources in a response's frame-ancestors directive, if any."""
    for directive in response[header].split("; "):
        name, _, sources = directive.partition(" ")
        if name == "frame-ancestors":
            return sources.split()
    return None


def oidc_params(registration):
    """Returns OIDC initiation parameters for a registration."""
    return {
        "iss": registration.issuer,
        "client_id": registration.client_id,
        "login_hint": "login-hint",
        "target_link_uri": "https://tool.example.edu/launch/",
        "lti_message_hint": "message-hint",
    }


def count_embed_domain_queries(captured):
    """Counts the queries made against the embed domain table."""
    return sum("lti_tool_embeddomain" in q["sql"] for q in captured.captured_queries)


@pytest.mark.django_db(transaction=True)
@pytest.mark.urls("tests.urls")
class TestLtiEmbedMiddleware:
    """Tests for LtiEmbedMiddleware."""

    CSP_OVERRIDE_VIEW_POLICY = build_policy(
        {"default-src": ["'self'", "cdn.example.com"]}
    )

    def test_no_embed_absent_lti(self, client, settings):
        response = client.get("/page/")
        assert response.status_code == 200
        assert response[CSP.HEADER_ENFORCE] == build_policy(settings.SECURE_CSP)

    @pytest.mark.asyncio
    async def test_no_embed_absent_lti_async(self, async_client, settings):
        response = await async_client.get("/async_page/")
        assert response.status_code == 200
        assert response[CSP.HEADER_ENFORCE] == build_policy(settings.SECURE_CSP)

    def test_lti_allows_embed(self, client, registration, launch_for):
        launch_for(registration)
        response = client.get("/page/")
        assert response.status_code == 200
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]

    @pytest.mark.asyncio
    async def test_lti_allows_embed_async(self, async_client, registration, launch_for):
        launch_for(registration)
        response = await async_client.get("/async_page/")
        assert response.status_code == 200
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]

    def test_multiple_domains(self, client, registration, extra_domain, launch_for):
        launch_for(registration)
        response = client.get("/page/")
        assert get_frame_ancestors(response) == ["'self'", DOMAIN, OTHER_DOMAIN]

    @pytest.mark.asyncio
    async def test_multiple_domains_async(
        self, async_client, registration, extra_domain, launch_for
    ):
        launch_for(registration)
        response = await async_client.get("/async_page/")
        assert get_frame_ancestors(response) == ["'self'", DOMAIN, OTHER_DOMAIN]

    def test_respects_existing_csp_override(self, client, registration, launch_for):
        launch_for(registration)
        response = client.get("/csp_override/")
        assert response.status_code == 200
        assert response[CSP.HEADER_ENFORCE] == self.CSP_OVERRIDE_VIEW_POLICY
        assert DOMAIN not in response[CSP.HEADER_ENFORCE]

    @pytest.mark.asyncio
    async def test_respects_existing_csp_override_async(
        self, async_client, registration, launch_for
    ):
        launch_for(registration)
        response = await async_client.get("/async_csp_override/")
        assert response.status_code == 200
        assert response[CSP.HEADER_ENFORCE] == self.CSP_OVERRIDE_VIEW_POLICY
        assert DOMAIN not in response[CSP.HEADER_ENFORCE]

    def test_no_domains_leaves_response_alone(
        self, client, settings, bare_registration, launch_for
    ):
        launch_for(bare_registration)
        response = client.get("/page/")
        assert response.status_code == 200
        assert response[CSP.HEADER_ENFORCE] == build_policy(settings.SECURE_CSP)

    @pytest.mark.asyncio
    async def test_no_domains_leaves_response_alone_async(
        self, async_client, settings, bare_registration, launch_for
    ):
        launch_for(bare_registration)
        response = await async_client.get("/async_page/")
        assert response.status_code == 200
        assert response[CSP.HEADER_ENFORCE] == build_policy(settings.SECURE_CSP)

    @pytest.mark.parametrize(
        ("csp_extra", "expected"),
        [
            pytest.param({}, [DOMAIN], id="missing"),
            pytest.param({"frame-ancestors": None}, [DOMAIN], id="none-value"),
            pytest.param(
                {"frame-ancestors": "'self'"}, ["'self'", DOMAIN], id="string"
            ),
            pytest.param(
                {"frame-ancestors": ["'self'", "https://other.example.edu"]},
                ["'self'", "https://other.example.edu", DOMAIN],
                id="list",
            ),
            pytest.param(
                {"frame-ancestors": ("'self'", "https://other.example.edu")},
                ["'self'", "https://other.example.edu", DOMAIN],
                id="tuple",
            ),
            pytest.param({"frame-ancestors": ["'none'"]}, [DOMAIN], id="none-keyword"),
            pytest.param(
                {"frame-ancestors": ["'None'"]}, [DOMAIN], id="none-keyword-mixed-case"
            ),
            pytest.param(
                {"frame-ancestors": [DOMAIN, "'self'"]},
                ["'self'", DOMAIN],
                id="existing-domain-not-repeated",
            ),
        ],
    )
    def test_merges_frame_ancestors(
        self, client, settings, registration, launch_for, csp_extra, expected
    ):
        settings.SECURE_CSP = {"default-src": ["'self'"], **csp_extra}
        launch_for(registration)
        response = client.get("/page/")
        assert response.status_code == 200
        assert get_frame_ancestors(response) == expected

    def test_report_only_merges_frame_ancestors(
        self, client, settings, registration, launch_for
    ):
        settings.SECURE_CSP_REPORT_ONLY = {"frame-ancestors": ["'self'"]}
        launch_for(registration)
        response = client.get("/page/")
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]
        assert get_frame_ancestors(response, CSP.HEADER_REPORT_ONLY) == [
            "'self'",
            DOMAIN,
        ]

    @pytest.mark.parametrize(
        "report_only",
        [
            pytest.param({"default-src": ["'self'"]}, id="missing"),
            pytest.param(
                {"default-src": ["'self'"], "frame-ancestors": None}, id="none-value"
            ),
        ],
    )
    def test_report_only_without_frame_ancestors_unchanged(
        self, client, settings, registration, launch_for, report_only
    ):
        settings.SECURE_CSP_REPORT_ONLY = report_only
        launch_for(registration)
        response = client.get("/page/")
        assert response[CSP.HEADER_REPORT_ONLY] == build_policy(report_only)

    def test_no_report_only_header_by_default(self, client, registration, launch_for):
        launch_for(registration)
        response = client.get("/page/")
        assert CSP.HEADER_REPORT_ONLY not in response

    @pytest.mark.parametrize(
        "path", ["/csp_report_only_override/", "/async_csp_report_only_override/"]
    )
    def test_respects_report_only_override(
        self, client, settings, registration, launch_for, path
    ):
        settings.SECURE_CSP_REPORT_ONLY = {"frame-ancestors": ["'self'"]}
        launch_for(registration)
        response = client.get(path)
        assert response[CSP.HEADER_REPORT_ONLY] == self.CSP_OVERRIDE_VIEW_POLICY
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]

    def test_launch_set_during_view_allows_embed(self, client, registration):
        response = client.get("/launch_page/", {"registration_id": registration.id})
        assert response.status_code == 200
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]

    @pytest.mark.asyncio
    async def test_launch_set_during_view_allows_embed_async(
        self, async_client, registration
    ):
        response = await async_client.get(
            "/async_launch_page/", {"registration_id": registration.id}
        )
        assert response.status_code == 200
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]

    @pytest.mark.parametrize("by_uuid", [True, False], ids=["uuid", "client-id"])
    def test_oidc_init_allows_embed(self, client, key, registration, by_uuid):
        path = f"/init/{registration.uuid}/" if by_uuid else "/init/"
        response = client.get(path, oidc_params(registration))
        assert response.status_code == 200
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]

    @pytest.mark.asyncio
    async def test_oidc_init_allows_embed_async(self, async_client, key, registration):
        response = await async_client.get("/init/", oidc_params(registration))
        assert response.status_code == 200
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]

    @pytest.mark.parametrize("case", ["unknown-issuer", "inactive"])
    def test_oidc_init_without_active_registration(self, client, key, case):
        registration = LtiRegistrationFactory(is_active=case != "inactive")
        EmbedDomainFactory(registration=registration, domain=DOMAIN)
        params = oidc_params(registration)
        if case == "unknown-issuer":
            params["iss"] = "https://unknown.example.edu"
        response = client.get("/init/", params)
        assert response.status_code == 200
        assert get_frame_ancestors(response) == ["'self'"]

    def test_caches_domains(self, client, registration, launch_for):
        launch_for(registration)
        with CaptureQueriesContext(connection) as first:
            client.get("/page/")
        with CaptureQueriesContext(connection) as second:
            client.get("/page/")
        assert count_embed_domain_queries(first) == 1
        assert count_embed_domain_queries(second) == 0

    def test_new_domain_replaces_cached_domains(
        self, client, bare_registration, launch_for
    ):
        launch_for(bare_registration)
        assert get_frame_ancestors(client.get("/page/")) == ["'self'"]
        EmbedDomainFactory(registration=bare_registration, domain=DOMAIN)
        response = client.get("/page/")
        assert get_frame_ancestors(response) == ["'self'", DOMAIN]
