from unittest import mock

from django.test import RequestFactory

import pytest
from pylti1p3.exception import LtiException

from lti_tool.constants import SESSION_KEY
from lti_tool.middleware import LtiLaunchMiddleware
from lti_tool.models import AbsentLtiLaunch

PATCH_TARGET = "lti_tool.middleware.get_launch_from_request"


class FakeSession(dict):
    """A minimal session supporting both sync and async access."""

    async def aget(self, key, default=None):
        return self.get(key, default)


class TestLtiLaunchMiddleware:
    """Tests for the LtiLaunchMiddleware."""

    @staticmethod
    def make_request(launch_id=None):
        request = RequestFactory().get("/")
        request.session = FakeSession()  # type: ignore[attr-defined]
        if launch_id is not None:
            request.session[SESSION_KEY] = launch_id
        return request

    def test_sync_launch_present(self):
        launch = object()
        request = self.make_request(launch_id="launch-id")
        get_response = mock.Mock(return_value="response")

        with mock.patch(PATCH_TARGET, return_value=launch) as get_launch:
            response = LtiLaunchMiddleware(get_response)(request)

        assert response == "response"
        assert request.lti_launch is launch
        get_launch.assert_called_once_with(request, "launch-id")
        get_response.assert_called_once_with(request)

    def test_sync_no_launch_id_in_session(self):
        launch = object()
        request = self.make_request()
        get_response = mock.Mock(return_value="response")

        with mock.patch(PATCH_TARGET, return_value=launch) as get_launch:
            response = LtiLaunchMiddleware(get_response)(request)

        assert response == "response"
        assert request.lti_launch is launch
        get_launch.assert_called_once_with(request, None)

    def test_sync_lti_exception_yields_absent_launch(self):
        request = self.make_request(launch_id="launch-id")
        get_response = mock.Mock(return_value="response")

        with mock.patch(PATCH_TARGET, side_effect=LtiException("bad launch")):
            response = LtiLaunchMiddleware(get_response)(request)

        assert response == "response"
        assert isinstance(request.lti_launch, AbsentLtiLaunch)
        get_response.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_async_launch_present(self):
        launch = object()
        request = self.make_request(launch_id="launch-id")
        get_response = mock.AsyncMock(return_value="response")

        with mock.patch(PATCH_TARGET, return_value=launch) as get_launch:
            response = await LtiLaunchMiddleware(get_response)(request)

        assert response == "response"
        assert request.lti_launch is launch
        get_launch.assert_called_once_with(request, "launch-id")
        get_response.assert_awaited_once_with(request)

    @pytest.mark.asyncio
    async def test_async_no_launch_id_in_session(self):
        launch = object()
        request = self.make_request()
        get_response = mock.AsyncMock(return_value="response")

        with mock.patch(PATCH_TARGET, return_value=launch) as get_launch:
            response = await LtiLaunchMiddleware(get_response)(request)

        assert response == "response"
        assert request.lti_launch is launch
        get_launch.assert_called_once_with(request, None)

    @pytest.mark.asyncio
    async def test_async_lti_exception_yields_absent_launch(self):
        request = self.make_request(launch_id="launch-id")
        get_response = mock.AsyncMock(return_value="response")

        with mock.patch(PATCH_TARGET, side_effect=LtiException("bad launch")):
            response = await LtiLaunchMiddleware(get_response)(request)

        assert response == "response"
        assert isinstance(request.lti_launch, AbsentLtiLaunch)
        get_response.assert_awaited_once_with(request)
